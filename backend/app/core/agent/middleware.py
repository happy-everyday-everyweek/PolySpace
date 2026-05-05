from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class ThreadStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    COMPLETED = "completed"
    ERROR = "error"


class ErrorStrategy(str, Enum):
    SKIP = "skip"
    ABORT = "abort"


class MiddlewareLayer(str, Enum):
    PRE_PROCESS = "pre_process"
    DISPATCH = "dispatch"
    POST_PROCESS = "post_process"


@dataclass
class MiddlewareAuditTrace:
    middleware_name: str
    layer: MiddlewareLayer = MiddlewareLayer.PRE_PROCESS
    started_at: float = 0.0
    finished_at: float = 0.0
    success: bool = True
    error: str | None = None
    duration_ms: float = 0.0
    input_summary: str | None = None
    output_summary: str | None = None
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_span_id: str | None = None


@dataclass
class MiddlewareContext:
    thread_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_message: str = ""
    messages: list[dict] = field(default_factory=list)
    uploads: list[dict] = field(default_factory=list)
    sandbox_results: list[dict] = field(default_factory=list)
    summary: str | None = None
    title: str | None = None
    todos: list[dict] = field(default_factory=list)
    clarification_needed: bool = False
    clarification_question: str | None = None
    memory_facts: list[dict] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0, "total": 0})
    metadata: dict[str, Any] = field(default_factory=dict)
    status: ThreadStatus = ThreadStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    emotion_context: dict | None = None
    action_plan: dict | None = None
    inner_voice: str | None = None
    reply: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    reflection: dict | None = None
    traces: list[MiddlewareAuditTrace] = field(default_factory=list)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def touch(self) -> None:
        self.updated_at = time.time()


