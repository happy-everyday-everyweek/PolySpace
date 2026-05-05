from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.core.agent.base import AgentContext, AgentMessage, BaseAgent
from app.core.agent.dashboard import AgentRunEvent, DashboardManager, dashboard_manager


@dataclass
class SubAgentTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    instruction: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    parent_trace_id: str | None = None


@dataclass
class SubAgentResult:
    task_id: str
    success: bool
    output: str
    error: str | None = None
    trace_id: str | None = None


class SubAgentExecutor:
    def __init__(self, dashboard: DashboardManager | None = None) -> None:
        self._dashboard = dashboard or dashboard_manager
        self._background_tasks: dict[str, asyncio.Task] = {}

    async def delegate(
        self,
        agent: BaseAgent,
        instruction: str,
        context: dict[str, Any] | None = None,
        parent_trace_id: str | None = None,
    ) -> SubAgentResult:
        task = SubAgentTask(
            agent_name=agent.__class__.__name__,
            instruction=instruction,
            context=context or {},
            parent_trace_id=parent_trace_id,
        )

        trace_id = parent_trace_id or str(uuid.uuid4())

        self._dashboard.add_event(
            trace_id=trace_id,
            event=AgentRunEvent(
                agent_name=task.agent_name,
                event_type="subagent_start",
                data={"instruction": instruction, "task_id": task.task_id},
            ),
        )

        try:
            agent_context = AgentContext(
                messages=[AgentMessage(role="user", content=instruction)],
                metadata=context or {},
            )
            result = await agent.run(agent_context)

            self._dashboard.add_event(
                trace_id=trace_id,
                event=AgentRunEvent(
                    agent_name=task.agent_name,
                    event_type="subagent_complete",
                    data={"task_id": task.task_id, "success": True},
                ),
            )

            output = ""
            if result.messages:
                output = result.messages[-1].content

            return SubAgentResult(
                task_id=task.task_id,
                success=True,
                output=output,
                trace_id=trace_id,
            )

        except Exception as e:
            self._dashboard.add_event(
                trace_id=trace_id,
                event=AgentRunEvent(
                    agent_name=task.agent_name,
                    event_type="subagent_error",
                    data={"task_id": task.task_id, "error": str(e)},
                ),
            )

            return SubAgentResult(
                task_id=task.task_id,
                success=False,
                output="",
                error=str(e),
                trace_id=trace_id,
            )

    async def delegate_background(
        self,
        agent: BaseAgent,
        instruction: str,
        context: dict[str, Any] | None = None,
        parent_trace_id: str | None = None,
        callback: Callable[[SubAgentResult], Awaitable[None]] | None = None,
    ) -> str:
        task_id = str(uuid.uuid4())

        async def _run():
            result = await self.delegate(
                agent, instruction, context, parent_trace_id
            )
            if callback:
                await callback(result)

        coro = _run()
        background_task = asyncio.create_task(coro)
        self._background_tasks[task_id] = background_task

        background_task.add_done_callback(
            lambda t: self._background_tasks.pop(task_id, None)
        )

        return task_id

    async def wait_for_task(self, task_id: str, timeout: float = 300.0) -> SubAgentResult | None:
        task = self._background_tasks.get(task_id)
        if not task:
            return None
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        return task.result() if task.done() else None

    def get_active_tasks(self) -> list[str]:
        return [
            tid for tid, task in self._background_tasks.items()
            if not task.done()
        ]

    async def cancel_task(self, task_id: str) -> bool:
        task = self._background_tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            return True
        return False


subagent_executor = SubAgentExecutor()
