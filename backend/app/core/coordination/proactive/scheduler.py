import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.core.coordination.context.aggregator import get_context_aggregator
from app.core.coordination.context.memory_builder import get_activity_memory_builder
from app.core.coordination.context.trigger import (
    ProactiveTrigger,
    TriggerCondition,
    TriggerConditionType,
    TriggerOperator,
)
from app.core.coordination.context.user_profile import get_user_profile
from app.core.coordination.proactive.channel_router import get_channel_router
from app.core.coordination.proactive.content_generator import get_content_generator
from app.core.coordination.proactive.service_registry import get_service_registry

logger = logging.getLogger(__name__)


class ServicePriority(str, Enum):
    URGENT = "urgent"
    IMPORTANT = "important"
    SUGGESTED = "suggested"
    CHITCHAT = "chitchat"


@dataclass
class ScheduledService:
    service_id: str
    service_name: str
    priority: ServicePriority
    content: str
    channel: str
    trigger_reason: str
    scheduled_at: float = field(default_factory=time.time)
    delivered: bool = False
    feedback: Optional[str] = None
    structured_content: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "priority": self.priority.value,
            "content": self.content,
            "channel": self.channel,
            "trigger_reason": self.trigger_reason,
            "scheduled_at": self.scheduled_at,
            "delivered": self.delivered,
            "feedback": self.feedback,
        }
        if self.structured_content:
            result["structured_content"] = self.structured_content
        return result


def _build_default_triggers() -> list[tuple]:
    ctype = TriggerConditionType
    cond = TriggerCondition
    return [
        ("daily_briefing", [cond(type=ctype.TIME_OF_DAY, params={"from_hour": 7, "to_hour": 9})],
         TriggerOperator.AND, "important", 3600.0, 3),
        ("meeting_prep", [cond(type=ctype.CONTEXT_SOURCE_ACTIVE, params={"source": "calendar"})],
         TriggerOperator.AND, "important", 600.0, 5),
        ("deadline_guard", [cond(type=ctype.CONTEXT_SOURCE_ACTIVE, params={"source": "calendar"})],
         TriggerOperator.AND, "urgent", 1800.0, 8),
        ("focus_protector", [cond(type=ctype.USER_ACTIVITY, params={"activity": "focused"})],
         TriggerOperator.AND, "important", 600.0, 6),
        ("smart_followup", [cond(type=ctype.IDLE_TIME, params={"min_seconds": 300, "max_seconds": 1800})],
         TriggerOperator.AND, "suggested", 900.0, 5),
        ("wellness_guard", [cond(type=ctype.TIME_OF_DAY, params={"from_hour": 9, "to_hour": 22})],
         TriggerOperator.AND, "suggested", 1800.0, 8),
        ("weather_advisor", [cond(type=ctype.TIME_OF_DAY, params={"from_hour": 6, "to_hour": 9})],
         TriggerOperator.AND, "important", 3600.0, 4),
        ("device_health", [cond(type=ctype.CONTEXT_SOURCE_ACTIVE, params={"source": "device_state"})],
         TriggerOperator.AND, "important", 1800.0, 5),
        ("security_guard", [cond(type=ctype.EVENT_COUNT, params={"source": "notification", "min_count": 1})],
         TriggerOperator.AND, "urgent", 300.0, 10),
        ("proactive_greeting", [cond(type=ctype.IDLE_TIME, params={"min_seconds": 1800, "max_seconds": 7200})],
         TriggerOperator.AND, "chitchat", 3600.0, 5),
        ("context_news", [cond(type=ctype.TIME_OF_DAY, params={"from_hour": 10, "to_hour": 12})],
         TriggerOperator.AND, "suggested", 7200.0, 3),
        ("doc_suggestion", [cond(type=ctype.USER_ACTIVITY, params={"activity": "working"})],
         TriggerOperator.AND, "suggested", 1800.0, 5),
        ("learning_path", [cond(type=ctype.IDLE_TIME, params={"min_seconds": 600, "max_seconds": 3600})],
         TriggerOperator.AND, "suggested", 14400.0, 2),
        ("commute_assistant", [cond(type=ctype.TIME_OF_DAY, params={"from_hour": 7, "to_hour": 9})],
         TriggerOperator.OR, "suggested", 3600.0, 4),
        ("expense_tracker", [cond(type=ctype.CONTEXT_SOURCE_ACTIVE, params={"source": "notification"})],
         TriggerOperator.AND, "suggested", 7200.0, 3),
        ("social_reminder", [cond(type=ctype.TIME_OF_DAY, params={"from_hour": 9, "to_hour": 11})],
         TriggerOperator.AND, "suggested", 86400.0, 2),
        ("idea_spark", [cond(type=ctype.IDLE_TIME, params={"min_seconds": 300, "max_seconds": 1800})],
         TriggerOperator.AND, "suggested", 7200.0, 3),
        ("writing_coach", [cond(type=ctype.USER_ACTIVITY, params={"activity": "working"})],
         TriggerOperator.AND, "suggested", 1800.0, 5),
        ("data_insight", [cond(type=ctype.TIME_OF_DAY, params={"from_hour": 9, "to_hour": 18})],
         TriggerOperator.AND, "suggested", 3600.0, 3),
        ("clipboard_insight", [cond(type=ctype.CONTEXT_SOURCE_ACTIVE, params={"source": "clipboard"})],
         TriggerOperator.AND, "suggested", 300.0, 10),
    ]


