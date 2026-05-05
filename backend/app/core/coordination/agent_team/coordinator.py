import logging
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ProactiveAgent:
    name: str
    domain: str
    description: str
    is_active: bool = True
    last_check: float = 0.0
    tasks_completed: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "is_active": self.is_active,
            "last_check": self.last_check,
            "tasks_completed": self.tasks_completed,
        }


BUILTIN_SPECIALISTS = [
    ProactiveAgent(name="email_specialist", domain="email", description="Handles email processing and reply suggestions"),
    ProactiveAgent(name="schedule_specialist", domain="schedule", description="Manages time and schedule optimization"),
    ProactiveAgent(name="document_specialist", domain="document", description="Assists with document writing and editing"),
    ProactiveAgent(name="data_specialist", domain="data", description="Handles data analysis and visualization"),
    ProactiveAgent(name="communication_specialist", domain="communication", description="Manages messages and social interactions"),
    ProactiveAgent(name="security_specialist", domain="security", description="Monitors security and privacy"),
    ProactiveAgent(name="wellness_specialist", domain="wellness", description="Tracks health and wellness"),
]


class AgentCoordinator:
    def __init__(self):
        self._agents: dict[str, ProactiveAgent] = {a.name: a for a in BUILTIN_SPECIALISTS}
        self._task_queue: list[dict] = []
        self._max_queue = 50
        self._conflict_resolution: str = "priority"

    def register_agent(self, agent: ProactiveAgent) -> None:
        self._agents[agent.name] = agent

    def unregister_agent(self, name: str) -> bool:
        if name in self._agents:
            del self._agents[name]
            return True
        return False

    async def assign_task(self, task: dict) -> Optional[str]:
        domain = task.get("domain", "")
        best_agent = self._find_best_agent(domain)
        if not best_agent:
            return None
        task_id = f"task_{int(time.time())}_{hash(task.get('description', '')) % 1000}"
        task_entry = {
            "task_id": task_id,
            "agent": best_agent.name,
            "domain": domain,
            "description": task.get("description", ""),
            "status": "assigned",
            "assigned_at": time.time(),
        }
        self._task_queue.append(task_entry)
        if len(self._task_queue) > self._max_queue:
            self._task_queue = self._task_queue[-self._max_queue:]
        best_agent.last_check = time.time()
        return task_id

    def _find_best_agent(self, domain: str) -> Optional[ProactiveAgent]:
        candidates = [a for a in self._agents.values() if a.is_active and a.domain == domain]
        if candidates:
            return min(candidates, key=lambda a: a.tasks_completed)
        generalists = [a for a in self._agents.values() if a.is_active]
        if generalists:
            return min(generalists, key=lambda a: a.tasks_completed)
        return None

    def resolve_conflicts(self, competing_agents: list[str]) -> Optional[str]:
        if self._conflict_resolution == "priority":
            priority_order = ["security_specialist", "email_specialist", "schedule_specialist", "communication_specialist"]
            for agent_name in priority_order:
                if agent_name in competing_agents and agent_name in self._agents:
                    return agent_name
        if competing_agents:
            return competing_agents[0]
        return None

    def list_agents(self) -> list[dict]:
        return [a.to_dict() for a in self._agents.values()]

    def get_task_queue(self, limit: int = 20) -> list[dict]:
        return self._task_queue[-limit:]


_coordinator: Optional[AgentCoordinator] = None


def get_agent_coordinator() -> AgentCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator()
    return _coordinator
