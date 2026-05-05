import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ContextSource(str, Enum):
    SCREEN = "screen"
    CHAT = "chat"
    NOTIFICATION = "notification"
    CALENDAR = "calendar"
    EMAIL = "email"
    FILE_OPERATION = "file_operation"
    LOCATION = "location"
    DEVICE_STATE = "device_state"
    CLIPBOARD = "clipboard"
    USER_INTERACTION = "user_interaction"


@dataclass
class ContextEvent:
    source: ContextSource
    data: dict
    timestamp: float = field(default_factory=time.time)
    priority: str = "normal"
    ttl: float = 3600.0
    metadata: dict = field(default_factory=dict)
    event_hash: str = ""

    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl

    def compute_hash(self) -> str:
        if self.event_hash:
            return self.event_hash
        source_part = self.source.value
        key_data = {}
        if isinstance(self.data, dict):
            for k in ("app", "title", "window_title", "subject", "filename", "action"):
                v = self.data.get(k)
                if v:
                    key_data[k] = str(v)[:100]
        content = f"{source_part}:{json.dumps(key_data, sort_keys=True)}"
        self.event_hash = str(hash(content))
        return self.event_hash


class ContextAggregator:
    def __init__(self):
        self._events: list[ContextEvent] = []
        self._max_events = 200
        self._source_buffers: dict[ContextSource, list[ContextEvent]] = {
            s: [] for s in ContextSource
        }
        self._buffer_max = 20
        self._subscribers: list = []
        self._lock = asyncio.Lock()
        self._last_aggregation: float = 0
        self._aggregation_interval: float = 10.0
        self._cached_context: Optional[dict] = None
        self._last_processed_ts: float = 0.0
        self._seen_hashes: dict[str, float] = {}
        self._hash_ttl: float = 300.0
        self._activity_summaries: list[dict] = []
        self._max_summaries = 30

    async def ingest(self, event: ContextEvent) -> None:
        event_hash = event.compute_hash()
        now = time.time()
        last_seen = self._seen_hashes.get(event_hash)
        if last_seen and (now - last_seen) < self._hash_ttl:
            return

        async with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]
            buf = self._source_buffers[event.source]
            buf.append(event)
            if len(buf) > self._buffer_max:
                self._source_buffers[event.source] = buf[-self._buffer_max:]
            self._seen_hashes[event_hash] = now

        self._cached_context = None

        for cb in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)
            except Exception as e:
                logger.error(f"Context subscriber error: {e}")

    async def ingest_batch(self, events: list[ContextEvent]) -> None:
        for event in events:
            await self.ingest(event)

    def _cleanup_seen_hashes(self) -> None:
        now = time.time()
        expired = [h for h, ts in self._seen_hashes.items() if (now - ts) > self._hash_ttl]
        for h in expired:
            del self._seen_hashes[h]

    def subscribe(self, callback) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback) -> None:
        self._subscribers = [cb for cb in self._subscribers if cb != callback]

    async def get_current_context(self) -> dict:
        now = time.time()
        if self._cached_context and (now - self._last_aggregation) < self._aggregation_interval:
            return self._cached_context
        async with self._lock:
            self._events = [e for e in self._events if not e.is_expired()]
        context = {
            "timestamp": now,
            "event_count": len(self._events),
            "sources": {},
            "recent_events": [],
            "summary": {},
        }
        for source in ContextSource:
            buf = self._source_buffers[source]
            if not buf:
                continue
            recent = [e for e in buf if not e.is_expired()]
            context["sources"][source.value] = {
                "count": len(recent),
                "latest": recent[-1].data if recent else None,
                "latest_time": recent[-1].timestamp if recent else None,
            }
        recent_all = sorted(
            [e for e in self._events if not e.is_expired()],
            key=lambda e: e.timestamp,
            reverse=True,
        )[:10]
        context["recent_events"] = [
            {
                "source": e.source.value,
                "data": e.data,
                "timestamp": e.timestamp,
                "priority": e.priority,
            }
            for e in recent_all
        ]
        context["summary"] = self._compute_summary()
        self._cached_context = context
        self._last_aggregation = now
        return context

    def get_incremental_events(self, since_ts: Optional[float] = None) -> list[dict]:
        if since_ts is None:
            since_ts = self._last_processed_ts
        new_events = [
            e for e in self._events
            if e.timestamp > since_ts and not e.is_expired()
        ]
        if new_events:
            self._last_processed_ts = max(e.timestamp for e in new_events)
        return [
            {
                "source": e.source.value,
                "data": e.data,
                "timestamp": e.timestamp,
                "priority": e.priority,
            }
            for e in new_events
        ]

    def get_events_since(self, since_ts: float) -> list[dict]:
        return [
            {
                "source": e.source.value,
                "data": e.data,
                "timestamp": e.timestamp,
                "priority": e.priority,
            }
            for e in self._events
            if e.timestamp > since_ts and not e.is_expired()
        ]

    def build_activity_summary(self, events: list[dict]) -> Optional[dict]:
        if not events:
            return None
        source_counts: dict[str, int] = {}
        activity_counts: dict[str, int] = {}
        entities: set[str] = set()
        for e in events:
            src = e.get("source", "unknown")
            source_counts[src] = source_counts.get(src, 0) + 1
            data = e.get("data", {})
            if isinstance(data, dict):
                for key in ("app", "activity", "action", "tool"):
                    val = data.get(key)
                    if val and isinstance(val, str):
                        activity_counts[val] = activity_counts.get(val, 0) + 1
                for key in ("app", "sender", "title", "topic", "filename"):
                    val = data.get(key)
                    if val and isinstance(val, str):
                        entities.add(val)
        primary_source = max(source_counts, key=source_counts.get) if source_counts else ""
        primary_activity = max(activity_counts, key=activity_counts.get) if activity_counts else ""
        total = sum(source_counts.values())
        confidence = max(source_counts.values()) / total if total > 0 else 0.0
        summary = {
            "primary_source": primary_source,
            "primary_activity": primary_activity,
            "confidence": min(1.0, confidence),
            "source_distribution": source_counts,
            "activity_distribution": dict(list(activity_counts.items())[:10]),
            "key_entities": list(entities)[:15],
            "event_count": len(events),
            "timestamp": time.time(),
        }
        self._activity_summaries.append(summary)
        if len(self._activity_summaries) > self._max_summaries:
            self._activity_summaries = self._activity_summaries[-self._max_summaries:]
        return summary

    def get_recent_summaries(self, limit: int = 10) -> list[dict]:
        return self._activity_summaries[-limit:]

    def _compute_summary(self) -> dict:
        active_sources = []
        urgent_count = 0
        for source in ContextSource:
            buf = self._source_buffers[source]
            recent = [e for e in buf if not e.is_expired()]
            if recent:
                active_sources.append(source.value)
                urgent_count += sum(1 for e in recent if e.priority == "urgent")
        return {
            "active_sources": active_sources,
            "urgent_event_count": urgent_count,
            "total_active_events": len([e for e in self._events if not e.is_expired()]),
        }

    def get_source_events(self, source: ContextSource, limit: int = 20) -> list[dict]:
        buf = self._source_buffers[source]
        recent = [e for e in buf if not e.is_expired()]
        return [
            {"source": e.source.value, "data": e.data, "timestamp": e.timestamp, "priority": e.priority}
            for e in recent[-limit:]
        ]

    async def get_context_for_llm(self) -> str:
        ctx = await self.get_current_context()
        parts = []
        for source_name, source_data in ctx.get("sources", {}).items():
            if source_data.get("latest"):
                parts.append(f"[{source_name}] latest: {json.dumps(source_data['latest'], ensure_ascii=False)}")
        summary = ctx.get("summary", {})
        parts.append(f"Active sources: {', '.join(summary.get('active_sources', []))}")
        parts.append(f"Urgent events: {summary.get('urgent_event_count', 0)}")
        return "\n".join(parts)

    async def get_current_context_for_agent(self) -> dict:
        ctx = await self.get_current_context()
        latest_events = ctx.get("recent_events", [])[:5]
        latest_summary = self._activity_summaries[-1] if self._activity_summaries else None
        return {
            "latest_capture": {
                "source": latest_events[0]["source"] if latest_events else None,
                "data": latest_events[0]["data"] if latest_events else None,
                "timestamp": latest_events[0]["timestamp"] if latest_events else None,
            } if latest_events else None,
            "latest_summary": {
                "primary_source": latest_summary["primary_source"],
                "primary_activity": latest_summary["primary_activity"],
                "confidence": latest_summary["confidence"],
                "key_entities": latest_summary["key_entities"][:5],
            } if latest_summary else None,
            "active_sources": ctx.get("summary", {}).get("active_sources", []),
            "urgent_count": ctx.get("summary", {}).get("urgent_event_count", 0),
        }

    async def search_context(self, query: str, limit: int = 5) -> list[dict]:
        query_lower = query.lower()
        results = []
        for e in reversed(self._events):
            if e.is_expired():
                continue
            data_str = json.dumps(e.data, ensure_ascii=False).lower()
            if query_lower in data_str or query_lower in e.source.value:
                results.append({
                    "source": e.source.value,
                    "data": e.data,
                    "timestamp": e.timestamp,
                    "priority": e.priority,
                })
                if len(results) >= limit:
                    break
        return results


_aggregator: Optional[ContextAggregator] = None


def get_context_aggregator() -> ContextAggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = ContextAggregator()
    return _aggregator
