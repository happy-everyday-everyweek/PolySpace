import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Optional

from app.core.agent.base import BaseAgent
from app.core.agent.middleware import LoopDetectionService, loop_detection_service
from app.core.llm.dispatcher import ModelDispatcher, TaskCategory
from app.core.tool.registry import ToolRegistry


@dataclass
class ReActStep:
    thought: str
    action: Optional[str] = None
    action_input: Optional[dict] = None
    observation: Optional[str] = None
    step_number: int = 0
    duration_ms: float = 0


class ToolResultCache:
    def __init__(self, max_size: int = 100, ttl_seconds: float = 300):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds

    def _make_key(self, tool_name: str, params: dict) -> str:
        sorted_params = json.dumps(params, sort_keys=True)
        raw = f"{tool_name}:{sorted_params}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, tool_name: str, params: dict) -> Optional[Any]:
        key = self._make_key(tool_name, params)
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                self._cache.move_to_end(key)
                return value
            del self._cache[key]
        return None

    def put(self, tool_name: str, params: dict, result: Any) -> None:
        key = self._make_key(tool_name, params)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (result, time.time())
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def invalidate(self, tool_name: str, params: dict) -> None:
        key = self._make_key(tool_name, params)
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()


class ReActAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        description: str,
        model_dispatcher: ModelDispatcher,
        tool_registry: Optional[ToolRegistry] = None,
        max_iterations: int = 10,
        execution_timeout: float = 120.0,
        cache_results: bool = True,
        loop_service: LoopDetectionService | None = None,
        capability_executor: Any = None,
    ):
        super().__init__(name, description, tool_registry)
        self._dispatcher = model_dispatcher
        self._max_iterations = max_iterations
        self._execution_timeout = execution_timeout
        self._cache_results = cache_results
        self._result_cache = ToolResultCache() if cache_results else None
        self._loop_service = loop_service or loop_detection_service
        self._step_callback: Optional[Callable[[ReActStep], None]] = None
        self._capability_executor = capability_executor

    def set_step_callback(self, callback: Callable[[ReActStep], None]) -> None:
        self._step_callback = callback

    async def think(self, message: str, **kwargs) -> dict:
        self.add_message("user", message)
        messages = self._build_messages()
        tools = None
        if self._capability_executor:
            from app.core.capability.registry import capability_registry
            tools = capability_registry.get_definitions()
        elif self._tool_registry:
            tools = self._tool_registry.get_definitions()
        response = await self._dispatcher.dispatch(
            TaskCategory.DAILY,
            messages=messages,
            tools=tools,
            **kwargs,
        )
        return {
            "content": response.choices[0].message.content,
            "tool_calls": [
                {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                for tc in (response.choices[0].message.tool_calls or [])
            ],
        }

    async def run(self, message: str, **kwargs) -> str:
        try:
            result = await asyncio.wait_for(
                self._run_loop(message, **kwargs),
                timeout=self._execution_timeout
            )
            return result
        except asyncio.TimeoutError:
            return "Execution timed out. The task may be too complex. Try breaking it into smaller steps."

    async def _run_loop(self, message: str, **kwargs) -> str:
        steps: list[ReActStep] = []
        thread_id = kwargs.get("thread_id", "react_default")

        for i in range(self._max_iterations):
            think_start = time.time()
            think_result = await self.think(message if i == 0 else "", **kwargs)
            tool_calls = think_result.get("tool_calls", [])
            content = think_result.get("content", "")

            if not tool_calls:
                self.add_message("assistant", content)
                return content

            step = ReActStep(thought=content, step_number=i + 1)

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
                        self._notify_step(step)
                        continue
                    else:
                        step.action = tool_name
                        step.action_input = tool_args
                        step.observation = (
                            "Warning: this action has been repeated. "
                            "Consider whether a different approach would be more effective."
                        )
                        self.add_message("tool", step.observation)

                cached_result = None
                if self._result_cache and isinstance(tool_args, dict):
                    cached_result = self._result_cache.get(tool_name, tool_args)

                if cached_result is not None:
                    step.action = tool_name
                    step.action_input = tool_args
                    step.observation = str(cached_result)
                    self.add_message("tool", f"[cached] {step.observation}")
                else:
                    try:
                        call_args = tool_args if isinstance(tool_args, dict) else {}
                        if self._capability_executor:
                            from app.core.capability.base import CapabilityCallContext
                            ctx = CapabilityCallContext(thread_id=thread_id)
                            cap_result = await self._capability_executor.execute(tool_name, call_args, ctx)
                            result = cap_result.data if cap_result.success else f"Error: {cap_result.error}"
                        else:
                            result = await self._tool_registry.call_tool(tool_name, **call_args)
                        step.action = tool_name
                        step.action_input = tool_args
                        step.observation = str(result)
                        self.add_message("tool", step.observation)
                        if self._result_cache and isinstance(tool_args, dict):
                            self._result_cache.put(tool_name, tool_args, result)
                    except Exception as e:
                        step.action = tool_name
                        step.action_input = tool_args
                        step.observation = f"Error: {str(e)}"
                        self.add_message("tool", step.observation)

                self._loop_service.record(thread_id, tool_name, tool_args)

            step.duration_ms = (time.time() - think_start) * 1000
            steps.append(step)
            self._notify_step(step)

        return "Max iterations reached without final answer."

    async def run_stream(self, message: str, **kwargs) -> AsyncIterator[ReActStep]:
        thread_id = kwargs.get("thread_id", "react_default")

        for i in range(self._max_iterations):
            think_start = time.time()
            think_result = await self.think(message if i == 0 else "", **kwargs)
            tool_calls = think_result.get("tool_calls", [])
            content = think_result.get("content", "")

            if not tool_calls:
                self.add_message("assistant", content)
                elapsed = (time.time() - think_start) * 1000
                final_step = ReActStep(
                    thought=content, step_number=i + 1, duration_ms=elapsed
                )
                yield final_step
                return

            step = ReActStep(thought=content, step_number=i + 1)

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
                    if self._capability_executor:
                        from app.core.capability.base import CapabilityCallContext
                        ctx = CapabilityCallContext(thread_id=thread_id)
                        cap_result = await self._capability_executor.execute(tool_name, call_args, ctx)
                        result = cap_result.data if cap_result.success else f"Error: {cap_result.error}"
                    else:
                        result = await self._tool_registry.call_tool(tool_name, **call_args)
                    step.action = tool_name
                    step.action_input = tool_args
                    step.observation = str(result)
                    self.add_message("tool", step.observation)
                except Exception as e:
                    step.action = tool_name
                    step.observation = f"Error: {str(e)}"
                    self.add_message("tool", step.observation)

                self._loop_service.record(thread_id, tool_name, tool_args)

            step.duration_ms = (time.time() - think_start) * 1000
            yield step

    def _build_messages(self) -> list[dict]:
        messages = []
        for msg in self._context.messages:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    def _notify_step(self, step: ReActStep) -> None:
        if self._step_callback:
            self._step_callback(step)
