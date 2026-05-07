from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class SproutSection:
    number: int = 0
    title: str = ""
    content: str = ""
    aha_moment: str = ""


@dataclass
class SproutReport:
    title: str = "发芽报告"
    sections: list[SproutSection] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class NoteItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "text"
    title: str = ""
    content: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    category: str = ""
    source_url: str = ""
    attachments: list[str] = field(default_factory=list)
    sprout_report: Optional[SproutReport] = None
    pinned: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class NotesService:
    def __init__(self) -> None:
        self._notes: dict[str, NoteItem] = {}

    async def create_note(
        self,
        title: str,
        content: str = "",
        note_type: str = "text",
        tags: list[str] | None = None,
        category: str = "",
        source_url: str = "",
        attachments: list[str] | None = None,
        pinned: bool = False,
    ) -> NoteItem:
        note = NoteItem(
            title=title,
            content=content,
            type=note_type,
            tags=tags or [],
            category=category,
            source_url=source_url,
            attachments=attachments or [],
            pinned=pinned,
        )
        self._notes[note.id] = note
        return note

    async def get_note(self, note_id: str) -> NoteItem | None:
        return self._notes.get(note_id)

    async def update_note(self, note_id: str, **updates: Any) -> NoteItem | None:
        note = self._notes.get(note_id)
        if not note:
            return None
        for key, value in updates.items():
            if hasattr(note, key):
                setattr(note, key, value)
        note.updated_at = datetime.now().isoformat()
        return note

    async def delete_note(self, note_id: str) -> bool:
        if note_id in self._notes:
            del self._notes[note_id]
            return True
        return False

    async def list_notes(
        self,
        note_type: str | None = None,
        tag: str | None = None,
        category: str | None = None,
        pinned_only: bool = False,
    ) -> list[NoteItem]:
        notes = list(self._notes.values())
        if note_type:
            notes = [n for n in notes if n.type == note_type]
        if tag:
            notes = [n for n in notes if tag in n.tags]
        if category:
            notes = [n for n in notes if n.category == category]
        if pinned_only:
            notes = [n for n in notes if n.pinned]
        pinned = sorted([n for n in notes if n.pinned], key=lambda n: n.updated_at, reverse=True)
        unpinned = sorted([n for n in notes if not n.pinned], key=lambda n: n.updated_at, reverse=True)
        return pinned + unpinned

    async def pin_note(self, note_id: str) -> NoteItem | None:
        note = self._notes.get(note_id)
        if not note:
            return None
        note.pinned = True
        note.updated_at = datetime.now().isoformat()
        return note

    async def unpin_note(self, note_id: str) -> NoteItem | None:
        note = self._notes.get(note_id)
        if not note:
            return None
        note.pinned = False
        note.updated_at = datetime.now().isoformat()
        return note

    async def search_notes(self, query: str) -> list[NoteItem]:
        query_lower = query.lower()
        results = []
        for note in self._notes.values():
            if (query_lower in note.title.lower()
                    or query_lower in note.content.lower()
                    or query_lower in note.summary.lower()
                    or any(query_lower in t.lower() for t in note.tags)):
                results.append(note)
        return sorted(results, key=lambda n: n.updated_at, reverse=True)

    async def set_sprout_report(self, note_id: str, report: SproutReport) -> NoteItem | None:
        note = self._notes.get(note_id)
        if not note:
            return None
        note.sprout_report = report
        note.updated_at = datetime.now().isoformat()
        return note


notes_service = NotesService()
