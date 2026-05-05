from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    PLANNER = "planner"
    DISPATCHER = "dispatcher"
    SUB = "sub"
    VERTICAL = "vertical"
    SUPERVISOR = "supervisor"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNED = "planned"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class ExecutionMode(str, Enum):
    AUTO = "auto"
    SINGLE = "single"
    MULTI = "multi"


class AgentTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    goal: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: str = ""
    parent_task_id: str | None = None
    sub_tasks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    supplements: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PlanStep:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    agent_role: AgentRole = AgentRole.SUB
    agent_name: str = ""
    dependencies: list[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    status: TaskStatus = TaskStatus.PENDING


@dataclass
class Plan:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    goal: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    rationale: str = ""
    created_at: float = field(default_factory=time.time)
    status: TaskStatus = TaskStatus.PENDING


@dataclass
class SupervisionReport:
    task_id: str = ""
    agent_name: str = ""
    quality_score: float = 0.0
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    approved: bool = True
    timestamp: float = field(default_factory=time.time)


class BaseAgentRole(ABC):
    def __init__(self, role: AgentRole, name: str, description: str = ""):
        self.role = role
        self.name = name
        self.description = description
        self._llm_call: Any = None

    def set_llm_call(self, fn):
        self._llm_call = fn

    async def _call_llm(self, prompt: str, system: str = "") -> str:
        if self._llm_call:
            return await self._llm_call(prompt, system)
        return ""

    @abstractmethod
    async def execute(self, task: AgentTask, context: dict | None = None) -> Any:
        ...


class PlanningAgent(BaseAgentRole):
    def __init__(self):
        super().__init__(AgentRole.PLANNER, "planner", "Decomposes complex tasks into executable plans with ordered steps")
        self._plan_history: list[Plan] = []

    async def execute(self, task: AgentTask, context: dict | None = None) -> Plan:
        prompt = f"""You are a task planning agent. Decompose the following task into a structured execution plan.

Task: {task.description}
Goal: {task.goal}
Priority: {task.priority.value}

Available agent roles:
- sub: Generic sub-agent for specific sub-tasks (can be dynamically created)
- vertical: Domain-specific agents (seo, education, pdf, markitdown, finance, etc.)
- supervisor: Quality monitoring and approval

Return JSON:
{{
  "rationale": "Why this plan structure",
  "steps": [
    {{
      "description": "Step description",
      "agent_role": "sub|vertical|supervisor",
      "agent_name": "specific agent name or empty for auto-assign",
      "dependencies": ["step_id_that_must_complete_first"],
      "estimated_duration": 30.0
    }}
  ]
}}"""

        response = await self._call_llm(prompt, "You are a task planning specialist. Create efficient, dependency-aware plans.")
        plan = Plan(task_id=task.id, goal=task.goal)
        try:
            parsed = json.loads(response)
            plan.rationale = parsed.get("rationale", "")
            for step_raw in parsed.get("steps", []):
                step = PlanStep(
                    description=step_raw.get("description", ""),
                    agent_role=AgentRole(step_raw.get("agent_role", "sub")),
                    agent_name=step_raw.get("agent_name", ""),
                    dependencies=step_raw.get("dependencies", []),
                    estimated_duration=step_raw.get("estimated_duration", 0),
                )
                plan.steps.append(step)
        except (json.JSONDecodeError, ValueError):
            plan.steps.append(PlanStep(
                description=task.description,
                agent_role=AgentRole.SUB,
                estimated_duration=60,
            ))
            plan.rationale = "Fallback: single-step plan due to parse error"

        self._plan_history.append(plan)
        return plan

    def get_plans(self, limit: int = 20) -> list[dict]:
        return [
            {"id": p.id, "task_id": p.task_id, "goal": p.goal, "steps": len(p.steps), "status": p.status.value}
            for p in self._plan_history[-limit:]
        ]


class DispatchAgent(BaseAgentRole):
    def __init__(self):
        super().__init__(AgentRole.DISPATCHER, "dispatcher", "Assigns plan steps to appropriate agents and manages execution flow")
        self._active_sub_agents: dict[str, BaseAgentRole] = {}
        self._execution_log: list[dict] = []

    async def execute(self, task: AgentTask, context: dict | None = None) -> Any:
        plan_data = context or {}
        plan: Plan | None = plan_data.get("plan")
        if not plan:
            return {"error": "No plan provided for dispatch"}

        results = {}
        completed_steps: set[str] = set()
        max_iterations = len(plan.steps) * 2

        for _ in range(max_iterations):
            ready_steps = [
                s for s in plan.steps
                if s.status == TaskStatus.PENDING
                and all(dep in completed_steps for dep in s.dependencies)
            ]
            if not ready_steps:
                if all(s.status in (TaskStatus.COMPLETED, TaskStatus.FAILED) for s in plan.steps):
                    break
                pending = [s for s in plan.steps if s.status == TaskStatus.PENDING]
                if not pending:
                    break
                for s in pending:
                    s.dependencies = []
                continue

            concurrent_tasks = []
            for step in ready_steps:
                step.status = TaskStatus.RUNNING
                agent = self._resolve_agent(step)
                sub_task = AgentTask(
                    description=step.description,
                    goal=step.description,
                    priority=task.priority,
                    status=TaskStatus.RUNNING,
                )
                concurrent_tasks.append((step, agent, sub_task))

            async def _execute_step(step: PlanStep, agent: BaseAgentRole, sub_task: AgentTask) -> tuple[PlanStep, Any, bool, str | None]:
                try:
                    result = await agent.execute(sub_task)
                    return step, result, True, None
                except Exception as exc:
                    return step, {"error": str(exc)}, False, str(exc)

            gather_results = await asyncio.gather(
                *[_execute_step(step, agent, sub_task) for step, agent, sub_task in concurrent_tasks],
                return_exceptions=False,
            )

            for step, result, success, error in gather_results:
                if success:
                    step.status = TaskStatus.COMPLETED
                    results[step.id] = result
                    completed_steps.add(step.id)
                    self._execution_log.append({
                        "step_id": step.id, "agent": step.description[:30], "status": "completed",
                        "timestamp": time.time(),
                    })
                else:
                    step.status = TaskStatus.FAILED
                    results[step.id] = result
                    completed_steps.add(step.id)
                    self._execution_log.append({
                        "step_id": step.id, "agent": step.description[:30], "status": "failed",
                        "error": error, "timestamp": time.time(),
                    })

        plan.status = TaskStatus.COMPLETED
        return {"plan_id": plan.id, "results": results, "steps_completed": len(completed_steps)}

    def _resolve_agent(self, step: PlanStep) -> BaseAgentRole:
        if step.agent_name and step.agent_name in self._active_sub_agents:
            return self._active_sub_agents[step.agent_name]

        if step.agent_role == AgentRole.VERTICAL:
            return self._get_vertical_agent(step.agent_name)

        agent = SubAgent(name=f"sub_{step.id[:8]}")
        if self._llm_call:
            agent.set_llm_call(self._llm_call)
        self._active_sub_agents[agent.name] = agent
        return agent

    def _get_vertical_agent(self, name: str) -> BaseAgentRole:
        from app.core.agent.vertical_agents import get_vertical_agent
        agent = get_vertical_agent(name)
        if agent:
            if self._llm_call:
                agent.set_llm_call(self._llm_call)
            return agent
        agent = SubAgent(name=f"vertical_{name}")
        if self._llm_call:
            agent.set_llm_call(self._llm_call)
        return agent

    def spawn_sub_agent(self, name: str, description: str = "") -> SubAgent:
        agent = SubAgent(name=name, description=description)
        if self._llm_call:
            agent.set_llm_call(self._llm_call)
        self._active_sub_agents[name] = agent
        return agent

    def get_active_agents(self) -> list[dict]:
        return [{"name": a.name, "role": a.role.value, "description": a.description} for a in self._active_sub_agents.values()]


class SubAgent(BaseAgentRole):
    def __init__(self, name: str = "", description: str = ""):
        super().__init__(AgentRole.SUB, name or f"sub_{str(uuid.uuid4())[:8]}", description or "Dynamically created sub-agent for specific tasks")

    async def execute(self, task: AgentTask, context: dict | None = None) -> Any:
        prompt = f"""Execute the following task and return the result.

Task: {task.description}
Goal: {task.goal}

Return a JSON result with your findings or actions taken.
If the task requires using tools, describe which tools you would call and with what parameters."""

        response = await self._call_llm(prompt, f"You are {self.name}, a specialized sub-agent. Execute the task precisely.")
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"result": response}


