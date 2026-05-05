import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.memory.manager import FileMemoryStorage, MemoryStorage, _utc_now_iso

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    confidence: float = 1.0
    source: str = ""
    created_at: str = field(default_factory=_utc_now_iso)
    accessed_at: str = field(default_factory=_utc_now_iso)
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkingMemory:
    def __init__(self, storage: MemoryStorage | None = None):
        self._storage = storage or FileMemoryStorage()
        self._entries: list[MemoryEntry] = []
        self._active_tasks: list[dict] = []
        self._file_contexts: dict[str, dict] = {}
        self._schedule_cache: list[dict] = []

    def _key(self) -> str:
        return "working"

    def record_task(self, title: str, status: str = "active", priority: str = "normal", due: str = "", source: str = "") -> str:
        entry = MemoryEntry(
            content=title,
            category="task",
            tags=["task", status, priority],
            source=source or "user",
            metadata={"status": status, "priority": priority, "due": due},
        )
        self._entries.append(entry)
        self._active_tasks.append({"id": entry.id, "title": title, "status": status, "priority": priority, "due": due})
        self._persist()
        return entry.id

    def record_file_operation(self, filename: str, operation: str, summary: str = "", source: str = "") -> str:
        entry = MemoryEntry(
            content=f"{operation}: {filename}" + (f" - {summary}" if summary else ""),
            category="file_operation",
            tags=["file", operation],
            source=source or "workspace",
            metadata={"filename": filename, "operation": operation},
        )
        self._entries.append(entry)
        self._file_contexts[filename] = {
            "last_operation": operation,
            "last_summary": summary,
            "last_access": _utc_now_iso(),
        }
        self._persist()
        return entry.id

    def record_schedule(self, event: str, time_str: str, location: str = "", source: str = "") -> str:
        entry = MemoryEntry(
            content=f"Schedule: {event} at {time_str}" + (f" ({location})" if location else ""),
            category="schedule",
            tags=["schedule", "calendar"],
            source=source or "calendar",
            metadata={"event": event, "time": time_str, "location": location},
        )
        self._entries.append(entry)
        self._schedule_cache.append({"event": event, "time": time_str, "location": location})
        self._persist()
        return entry.id

    def record_decision(self, decision: str, context: str = "", outcome: str = "", source: str = "") -> str:
        entry = MemoryEntry(
            content=decision,
            category="decision",
            tags=["decision"],
            confidence=0.8,
            source=source or "agent",
            metadata={"context": context, "outcome": outcome},
        )
        self._entries.append(entry)
        self._persist()
        return entry.id

    def record_knowledge(self, content: str, tags: list[str] | None = None, confidence: float = 1.0, source: str = "") -> str:
        entry = MemoryEntry(
            content=content,
            category="knowledge",
            tags=tags or ["knowledge"],
            confidence=confidence,
            source=source or "learning",
        )
        self._entries.append(entry)
        self._persist()
        return entry.id

    def get_active_tasks(self) -> list[dict]:
        return [t for t in self._active_tasks if t.get("status") == "active"]

    def get_file_context(self, filename: str) -> dict | None:
        return self._file_contexts.get(filename)

    def get_recent_schedule(self, limit: int = 10) -> list[dict]:
        return self._schedule_cache[-limit:]

    def search(self, query: str, category: str | None = None, limit: int = 20) -> list[MemoryEntry]:
        results = []
        query_lower = query.lower()
        for entry in reversed(self._entries):
            if category and entry.category != category:
                continue
            if query_lower in entry.content.lower() or any(query_lower in t for t in entry.tags):
                entry.access_count += 1
                entry.accessed_at = _utc_now_iso()
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def get_summary(self) -> dict:
        categories: dict[str, int] = {}
        for entry in self._entries:
            categories[entry.category] = categories.get(entry.category, 0) + 1
        return {
            "total_entries": len(self._entries),
            "active_tasks": len(self.get_active_tasks()),
            "tracked_files": len(self._file_contexts),
            "scheduled_events": len(self._schedule_cache),
            "categories": categories,
        }

    def _persist(self):
        data = self._storage.load(self._key())
        data["working_entries"] = [
            {
                "id": e.id, "content": e.content, "category": e.category,
                "tags": e.tags, "confidence": e.confidence, "source": e.source,
                "created_at": e.created_at, "metadata": e.metadata,
            }
            for e in self._entries[-200:]
        ]
        data["active_tasks"] = self._active_tasks[-50:]
        data["file_contexts"] = dict(list(self._file_contexts.items())[-100:])
        data["schedule_cache"] = self._schedule_cache[-50:]
        self._storage.save(data, self._key())

    def load(self):
        data = self._storage.load(self._key())
        self._entries = []
        for raw in data.get("working_entries", []):
            self._entries.append(MemoryEntry(
                id=raw.get("id", str(uuid.uuid4())),
                content=raw.get("content", ""),
                category=raw.get("category", ""),
                tags=raw.get("tags", []),
                confidence=raw.get("confidence", 1.0),
                source=raw.get("source", ""),
                created_at=raw.get("created_at", ""),
                metadata=raw.get("metadata", {}),
            ))
        self._active_tasks = data.get("active_tasks", [])
        self._file_contexts = data.get("file_contexts", {})
        self._schedule_cache = data.get("schedule_cache", [])


