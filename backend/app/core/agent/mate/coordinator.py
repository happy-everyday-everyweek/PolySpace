import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.core.agent.base import BaseAgent
from app.core.llm.dispatcher import ModelDispatcher, TaskCategory
from app.core.tool.registry import ToolRegistry


@dataclass
class AgentTask:
    id: str
    description: str
    assigned_agent: Optional[str] = None
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class MateCoordinator:
    def __init__(self, model_dispatcher: ModelDispatcher, tool_registry: Optional[ToolRegistry] = None):
        self._dispatcher = model_dispatcher
        self._tool_registry = tool_registry
        self._agents: dict[str, BaseAgent] = {}
        self._tasks: dict[str, AgentTask] = {}
        self._fallback_agents: dict[str, list[str]] = {}

    def register_agent(self, agent: BaseAgent, fallback_names: Optional[list[str]] = None) -> None:
        self._agents[agent.name] = agent
        if fallback_names:
            self._fallback_agents[agent.name] = fallback_names

    def unregister_agent(self, name: str) -> None:
        self._agents.pop(name, None)
        self._fallback_agents.pop(name, None)

    async def delegate(self, task: AgentTask) -> AgentTask:
        if not task.assigned_agent:
            task.assigned_agent = await self._select_agent(task.description)
        agent = self._agents.get(task.assigned_agent)
        if not agent:
            task.status = "error"
            task.error = f"Agent '{task.assigned_agent}' not found"
            return task
        try:
            task.status = "running"
            result = await agent.run(task.description)
            task.result = result
            task.status = "completed"
        except Exception as e:
            task.status = "error"
            task.error = str(e)
            task = await self._handle_failure(task)
        return task

    async def delegate_parallel(self, tasks: list[AgentTask]) -> list[AgentTask]:
        results = await asyncio.gather(
            *[self.delegate(t) for t in tasks],
            return_exceptions=True,
        )
        completed = []
        for r in results:
            if isinstance(r, Exception):
                completed.append(AgentTask(id="error", description=str(r), status="error", error=str(r)))
            else:
                completed.append(r)
        return completed

    async def _select_agent(self, description: str) -> str:
        if not self._agents:
            raise RuntimeError("No agents registered")
        agent_names = list(self._agents.keys())
        if len(agent_names) == 1:
            return agent_names[0]
        messages = [
            {
                "role": "system",
                "content": (
                    "Select the best agent for this task. "
                    f"Available agents: {', '.join(agent_names)}. "
                    "Respond with only the agent name."
                ),
            },
            {"role": "user", "content": description},
        ]
        response = await self._dispatcher.dispatch(
            TaskCategory.INTENT,
            messages=messages,
        )
        selected = response.choices[0].message.content.strip()
        if selected in self._agents:
            return selected
        return agent_names[0]

    async def _handle_failure(self, task: AgentTask) -> AgentTask:
        fallbacks = self._fallback_agents.get(task.assigned_agent, [])
        for fallback_name in fallbacks:
            fallback_agent = self._agents.get(fallback_name)
            if fallback_agent:
                try:
                    result = await fallback_agent.run(task.description)
                    task.result = result
                    task.status = "completed"
                    task.assigned_agent = fallback_name
                    return task
                except Exception:
                    continue
        return task

    def get_task_status(self, task_id: str) -> Optional[AgentTask]:
        return self._tasks.get(task_id)

    def list_agents(self) -> list[dict]:
        return [
            {"name": agent.name, "description": agent.description}
            for agent in self._agents.values()
        ]
