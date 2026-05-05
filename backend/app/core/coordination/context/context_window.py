import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextBucket:
    events: list[dict] = field(default_factory=list)
    summary: str = ""
    key_entities: list[str] = field(default_factory=list)
    event_count: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    primary_source: str = ""
    primary_activity: str = ""

    def add_event(self, event: dict) -> None:
        self.events.append(event)
        self.event_count += 1
        ts = event.get("timestamp", time.time())
        if self.start_time == 0.0 or ts < self.start_time:
            self.start_time = ts
        if ts > self.end_time:
            self.end_time = ts

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "key_entities": self.key_entities,
            "event_count": self.event_count,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "primary_source": self.primary_source,
            "primary_activity": self.primary_activity,
        }


@dataclass
class ActivityWindow:
    window_id: str = ""
    events: list[dict] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    primary_source: str = ""
    primary_activity: str = ""
    summary: str = ""
    key_entities: list[str] = field(default_factory=list)
    summarized: bool = False

    def add_event(self, event: dict) -> None:
        self.events.append(event)
        ts = event.get("timestamp", time.time())
        if self.start_time == 0.0 or ts < self.start_time:
            self.start_time = ts
        if ts > self.end_time:
            self.end_time = ts

    @property
    def span_seconds(self) -> float:
        if self.start_time == 0.0:
            return 0.0
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        return {
            "window_id": self.window_id,
            "event_count": len(self.events),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "span_seconds": self.span_seconds,
            "primary_source": self.primary_source,
            "primary_activity": self.primary_activity,
            "summary": self.summary,
            "key_entities": self.key_entities,
            "summarized": self.summarized,
        }