class BaseMiddleware(ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        ...


class LoopDetectionService:
    def __init__(
        self,
        warn_threshold: int = 3,
        hard_limit: int = 5,
        window_size: int = 20,
        max_tracked_threads: int = 100,
    ):
        self._warn_threshold = warn_threshold
        self._hard_limit = hard_limit
        self._window_size = window_size
        self._max_tracked = max_tracked_threads
        self._thread_windows: OrderedDict[str, list[str]] = OrderedDict()
        self._warned_hashes: set[str] = set()

    def _hash_tool_call(self, name: str, arguments: Any) -> str:
        if isinstance(arguments, dict):
            try:
                sorted_args = json.dumps(arguments, sort_keys=True)
            except (TypeError, ValueError):
                sorted_args = str(arguments)
        elif isinstance(arguments, str):
            sorted_args = arguments
        else:
            sorted_args = str(arguments)
        raw = f"{name}:{sorted_args}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _hash_message_tool_calls(self, msg: dict) -> str | None:
        tool_calls = msg.get("tool_calls") or msg.get("metadata", {}).get("tool_calls")
        if not tool_calls:
            return None
        parts = []
        for tc in tool_calls:
            name = tc.get("name", tc.get("function", {}).get("name", ""))
            args = tc.get("arguments", tc.get("function", {}).get("arguments", {}))
            if isinstance(args, dict):
                args = json.dumps(args, sort_keys=True)
            parts.append(f"{name}:{args}")
        return hashlib.md5("|".join(parts).encode()).hexdigest()

    def _get_window(self, thread_id: str) -> list[str]:
        if thread_id not in self._thread_windows:
            if len(self._thread_windows) >= self._max_tracked:
                self._thread_windows.popitem(last=False)
            self._thread_windows[thread_id] = []
        return self._thread_windows[thread_id]

    def record(self, thread_id: str, name: str, arguments: Any) -> None:
        call_hash = self._hash_tool_call(name, arguments)
        window = self._get_window(thread_id)
        window.append(call_hash)
        if len(window) > self._window_size:
            del window[: len(window) - self._window_size]

    def check(self, thread_id: str, name: str, arguments: Any) -> tuple[bool, str]:
        call_hash = self._hash_tool_call(name, arguments)
        window = self._get_window(thread_id)
        count = window.count(call_hash)
        if count >= self._hard_limit:
            return True, "hard_limit"
        if count >= self._warn_threshold:
            return True, "warning"
        return False, ""

    def check_message(self, thread_id: str, msg: dict) -> tuple[bool, str, str | None]:
        call_hash = self._hash_message_tool_calls(msg)
        if not call_hash:
            return False, "", None
        window = self._get_window(thread_id)
        window.append(call_hash)
        if len(window) > self._window_size:
            del window[: len(window) - self._window_size]
        count = window.count(call_hash)
        if count >= self._hard_limit:
            return True, "hard_limit", call_hash
        if count >= self._warn_threshold:
            if call_hash not in self._warned_hashes:
                self._warned_hashes.add(call_hash)
            return True, "warning", call_hash
        return False, "", call_hash

    def cleanup(self) -> int:
        if len(self._thread_windows) <= self._max_tracked:
            return 0
        removed = 0
        while len(self._thread_windows) > self._max_tracked * 0.8:
            self._thread_windows.popitem(last=False)
            removed += 1
        return removed


loop_detection_service = LoopDetectionService()


class ThreadDataMiddleware(BaseMiddleware):
    def __init__(self, chat_history_store: Any = None):
        self._history_store = chat_history_store

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        if not context.thread_id:
            context.thread_id = str(uuid.uuid4())
        context.metadata["thread_created_at"] = context.metadata.get(
            "thread_created_at", __import__("datetime").datetime.now().isoformat()
        )

        if self._history_store and hasattr(self._history_store, "get_history"):
            context.metadata["chat_history"] = self._history_store.get_history(context.thread_id)
        elif "chat_history" not in context.metadata:
            context.metadata["chat_history"] = []

        return await next_middleware(context)


class UploadsMiddleware(BaseMiddleware):
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        for upload in context.uploads:
            context.messages.append(
                {
                    "role": "user",
                    "content": f"[Uploaded file: {upload.get('filename', 'unknown')}]",
                    "metadata": {"type": "upload", **upload},
                }
            )
        return await next_middleware(context)


class SandboxMiddleware(BaseMiddleware):
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        for result in context.sandbox_results:
            context.messages.append(
                {
                    "role": "assistant",
                    "content": f"[Sandbox execution result]\n{result.get('output', '')}",
                    "metadata": {"type": "sandbox_result", **result},
                }
            )
        return await next_middleware(context)


class SummarizationMiddleware(BaseMiddleware):
    def __init__(self, max_messages: int = 20, keep_recent: int = 6, llm_dispatch_fn: Any = None):
        self._max_messages = max_messages
        self._keep_recent = keep_recent
        self._llm_dispatch = llm_dispatch_fn

    async def _generate_summary(self, old_messages: list[dict]) -> str:
        if not self._llm_dispatch:
            return "Conversation summarized (older messages truncated)"
        try:
            conversation = "\n".join(
                f"{m.get('role', 'unknown')}: {m.get('content', '')[:200]}"
                for m in old_messages
            )
            prompt = (
                "Summarize the following conversation concisely, "
                "preserving key facts, decisions, and context:\n"
                f"{conversation[:3000]}"
            )
            return await self._llm_dispatch(prompt)
        except Exception as e:
            logger.warning(f"LLM summarization failed, falling back to truncation: {e}")
            return "Conversation summarized (older messages truncated)"

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        if len(context.messages) > self._max_messages and not context.summary:
            old_messages = context.messages[: len(context.messages) - self._keep_recent]
            recent = context.messages[-self._keep_recent :]
            context.summary = await self._generate_summary(old_messages)
            has_system = (
                context.messages
                and context.messages[0].get("role") == "system"
            )
            system_prefix = context.messages[:1] if has_system else []
            context.messages = system_prefix + [
                {"role": "system", "content": f"Previous conversation summary: {context.summary}"}
            ] + recent
        return await next_middleware(context)


class TitleMiddleware(BaseMiddleware):
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        if not context.title and context.user_message:
            title = context.user_message[:50]
            if len(context.user_message) > 50:
                title += "..."
            context.title = title
        return await next_middleware(context)


class TodoListMiddleware(BaseMiddleware):
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        for todo in context.todos:
            context.messages.append(
                {
                    "role": "system",
                    "content": f"[Todo: {todo.get('text', '')} - Status: {todo.get('status', 'pending')}]",
                    "metadata": {"type": "todo", **todo},
                }
            )
        return await next_middleware(context)


class ClarificationMiddleware(BaseMiddleware):
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        if context.clarification_needed and context.clarification_question:
            context.messages.append(
                {
                    "role": "assistant",
                    "content": context.clarification_question,
                    "metadata": {"type": "clarification"},
                }
            )
        return await next_middleware(context)


class LoopDetectionMiddleware(BaseMiddleware):
    def __init__(self, service: LoopDetectionService | None = None):
        self._service = service or loop_detection_service

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        context = await next_middleware(context)
        if not context.messages:
            return context

        last_msg = context.messages[-1]
        is_loop, loop_level, call_hash = self._service.check_message(context.thread_id, last_msg)
        if not is_loop:
            return context

        if loop_level == "hard_limit":
            logger.warning(
                f"Loop detected in thread {context.thread_id}: "
                f"hash {call_hash} repeated, stripping tool calls"
            )
            if "tool_calls" in last_msg:
                del last_msg["tool_calls"]
            if "metadata" in last_msg and "tool_calls" in last_msg["metadata"]:
                del last_msg["metadata"]["tool_calls"]
        elif loop_level == "warning" and call_hash not in self._service._warned_hashes:
            self._service._warned_hashes.add(call_hash)
            context.messages.append({
                "role": "system",
                "content": "You are repeating the same action. Please try a different approach or conclude.",
            })

        return context


class TokenUsageMiddleware(BaseMiddleware):
    def __init__(self, max_total_tokens: int = 200000, max_tracked_threads: int = 500, thread_ttl: float = 86400.0):
        self._max_total_tokens = max_total_tokens
        self._max_tracked = max_tracked_threads
        self._thread_ttl = thread_ttl
        self._thread_usage: OrderedDict[str, tuple[int, float]] = OrderedDict()

    def _cleanup_stale(self) -> None:
        now = time.time()
        stale = [
            tid for tid, (_, ts) in self._thread_usage.items()
            if now - ts > self._thread_ttl
        ]
        for tid in stale:
            del self._thread_usage[tid]
        if len(self._thread_usage) > self._max_tracked:
            while len(self._thread_usage) > self._max_tracked * 0.8:
                self._thread_usage.popitem(last=False)

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        context = await next_middleware(context)
        usage = context.metadata.get("token_usage", {})
        input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", 0))
        output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0))
        total = input_tokens + output_tokens

        context.token_usage["input"] += input_tokens
        context.token_usage["output"] += output_tokens
        context.token_usage["total"] += total

        prev_cumulative, _ = self._thread_usage.get(context.thread_id, (0, 0))
        cumulative = prev_cumulative + total
        self._thread_usage[context.thread_id] = (cumulative, time.time())
        self._thread_usage.move_to_end(context.thread_id)

        if total > 0:
            try:
                from app.core.audit.service import audit_service
                model_name = context.metadata.get("model_name", "")
                session_id = context.metadata.get("session_id", "")
                await audit_service.record_token_usage(
                    thread_id=context.thread_id,
                    session_id=session_id,
                    model_name=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            except Exception:
                pass

        if cumulative > self._max_total_tokens:
            context.messages.append({
                "role": "system",
                "content": (
                    f"Token budget approaching limit "
                    f"({cumulative}/{self._max_total_tokens}). "
                    "Please wrap up the conversation soon."
                ),
            })

        self._cleanup_stale()
        return context


class MemoryInjectionMiddleware(BaseMiddleware):
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        if not context.memory_facts:
            return await next_middleware(context)

        facts_text = "\n".join(
            f"- {f.get('content', f.get('text', str(f)))}"
            for f in context.memory_facts
        )
        memory_msg = {
            "role": "system",
            "content": f"[Relevant memories]\n{facts_text}",
        }

        if context.messages and context.messages[0].get("role") == "system":
            context.messages.insert(1, memory_msg)
        else:
            context.messages.insert(0, memory_msg)

        return await next_middleware(context)


class EmotionMiddleware(BaseMiddleware):
    def __init__(self, heartflow: Any):
        self._heartflow = heartflow

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        await self._heartflow.process_input(context.user_message)
        context.emotion_context = self._heartflow.get_emotion_context()
        context.metadata["emotion_modifier"] = self._heartflow.get_emotion_prompt_modifier()
        return await next_middleware(context)


class PFCPlanningMiddleware(BaseMiddleware):
    def __init__(self, pfc: Any, persona: Any, greeting: Any):
        self._pfc = pfc
        self._persona = persona
        self._greeting = greeting

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        self._greeting.update_interaction()
        self._pfc.update_user_message_time()

        emotion_ctx = context.emotion_context or {}
        action_type, action_reason, thinking_chain = await self._pfc.plan_action(
            observation_info=context.user_message[:200],
            conversation_info=f"用户消息: {context.user_message[:100]}",
            emotion_context=emotion_ctx,
            relationship=self._persona.relationship.value,
        )
        context.action_plan = {
            "action_type": action_type.value if hasattr(action_type, "value") else str(action_type),
            "action_reason": action_reason,
            "thinking_chain": thinking_chain,
        }
        context.metadata["action_type"] = action_type
        context.metadata["action_reason"] = action_reason
        return await next_middleware(context)


class InnerVoiceMiddleware(BaseMiddleware):
    def __init__(self, inner_voice: Any, persona: Any):
        self._inner_voice = inner_voice
        self._persona = persona

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        emotion_ctx = context.emotion_context or {}
        inner_voice_entry = await self._inner_voice.generate_inner_voice(
            user_message=context.user_message,
            emotion_context=emotion_ctx,
            persona_section=self._persona.get_persona_prompt_section(),
            relationship=self._persona.relationship.value,
        )
        context.inner_voice = self._inner_voice.get_inner_voice_for_prompt(inner_voice_entry)
        context.metadata["inner_voice_entry"] = inner_voice_entry
        return await next_middleware(context)


class SystemPromptMiddleware(BaseMiddleware):
    def __init__(
        self,
        persona: Any,
        memory_manager: Any,
        capability_registry: Any = None,
        device_manager: Any = None,
        max_history: int = 20,
        tool_registry: Any = None,
    ):
        self._persona = persona
        self._memory = memory_manager
        self._capability_registry = capability_registry
        self._device_manager = device_manager
        self._max_history = max_history
        self._tool_registry = tool_registry

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        from app.core.agent.prompts import build_capability_summary, build_platform_info, build_system_prompt

        persona_section = self._persona.get_persona_prompt_section()
        memories = await self._memory.retrieve(context.user_message, top_k=5)
        memory_context = "\n".join(m.content for m in memories) if memories else ""
        context.memory_facts = [{"content": m.content} for m in memories] if memories else []

        rel_map = {
            "stranger": "你和用户刚认识",
            "acquaintance": "你和用户有些熟悉了",
            "friend": "你和用户是朋友",
            "close_friend": "你和用户是密友",
        }
        relationship_context = rel_map.get(self._persona.relationship.value, "")
        emotion_modifier = context.metadata.get("emotion_modifier", "")

        cap_summary = ""
        if self._capability_registry:
            cap_summary = build_capability_summary(self._capability_registry)
        elif self._tool_registry:
            tool_defs = self._tool_registry.get_definitions()
            tool_names = [
                td.get("function", {}).get("name", "")
                for td in tool_defs
                if td.get("function")
            ]
            if tool_names:
                cap_summary = f"可用工具: {', '.join(tool_names)}"
        platform_info = build_platform_info(self._device_manager) if self._device_manager else ""

        system_content = build_system_prompt(
            persona_section=persona_section,
            emotion_modifier=emotion_modifier,
            inner_voice_context=context.inner_voice or "",
            memory_context=memory_context,
            relationship_context=relationship_context,
            capability_summary=cap_summary,
            platform_info=platform_info,
        )

        history_messages = []
        if context.metadata.get("chat_history"):
            chat_history = context.metadata["chat_history"]
            history_messages = chat_history[-self._max_history:]

        context.messages = [
            {"role": "system", "content": system_content},
        ] + history_messages + [
            {"role": "user", "content": context.user_message},
        ]

        return await next_middleware(context)


class LLMDispatchMiddleware(BaseMiddleware):
    def __init__(
        self,
        dispatcher: Any,
        tool_registry: Any,
        expression: Any,
        persona: Any,
        capability_registry: Any = None,
    ):
        self._dispatcher = dispatcher
        self._tools = tool_registry
        self._expression = expression
        self._persona = persona
        self._capability_registry = capability_registry

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        from app.core.llm.dispatcher import TaskCategory

        persona_modifiers = self._persona.get_expression_modifiers()
        self._expression.configure_from_persona(persona_modifiers)

        tools = None
        if self._capability_registry:
            tools = self._capability_registry.get_definitions()
        elif self._tools:
            tools = self._tools.get_definitions()

        response = await self._dispatcher.dispatch(
            TaskCategory.DAILY,
            messages=context.messages,
            tools=tools,
        )

        msg = response.choices[0].message if response.choices else None
        tool_calls = []
        tool_results = []
        cards = []

        if msg and hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls = [
                {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                for tc in msg.tool_calls
            ]

            for tc_info in tool_calls:
                try:
                    raw_args = tc_info["arguments"]
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                    if self._tools:
                        result = await self._tools.call_tool(tc_info["name"], **args)
                        tool_results.append({
                            "tool_call_id": tc_info["id"],
                            "name": tc_info["name"],
                            "result": result,
                        })
                        if isinstance(result, dict) and "card" in result:
                            cards.append(result["card"])
                    else:
                        tool_results.append({
                            "tool_call_id": tc_info["id"],
                            "name": tc_info["name"],
                            "result": {"error": "Tool registry not available"},
                        })
                except Exception as e:
                    tool_results.append({
                        "tool_call_id": tc_info["id"],
                        "name": tc_info["name"],
                        "result": {"error": str(e)},
                    })

        if tool_results:
            messages = list(context.messages)
            messages.append({"role": "assistant", "content": None, "tool_calls": [
                {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                for tc in tool_calls
            ]})
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": json.dumps(tr["result"], ensure_ascii=False, default=str),
                })
            second_response = await self._dispatcher.dispatch(
                TaskCategory.DAILY,
                messages=messages,
                tools=tools,
            )
            reply = second_response.choices[0].message.content or "" if second_response.choices else ""
        else:
            reply = msg.content if (msg and msg.content) else ""

        emotion_ctx = context.emotion_context or {}
        emotion_label = emotion_ctx.get("label", "平淡中性")
        emotion_intensity = emotion_ctx.get("intensity", 0.3)
        reply = self._expression.apply_expression_style(reply, emotion_label, emotion_intensity)

        context.reply = reply
        context.metadata["llm_response"] = response
        context.tool_calls = tool_calls
        if cards:
            context.metadata["cards"] = cards

        if hasattr(response, "usage") and response.usage:
            context.metadata["token_usage"] = {
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
            }

        return await next_middleware(context)


class ReflectionMiddleware(BaseMiddleware):
    def __init__(self, pfc: Any):
        self._pfc = pfc

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        emotion_ctx = context.emotion_context or {}
        reflection_score, reflection_suggestion = self._pfc.reflect_on_reply(
            context.reply, emotion_ctx
        )
        if reflection_suggestion:
            context.reflection = {
                "score": reflection_score,
                "suggestion": reflection_suggestion,
            }
        return await next_middleware(context)


class ToolExecutionMiddleware(BaseMiddleware):
    def __init__(self, policy_engine: Any, tool_registry: Any = None):
        self._policies = policy_engine
        self._tools = tool_registry

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        response = context.metadata.get("llm_response")
        if not response:
            return await next_middleware(context)

        msg = response.choices[0].message if response.choices else None
        if not (msg and hasattr(msg, "tool_calls") and msg.tool_calls):
            return await next_middleware(context)

        import json

        tool_calls = []
        cards = []

        for tc in msg.tool_calls:
            action_result, policy_msg = self._policies.evaluate(tc.function.name)

            tc_info = {
                "id": tc.id,
                "name": tc.function.name,
                "arguments": tc.function.arguments,
                "policy_action": action_result.value,
            }

            if action_result.value == "allow" and self._tools:
                try:
                    raw_args = tc.function.arguments
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                    result = await self._tools.call_tool(tc.function.name, **args)
                    tc_info["result"] = result
                    tc_info["executed"] = True

                    if isinstance(result, dict) and "card" in result:
                        cards.append(result["card"])

                    logger.info(f"Tool {tc.function.name} executed successfully")
                except Exception as e:
                    logger.error(f"Tool {tc.function.name} execution failed: {e}")
                    tc_info["result"] = {"error": str(e)}
                    tc_info["executed"] = False
            else:
                tc_info["executed"] = False
                if action_result.value != "allow":
                    tc_info["result"] = {"error": f"Policy blocked: {policy_msg}"}

            tool_calls.append(tc_info)

        context.tool_calls = tool_calls
        if cards:
            context.metadata["cards"] = cards

        return await next_middleware(context)


class MemoryStoreMiddleware(BaseMiddleware):
    def __init__(self, memory_manager: Any, greeting_manager: Any, chat_history_store: Any = None):
        self._memory = memory_manager
        self._greeting = greeting_manager
        self._history_store = chat_history_store

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        store_user = asyncio.create_task(
            self._memory.store(context.user_message, {"role": "user", "session_id": context.thread_id})
        )
        store_reply = asyncio.create_task(
            self._memory.store(context.reply, {"role": "assistant", "session_id": context.thread_id})
        )
        await asyncio.gather(store_user, store_reply)
        self._greeting.update_last_topics([context.user_message[:50]])

        if self._history_store and hasattr(self._history_store, "add_message"):
            self._history_store.add_message(context.thread_id, {
                "role": "user",
                "content": context.user_message,
            })
            self._history_store.add_message(context.thread_id, {
                "role": "assistant",
                "content": context.reply,
            })

            if context.metadata.get("chat_history"):
                context.metadata["chat_history"].append({
                    "role": "user",
                    "content": context.user_message,
                })
                context.metadata["chat_history"].append({
                    "role": "assistant",
                    "content": context.reply,
                })

        return await next_middleware(context)


class MiddlewareChain:
    def __init__(self, error_strategy: ErrorStrategy = ErrorStrategy.SKIP) -> None:
        self._middlewares: list[tuple[MiddlewareLayer, BaseMiddleware]] = []
        self._error_strategy = error_strategy

    def add(
        self,
        middleware: BaseMiddleware,
        layer: MiddlewareLayer = MiddlewareLayer.PRE_PROCESS,
    ) -> "MiddlewareChain":
        self._middlewares.append((layer, middleware))
        return self

    def add_pre_process(self, middleware: BaseMiddleware) -> "MiddlewareChain":
        return self.add(middleware, MiddlewareLayer.PRE_PROCESS)

    def add_dispatch(self, middleware: BaseMiddleware) -> "MiddlewareChain":
        return self.add(middleware, MiddlewareLayer.DISPATCH)

    def add_post_process(self, middleware: BaseMiddleware) -> "MiddlewareChain":
        return self.add(middleware, MiddlewareLayer.POST_PROCESS)

    def insert_before(self, target_name: str, middleware: BaseMiddleware, layer: MiddlewareLayer | None = None) -> bool:
        for i, (existing_layer, mw) in enumerate(self._middlewares):
            if mw.name == target_name:
                actual_layer = layer if layer is not None else existing_layer
                self._middlewares.insert(i, (actual_layer, middleware))
                return True
        return False

    def insert_after(self, target_name: str, middleware: BaseMiddleware, layer: MiddlewareLayer | None = None) -> bool:
        for i, (existing_layer, mw) in enumerate(self._middlewares):
            if mw.name == target_name:
                actual_layer = layer if layer is not None else existing_layer
                self._middlewares.insert(i + 1, (actual_layer, middleware))
                return True
        return False

    def remove(self, name: str) -> bool:
        for i, (_, mw) in enumerate(self._middlewares):
            if mw.name == name:
                self._middlewares.pop(i)
                return True
        return False

    def list_middlewares(self) -> list[str]:
        return [mw.name for _, mw in self._middlewares]

    def get_layer_structure(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {
            MiddlewareLayer.PRE_PROCESS.value: [],
            MiddlewareLayer.DISPATCH.value: [],
            MiddlewareLayer.POST_PROCESS.value: [],
        }
        for layer, mw in self._middlewares:
            result[layer.value].append(mw.name)
        return result

    async def execute(self, context: MiddlewareContext) -> MiddlewareContext:
        async def final_handler(ctx: MiddlewareContext) -> MiddlewareContext:
            return ctx

        handler: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]] = final_handler
        for layer, middleware in reversed(self._middlewares):
            current_middleware = middleware
            current_handler = handler
            current_layer = layer
            error_strategy = self._error_strategy
            parent_span = context.span_id

            async def make_handler(
                mw: BaseMiddleware,
                nh: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
                strategy: ErrorStrategy,
                mw_layer: MiddlewareLayer,
                parent_span_id: str,
            ) -> Callable[[MiddlewareContext], Awaitable[MiddlewareContext]]:
                async def h(ctx: MiddlewareContext) -> MiddlewareContext:
                    trace = MiddlewareAuditTrace(
                        middleware_name=mw.name,
                        layer=mw_layer,
                        started_at=time.time(),
                        parent_span_id=parent_span_id,
                        input_summary=ctx.user_message[:100] if ctx.user_message else None,
                    )
                    try:
                        result = await mw.process(ctx, nh)
                        trace.finished_at = time.time()
                        trace.success = True
                        trace.duration_ms = (trace.finished_at - trace.started_at) * 1000
                        trace.output_summary = result.reply[:100] if result.reply else None
                        ctx.traces.append(trace)
                        return result
                    except asyncio.CancelledError:
                        trace.finished_at = time.time()
                        trace.success = False
                        trace.error = "cancelled"
                        trace.duration_ms = (trace.finished_at - trace.started_at) * 1000
                        ctx.traces.append(trace)
                        raise
                    except Exception as e:
                        trace.finished_at = time.time()
                        trace.success = False
                        trace.error = str(e)
                        trace.duration_ms = (trace.finished_at - trace.started_at) * 1000
                        ctx.traces.append(trace)
                        logger.error(
                            f"Middleware {mw.name} failed: {e}",
                            exc_info=True,
                        )
                        if strategy == ErrorStrategy.ABORT:
                            raise
                        return await nh(ctx)
                return h

            handler = make_handler(current_middleware, current_handler, error_strategy, current_layer, parent_span)

        return await handler(context)

    def get_stats(self) -> dict[str, Any]:
        return {
            "middleware_count": len(self._middlewares),
            "middlewares": self.list_middlewares(),
            "layer_structure": self.get_layer_structure(),
            "error_strategy": self._error_strategy.value,
        }


