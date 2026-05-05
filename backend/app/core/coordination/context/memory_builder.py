import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from app.core.coordination.context.context_window import SlidingContextWindow

logger = logging.getLogger(__name__)


@dataclass
class ActivityMemory:
    memory_id: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    primary_source: str = ""
    primary_activity: str = ""
    title: str = ""
    summary: str = ""
    key_entities: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    raw_context: str = ""
    project_hint: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "primary_source": self.primary_source,
            "primary_activity": self.primary_activity,
            "title": self.title,
            "summary": self.summary,
            "key_entities": self.key_entities,
            "action_items": self.action_items,
            "raw_context": self.raw_context[:500],
            "project_hint": self.project_hint,
            "created_at": self.created_at,
        }


MEMORY_SYSTEM_PROMPT = (
    "You are a memory summarizer for PolySpace. "
    "Given context events from a user's activity window, produce JSON:\n"
    '{"title": "one-line description (max 80 chars)", '
    '"summary": "2-3 sentences of work context", '
    '"action_items": ["follow-up action (max 3)"], '
    '"project_hint": "project name if visible"}\n'
    "Rules: Be specific and factual. No speculation. No emojis. Only valid JSON."
)


class ActivityMemoryBuilder:
    def __init__(self, context_window: Optional[SlidingContextWindow] = None, llm_dispatcher=None):
        self._context_window = context_window or SlidingContextWindow()
        self._dispatcher = llm_dispatcher
        self._memories: list[ActivityMemory] = []
        self._max_memories = 100
        self._memory_counter: int = 0
        self._raw_context_max_len: int = 1500
        self._ocr_text_max_len: int = 300
        self._llm_budget_per_cycle: int = 3
        self._llm_calls_this_cycle: int = 0

    def set_dispatcher(self, dispatcher) -> None:
        self._dispatcher = dispatcher

    async def build_memories(self) -> list[ActivityMemory]:
        unsummarized = self._context_window.get_unsummarized_windows()
        if not unsummarized:
            return []

        self._llm_calls_this_cycle = 0
        new_memories = []
        for window in unsummarized:
            try:
                memory = await self._summarize_window(window)
                if memory:
                    new_memories.append(memory)
                    self._memories.append(memory)
                    self._context_window.mark_window_summarized(window.window_id, memory.summary)
            except Exception as e:
                logger.error(f"Failed to build memory for window {window.window_id}: {e}")

        if len(self._memories) > self._max_memories:
            self._memories = self._memories[-self._max_memories:]

        return new_memories

    async def _summarize_window(self, window) -> Optional[ActivityMemory]:
        events = window.events
        if not events:
            return None

        raw_context = self._build_raw_context(events)

        if self._dispatcher and self._llm_calls_this_cycle < self._llm_budget_per_cycle:
            self._llm_calls_this_cycle += 1
            return await self._summarize_with_llm(window, raw_context)
        return self._summarize_from_rules(window, raw_context)

    def _build_raw_context(self, events: list[dict]) -> str:
        parts = []
        for e in events:
            ts = e.get("timestamp", 0)
            source = e.get("source", "unknown")
            data = e.get("data", {})
            line = f"[{ts}] {source}"
            if isinstance(data, dict):
                title = data.get("title", data.get("window_title", data.get("subject", "")))
                app = data.get("app", "")
                if app:
                    line += f" | {app}"
                if title:
                    line += f" | {title}"
                text_content = data.get("ocr_text", data.get("content", data.get("body", "")))
                if text_content and isinstance(text_content, str):
                    truncated = text_content[:self._ocr_text_max_len]
                    if len(text_content) > self._ocr_text_max_len:
                        truncated += "..."
                    line += f"\n{truncated}"
            parts.append(line)
        raw = "\n---\n".join(parts)
        return raw[:self._raw_context_max_len]

    async def _summarize_with_llm(self, window, raw_context: str) -> ActivityMemory:
        from app.core.llm.dispatcher import TaskCategory

        prompt = (
            f"Activity window ({window.start_time:.0f} to {window.end_time:.0f}):\n\n"
            f"{raw_context}\n\n"
            f"Summarize. Output only valid JSON."
        )

        try:
            response = await self._dispatcher.dispatch(
                TaskCategory.DAILY,
                messages=[
                    {"role": "system", "content": MEMORY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            raw = response.choices[0].message.content.strip()
            return self._parse_llm_memory(window, raw_context, raw)
        except Exception as e:
            logger.error(f"LLM memory summarization failed: {e}")
            return self._summarize_from_rules(window, raw_context)

    def _parse_llm_memory(self, window, raw_context: str, raw_output: str) -> ActivityMemory:
        self._memory_counter += 1
        memory = ActivityMemory(
            memory_id=f"mem_{self._memory_counter}_{int(time.time())}",
            start_time=window.start_time,
            end_time=window.end_time,
            primary_source=window.primary_source,
            primary_activity=window.primary_activity,
            key_entities=window.key_entities[:10],
            raw_context=raw_context,
        )

        json_match = re.search(r'\{[\s\S]*\}', raw_output)
        if json_match:
            try:
                data = json.loads(json_match.group())
                memory.title = str(data.get("title", ""))[:80]
                memory.summary = str(data.get("summary", ""))
                memory.action_items = [str(a) for a in data.get("action_items", [])][:3]
                memory.project_hint = str(data.get("project_hint", ""))
                return memory
            except json.JSONDecodeError:
                pass

        memory.title = f"Activity: {window.primary_activity or window.primary_source}"
        memory.summary = raw_output[:300]
        return memory

    def _summarize_from_rules(self, window, raw_context: str) -> ActivityMemory:
        self._memory_counter += 1
        source_dist: dict[str, int] = {}
        activity_dist: dict[str, int] = {}
        for e in window.events:
            src = e.get("source", "unknown")
            source_dist[src] = source_dist.get(src, 0) + 1
            data = e.get("data", {})
            if isinstance(data, dict):
                for key in ("app", "activity", "action"):
                    val = data.get(key)
                    if val and isinstance(val, str):
                        activity_dist[val] = activity_dist.get(val, 0) + 1

        primary_source = max(source_dist, key=source_dist.get) if source_dist else ""
        primary_activity = max(activity_dist, key=activity_dist.get) if activity_dist else ""

        title_parts = []
        if primary_activity:
            title_parts.append(primary_activity)
        elif primary_source:
            title_parts.append(f"{primary_source} activity")
        else:
            title_parts.append("General activity")
        title = " | ".join(title_parts)[:80]

        duration = window.end_time - window.start_time if window.end_time > window.start_time else 0
        duration_str = f"{duration:.0f}s" if duration < 3600 else f"{duration/3600:.1f}h"
        summary = f"User was engaged in {primary_activity or primary_source} for {duration_str}. "
        summary += f"Involved {len(window.events)} events across {len(source_dist)} sources."

        return ActivityMemory(
            memory_id=f"mem_{self._memory_counter}_{int(time.time())}",
            start_time=window.start_time,
            end_time=window.end_time,
            primary_source=primary_source,
            primary_activity=primary_activity,
            title=title,
            summary=summary,
            key_entities=window.key_entities[:10],
            raw_context=raw_context,
        )

    def get_recent_memories(self, limit: int = 10) -> list[dict]:
        return [m.to_dict() for m in self._memories[-limit:]]

    def search_memories(self, query: str, limit: int = 5) -> list[dict]:
        query_lower = query.lower()
        results = []
        for m in reversed(self._memories):
            entities_str = " ".join(m.key_entities)
            searchable = (
                f"{m.title} {m.summary} "
                f"{m.primary_activity} {m.project_hint} "
                f"{entities_str}"
            ).lower()
            if query_lower in searchable:
                results.append(m.to_dict())
                if len(results) >= limit:
                    break
        return results

    def get_latest_memory(self) -> Optional[dict]:
        if self._memories:
            return self._memories[-1].to_dict()
        return None


_builder: Optional[ActivityMemoryBuilder] = None


def get_activity_memory_builder() -> ActivityMemoryBuilder:
    global _builder
    if _builder is None:
        _builder = ActivityMemoryBuilder()
    return _builder