class InteractionMemory:
    def __init__(self, storage: MemoryStorage | None = None):
        self._storage = storage or FileMemoryStorage()
        self._entries: list[MemoryEntry] = []
        self._user_preferences: dict[str, Any] = {}
        self._emotion_history: list[dict] = []
        self._conversation_topics: list[dict] = []
        self._communication_style: dict[str, Any] = {}

    def _key(self) -> str:
        return "interaction"

    def record_conversation(self, topic: str, mood: str = "neutral", key_points: list[str] | None = None, source: str = "") -> str:
        entry = MemoryEntry(
            content=topic,
            category="conversation",
            tags=["conversation", mood],
            source=source or "chat",
            metadata={"mood": mood, "key_points": key_points or []},
        )
        self._entries.append(entry)
        self._conversation_topics.append({
            "topic": topic,
            "mood": mood,
            "time": _utc_now_iso(),
            "key_points": key_points or [],
        })
        self._persist()
        return entry.id

    def record_emotion(self, emotion: str, intensity: float = 0.5, trigger: str = "", source: str = "") -> str:
        entry = MemoryEntry(
            content=f"Emotion: {emotion} (intensity: {intensity})" + (f" triggered by: {trigger}" if trigger else ""),
            category="emotion",
            tags=["emotion", emotion],
            confidence=intensity,
            source=source or "interaction",
            metadata={"emotion": emotion, "intensity": intensity, "trigger": trigger},
        )
        self._entries.append(entry)
        self._emotion_history.append({
            "emotion": emotion,
            "intensity": intensity,
            "trigger": trigger,
            "time": _utc_now_iso(),
        })
        self._persist()
        return entry.id

    def record_preference(self, key: str, value: Any, confidence: float = 0.8, source: str = "") -> str:
        entry = MemoryEntry(
            content=f"Preference: {key} = {value}",
            category="preference",
            tags=["preference", key],
            confidence=confidence,
            source=source or "inferred",
            metadata={"key": key, "value": value},
        )
        self._entries.append(entry)
        self._user_preferences[key] = {"value": value, "confidence": confidence, "updated_at": _utc_now_iso()}
        self._persist()
        return entry.id

    def record_communication_style(self, style_key: str, style_value: str, context: str = "", source: str = "") -> str:
        entry = MemoryEntry(
            content=f"Communication style: {style_key} -> {style_value}",
            category="communication_style",
            tags=["style", style_key],
            source=source or "observed",
            metadata={"style_key": style_key, "style_value": style_value, "context": context},
        )
        self._entries.append(entry)
        self._communication_style[style_key] = {"value": style_value, "context": context, "updated_at": _utc_now_iso()}
        self._persist()
        return entry.id

    def record_feedback(self, feedback: str, sentiment: str = "neutral", context: str = "", source: str = "") -> str:
        entry = MemoryEntry(
            content=feedback,
            category="feedback",
            tags=["feedback", sentiment],
            confidence=0.9 if source == "explicit" else 0.6,
            source=source or "observed",
            metadata={"sentiment": sentiment, "context": context},
        )
        self._entries.append(entry)
        self._persist()
        return entry.id

    def get_preference(self, key: str, default: Any = None) -> Any:
        pref = self._user_preferences.get(key)
        if pref:
            return pref.get("value", default)
        return default

    def get_communication_style(self, key: str, default: str = "") -> str:
        style = self._communication_style.get(key)
        if style:
            return style.get("value", default)
        return default

    def get_recent_emotions(self, limit: int = 10) -> list[dict]:
        return self._emotion_history[-limit:]

    def get_recent_topics(self, limit: int = 10) -> list[dict]:
        return self._conversation_topics[-limit:]

    def search(self, query: str, category: str | None = None, limit: int = 20) -> list[MemoryEntry]:
        results = []
        query_lower = query.lower()
        for entry in reversed(self._entries):
            if category and entry.category != category:
                continue
            if query_lower in entry.content.lower() or any(query_lower in t for t in entry.tags):
                entry.access_count += 1
                entry.accessed_at = _utc_now_iso()
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def get_summary(self) -> dict:
        categories: dict[str, int] = {}
        for entry in self._entries:
            categories[entry.category] = categories.get(entry.category, 0) + 1
        return {
            "total_entries": len(self._entries),
            "preferences": len(self._user_preferences),
            "communication_styles": len(self._communication_style),
            "emotion_records": len(self._emotion_history),
            "conversation_topics": len(self._conversation_topics),
            "categories": categories,
        }

    def _persist(self):
        data = self._storage.load(self._key())
        data["interaction_entries"] = [
            {
                "id": e.id, "content": e.content, "category": e.category,
                "tags": e.tags, "confidence": e.confidence, "source": e.source,
                "created_at": e.created_at, "metadata": e.metadata,
            }
            for e in self._entries[-200:]
        ]
        data["user_preferences"] = self._user_preferences
        data["emotion_history"] = self._emotion_history[-100:]
        data["conversation_topics"] = self._conversation_topics[-100:]
        data["communication_style"] = self._communication_style
        self._storage.save(data, self._key())

    def load(self):
        data = self._storage.load(self._key())
        self._entries = []
        for raw in data.get("interaction_entries", []):
            self._entries.append(MemoryEntry(
                id=raw.get("id", str(uuid.uuid4())),
                content=raw.get("content", ""),
                category=raw.get("category", ""),
                tags=raw.get("tags", []),
                confidence=raw.get("confidence", 1.0),
                source=raw.get("source", ""),
                created_at=raw.get("created_at", ""),
                metadata=raw.get("metadata", {}),
            ))
        self._user_preferences = data.get("user_preferences", {})
        self._emotion_history = data.get("emotion_history", [])
        self._conversation_topics = data.get("conversation_topics", [])
        self._communication_style = data.get("communication_style", {})


class DualMemorySystem:
    def __init__(self, storage: MemoryStorage | None = None):
        self._storage = storage or FileMemoryStorage()
        self.working = WorkingMemory(self._storage)
        self.interaction = InteractionMemory(self._storage)
        self._loaded = False

    def ensure_loaded(self):
        if not self._loaded:
            self.working.load()
            self.interaction.load()
            self._loaded = True

    def get_combined_summary(self) -> dict:
        self.ensure_loaded()
        return {
            "working": self.working.get_summary(),
            "interaction": self.interaction.get_summary(),
        }

    def search_all(self, query: str, limit: int = 20) -> dict:
        self.ensure_loaded()
        return {
            "working": [
                {"id": e.id, "content": e.content, "category": e.category, "tags": e.tags, "confidence": e.confidence}
                for e in self.working.search(query, limit=limit)
            ],
            "interaction": [
                {"id": e.id, "content": e.content, "category": e.category, "tags": e.tags, "confidence": e.confidence}
                for e in self.interaction.search(query, limit=limit)
            ],
        }


_dual_memory: DualMemorySystem | None = None


def get_dual_memory() -> DualMemorySystem:
    global _dual_memory
    if _dual_memory is None:
        _dual_memory = DualMemorySystem()
    return _dual_memory