def create_default_chain() -> MiddlewareChain:
    chain = MiddlewareChain(error_strategy=ErrorStrategy.SKIP)
    chain.add_pre_process(ThreadDataMiddleware())
    chain.add_pre_process(MemoryInjectionMiddleware())
    chain.add_pre_process(UploadsMiddleware())
    chain.add_pre_process(SandboxMiddleware())
    chain.add_pre_process(SummarizationMiddleware())
    chain.add_post_process(TitleMiddleware())
    chain.add_post_process(TodoListMiddleware())
    chain.add_post_process(ClarificationMiddleware())
    chain.add_post_process(LoopDetectionMiddleware())
    chain.add_post_process(TokenUsageMiddleware())
    return chain


def create_chat_chain(
    heartflow: Any,
    pfc: Any,
    persona: Any,
    greeting: Any,
    inner_voice: Any,
    memory_manager: Any,
    dispatcher: Any,
    tool_registry: Any,
    expression: Any,
    policy_engine: Any,
    llm_dispatch_fn: Any = None,
    capability_registry: Any = None,
    device_manager: Any = None,
) -> MiddlewareChain:
    chain = MiddlewareChain(error_strategy=ErrorStrategy.SKIP)
    chain.add_pre_process(ThreadDataMiddleware())
    chain.add_pre_process(EmotionMiddleware(heartflow))
    chain.add_pre_process(PFCPlanningMiddleware(pfc, persona, greeting))
    chain.add_pre_process(InnerVoiceMiddleware(inner_voice, persona))
    chain.add_dispatch(SystemPromptMiddleware(persona, memory_manager, capability_registry, device_manager))
    chain.add_dispatch(SummarizationMiddleware(llm_dispatch_fn=llm_dispatch_fn))
    chain.add_dispatch(MemoryInjectionMiddleware())
    chain.add_dispatch(LLMDispatchMiddleware(dispatcher, tool_registry, expression, persona, capability_registry))
    chain.add_dispatch(ReflectionMiddleware(pfc))
    chain.add_dispatch(ToolExecutionMiddleware(policy_engine, tool_registry))
    chain.add_post_process(MemoryStoreMiddleware(memory_manager, greeting))
    chain.add_post_process(LoopDetectionMiddleware())
    chain.add_post_process(TokenUsageMiddleware())
    chain.add_post_process(TitleMiddleware())
    return chain


