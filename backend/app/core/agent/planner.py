from typing import Optional

from app.core.agent.base import BaseAgent
from app.core.llm.dispatcher import ModelDispatcher, TaskCategory
from app.core.tool.registry import ToolRegistry


class PlannerAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        description: str,
        model_dispatcher: ModelDispatcher,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        super().__init__(name, description, tool_registry)
        self._dispatcher = model_dispatcher

    async def think(self, message: str, **kwargs) -> dict:
        self.add_message("user", message)
        messages = self._build_planning_messages()
        response = await self._dispatcher.dispatch(
            TaskCategory.PLANNING,
            messages=messages,
            **kwargs,
        )
        content = response.choices[0].message.content
        return {"plan": content}

    async def run(self, message: str, **kwargs) -> str:
        result = await self.think(message, **kwargs)
        plan = result["plan"]
        self.add_message("assistant", plan)
        return plan

    def _build_planning_messages(self) -> list[dict]:
        system_msg = {
            "role": "system",
            "content": (
                "You are a task planner. Break down complex tasks into clear, actionable steps. "
                "Consider dependencies between steps and suggest the optimal execution order."
            ),
        }
        messages = [system_msg]
        for msg in self._context.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        return messages
