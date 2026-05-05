from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoItem:
    memo_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    color: str = "default"
    pinned: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MemoService:
    def __init__(self) -> None:
        self._memos: dict[str, MemoItem] = {}

    async def create_memo(
        self,
        title: str,
        content: str = "",
        color: str = "default",
        pinned: bool = False,
        tags: list[str] | None = None,
    ) -> MemoItem:
        memo = MemoItem(
            title=title,
            content=content,
            color=color,
            pinned=pinned,
            tags=tags or [],
        )
        self._memos[memo.memo_id] = memo
        return memo

    async def get_memo(self, memo_id: str) -> MemoItem | None:
        return self._memos.get(memo_id)

    async def update_memo(self, memo_id: str, **updates: Any) -> MemoItem | None:
        memo = self._memos.get(memo_id)
        if not memo:
            return None
        for key, value in updates.items():
            if hasattr(memo, key):
                setattr(memo, key, value)
        memo.updated_at = datetime.now().isoformat()
        return memo

    async def delete_memo(self, memo_id: str) -> bool:
        if memo_id in self._memos:
            del self._memos[memo_id]
            return True
        return False

    async def list_memos(self, tag: str | None = None, pinned_only: bool = False) -> list[MemoItem]:
        memos = list(self._memos.values())
        if tag:
            memos = [m for m in memos if tag in m.tags]
        if pinned_only:
            memos = [m for m in memos if m.pinned]
        pinned = sorted([m for m in memos if m.pinned], key=lambda m: m.updated_at, reverse=True)
        unpinned = sorted([m for m in memos if not m.pinned], key=lambda m: m.updated_at, reverse=True)
        return pinned + unpinned

    async def pin_memo(self, memo_id: str) -> MemoItem | None:
        memo = self._memos.get(memo_id)
        if not memo:
            return None
        memo.pinned = True
        memo.updated_at = datetime.now().isoformat()
        return memo

    async def unpin_memo(self, memo_id: str) -> MemoItem | None:
        memo = self._memos.get(memo_id)
        if not memo:
            return None
        memo.pinned = False
        memo.updated_at = datetime.now().isoformat()
        return memo

    async def search_memos(self, query: str) -> list[MemoItem]:
        query_lower = query.lower()
        results = []
        for memo in self._memos.values():
            if query_lower in memo.title.lower() or query_lower in memo.content.lower():
                results.append(memo)
        return sorted(results, key=lambda m: m.updated_at, reverse=True)


memo_service = MemoService()