class InteractionMemoryStoreMiddleware(BaseMiddleware):
    def __init__(self, interaction_memory: Any, greeting_manager: Any):
        self._interaction_memory = interaction_memory
        self._greeting = greeting_manager

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        session_id = context.thread_id
        emotion_ctx = context.emotion_context or {}
        emotion_label = emotion_ctx.get("label", "")
        emotion_intensity = emotion_ctx.get("intensity", 0.0)
        inner_voice_text = context.inner_voice or ""

        await self._interaction_memory.record(
            content=context.user_message,
            role="user",
            emotion_label=emotion_label,
            emotion_intensity=emotion_intensity,
            session_id=session_id,
        )
        await self._interaction_memory.record(
            content=context.reply,
            role="assistant",
            emotion_label=emotion_label,
            emotion_intensity=emotion_intensity,
            inner_voice=inner_voice_text,
            session_id=session_id,
        )

        if context.metadata.get("chat_history") is None:
            context.metadata["chat_history"] = []

        context.metadata["chat_history"].append({
            "role": "user",
            "content": context.user_message,
        })
        context.metadata["chat_history"].append({
            "role": "assistant",
            "content": context.reply,
        })

        if self._greeting:
            self._greeting.update_last_topics([context.user_message[:50]])

        return await next_middleware(context)


