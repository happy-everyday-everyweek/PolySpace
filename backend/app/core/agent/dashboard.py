from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentRunEvent:
    agent_name: str
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentRunTrace:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: list[AgentRunEvent] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    status: str = "running"

    def add_event(self, event: AgentRunEvent) -> None:
        self.events.append(event)
        if event.event_type in ("complete", "error"):
            self.status = "completed" if event.event_type == "complete" else "error"

    @property
    def duration(self) -> float:
        if not self.events:
            return 0.0
        return self.events[-1].timestamp - self.created_at

    @property
    def agent_names(self) -> list[str]:
        seen = set()
        result = []
        for e in self.events:
            if e.agent_name not in seen:
                seen.add(e.agent_name)
                result.append(e.agent_name)
        return result

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        return [
            {"agent": e.agent_name, **e.data}
            for e in self.events
            if e.event_type == "tool_call"
        ]


class DashboardManager:
    def __init__(self, max_traces: int = 500) -> None:
        self._traces: dict[str, AgentRunTrace] = {}
        self._max_traces = max_traces

    def create_trace(self, trace_id: str | None = None) -> AgentRunTrace:
        trace = AgentRunTrace(trace_id=trace_id or str(uuid.uuid4()))
        self._traces[trace.trace_id] = trace
        self._evict_if_needed()
        return trace

    def add_event(self, trace_id: str, event: AgentRunEvent) -> AgentRunTrace | None:
        trace = self._traces.get(trace_id)
        if not trace:
            trace = self.create_trace(trace_id)
        trace.add_event(event)
        return trace

    def get_trace(self, trace_id: str) -> AgentRunTrace | None:
        return self._traces.get(trace_id)

    def list_traces(self, limit: int = 50, status: str | None = None) -> list[AgentRunTrace]:
        traces = list(self._traces.values())
        if status:
            traces = [t for t in traces if t.status == status]
        traces.sort(key=lambda t: t.created_at, reverse=True)
        return traces[:limit]

    def get_active_traces(self) -> list[AgentRunTrace]:
        return [t for t in self._traces.values() if t.status == "running"]

    def get_stats(self) -> dict[str, Any]:
        total = len(self._traces)
        active = sum(1 for t in self._traces.values() if t.status == "running")
        completed = sum(1 for t in self._traces.values() if t.status == "completed")
        errors = sum(1 for t in self._traces.values() if t.status == "error")
        return {
            "total_traces": total,
            "active": active,
            "completed": completed,
            "errors": errors,
        }

    def _evict_if_needed(self) -> None:
        if len(self._traces) <= self._max_traces:
            return
        traces = sorted(self._traces.values(), key=lambda t: t.created_at)
        while len(self._traces) > self._max_traces * 0.8:
            oldest = traces.pop(0)
            self._traces.pop(oldest.trace_id, None)


dashboard_manager = DashboardManager()
