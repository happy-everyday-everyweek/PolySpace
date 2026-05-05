from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.core.tool.base import BaseTool


@dataclass
class ScheduledTask:
    task_id: str
    name: str
    cron_expression: str
    command: str
    enabled: bool = True
    last_run: float | None = None
    next_run: float | None = None


class SchedulerTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="scheduler",
            description="Schedule and manage recurring tasks",
        )
        self._tasks: dict[str, ScheduledTask] = {}
        self._running: bool = False

    async def _on_activate(self) -> None:
        self._running = True

    async def _on_call(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "")

        if action == "create":
            task = ScheduledTask(
                task_id=str(uuid.uuid4()),
                name=kwargs.get("name", "unnamed"),
                cron_expression=kwargs.get("cron", "* * * * *"),
                command=kwargs.get("command", ""),
                enabled=True,
            )
            self._tasks[task.task_id] = task
            return {"task_id": task.task_id, "name": task.name, "status": "created"}

        elif action == "list":
            return {
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "name": t.name,
                        "cron": t.cron_expression,
                        "command": t.command,
                        "enabled": t.enabled,
                        "last_run": t.last_run,
                    }
                    for t in self._tasks.values()
                ]
            }

        elif action == "delete":
            task_id = kwargs.get("task_id", "")
            if task_id in self._tasks:
                del self._tasks[task_id]
                return {"success": True, "task_id": task_id}
            return {"error": f"Task not found: {task_id}"}

        elif action == "toggle":
            task_id = kwargs.get("task_id", "")
            task = self._tasks.get(task_id)
            if task:
                task.enabled = not task.enabled
                return {"task_id": task_id, "enabled": task.enabled}
            return {"error": f"Task not found: {task_id}"}

        elif action == "run_now":
            task_id = kwargs.get("task_id", "")
            task = self._tasks.get(task_id)
            if task:
                import time
                task.last_run = time.time()
                return {"task_id": task_id, "status": "executed", "command": task.command}
            return {"error": f"Task not found: {task_id}"}

        else:
            return {"error": f"Unknown action: {action}"}

    async def _on_hibernate(self) -> None:
        self._running = False

    def get_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "list", "delete", "toggle", "run_now"],
                            "description": "Scheduler action",
                        },
                        "name": {"type": "string", "description": "Task name"},
                        "cron": {"type": "string", "description": "Cron expression for scheduling"},
                        "command": {"type": "string", "description": "Command to execute"},
                        "task_id": {"type": "string", "description": "Task ID for operations"},
                    },
                    "required": ["action"],
                },
            },
        }