class FullRecallMiddleware(BaseMiddleware):
    def __init__(self, interaction_memory: Any):
        self._interaction_memory = interaction_memory

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        recent = await self._interaction_memory.recall_recent(count=30)
        if recent:
            existing_ids = {f.get("id") for f in context.memory_facts if f.get("id")}
            new_facts = [
                {"content": e.content, "role": e.role, "id": e.id}
                for e in recent
                if e.id not in existing_ids
            ]
            context.memory_facts = context.memory_facts + new_facts
        return await next_middleware(context)


def create_interaction_chain(
    heartflow: Any,
    pfc: Any,
    persona: Any,
    greeting: Any,
    inner_voice: Any,
    interaction_memory: Any,
    dispatcher: Any,
    tool_registry: Any,
    expression: Any,
    policy_engine: Any,
    llm_dispatch_fn: Any = None,
    capability_registry: Any = None,
    device_manager: Any = None,
) -> MiddlewareChain:
    chain = MiddlewareChain(error_strategy=ErrorStrategy.SKIP)
    chain.add_pre_process(ThreadDataMiddleware())
    chain.add_pre_process(EmotionMiddleware(heartflow))
    chain.add_pre_process(PFCPlanningMiddleware(pfc, persona, greeting))
    chain.add_pre_process(InnerVoiceMiddleware(inner_voice, persona))
    chain.add_pre_process(FullRecallMiddleware(interaction_memory))
    chain.add_dispatch(SystemPromptMiddleware(persona, interaction_memory, capability_registry, device_manager))
    chain.add_dispatch(SummarizationMiddleware(llm_dispatch_fn=llm_dispatch_fn))
    chain.add_dispatch(MemoryInjectionMiddleware())
    chain.add_dispatch(LLMDispatchMiddleware(dispatcher, tool_registry, expression, persona, capability_registry))
    chain.add_dispatch(ReflectionMiddleware(pfc))
    chain.add_dispatch(ToolExecutionMiddleware(policy_engine, tool_registry))
    chain.add_post_process(InteractionMemoryStoreMiddleware(interaction_memory, greeting))
    chain.add_post_process(LoopDetectionMiddleware())
    chain.add_post_process(TokenUsageMiddleware())
    chain.add_post_process(TitleMiddleware())
    return chain


