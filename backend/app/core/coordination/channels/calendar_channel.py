import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CalendarInjection:
    title: str
    description: str
    start_time: str
    end_time: str
    location: str = ""
    ai_suggestion: str = ""
    status: str = "pending"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location": self.location,
            "ai_suggestion": self.ai_suggestion,
            "status": self.status,
            "created_at": self.created_at,
        }


class CalendarChannel:
    def __init__(self):
        self._injections: list[CalendarInjection] = []
        self._max_injections = 50
        self._templates: dict[str, dict] = {
            "focus_time": {"title": "Focus Time", "duration_minutes": 90, "description": "AI-suggested focus block"},
            "break_time": {"title": "Break", "duration_minutes": 15, "description": "Take a rest"},
            "learning_time": {"title": "Learning Time", "duration_minutes": 60, "description": "AI-suggested learning session"},
            "review_time": {"title": "Daily Review", "duration_minutes": 30, "description": "Review today's progress"},
        }

    async def inject(self, template_name: str, start_time: str, context: str = "") -> CalendarInjection:
        template = self._templates.get(template_name, self._templates["focus_time"])
        duration = template.get("duration_minutes", 60)
        from datetime import datetime, timedelta
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.isoformat()
        except (ValueError, TypeError):
            end_time = start_time
        injection = CalendarInjection(
            title=template.get("title", "AI Suggestion"),
            description=template.get("description", ""),
            start_time=start_time,
            end_time=end_time,
            ai_suggestion=context or template.get("description", ""),
            status="pending",
        )
        self._injections.append(injection)
        if len(self._injections) > self._max_injections:
            self._injections = self._injections[-self._max_injections:]
        return injection

    def accept(self, injection_id: str) -> bool:
        for inj in self._injections:
            if id(inj) == injection_id and inj.status == "pending":
                inj.status = "accepted"
                return True
        return False

    def reject(self, injection_id: str) -> bool:
        for inj in self._injections:
            if id(inj) == injection_id and inj.status == "pending":
                inj.status = "rejected"
                return True
        return False

    def get_pending(self) -> list[dict]:
        return [i.to_dict() for i in self._injections if i.status == "pending"]

    def get_history(self, limit: int = 20) -> list[dict]:
        return [i.to_dict() for i in self._injections[-limit:]]


_channel: Optional[CalendarChannel] = None


def get_calendar_channel() -> CalendarChannel:
    global _channel
    if _channel is None:
        _channel = CalendarChannel()
    return _channel