class SlidingContextWindow:
    def __init__(self):
        self._precise: ContextBucket = ContextBucket()
        self._compressed: ContextBucket = ContextBucket()
        self._trend: ContextBucket = ContextBucket()
        self._long_term: ContextBucket = ContextBucket()
        self._precise_ttl = 300.0
        self._compressed_ttl = 3600.0
        self._trend_ttl = 86400.0
        self._long_term_ttl = 604800.0
        self._last_compress: float = 0.0
        self._compress_interval: float = 300.0

        self._activity_windows: list[ActivityWindow] = []
        self._current_window: Optional[ActivityWindow] = None
        self._activity_gap_threshold: float = 120.0
        self._min_window_span: float = 30.0
        self._max_window_events: int = 100
        self._max_windows: int = 50
        self._last_processed_ts: float = 0.0
        self._window_counter: int = 0

    def add_event(self, event: dict) -> None:
        self._precise.add_event(event)
        now = time.time()
        self._precise.events = [
            e for e in self._precise.events
            if (now - e.get("timestamp", 0)) < self._precise_ttl
        ]
        self._add_to_activity_window(event)
        if (now - self._last_compress) >= self._compress_interval:
            self._compress()
            self._last_compress = now

    def _add_to_activity_window(self, event: dict) -> None:
        ts = event.get("timestamp", time.time())

        if self._current_window is None:
            self._current_window = self._create_window()
            self._current_window.add_event(event)
            return

        gap = ts - self._current_window.end_time
        if gap > self._activity_gap_threshold:
            self._finalize_current_window()
            self._current_window = self._create_window()

        self._current_window.add_event(event)
        if len(self._current_window.events) >= self._max_window_events:
            self._finalize_current_window()
            self._current_window = self._create_window()

    def _create_window(self) -> ActivityWindow:
        self._window_counter += 1
        return ActivityWindow(window_id=f"w_{self._window_counter}_{int(time.time())}")

    def _finalize_current_window(self) -> None:
        if self._current_window is None:
            return
        if self._current_window.span_seconds < self._min_window_span and len(self._current_window.events) < 3:
            if self._activity_windows:
                for e in self._current_window.events:
                    self._activity_windows[-1].add_event(e)
                last_w = self._activity_windows[-1]
                last_w.primary_source = self._detect_primary_source(last_w.events)
                last_w.primary_activity = self._detect_primary_activity(last_w.events)
            self._current_window = None
            return

        self._current_window.primary_source = self._detect_primary_source(self._current_window.events)
        self._current_window.primary_activity = self._detect_primary_activity(self._current_window.events)
        self._current_window.key_entities = self._extract_entities(self._current_window.events)
        self._activity_windows.append(self._current_window)

        if len(self._activity_windows) > self._max_windows:
            self._merge_oldest_windows()

        self._current_window = None

    def _merge_oldest_windows(self) -> None:
        if len(self._activity_windows) < 3:
            return
        oldest = self._activity_windows[0]
        second = self._activity_windows[1]
        merged = ActivityWindow(
            window_id=f"merged_{oldest.window_id}",
            events=oldest.events + second.events,
            start_time=min(oldest.start_time, second.start_time),
            end_time=max(oldest.end_time, second.end_time),
            summarized=oldest.summarized and second.summarized,
        )
        merged.primary_source = self._detect_primary_source(merged.events)
        merged.primary_activity = self._detect_primary_activity(merged.events)
        merged.key_entities = self._extract_entities(merged.events)
        if oldest.summary and second.summary:
            merged.summary = f"{oldest.summary}; {second.summary}"
        self._activity_windows = [merged] + self._activity_windows[2:]

    def _detect_primary_source(self, events: list[dict]) -> str:
        if not events:
            return ""
        source_counts: dict[str, int] = {}
        for e in events:
            src = e.get("source", e.get("data", {}).get("source", "unknown"))
            source_counts[src] = source_counts.get(src, 0) + 1
        if not source_counts:
            return ""
        return max(source_counts, key=source_counts.get)

    def _detect_primary_activity(self, events: list[dict]) -> str:
        if not events:
            return ""
        activity_counts: dict[str, int] = {}
        for e in events:
            data = e.get("data", {})
            for key in ("app", "activity", "action", "tool"):
                val = data.get(key)
                if val and isinstance(val, str):
                    activity_counts[val] = activity_counts.get(val, 0) + 1
        if not activity_counts:
            return ""
        return max(activity_counts, key=activity_counts.get)

    def _extract_entities(self, events: list[dict]) -> list[str]:
        entities = set()
        for e in events:
            data = e.get("data", {})
            if isinstance(data, dict):
                for key in ("app", "sender", "title", "topic", "filename"):
                    val = data.get(key)
                    if val and isinstance(val, str):
                        entities.add(val)
        return list(entities)[:20]

    def get_unsummarized_windows(self) -> list[ActivityWindow]:
        now = time.time()
        unsummarized = []
        for w in self._activity_windows:
            if w.summarized:
                continue
            idle_time = now - w.end_time
            if w.span_seconds >= self._min_window_span or idle_time >= self._activity_gap_threshold:
                unsummarized.append(w)
        if self._current_window and not self._current_window.summarized:
            idle_time = now - self._current_window.end_time
            if idle_time >= self._activity_gap_threshold:
                unsummarized.append(self._current_window)
        return unsummarized

    def mark_window_summarized(self, window_id: str, summary: str) -> None:
        for w in self._activity_windows:
            if w.window_id == window_id:
                w.summary = summary
                w.summarized = True
                break
        if self._current_window and self._current_window.window_id == window_id:
            self._current_window.summary = summary
            self._current_window.summarized = True

    def _compress(self) -> None:
        now = time.time()
        expired_precise = [
            e for e in self._precise.events
            if (now - e.get("timestamp", 0)) >= self._precise_ttl
            and (now - e.get("timestamp", 0)) < self._compressed_ttl
        ]
        for e in expired_precise:
            self._compressed.add_event(e)
        self._compressed.events = [
            e for e in self._compressed.events
            if (now - e.get("timestamp", 0)) < self._compressed_ttl
        ]
        expired_compressed = [
            e for e in self._compressed.events
            if (now - e.get("timestamp", 0)) >= self._compressed_ttl
            and (now - e.get("timestamp", 0)) < self._trend_ttl
        ]
        for e in expired_compressed:
            self._trend.add_event(e)
        self._trend.events = [
            e for e in self._trend.events
            if (now - e.get("timestamp", 0)) < self._trend_ttl
        ]
        expired_trend = [
            e for e in self._trend.events
            if (now - e.get("timestamp", 0)) >= self._trend_ttl
            and (now - e.get("timestamp", 0)) < self._long_term_ttl
        ]
        for e in expired_trend:
            self._long_term.add_event(e)
        self._long_term.events = [
            e for e in self._long_term.events
            if (now - e.get("timestamp", 0)) < self._long_term_ttl
        ]
        self._update_summaries()
        self._cleanup_old_windows()

    def _cleanup_old_windows(self) -> None:
        now = time.time()
        self._activity_windows = [
            w for w in self._activity_windows
            if (now - w.end_time) < self._long_term_ttl
        ]

    def _update_summaries(self) -> None:
        self._precise.summary = f"{self._precise.event_count} events in last 5min"
        self._precise.key_entities = self._extract_entities(self._precise.events)
        self._compressed.summary = f"{self._compressed.event_count} events in last 1hr"
        self._compressed.key_entities = self._extract_entities(self._compressed.events)
        self._trend.summary = f"{self._trend.event_count} events in last 24hr"
        self._trend.key_entities = self._extract_entities(self._trend.events)
        self._long_term.summary = f"{self._long_term.event_count} events in last 7d"
        self._long_term.key_entities = self._extract_entities(self._long_term.events)

    def get_window(self, level: str = "all") -> dict:
        result = {}
        if level in ("all", "precise"):
            result["precise"] = self._precise.to_dict()
        if level in ("all", "compressed"):
            result["compressed"] = self._compressed.to_dict()
        if level in ("all", "trend"):
            result["trend"] = self._trend.to_dict()
        if level in ("all", "long_term"):
            result["long_term"] = self._long_term.to_dict()
        return result

    def get_full_context(self) -> dict:
        return {
            "precise": self._precise.to_dict(),
            "compressed": self._compressed.to_dict(),
            "trend": self._trend.to_dict(),
            "long_term": self._long_term.to_dict(),
        }

    def get_activity_windows(self, limit: int = 10) -> list[dict]:
        windows = sorted(self._activity_windows, key=lambda w: w.end_time, reverse=True)[:limit]
        return [w.to_dict() for w in windows]

    def get_current_activity_window(self) -> Optional[dict]:
        if self._current_window:
            return self._current_window.to_dict()
        if self._activity_windows:
            return self._activity_windows[-1].to_dict()
        return None

    def get_primary_activity(self) -> dict:
        now = time.time()
        recent_windows = [
            w for w in self._activity_windows
            if (now - w.end_time) < self._compressed_ttl
        ]
        if not recent_windows:
            return {"source": "", "activity": "", "confidence": 0.0}
        source_counts: dict[str, int] = {}
        activity_counts: dict[str, int] = {}
        total_events = 0
        for w in recent_windows:
            weight = max(0.1, 1.0 - (now - w.end_time) / self._compressed_ttl)
            for e in w.events:
                src = e.get("source", e.get("data", {}).get("source", "unknown"))
                source_counts[src] = source_counts.get(src, 0) + weight
                total_events += weight
                data = e.get("data", {})
                for key in ("app", "activity", "action"):
                    val = data.get(key)
                    if val and isinstance(val, str):
                        activity_counts[val] = activity_counts.get(val, 0) + weight
        primary_source = max(source_counts, key=source_counts.get) if source_counts else ""
        primary_activity = max(activity_counts, key=activity_counts.get) if activity_counts else ""
        top_count = max(source_counts.values()) if source_counts else 0
        confidence = top_count / total_events if total_events > 0 else 0.0
        return {
            "source": primary_source,
            "activity": primary_activity,
            "confidence": min(1.0, confidence),
        }
