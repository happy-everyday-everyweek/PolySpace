import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from app.core.agent.base import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)
    examples: list[str] = field(default_factory=list)


@dataclass
class AgentDescriptor:
    name: str
    description: str
    capabilities: list[AgentCapability] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    fallback_names: list[str] = field(default_factory=list)
    max_concurrent: int = 3
    timeout_seconds: float = 300.0


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
        self._descriptors: dict[str, AgentDescriptor] = {}
        self._factories: dict[str, Callable[[], BaseAgent]] = {}

    def register(
        self,
        agent: BaseAgent,
        fallback_names: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        max_concurrent: int = 3,
        timeout_seconds: float = 300.0,
    ) -> None:
        self._agents[agent.name] = agent
        self._descriptors[agent.name] = AgentDescriptor(
            name=agent.name,
            description=agent.description,
            tags=tags or [],
            fallback_names=fallback_names or [],
            max_concurrent=max_concurrent,
            timeout_seconds=timeout_seconds,
        )

    def register_factory(
        self,
        name: str,
        description: str,
        factory: Callable[[], BaseAgent],
        tags: Optional[list[str]] = None,
        fallback_names: Optional[list[str]] = None,
    ) -> None:
        self._factories[name] = factory
        self._descriptors[name] = AgentDescriptor(
            name=name,
            description=description,
            tags=tags or [],
            fallback_names=fallback_names or [],
        )

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)
        self._descriptors.pop(name, None)
        self._factories.pop(name, None)

    def get(self, name: str) -> Optional[BaseAgent]:
        if name in self._agents:
            return self._agents[name]
        if name in self._factories:
            agent = self._factories[name]()
            self._agents[name] = agent
            return agent
        return None

    def get_descriptor(self, name: str) -> Optional[AgentDescriptor]:
        return self._descriptors.get(name)

    def list_agents(self) -> list[dict]:
        result = []
        for name, desc in self._descriptors.items():
            result.append({
                "name": desc.name,
                "description": desc.description,
                "tags": desc.tags,
                "capabilities": [{"name": c.name, "description": c.description} for c in desc.capabilities],
                "fallback_names": desc.fallback_names,
                "loaded": name in self._agents,
            })
        return result

    def find_by_tag(self, tag: str) -> list[BaseAgent]:
        agents = []
        for name, desc in self._descriptors.items():
            if tag in desc.tags:
                agent = self.get(name)
                if agent:
                    agents.append(agent)
        return agents

    def find_by_capability(self, capability_name: str) -> list[BaseAgent]:
        agents = []
        for name, desc in self._descriptors.items():
            for cap in desc.capabilities:
                if cap.name == capability_name:
                    agent = self.get(name)
                    if agent:
                        agents.append(agent)
                    break
        return agents


agent_registry = AgentRegistry()
