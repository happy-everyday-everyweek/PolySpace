from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class KnowledgeEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    source: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeService:
    def __init__(self, data_dir: str | None = None) -> None:
        if data_dir is None:
            data_dir = os.path.join(os.getcwd(), "data", "knowledge")
        self._data_dir = data_dir
        self._entries: dict[str, KnowledgeEntry] = {}
        self._vector_store = None
        os.makedirs(data_dir, exist_ok=True)

    async def add_entry(self, title: str, content: str, source: str = "", tags: list[str] | None = None, **metadata: Any) -> KnowledgeEntry:
        entry = KnowledgeEntry(title=title, content=content, source=source, tags=tags or [], metadata=metadata)
        self._entries[entry.entry_id] = entry
        if self._vector_store:
            try:
                from app.core.memory.vector_store import VectorStore
                if isinstance(self._vector_store, VectorStore):
                    await self._vector_store.add(entry.entry_id, content, {"title": title, "tags": tags})
            except Exception:
                pass
        return entry

    async def get_entry(self, entry_id: str) -> KnowledgeEntry | None:
        return self._entries.get(entry_id)

    async def update_entry(self, entry_id: str, **updates: Any) -> KnowledgeEntry | None:
        entry = self._entries.get(entry_id)
        if not entry:
            return None
        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        entry.updated_at = datetime.now().isoformat()
        return entry

    async def delete_entry(self, entry_id: str) -> bool:
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    async def search(self, query: str, limit: int = 10) -> list[KnowledgeEntry]:
        if self._vector_store:
            try:
                from app.core.memory.vector_store import VectorStore
                if isinstance(self._vector_store, VectorStore):
                    results = await self._vector_store.search(query, limit)
                    entries = []
                    for r in results:
                        entry = self._entries.get(r.get("id", ""))
                        if entry:
                            entries.append(entry)
                    return entries
            except Exception:
                pass

        query_lower = query.lower()
        results = []
        for entry in self._entries.values():
            score = 0
            if query_lower in entry.title.lower():
                score += 3
            if query_lower in entry.content.lower():
                score += 2
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 1
            if score > 0:
                results.append((score, entry))
        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results[:limit]]

    async def list_entries(self, tag: str | None = None, limit: int = 50) -> list[KnowledgeEntry]:
        entries = list(self._entries.values())
        if tag:
            entries = [e for e in entries if tag in e.tags]
        return sorted(entries, key=lambda e: e.updated_at, reverse=True)[:limit]

    async def upload_file(self, filename: str, content: str, source: str = "") -> KnowledgeEntry:
        return await self.add_entry(
            title=filename,
            content=content,
            source=source or "file_upload",
            tags=["uploaded", "file"],
            filename=filename,
        )


knowledge_service = KnowledgeService()