DEFAULT_TRIGGERS = _build_default_triggers()


class ProactiveScheduler:
    def __init__(self):
        self._aggregator = get_context_aggregator()
        self._user_profile = get_user_profile()
        self._registry = get_service_registry()
        self._router = get_channel_router()
        self._generator = get_content_generator()
        self._memory_builder = get_activity_memory_builder()
        self._trigger = ProactiveTrigger()
        self._register_default_triggers()
        self._queue: list[ScheduledService] = []
        self._delivered: list[ScheduledService] = []
        self._max_delivered = 100
        self._running = False
        self._check_interval = 60.0
        self._memory_build_interval = 120.0
        self._optimize_interval = 3600.0
        self._task: Optional[asyncio.Task] = None
        self._memory_task: Optional[asyncio.Task] = None
        self._optimize_task: Optional[asyncio.Task] = None
        self._ws_manager = None
        self._cooldowns: dict[str, float] = {}
        self._default_cooldown = 300.0
        self._last_memory_build: float = 0.0
        self._last_evaluation_ts: float = 0.0
        self._last_optimize: float = 0.0
        self._has_incremental_events: bool = False
        self._meeting_quiet_mode: bool = True
        self._focus_filter: bool = True
        self._mood_aware: bool = True

    def _register_default_triggers(self) -> None:
        for trigger_id, conditions, operator, priority, cooldown, max_daily in DEFAULT_TRIGGERS:
            self._trigger.register(trigger_id, conditions, operator, priority, cooldown, max_daily)

    def set_ws_manager(self, ws_manager) -> None:
        self._ws_manager = ws_manager

    def set_llm_dispatcher(self, dispatcher) -> None:
        self._generator._dispatcher = dispatcher
        self._memory_builder.set_dispatcher(dispatcher)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        self._memory_task = asyncio.create_task(self._memory_build_loop())
        self._optimize_task = asyncio.create_task(self._optimize_loop())
        logger.info("ProactiveScheduler started with %d default triggers", len(DEFAULT_TRIGGERS))

    async def stop(self) -> None:
        self._running = False
        for task in (self._task, self._memory_task, self._optimize_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._task = None
        self._memory_task = None
        self._optimize_task = None
        logger.info("ProactiveScheduler stopped")

    async def _scheduler_loop(self) -> None:
        while self._running:
            try:
                await self._evaluate_and_schedule()
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
            await asyncio.sleep(self._check_interval)

    async def _memory_build_loop(self) -> None:
        while self._running:
            try:
                now = time.time()
                if (now - self._last_memory_build) >= self._memory_build_interval:
                    new_memories = await self._memory_builder.build_memories()
                    if new_memories:
                        logger.info(f"Built {len(new_memories)} activity memories")
                    self._last_memory_build = now
            except Exception as e:
                logger.error(f"Memory build loop error: {e}")
            await asyncio.sleep(self._memory_build_interval)

    async def _optimize_loop(self) -> None:
        while self._running:
            try:
                now = time.time()
                if (now - self._last_optimize) >= self._optimize_interval:
                    adjustments = self._registry.auto_optimize()
                    if adjustments:
                        logger.info(f"Auto-optimized services: {adjustments}")
                    self._last_optimize = now
            except Exception as e:
                logger.error(f"Optimize loop error: {e}")
            await asyncio.sleep(self._optimize_interval)

    async def _evaluate_and_schedule(self) -> None:
        incremental = self._aggregator.get_incremental_events(self._last_evaluation_ts)
        self._has_incremental_events = len(incremental) > 0

        if self._has_incremental_events:
            summary = self._aggregator.build_activity_summary(incremental)
            self._last_evaluation_ts = time.time()
        else:
            summary = None

        context = await self._aggregator.get_current_context()
        if summary:
            context["activity_summary"] = summary

        profile = self._user_profile.get_current()
        if self._user_profile._interaction_times:
            profile["last_interaction"] = self._user_profile._interaction_times[-1]
        else:
            profile["last_interaction"] = 0

        if summary:
            profile["primary_source"] = summary.get("primary_source", "")
            profile["primary_activity"] = summary.get("primary_activity", "")
            profile["activity_confidence"] = summary.get("confidence", 0.0)

        trigger_results = self._trigger.evaluate(context, profile)
        for result in trigger_results:
            if not result.triggered:
                continue
            service_config = self._registry.get_service(result.trigger_id)
            if not service_config or not service_config.get("enabled", True):
                continue
            now = time.time()
            cooldown_key = result.trigger_id
            last_fire = self._cooldowns.get(cooldown_key, 0)
            cooldown = service_config.get("cooldown_seconds", self._default_cooldown)
            if (now - last_fire) < cooldown:
                continue
            if not self._should_deliver(profile, result.priority):
                continue

            schema_result = await self._generator.generate_structured(
                service_name=result.trigger_id,
                context=context,
                user_profile=profile,
                trigger_reason=", ".join(result.conditions_met),
            )
            content = schema_result.to_text()
            structured = schema_result.to_dict()

            channel = self._router.select_channel(
                urgency=result.priority,
                user_activity=profile.get("activity", "unknown"),
                user_mood=profile.get("mood", "unknown"),
            )
            valid_priorities = [e.value for e in ServicePriority]
            priority = (
                ServicePriority(result.priority)
                if result.priority in valid_priorities
                else ServicePriority.SUGGESTED
            )
            scheduled = ScheduledService(
                service_id=f"svc_{int(now)}_{result.trigger_id}",
                service_name=result.trigger_id,
                priority=priority,
                content=content,
                channel=channel,
                trigger_reason=", ".join(result.conditions_met),
                structured_content=structured,
            )
            self._queue.append(scheduled)
            self._cooldowns[cooldown_key] = now
            self._registry.record_fire(result.trigger_id)
            await self._deliver(scheduled)

    def _should_deliver(self, profile: dict, priority: str) -> bool:
        activity = profile.get("activity", "unknown")
        if self._meeting_quiet_mode and activity == "in_meeting" and priority not in ("urgent", "critical"):
            return False
        if self._focus_filter and activity == "focused" and priority in ("suggested", "chitchat"):
            return False
        confidence = profile.get("activity_confidence", 0.0)
        if self._focus_filter and confidence > 0.7 and activity == "focused" and priority == "suggested":
            return False
        if self._mood_aware:
            mood = profile.get("mood", "unknown")
            if mood == "stressed" and priority in ("suggested", "chitchat"):
                return False
            if mood == "tired" and priority == "chitchat":
                return False
        return True

    async def _deliver(self, service: ScheduledService) -> None:
        service.delivered = True
        self._delivered.append(service)
        if len(self._delivered) > self._max_delivered:
            self._delivered = self._delivered[-self._max_delivered:]
        if self._ws_manager:
            try:
                await self._ws_manager.broadcast(json.dumps({
                    "type": "proactive_service",
                    "data": service.to_dict(),
                }))
            except Exception as e:
                logger.error(f"Proactive service delivery failed: {e}")

    async def manual_trigger(
        self, service_name: str,
        context_override: Optional[dict] = None,
    ) -> Optional[ScheduledService]:
        context = context_override or await self._aggregator.get_current_context()
        profile = self._user_profile.get_current()
        schema_result = await self._generator.generate_structured(
            service_name=service_name,
            context=context,
            user_profile=profile,
            trigger_reason="manual_trigger",
        )
        channel = self._router.select_channel(
            urgency="normal",
            user_activity=profile.get("activity", "unknown"),
            user_mood=profile.get("mood", "unknown"),
        )
        service = ScheduledService(
            service_id=f"svc_manual_{int(time.time())}_{service_name}",
            service_name=service_name,
            priority=ServicePriority.SUGGESTED,
            content=schema_result.to_text(),
            channel=channel,
            trigger_reason="manual_trigger",
            structured_content=schema_result.to_dict(),
        )
        await self._deliver(service)
        self._registry.record_fire(service_name)
        return service

    def record_feedback(self, service_id: str, feedback: str) -> bool:
        for svc in self._delivered:
            if svc.service_id == service_id:
                svc.feedback = feedback
                self._registry.record_feedback(svc.service_name, feedback)
                return True
        return False

    def get_stats(self) -> dict:
        total = len(self._delivered)
        accepted = sum(1 for s in self._delivered if s.feedback == "accepted")
        ignored = sum(1 for s in self._delivered if s.feedback == "ignored")
        negative = sum(1 for s in self._delivered if s.feedback == "negative")
        return {
            "total_delivered": total,
            "accepted": accepted,
            "ignored": ignored,
            "negative": negative,
            "accept_rate": accepted / total if total > 0 else 0.0,
            "pending_queue": len(self._queue),
            "activity_memories": len(self._memory_builder._memories),
        }

    def get_history(self, limit: int = 50) -> list[dict]:
        return [s.to_dict() for s in self._delivered[-limit:]]

    def register_trigger(
        self, trigger_id: str, conditions: list,
        operator: str = "and", priority: str = "normal",
        cooldown: float = 300.0, max_daily: int = 10,
    ) -> None:
        op = TriggerOperator(operator) if operator in [e.value for e in TriggerOperator] else TriggerOperator.AND
        self._trigger.register(trigger_id, conditions, op, priority, cooldown, max_daily)

    async def get_current_context_for_agent(self) -> dict:
        return await self._aggregator.get_current_context_for_agent()

    async def search_context(self, query: str, limit: int = 5) -> list[dict]:
        return await self._aggregator.search_context(query, limit)

    def get_recent_memories(self, limit: int = 10) -> list[dict]:
        return self._memory_builder.get_recent_memories(limit)

    def search_memories(self, query: str, limit: int = 5) -> list[dict]:
        return self._memory_builder.search_memories(query, limit)


_scheduler: Optional[ProactiveScheduler] = None


def get_proactive_scheduler() -> ProactiveScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = ProactiveScheduler()
    return _scheduler
