import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class InteractionMemoryEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    role: str = ""
    emotion_label: str = ""
    emotion_intensity: float = 0.0
    inner_voice: str = ""
    session_id: str = ""
    topic: str = ""
    tags: list[str] = field(default_factory=list)
    importance: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "emotion_label": self.emotion_label,
            "emotion_intensity": self.emotion_intensity,
            "inner_voice": self.inner_voice,
            "session_id": self.session_id,
            "topic": self.topic,
            "tags": self.tags,
            "importance": self.importance,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class InteractionMemoryStore:
    _BASE_DIR = Path(settings.DATA_DIR)

    def __init__(self, storage_dir: Path | str | None = None):
        if storage_dir is None:
            storage_dir = self._BASE_DIR / "interaction_memory"
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[InteractionMemoryEntry] = []
        self._session_index: dict[str, list[int]] = {}
        self._topic_index: dict[str, set[int]] = {}
        self._keyword_index: dict[str, set[int]] = {}
        self._pending_count: int = 0
        self._flush_threshold: int = 10
        self._flush_task: asyncio.Task | None = None
        self._loaded = False

    def _file_path(self) -> Path:
        return self._dir / "interaction_entries.json"

    def load(self) -> None:
        if self._loaded:
            return
        fp = self._file_path()
        if not fp.exists():
            self._loaded = True
            return
        try:
            raw = fp.read_text(encoding="utf-8")
            data = json.loads(raw)
            for item in data.get("entries", []):
                entry = InteractionMemoryEntry(
                    id=item.get("id", str(uuid.uuid4())),
                    content=item.get("content", ""),
                    role=item.get("role", ""),
                    emotion_label=item.get("emotion_label", ""),
                    emotion_intensity=item.get("emotion_intensity", 0.0),
                    inner_voice=item.get("inner_voice", ""),
                    session_id=item.get("session_id", ""),
                    topic=item.get("topic", ""),
                    tags=item.get("tags", []),
                    importance=item.get("importance", 0.0),
                    metadata=item.get("metadata", {}),
                    created_at=item.get("created_at", _utc_now_iso()),
                )
                self._add_entry_indices(len(self._entries), entry)
                self._entries.append(entry)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load interaction memory: %s", e)
        self._loaded = True

    def _add_entry_indices(self, idx: int, entry: InteractionMemoryEntry) -> None:
        if entry.session_id:
            self._session_index.setdefault(entry.session_id, []).append(idx)
        if entry.topic:
            self._topic_index.setdefault(entry.topic, set()).add(idx)
        for tag in entry.tags:
            self._topic_index.setdefault(tag, set()).add(idx)
        self._index_keywords(idx, entry.content)

    def _index_keywords(self, idx: int, content: str) -> None:
        content_lower = content.lower()
        words = content_lower.split()
        for word in words:
            cleaned = word.strip(".,!?;:()[]{}\"'").strip()
            if len(cleaned) >= 2:
                self._keyword_index.setdefault(cleaned, set()).add(idx)

    def add_entry(self, entry: InteractionMemoryEntry) -> None:
        idx = len(self._entries)
        self._add_entry_indices(idx, entry)
        self._entries.append(entry)
        self._pending_count += 1
        if self._pending_count >= self._flush_threshold:
            self._flush_sync()
            self._pending_count = 0
        else:
            self._schedule_flush()

    def _schedule_flush(self) -> None:
        if self._flush_task is None or self._flush_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._flush_task = loop.create_task(self._delayed_flush())
            except RuntimeError:
                self._flush_sync()

    async def _delayed_flush(self) -> None:
        await asyncio.sleep(2.0)
        self._flush_sync()
        self._pending_count = 0

    def _flush_sync(self) -> None:
        fp = self._file_path()
        try:
            data = {"entries": [e.to_dict() for e in self._entries]}
            tmp = fp.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(fp)
        except OSError as e:
            logger.error("Failed to flush interaction memory: %s", e)


