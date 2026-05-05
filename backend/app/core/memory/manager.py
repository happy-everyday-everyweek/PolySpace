import abc
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class MemoryItem:
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    created_at: str = field(default_factory=_utc_now_iso)
    accessed_at: str = field(default_factory=_utc_now_iso)
    access_count: int = 0
    ttl_seconds: Optional[int] = None


def _create_empty_structured_memory() -> dict[str, Any]:
    return {
        "version": "1.0",
        "lastUpdated": _utc_now_iso(),
        "user": {
            "workContext": {"summary": "", "updatedAt": ""},
            "personalContext": {"summary": "", "updatedAt": ""},
            "topOfMind": {"summary": "", "updatedAt": ""},
        },
        "history": {
            "recentMonths": {"summary": "", "updatedAt": ""},
            "earlierContext": {"summary": "", "updatedAt": ""},
            "longTermBackground": {"summary": "", "updatedAt": ""},
        },
        "facts": [],
    }


class MemoryStorage(abc.ABC):
    @abc.abstractmethod
    def load(self, agent_name: str | None = None) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def save(self, memory_data: dict[str, Any], agent_name: str | None = None) -> bool:
        pass


class FileMemoryStorage(MemoryStorage):
    def __init__(self, base_dir: str | Path | None = None):
        if base_dir is None:
            base_dir = Path(settings.DATA_DIR)
        self._base_dir = Path(base_dir)
        self._memory_dir = self._base_dir / "memory"
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str | None, tuple[dict[str, Any], float | None]] = {}
        self._write_buffer: dict[str | None, dict[str, Any]] = {}
        self._flush_task: Optional[asyncio.Task] = None

    def _get_file_path(self, agent_name: str | None = None) -> Path:
        if agent_name:
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in agent_name)
            return self._memory_dir / f"memory_{safe_name}.json"
        return self._memory_dir / "memory_global.json"

    def load(self, agent_name: str | None = None) -> dict[str, Any]:
        cached = self._cache.get(agent_name)
        file_path = self._get_file_path(agent_name)
        if cached:
            data, mtime = cached
            try:
                current_mtime = file_path.stat().st_mtime if file_path.exists() else None
                if current_mtime == mtime:
                    return data
            except OSError:
                return data

        if not file_path.exists():
            empty = _create_empty_structured_memory()
            self._cache[agent_name] = (empty, None)
            return empty

        try:
            raw = file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            mtime = file_path.stat().st_mtime
            self._cache[agent_name] = (data, mtime)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load memory for {agent_name}: {e}")
            empty = _create_empty_structured_memory()
            self._cache[agent_name] = (empty, None)
            return empty

    def reload(self, agent_name: str | None = None) -> dict[str, Any]:
        self._cache.pop(agent_name, None)
        return self.load(agent_name)

    def save(self, memory_data: dict[str, Any], agent_name: str | None = None) -> bool:
        memory_data["lastUpdated"] = _utc_now_iso()
        self._write_buffer[agent_name] = memory_data
        self._cache[agent_name] = (memory_data, None)
        self._schedule_flush()
        return True

    def _schedule_flush(self) -> None:
        if self._flush_task is None or self._flush_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._flush_task = loop.create_task(self._flush_buffer())
            except RuntimeError:
                self._flush_buffer_sync()

    async def _flush_buffer(self) -> None:
        await asyncio.sleep(2.0)
        self._flush_buffer_sync()

    def _flush_buffer_sync(self) -> None:
        for agent_name, memory_data in list(self._write_buffer.items()):
            file_path = self._get_file_path(agent_name)
            try:
                tmp_path = file_path.with_suffix(".tmp")
                tmp_path.write_text(json.dumps(memory_data, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp_path.replace(file_path)
                mtime = file_path.stat().st_mtime
                self._cache[agent_name] = (memory_data, mtime)
            except OSError as e:
                logger.error("Failed to flush memory for %s: %s", agent_name, e)
        self._write_buffer.clear()


class MemoryManager:
    def __init__(self, vector_store=None, consolidator=None, storage: MemoryStorage | None = None):
        self._vector_store = vector_store
        self._consolidator = consolidator
        self._storage = storage or FileMemoryStorage()
        self._short_term: list[MemoryItem] = []
        self._long_term: list[MemoryItem] = []
        self._max_short_term = 100
        self._keyword_index: dict[str, set[int]] = {}

    def _index_item(self, idx: int, content_lower: str) -> None:
        words = content_lower.split()
        for word in words:
            if len(word) >= 2:
                if word not in self._keyword_index:
                    self._keyword_index[word] = set()
                self._keyword_index[word].add(idx)

    def _rebuild_index(self) -> None:
        self._keyword_index.clear()
        for idx, item in enumerate(self._short_term):
            self._index_item(idx, item.content.lower())

    async def store(self, content: str, metadata: Optional[dict] = None) -> str:
        item_id = str(uuid.uuid4())
        item = MemoryItem(id=item_id, content=content, metadata=metadata or {})
        self._short_term.append(item)
        if len(self._short_term) > self._max_short_term:
            self._short_term = self._short_term[-self._max_short_term:]
            self._rebuild_index()
        else:
            self._index_item(len(self._short_term) - 1, content.lower())
        if self._vector_store:
            await self._vector_store.add([content], [metadata or {}], [item_id])

        await audit_service.record(
            category=AuditCategory.MEMORY_WRITE,
            action="memory_store",
            level=AuditLevel.INFO,
            actor_type="agent",
            resource_type="memory",
            resource_id=item_id,
            status="success",
            detail=json.dumps({
                "content_length": len(content),
                "has_metadata": metadata is not None,
            }, ensure_ascii=False),
        )

        return item_id

    async def retrieve(self, query: str, top_k: int = 5) -> list[MemoryItem]:
        results: list[MemoryItem] = []
        seen_ids: set[str] = set()
        if self._vector_store:
            search_results = await self._vector_store.search(query, top_k)
            for sr in search_results:
                item = MemoryItem(
                    id=sr.get("id", ""),
                    content=sr.get("content", ""),
                    metadata=sr.get("metadata", {}),
                )
                results.append(item)
                seen_ids.add(item.id)

        query_lower = query.lower()
        query_words = query_lower.split()
        candidate_indices: set[int] = set()
        if len(query_words) <= 3 and self._keyword_index:
            for word in query_words:
                if word in self._keyword_index:
                    candidate_indices.update(self._keyword_index[word])
            for idx in candidate_indices:
                if idx < len(self._short_term):
                    item = self._short_term[idx]
                    if item.id not in seen_ids and query_lower in item.content.lower():
                        results.append(item)
                        seen_ids.add(item.id)
        else:
            for item in self._short_term:
                if item.id not in seen_ids and query_lower in item.content.lower():
                    results.append(item)

        await audit_service.record(
            category=AuditCategory.MEMORY_READ,
            action="memory_retrieve",
            level=AuditLevel.INFO,
            actor_type="agent",
            resource_type="memory",
            status="success",
            detail=json.dumps({
                "query_length": len(query),
                "top_k": top_k,
                "results_count": len(results[:top_k]),
            }, ensure_ascii=False),
        )

        return results[:top_k]

    async def consolidate(self) -> None:
        if self._consolidator:
            await self._consolidator.consolidate(self._short_term, self._long_term)

        await audit_service.record(
            category=AuditCategory.MEMORY_CONSOLIDATE,
            action="memory_consolidate",
            level=AuditLevel.INFO,
            actor_type="system",
            resource_type="memory",
            status="success",
            detail=json.dumps({
                "short_term_count": len(self._short_term),
                "long_term_count": len(self._long_term),
            }, ensure_ascii=False),
        )

    def get_short_term_memory(self, limit: int = 20) -> list[MemoryItem]:
        return self._short_term[-limit:]

    def clear_short_term(self) -> None:
        self._short_term.clear()

    def load_structured_memory(self, agent_name: str | None = None) -> dict[str, Any]:
        return self._storage.load(agent_name)

    def save_structured_memory(self, memory_data: dict[str, Any], agent_name: str | None = None) -> bool:
        return self._storage.save(memory_data, agent_name)

    def add_fact(self, content: str, confidence: float = 1.0, agent_name: str | None = None) -> bool:
        memory = self.load_structured_memory(agent_name)
        memory["facts"].append({
            "id": str(uuid.uuid4()),
            "content": content,
            "confidence": confidence,
            "createdAt": _utc_now_iso(),
        })
        return self.save_structured_memory(memory, agent_name)

    def update_user_context(self, section: str, summary: str, agent_name: str | None = None) -> bool:
        memory = self.load_structured_memory(agent_name)
        if section in memory.get("user", {}):
            memory["user"][section]["summary"] = summary
            memory["user"][section]["updatedAt"] = _utc_now_iso()
            return self.save_structured_memory(memory, agent_name)
        return False

    def update_history_context(self, section: str, summary: str, agent_name: str | None = None) -> bool:
        memory = self.load_structured_memory(agent_name)
        if section in memory.get("history", {}):
            memory["history"][section]["summary"] = summary
            memory["history"][section]["updatedAt"] = _utc_now_iso()
            return self.save_structured_memory(memory, agent_name)
        return False


_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
