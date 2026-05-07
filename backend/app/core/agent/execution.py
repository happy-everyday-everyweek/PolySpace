import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Callable

from app.core.agent.base import BaseAgent
from app.core.agent.middleware import LoopDetectionService, loop_detection_service
from app.core.audit.service import audit_service
from app.core.llm.dispatcher import ModelDispatcher, TaskCategory
from app.core.memory.manager import MemoryManager, get_memory_manager
from app.core.tool.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStep:
    thought: str = ""
    action: str | None = None
    action_input: dict | None = None
    observation: str | None = None
    tool_calls: list[dict] = field(default_factory=list)
    step_number: int = 0
    duration_ms: float = 0


class ExecutionAgent(BaseAgent):
    def __init__(
        self,
        name: str = "execution",
        description: str = "Execution agent without emotion system, focused on task completion",
        model_dispatcher: ModelDispatcher | None = None,
        tool_registry: ToolRegistry | None = None,
        memory_manager: MemoryManager | None = None,
        max_iterations: int = 10,
        execution_timeout: float = 120.0,
        loop_service: LoopDetectionService | None = None,
        execution_tools: list[str] | None = None,
    ):
        super().__init__(name, description, tool_registry)
        self._dispatcher = model_dispatcher
        self._memory = memory_manager or get_memory_manager()
        self._max_iterations = max_iterations
        self._execution_timeout = execution_timeout
        self._loop_service = loop_service or loop_detection_service
        self._execution_tools = execution_tools or []
        self._step_callback: Callable[[ExecutionStep], None] | None = None

    @property
    def has_emotion_system(self) -> bool:
        return False

    @property
    def has_full_recall_memory(self) -> bool:
        return False

    def set_step_callback(self, callback: Callable[[ExecutionStep], None]) -> None:
        self._step_callback = callback

    async def _record_token_usage(self, usage, thread_id: str) -> None:
        try:
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0
            if input_tokens > 0 or output_tokens > 0:
                model_name = ""
                try:
                    model_config = self._dispatcher.resolve_model(TaskCategory.DAILY)
                    model_name = model_config.model_id or ""
                except Exception:
                    pass
                await audit_service.record_token_usage(
                    thread_id=thread_id,
                    session_id="",
                    model_name=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
        except Exception as e:
            logger.warning(f"Failed to record token usage: {e}")

    async def think(self, message: str, **kwargs) -> dict:
        if message:
            self.add_message("user", message)

        memories = await self._memory.retrieve(message, top_k=5)
        memory_context = "\n".join(m.content for m in memories) if memories else ""

        tools_info = ""
        excluded_tools = {"execute_task", "read_file", "search"}
        if self._tool_registry:
            tool_defs = self._tool_registry.get_definitions()
            filtered_defs = [
                t for t in tool_defs
                if t.get("function", {}).get("name") not in excluded_tools
            ]
            tool_details = []
            for t in filtered_defs:
                func = t.get("function", {})
                name = func.get("name", "")
                desc = func.get("description", "")
                params = func.get("parameters", {}).get("properties", {})
                param_desc = ", ".join(
                    f"{k}: {v.get('description', v.get('type', ''))}"
                    for k, v in params.items()
                )
                tool_details.append(f"- {name}: {desc} (参数: {param_desc})")
            if tool_details:
                tools_info = (
                    "## 可用工具（必须使用）\n"
                    "你拥有以下工具，必须在需要时主动调用它们来完成任务。"
                    "不要仅用文字回复来代替工具调用。\n\n"
                    + "\n".join(tool_details) + "\n\n"
                    "## 工具使用规则\n"
                    "1. 当任务需要创建、修改、搜索、读取内容时，必须调用对应工具\n"
                    "2. 不要只回复文字说'我来做'而不实际调用工具\n"
                    "3. 每一步都应该考虑是否有合适的工具可以使用\n"
                    "4. 仅使用上述列出的工具，不要声称或尝试使用未列出的工具\n"
                    "5. 如果工具调用失败，尝试替代方案或报告错误\n"
                )

        from app.core.agent.prompts import build_execution_prompt
        system_content = build_execution_prompt(
            task_description="",
            tools_info=tools_info,
            execution_context=memory_context,
        )

        messages = [{"role": "system", "content": system_content}]
        for msg in self._context.messages:
            messages.append({"role": msg.role, "content": msg.content})

        tools = (
            [t for t in self._tool_registry.get_definitions()
             if t.get("function", {}).get("name") not in excluded_tools]
            if self._tool_registry else None
        )

        response = await self._dispatcher.dispatch(
            TaskCategory.DAILY,
            messages=messages,
            tools=tools,
            **kwargs,
        )

        if hasattr(response, "usage") and response.usage:
            await self._record_token_usage(response.usage, kwargs.get("thread_id", ""))

        tool_calls = []
        msg = response.choices[0].message if response.choices else None
        if msg and hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls = [
                {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                for tc in msg.tool_calls
            ]

        return {
            "content": response.choices[0].message.content,
            "tool_calls": tool_calls,
        }

    async def run(self, message: str, **kwargs) -> str:
        try:
            result = await asyncio.wait_for(
                self._run_loop(message, **kwargs),
                timeout=self._execution_timeout,
            )
            return result
        except asyncio.TimeoutError:
            return "Execution timed out. The task may be too complex. Try breaking it into smaller steps."

    async def _run_loop(self, message: str, **kwargs) -> str:
        steps: list[ExecutionStep] = []
        thread_id = kwargs.get("thread_id", "exec_default")

        for i in range(self._max_iterations):
            think_start = time.monotonic()
            think_result = await self.think(message if i == 0 else "", **kwargs)
            tool_calls = think_result.get("tool_calls", [])
            content = think_result.get("content", "")

            if not tool_calls:
                self.add_message("assistant", content)

                await self._memory.store(
                    message,
                    {"role": "user", "session_id": thread_id, "agent": "execution"},
                )
                await self._memory.store(
                    content,
                    {"role": "assistant", "session_id": thread_id, "agent": "execution"},
                )

                return content

            step = ExecutionStep(thought=content, step_number=i + 1)

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]

                is_loop, loop_level = self._loop_service.check(thread_id, tool_name, tool_args)
                if is_loop:
                    if loop_level == "hard_limit":
                        step.action = tool_name
                        step.action_input = tool_args
                        step.observation = (
                            "Loop detected: you have repeated this exact action too many times. "
                            "You MUST try a completely different approach or give a direct answer."
                        )
                        self.add_message("tool", step.observation)
                        steps.append(step)
                        if self._step_callback:
                            self._step_callback(step)
                        continue
                    else:
                        step.action = tool_name
                        step.action_input = tool_args
                        step.observation = (
                            "Warning: this action has been repeated. "
                            "Consider whether a different approach would be more effective."
                        )
                        self.add_message("tool", step.observation)

                try:
                    call_args = tool_args if isinstance(tool_args, dict) else {}
                    result = await self._tool_registry.call_tool(tool_name, **call_args)
                    step.action = tool_name
                    step.action_input = tool_args
                    step.observation = str(result)
                    self.add_message("tool", step.observation)
                except Exception as e:
                    step.action = tool_name
                    step.action_input = tool_args
                    step.observation = f"Error: {e}"
                    self.add_message("tool", step.observation)

                self._loop_service.record(thread_id, tool_name, tool_args)

            step.duration_ms = (time.monotonic() - think_start) * 1000
            steps.append(step)
            if self._step_callback:
                self._step_callback(step)

        return "Max iterations reached without final answer."

    async def run_stream(self, message: str, **kwargs) -> AsyncIterator[ExecutionStep]:
        thread_id = kwargs.get("thread_id", "exec_default")

        for i in range(self._max_iterations):
            think_start = time.monotonic()
            think_result = await self.think(message if i == 0 else "", **kwargs)
            tool_calls = think_result.get("tool_calls", [])
            content = think_result.get("content", "")

            if not tool_calls:
                self.add_message("assistant", content)
                step = ExecutionStep(
                    thought=content,
                    step_number=i + 1,
                    duration_ms=(time.monotonic() - think_start) * 1000,
                )
                yield step
                return

            step = ExecutionStep(thought=content, step_number=i + 1)

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]

                is_loop, loop_level = self._loop_service.check(thread_id, tool_name, tool_args)
                if is_loop and loop_level == "hard_limit":
                    step.action = tool_name
                    step.observation = "Loop detected. Switching strategy."
                    self.add_message("tool", step.observation)
                    yield step
                    continue

                try:
                    call_args = tool_args if isinstance(tool_args, dict) else {}
                    result = await self._tool_registry.call_tool(tool_name, **call_args)
                    step.action = tool_name
                    step.action_input = tool_args
                    step.observation = str(result)
                    self.add_message("tool", step.observation)
                except Exception as e:
                    step.action = tool_name
                    step.observation = f"Error: {e}"
                    self.add_message("tool", step.observation)

                self._loop_service.record(thread_id, tool_name, tool_args)

            step.duration_ms = (time.monotonic() - think_start) * 1000
            yield step

    async def execute_task(self, task_description: str, goal: str = "", **kwargs) -> dict:
        prompt = task_description
        if goal:
            prompt = f"Task: {task_description}\nGoal: {goal}"

        result = await self.run(prompt, **kwargs)

        await self._memory.store(
            result,
            {
                "role": "execution_result",
                "task": task_description,
                "goal": goal,
                "agent": "execution",
            },
        )

        return {
            "task": task_description,
            "goal": goal,
            "result": result,
            "status": "completed",
        }

    async def recall_context(self, query: str, top_k: int = 5) -> list:
        return await self._memory.retrieve(query, top_k=top_k)