class ExecutionSystemPromptMiddleware(BaseMiddleware):
    def __init__(self, memory_manager: Any, capability_registry: Any = None):
        self._memory = memory_manager
        self._capability_registry = capability_registry

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        from app.core.agent.prompts import build_capability_summary

        memories = await self._memory.retrieve(context.user_message, top_k=5)
        memory_context = "\n".join(m.content for m in memories) if memories else ""
        context.memory_facts = [{"content": m.content} for m in memories] if memories else []

        system_content = (
            "You are a task execution agent. Your sole purpose is to complete tasks efficiently and accurately. "
            "Focus on producing correct, actionable results. Do not add emotional or conversational elements."
        )
        if memory_context:
            system_content += f"\n\n[Relevant context]\n{memory_context}"

        cap_summary = build_capability_summary(self._capability_registry) if self._capability_registry else ""
        if cap_summary:
            system_content += f"\n\n[Available capabilities]\n{cap_summary}"

        context.messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": context.user_message},
        ]
        return await next_middleware(context)


class ExecutionDispatchMiddleware(BaseMiddleware):
    def __init__(self, dispatcher: Any, tool_registry: Any, capability_registry: Any = None):
        self._dispatcher = dispatcher
        self._tools = tool_registry
        self._capability_registry = capability_registry

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        from app.core.llm.dispatcher import TaskCategory

        tools = None
        if self._capability_registry:
            tools = self._capability_registry.get_definitions()
        elif self._tools:
            tools = self._tools.get_definitions()

        response = await self._dispatcher.dispatch(
            TaskCategory.DAILY,
            messages=context.messages,
            tools=tools,
        )

        reply = response.choices[0].message.content
        context.reply = reply
        context.metadata["llm_response"] = response

        if hasattr(response, "usage") and response.usage:
            context.metadata["token_usage"] = {
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
            }

        return await next_middleware(context)