class VerticalAgent(BaseAgentRole):
    def __init__(self, name: str, domain: str, description: str = "", system_prompt: str = "", tools: list[str] | None = None):
        super().__init__(AgentRole.VERTICAL, name, description or f"Vertical domain agent for {domain}")
        self.domain = domain
        self.system_prompt = system_prompt or f"You are a specialized {domain} agent."
        self.tools = tools or []
        self._is_built_in = False
        self._creator = "system"

    async def execute(self, task: AgentTask, context: dict | None = None) -> Any:
        tools_desc = f"\nAvailable tools: {', '.join(self.tools)}" if self.tools else ""
        prompt = f"""Execute the following task using your {self.domain} expertise.

Task: {task.description}
Goal: {task.goal}{tools_desc}

Return JSON with your result."""

        response = await self._call_llm(prompt, self.system_prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"result": response}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "is_built_in": self._is_built_in,
            "creator": self._creator,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VerticalAgent":
        agent = cls(
            name=data.get("name", ""),
            domain=data.get("domain", ""),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            tools=data.get("tools", []),
        )
        agent._is_built_in = data.get("is_built_in", False)
        agent._creator = data.get("creator", "system")
        return agent


class SupervisorAgent(BaseAgentRole):
    def __init__(self):
        super().__init__(AgentRole.SUPERVISOR, "supervisor", "Monitors agent execution quality, detects issues, and approves or rejects results")
        self._reports: list[SupervisionReport] = []
        self._quality_threshold = 0.6

    async def execute(self, task: AgentTask, context: dict | None = None) -> SupervisionReport:
        ctx = context or {}
        result = ctx.get("result")
        agent_name = ctx.get("agent_name", task.assigned_to)

        prompt = f"""Review the following agent execution result for quality.

Original task: {task.description}
Executed by: {agent_name}
Result: {json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)}

Evaluate:
1. Does the result address the task? (0-1 score)
2. Are there any issues or errors?
3. Any suggestions for improvement?

Return JSON:
{{
  "quality_score": 0.0-1.0,
  "issues": ["issue1", ...],
  "suggestions": ["suggestion1", ...],
  "approved": true/false
}}"""

        response = await self._call_llm(prompt, "You are a quality assurance supervisor. Be thorough but fair.")
        report = SupervisionReport(task_id=task.id, agent_name=agent_name)
        try:
            parsed = json.loads(response)
            report.quality_score = float(parsed.get("quality_score", 0))
            report.issues = parsed.get("issues", [])
            report.suggestions = parsed.get("suggestions", [])
            report.approved = parsed.get("approved", report.quality_score >= self._quality_threshold)
        except (json.JSONDecodeError, ValueError):
            report.quality_score = 0.5
            report.issues = ["Failed to parse supervisor evaluation"]
            report.approved = True

        self._reports.append(report)
        return report

    def get_reports(self, limit: int = 50) -> list[dict]:
        return [
            {"task_id": r.task_id, "agent_name": r.agent_name, "quality_score": r.quality_score,
             "approved": r.approved, "issues": r.issues, "timestamp": r.timestamp}
            for r in self._reports[-limit:]
        ]