class FullRecallMemory:
    def __init__(self, store: InteractionMemoryStore | None = None):
        self._store = store or InteractionMemoryStore()

    def ensure_loaded(self) -> None:
        self._store.load()

    async def record(
        self,
        content: str,
        role: str = "",
        emotion_label: str = "",
        emotion_intensity: float = 0.0,
        inner_voice: str = "",
        session_id: str = "",
        topic: str = "",
        tags: list[str] | None = None,
        importance: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        self.ensure_loaded()
        entry = InteractionMemoryEntry(
            content=content,
            role=role,
            emotion_label=emotion_label,
            emotion_intensity=emotion_intensity,
            inner_voice=inner_voice,
            session_id=session_id,
            topic=topic,
            tags=tags or [],
            importance=importance,
            metadata=metadata or {},
        )
        self._store.add_entry(entry)

        await audit_service.record(
            category=AuditCategory.MEMORY_WRITE,
            action="interaction_memory_record",
            level=AuditLevel.INFO,
            actor_type="interaction_agent",
            resource_type="interaction_memory",
            resource_id=entry.id,
            status="success",
            detail=json.dumps({
                "content_length": len(content),
                "role": role,
                "emotion_label": emotion_label,
                "session_id": session_id,
            }, ensure_ascii=False),
        )

        return entry.id

    async def retrieve(self, query: str, top_k: int = 5) -> list:
        self.ensure_loaded()
        results = await self.search(query, limit=top_k)
        if results:
            return results
        return await self.recall_recent(count=top_k)

    async def recall_all(self, limit: int = 0) -> list[InteractionMemoryEntry]:
        self.ensure_loaded()
        entries = self._store._entries
        if limit > 0:
            return list(entries[-limit:])
        return list(entries)

    async def recall_by_session(self, session_id: str) -> list[InteractionMemoryEntry]:
        self.ensure_loaded()
        indices = self._store._session_index.get(session_id, [])
        return [self._store._entries[i] for i in indices if i < len(self._store._entries)]

    async def recall_by_topic(self, topic: str, limit: int = 0) -> list[InteractionMemoryEntry]:
        self.ensure_loaded()
        indices = self._store._topic_index.get(topic, set())
        entries = [self._store._entries[i] for i in indices if i < len(self._store._entries)]
        entries.sort(key=lambda e: e.created_at, reverse=True)
        if limit > 0:
            return entries[:limit]
        return entries

    async def recall_recent(self, count: int = 50) -> list[InteractionMemoryEntry]:
        self.ensure_loaded()
        return list(self._store._entries[-count:])

    async def recall_with_emotion(
        self, emotion_label: str = "", min_intensity: float = 0.0, limit: int = 0
    ) -> list[InteractionMemoryEntry]:
        self.ensure_loaded()
        results = []
        for entry in reversed(self._store._entries):
            if emotion_label and entry.emotion_label != emotion_label:
                continue
            if entry.emotion_intensity < min_intensity:
                continue
            results.append(entry)
            if limit > 0 and len(results) >= limit:
                break
        return results

    async def search(self, query: str, limit: int = 0) -> list[InteractionMemoryEntry]:
        self.ensure_loaded()
        query_lower = query.lower()
        strip_chars = ".,!?;:()[]{}\"'"
        query_words = [
            w.strip(strip_chars).strip()
            for w in query_lower.split()
            if len(w.strip(strip_chars).strip()) >= 2
        ]

        scored: list[tuple[float, InteractionMemoryEntry]] = []

        if query_words and self._store._keyword_index:
            candidate_indices: dict[int, float] = {}
            for word in query_words:
                for indexed_word, indices in self._store._keyword_index.items():
                    if word in indexed_word or indexed_word in word:
                        for idx in indices:
                            candidate_indices[idx] = candidate_indices.get(idx, 0.0) + 1.0

            for idx, score in candidate_indices.items():
                if idx < len(self._store._entries):
                    entry = self._store._entries[idx]
                    if query_lower in entry.content.lower():
                        score += 2.0
                    if any(query_lower in tag.lower() for tag in entry.tags):
                        score += 1.5
                    if query_lower in entry.topic.lower():
                        score += 1.5
                    if entry.importance > 0:
                        score += entry.importance * 0.5
                    scored.append((score, entry))
        else:
            for entry in reversed(self._store._entries):
                score = 0.0
                if query_lower in entry.content.lower():
                    score += 2.0
                if any(query_lower in tag.lower() for tag in entry.tags):
                    score += 1.5
                if query_lower in entry.topic.lower():
                    score += 1.5
                if entry.importance > 0:
                    score += entry.importance * 0.5
                if score > 0:
                    scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [entry for _, entry in scored]
        if limit > 0:
            return results[:limit]
        return results

    def get_summary(self) -> dict[str, Any]:
        self.ensure_loaded()
        entries = self._store._entries
        emotion_counts: dict[str, int] = {}
        topic_counts: dict[str, int] = {}
        for e in entries:
            if e.emotion_label:
                emotion_counts[e.emotion_label] = emotion_counts.get(e.emotion_label, 0) + 1
            if e.topic:
                topic_counts[e.topic] = topic_counts.get(e.topic, 0) + 1
        return {
            "total_entries": len(entries),
            "sessions": len(self._store._session_index),
            "topics": len(self._store._topic_index),
            "emotion_distribution": emotion_counts,
            "top_topics": dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        }


_interaction_memory: FullRecallMemory | None = None


def get_interaction_memory() -> FullRecallMemory:
    global _interaction_memory
    if _interaction_memory is None:
        _interaction_memory = FullRecallMemory()
    return _interaction_memory
