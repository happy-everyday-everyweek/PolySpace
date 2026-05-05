from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CalendarEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    start_time: str = ""
    end_time: str = ""
    location: str = ""
    reminders: list[dict[str, Any]] = field(default_factory=list)
    recurring: dict[str, Any] | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CalendarService:
    def __init__(self) -> None:
        self._events: dict[str, CalendarEvent] = {}

    async def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str = "",
        description: str = "",
        location: str = "",
        reminders: list[dict[str, Any]] | None = None,
        recurring: dict[str, Any] | None = None,
    ) -> CalendarEvent:
        event = CalendarEvent(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time or start_time,
            location=location,
            reminders=reminders or [],
            recurring=recurring,
        )
        self._events[event.event_id] = event
        return event

    async def get_event(self, event_id: str) -> CalendarEvent | None:
        return self._events.get(event_id)

    async def update_event(self, event_id: str, **updates: Any) -> CalendarEvent | None:
        event = self._events.get(event_id)
        if not event:
            return None
        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)
        event.updated_at = datetime.now().isoformat()
        return event

    async def delete_event(self, event_id: str) -> bool:
        if event_id in self._events:
            del self._events[event_id]
            return True
        return False

    async def list_events(self, start_date: str | None = None, end_date: str | None = None) -> list[CalendarEvent]:
        events = list(self._events.values())
        if start_date:
            events = [e for e in events if e.start_time >= start_date]
        if end_date:
            events = [e for e in events if e.start_time <= end_date]
        return sorted(events, key=lambda e: e.start_time)

    async def get_upcoming(self, limit: int = 10) -> list[CalendarEvent]:
        now = datetime.now().isoformat()
        upcoming = [e for e in self._events.values() if e.start_time >= now]
        return sorted(upcoming, key=lambda e: e.start_time)[:limit]

    async def add_reminder(self, event_id: str, minutes_before: int = 15, method: str = "notification") -> dict[str, Any] | None:
        event = self._events.get(event_id)
        if not event:
            return None
        reminder = {"minutes_before": minutes_before, "method": method}
        event.reminders.append(reminder)
        return reminder


calendar_service = CalendarService()
