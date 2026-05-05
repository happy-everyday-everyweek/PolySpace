from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ThreadStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ThreadMessage:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreadState:
    thread_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ThreadStatus = ThreadStatus.ACTIVE
    messages: list[ThreadMessage] = field(default_factory=list)
    title: str | None = None
    summary: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, **metadata: Any) -> None:
        self.messages.append(ThreadMessage(role=role, content=content, metadata=metadata))
        self.updated_at = time.time()
        if self.status == ThreadStatus.IDLE:
            self.status = ThreadStatus.ACTIVE

    def get_recent_messages(self, count: int = 20) -> list[ThreadMessage]:
        return self.messages[-count:]

    def to_openai_messages(self) -> list[dict[str, str]]:
        result = []
        if self.summary:
            result.append({"role": "system", "content": f"Previous conversation summary: {self.summary}"})
        for msg in self.messages:
            result.append({"role": msg.role, "content": msg.content})
        return result

    def mark_idle(self) -> None:
        if self.status == ThreadStatus.ACTIVE:
            self.status = ThreadStatus.IDLE
            self.updated_at = time.time()

    def mark_completed(self) -> None:
        self.status = ThreadStatus.COMPLETED
        self.updated_at = time.time()

    def mark_error(self) -> None:
        self.status = ThreadStatus.ERROR
        self.updated_at = time.time()


class ThreadStateManager:
    def __init__(self, max_threads: int = 1000, idle_timeout: float = 3600.0) -> None:
        self._threads: dict[str, ThreadState] = {}
        self._max_threads = max_threads
        self._idle_timeout = idle_timeout

    def create_thread(self, title: str | None = None) -> ThreadState:
        thread = ThreadState(title=title)
        self._threads[thread.thread_id] = thread
        self._evict_if_needed()
        return thread

    def get_thread(self, thread_id: str) -> ThreadState | None:
        return self._threads.get(thread_id)

    def get_or_create(self, thread_id: str) -> ThreadState:
        if thread_id in self._threads:
            return self._threads[thread_id]
        thread = ThreadState(thread_id=thread_id)
        self._threads[thread_id] = thread
        return thread

    def delete_thread(self, thread_id: str) -> bool:
        if thread_id in self._threads:
            del self._threads[thread_id]
            return True
        return False

    def list_threads(self, status: ThreadStatus | None = None) -> list[ThreadState]:
        threads = list(self._threads.values())
        if status:
            threads = [t for t in threads if t.status == status]
        return sorted(threads, key=lambda t: t.updated_at, reverse=True)

    def add_message(self, thread_id: str, role: str, content: str, **metadata: Any) -> ThreadState:
        thread = self.get_or_create(thread_id)
        thread.add_message(role, content, **metadata)
        return thread

    def cleanup_idle(self) -> int:
        now = time.time()
        to_remove = []
        for tid, thread in self._threads.items():
            if thread.status == ThreadStatus.IDLE and (now - thread.updated_at) > self._idle_timeout:
                to_remove.append(tid)
            elif thread.status == ThreadStatus.COMPLETED and (now - thread.updated_at) > self._idle_timeout * 2:
                to_remove.append(tid)

        for tid in to_remove:
            del self._threads[tid]

        return len(to_remove)

    def _evict_if_needed(self) -> None:
        if len(self._threads) <= self._max_threads:
            return
        threads = self.list_threads()
        while len(self._threads) > self._max_threads * 0.8 and threads:
            oldest = threads.pop()
            if oldest.status == ThreadStatus.ACTIVE:
                continue
            self._threads.pop(oldest.thread_id, None)


thread_state_manager = ThreadStateManager()