class MultiAgentOrchestrator:
    def __init__(self):
        self.planner = PlanningAgent()
        self.dispatcher = DispatchAgent()
        self.supervisor = SupervisorAgent()
        self._vertical_agents: dict[str, VerticalAgent] = {}
        self._tasks: dict[str, AgentTask] = {}
        self._mode: str = "auto"
        self._llm_call: Any = None
        self._evolution: Any = None

    def set_llm_call(self, fn):
        self._llm_call = fn
        self.planner.set_llm_call(fn)
        self.dispatcher.set_llm_call(fn)
        self.supervisor.set_llm_call(fn)

    def set_evolution_engine(self, engine):
        self._evolution = engine

    def set_mode(self, mode: str):
        if mode not in ("auto", "single", "multi"):
            raise ValueError(f"Invalid execution mode: {mode}. Must be 'auto', 'single', or 'multi'")
        self._mode = mode

    def _decide_mode(self, task: AgentTask) -> str:
        if self._mode != "auto":
            return self._mode
        desc = task.description.lower()
        goal = task.goal.lower()
        combined = f"{desc} {goal}"
        multi_keywords = [
            "分析并生成", "调研并总结", "多步骤", "协调", "协作",
            "同时", "并行", "多个", "综合", "规划并执行",
            "analyze and generate", "research and summarize", "multi-step",
            "coordinate", "collaborate", "parallel", "multiple",
            "comprehensive", "plan and execute",
        ]
        single_keywords = [
            "简单", "单个", "直接", "快速", "查询",
            "simple", "single", "direct", "quick", "query", "lookup",
        ]
        multi_score = sum(1 for kw in multi_keywords if kw in combined)
        single_score = sum(1 for kw in single_keywords if kw in combined)
        if multi_score > single_score:
            return "multi"
        if single_score > multi_score:
            return "single"
        if len(combined) > 200 or task.priority in (TaskPriority.HIGH, TaskPriority.URGENT):
            return "multi"
        return "single"

    def register_vertical_agent(self, agent: VerticalAgent):
        self._vertical_agents[agent.name] = agent
        if self._llm_call:
            agent.set_llm_call(self._llm_call)

    def unregister_vertical_agent(self, name: str) -> bool:
        return self._vertical_agents.pop(name, None) is not None

    def list_vertical_agents(self) -> list[dict]:
        return [a.to_dict() for a in self._vertical_agents.values()]

    async def submit_task(self, description: str, goal: str = "", priority: TaskPriority = TaskPriority.NORMAL) -> AgentTask:
        task = AgentTask(description=description, goal=goal or description, priority=priority)
        self._tasks[task.id] = task
        return task

    async def execute_task(self, task_id: str) -> dict:
        task = self._tasks.get(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}

        task.status = TaskStatus.RUNNING
        task.started_at = time.time()

        effective_mode = self._decide_mode(task)

        try:
            if effective_mode == "single":
                result = await self._execute_single(task)
            else:
                result = await self._execute_multi(task)

            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()
            if self._evolution:
                duration = task.completed_at - (task.started_at or task.created_at)
                self._evolution.observe_execution(task.description, result, True, duration, task.assigned_to)
            return {"task_id": task.id, "status": "completed", "result": result}
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()
            if self._evolution:
                duration = task.completed_at - (task.started_at or task.created_at)
                self._evolution.observe_execution(task.description, None, False, duration, task.assigned_to)
            return {"task_id": task.id, "status": "failed", "error": str(e)}

    async def _execute_single(self, task: AgentTask) -> Any:
        sub = SubAgent(name="single_agent")
        if self._llm_call:
            sub.set_llm_call(self._llm_call)
        task.assigned_to = "single_agent"
        result = await sub.execute(task)

        report = await self.supervisor.execute(task, {"result": result, "agent_name": "single_agent"})
        if not report.approved:
            return {"result": result, "supervision": {"approved": False, "quality_score": report.quality_score, "issues": report.issues}}
        return result

    async def _execute_multi(self, task: AgentTask) -> Any:
        plan = await self.planner.execute(task)
        task.status = TaskStatus.PLANNED

        dispatch_result = await self.dispatcher.execute(task, {"plan": plan})
        task.status = TaskStatus.DISPATCHED

        report = await self.supervisor.execute(task, {"result": dispatch_result, "agent_name": "dispatcher"})
        if not report.approved and report.quality_score < 0.4:
            return {"result": dispatch_result, "supervision": {"approved": False, "quality_score": report.quality_score, "issues": report.issues, "suggestions": report.suggestions}}

        return dispatch_result

    def supplement_task(self, task_id: str, info: str, source: str = "user") -> dict | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        supplement = {
            "info": info,
            "source": source,
            "timestamp": time.time(),
        }
        task.supplements.append(supplement)
        task.metadata.setdefault("supplements", []).append(supplement)
        return {"task_id": task_id, "supplement_added": True, "total_supplements": len(task.supplements)}

    def get_task(self, task_id: str) -> dict | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {
            "id": task.id, "description": task.description, "goal": task.goal,
            "priority": task.priority.value, "status": task.status.value,
            "assigned_to": task.assigned_to, "result": task.result,
            "error": task.error, "created_at": task.created_at,
            "completed_at": task.completed_at, "supplements": task.supplements,
        }

    def list_tasks(self, status: TaskStatus | None = None, limit: int = 50) -> list[dict]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return [
            {"id": t.id, "description": t.description[:80], "status": t.status.value, "priority": t.priority.value}
            for t in sorted(tasks, key=lambda x: x.created_at, reverse=True)[:limit]
        ]

    def get_status(self) -> dict:
        return {
            "execution_mode": self._mode,
            "vertical_agents": len(self._vertical_agents),
            "active_sub_agents": len(self.dispatcher._active_sub_agents),
            "total_tasks": len(self._tasks),
            "pending_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING]),
            "completed_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.FAILED]),
            "supervision_reports": len(self.supervisor._reports),
        }


_orchestrator: MultiAgentOrchestrator | None = None


def get_orchestrator() -> MultiAgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator()
    return _orchestrator
