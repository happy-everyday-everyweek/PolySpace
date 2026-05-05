import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from app.core.coordination.context.aggregator import (
    ContextAggregator,
    ContextEvent,
    ContextSource,
    get_context_aggregator,
)

logger = logging.getLogger(__name__)


@dataclass
class ScreenContext:
    app_name: str = ""
    activity_name: str = ""
    ocr_text: str = ""
    ui_elements: list[dict] = field(default_factory=list)
    content_hash: str = ""
    is_sensitive: bool = False
    timestamp: float = field(default_factory=time.time)


class ScreenContextHandler:
    def __init__(self, aggregator: Optional[ContextAggregator] = None):
        self._aggregator = aggregator or get_context_aggregator()
        self._last_hash: str = ""
        self._last_app: str = ""
        self._history: list[ScreenContext] = []
        self._max_history = 50
        self._sensitive_apps = {"payment", "banking", "password_manager", "crypto"}

    async def process_screen_data(self, screen_data: dict) -> Optional[ScreenContext]:
        content_hash = screen_data.get("content_hash", "")
        if content_hash and content_hash == self._last_hash:
            return None
        app_name = screen_data.get("app_name", screen_data.get("app", ""))
        is_sensitive = self._is_sensitive_screen(app_name, screen_data)
        if is_sensitive:
            screen_data = self._sanitize(screen_data)
        ctx = ScreenContext(
            app_name=app_name,
            activity_name=screen_data.get("activity_name", ""),
            ocr_text=screen_data.get("ocr_text", ""),
            ui_elements=screen_data.get("ui_elements", []),
            content_hash=content_hash,
            is_sensitive=is_sensitive,
        )
        self._last_hash = content_hash
        self._last_app = app_name
        self._history.append(ctx)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        event = ContextEvent(
            source=ContextSource.SCREEN,
            data={
                "app": app_name,
                "activity": ctx.activity_name,
                "ocr_text": ctx.ocr_text[:500] if ctx.ocr_text else "",
                "content_hash": content_hash,
                "is_sensitive": is_sensitive,
            },
            priority="high" if is_sensitive else "normal",
        )
        await self._aggregator.ingest(event)
        return ctx

    def _is_sensitive_screen(self, app_name: str, data: dict) -> bool:
        app_lower = app_name.lower()
        for sensitive in self._sensitive_apps:
            if sensitive in app_lower:
                return True
        ocr_text = data.get("ocr_text", "").lower()
        sensitive_keywords = ["password", "pin", "cvv", "card number", "ssn"]
        for kw in sensitive_keywords:
            if kw in ocr_text:
                return True
        return False

    def _sanitize(self, data: dict) -> dict:
        data = dict(data)
        data["ocr_text"] = "[REDACTED - sensitive content]"
        data["ui_elements"] = []
        return data

    async def analyze_with_llm(self, screen_context: ScreenContext) -> Optional[dict]:
        if screen_context.is_sensitive or not screen_context.ocr_text:
            return None
        from app.core.llm.dispatcher import TaskCategory, get_model_dispatcher
        dispatcher = get_model_dispatcher()
        prompt = (
            "Analyze the screen content and determine what the user is doing. Return JSON:\n"
            '{"current_task": "description", "next_step_suggestion": "suggestion", '
            '"topic": "main topic", "sentiment": "positive/neutral/negative"}'
        )
        try:
            response = await dispatcher.dispatch(
                TaskCategory.DAILY,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": screen_context.ocr_text[:1000]},
                ],
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Screen LLM analysis failed: {e}")
            return None

    def get_history(self, limit: int = 20) -> list[dict]:
        return [
            {
                "app": ctx.app_name,
                "activity": ctx.activity_name,
                "ocr_text": ctx.ocr_text[:200] if not ctx.is_sensitive else "[REDACTED]",
                "timestamp": ctx.timestamp,
            }
            for ctx in self._history[-limit:]
        ]


_handler: Optional[ScreenContextHandler] = None


def get_screen_handler() -> ScreenContextHandler:
    global _handler
    if _handler is None:
        _handler = ScreenContextHandler()
    return _handler