class ExecutionMemoryStoreMiddleware(BaseMiddleware):
    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable[[MiddlewareContext], Awaitable[MiddlewareContext]],
    ) -> MiddlewareContext:
        store_user = asyncio.create_task(
            self._memory.store(
                context.user_message,
                {"role": "user", "session_id": context.thread_id, "agent": "execution"},
            )
        )
        store_reply = asyncio.create_task(
            self._memory.store(
                context.reply,
                {"role": "assistant", "session_id": context.thread_id, "agent": "execution"},
            )
        )
        await asyncio.gather(store_user, store_reply)
        return await next_middleware(context)


def create_execution_chain(
    memory_manager: Any,
    dispatcher: Any,
    tool_registry: Any,
    policy_engine: Any,
    llm_dispatch_fn: Any = None,
    capability_registry: Any = None,
) -> MiddlewareChain:
    chain = MiddlewareChain(error_strategy=ErrorStrategy.SKIP)
    chain.add_pre_process(ThreadDataMiddleware())
    chain.add_dispatch(ExecutionSystemPromptMiddleware(memory_manager, capability_registry))
    chain.add_dispatch(MemoryInjectionMiddleware())
    chain.add_dispatch(SummarizationMiddleware(llm_dispatch_fn=llm_dispatch_fn))
    chain.add_dispatch(ExecutionDispatchMiddleware(dispatcher, tool_registry, capability_registry))
    chain.add_dispatch(ToolExecutionMiddleware(policy_engine, tool_registry))
    chain.add_post_process(ExecutionMemoryStoreMiddleware(memory_manager))
    chain.add_post_process(LoopDetectionMiddleware())
    chain.add_post_process(TokenUsageMiddleware())
    chain.add_post_process(TitleMiddleware())
    return chain
