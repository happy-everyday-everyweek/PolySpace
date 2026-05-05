from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.core.tool.registry import ToolRegistry


@dataclass
class AgentMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)


@dataclass
class AgentContext:
    messages: list[AgentMessage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.name = name
        self.description = description
        self._tool_registry = tool_registry
        self._context = AgentContext()

    @property
    def context(self) -> AgentContext:
        return self._context

    @abstractmethod
    async def run(self, message: str, **kwargs) -> str:
        ...

    @abstractmethod
    async def think(self, message: str, **kwargs) -> dict:
        ...

    def add_message(self, role: str, content: str) -> None:
        self._context.messages.append(AgentMessage(role=role, content=content))

    def get_history(self, limit: Optional[int] = None) -> list[AgentMessage]:
        if limit:
            return self._context.messages[-limit:]
        return self._context.messages

    def clear_history(self) -> None:
        self._context.messages.clear()
