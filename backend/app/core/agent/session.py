import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_key: str = ""
    agent_name: str = ""
    channel: str = "web"
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    message_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionRouter:
    def __init__(self, max_sessions: int = 5000, idle_ttl_seconds: float = 86400):
        self._sessions: dict[str, Session] = {}
        self._key_to_id: dict[str, str] = {}
        self._max_sessions = max_sessions
        self._idle_ttl = idle_ttl_seconds

    def create_session(
        self,
        agent_name: str = "main",
        channel: str = "web",
        session_key: str | None = None,
        metadata: dict | None = None,
    ) -> Session:
        if not session_key:
            session_key = f"agent:{agent_name}:{channel}"

        if session_key in self._key_to_id:
            existing_id = self._key_to_id[session_key]
            existing = self._sessions.get(existing_id)
            if existing:
                existing.last_active_at = time.time()
                existing.message_count += 1
                return existing

        self._evict_idle()

        session = Session(
            session_key=session_key,
            agent_name=agent_name,
            channel=channel,
            metadata=metadata or {},
        )
        self._sessions[session.id] = session
        self._key_to_id[session_key] = session.id
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session:
            session.last_active_at = time.time()
        return session

    def get_by_key(self, session_key: str) -> Optional[Session]:
        session_id = self._key_to_id.get(session_key)
        if session_id:
            return self.get_session(session_id)
        return None

    def resolve_agent(self, session_key: str) -> str:
        parts = session_key.split(":")
        if len(parts) >= 2 and parts[0] == "agent":
            return parts[1]
        if len(parts) >= 2 and parts[0] == "cron":
            return "cron"
        if len(parts) >= 2 and parts[0] == "acp":
            return "acp"
        return "main"

    def list_sessions(self, agent_name: str | None = None) -> list[dict]:
        sessions = self._sessions.values()
        if agent_name:
            sessions = [s for s in sessions if s.agent_name == agent_name]
        return [
            {
                "id": s.id,
                "session_key": s.session_key,
                "agent_name": s.agent_name,
                "channel": s.channel,
                "message_count": s.message_count,
                "last_active_at": s.last_active_at,
            }
            for s in sessions
        ]

    def close_session(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if session:
            self._key_to_id.pop(session.session_key, None)
            return True
        return False

    def _evict_idle(self):
        if len(self._sessions) < self._max_sessions:
            return
        now = time.time()
        cutoff = now - self._idle_ttl
        to_remove = [
            sid for sid, s in self._sessions.items()
            if s.last_active_at < cutoff
        ]
        for sid in to_remove:
            session = self._sessions.pop(sid)
            self._key_to_id.pop(session.session_key, None)
        if to_remove:
            logger.info(f"Evicted {len(to_remove)} idle sessions")
        if len(self._sessions) >= self._max_sessions:
            oldest = sorted(self._sessions.items(), key=lambda x: x[1].last_active_at)
            for sid, _ in oldest[: len(oldest) // 4]:
                session = self._sessions.pop(sid)
                self._key_to_id.pop(session.session_key, None)


_session_router: SessionRouter | None = None


def get_session_router() -> SessionRouter:
    global _session_router
    if _session_router is None:
        _session_router = SessionRouter()
    return _session_router
