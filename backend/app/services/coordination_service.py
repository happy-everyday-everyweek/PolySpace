import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    EMAIL_ALERT = "email_alert"
    TASK_REMINDER = "task_reminder"
    SCHEDULE_REMINDER = "schedule_reminder"
    PROACTIVE_GREETING = "proactive_greeting"
    AI_ACTION_REPORT = "ai_action_report"
    URGENT_ATTENTION = "urgent_attention"
    PROACTIVE_SERVICE = "proactive_service"
    SCENE_CHANGE = "scene_change"
    AUTOMATION_TRIGGER = "automation_trigger"


class ScheduleItemType(Enum):
    EMAIL_CHECK = "email_check"
    TASK_REVIEW = "task_review"
    USER_REMINDER = "user_reminder"
    PROACTIVE_OUTREACH = "proactive_outreach"
    SYSTEM_MAINTENANCE = "system_maintenance"
    HABIT_LEARNING = "habit_learning"
    CONTEXT_REFRESH = "context_refresh"
    PRIVACY_AUDIT = "privacy_audit"


@dataclass
class Notification:
    id: str
    type: NotificationType
    title: str
    content: str
    priority: str
    source: str
    created_at: float
    read: bool = False
    action_required: bool = False
    action_data: Optional[dict] = None
    dismissed: bool = False


@dataclass
class ScheduleItem:
    id: str
    type: ScheduleItemType
    title: str
    description: str
    scheduled_time: float
    executed: bool = False
    recurring: bool = False
    interval_seconds: int = 0
    last_executed: Optional[float] = None


@dataclass
class AIDailyPlan:
    date: str
    email_checks: list[dict] = field(default_factory=list)
    scheduled_reminders: list[dict] = field(default_factory=list)
    proactive_actions: list[dict] = field(default_factory=list)
    pending_tasks: list[dict] = field(default_factory=list)
    summary: str = ""


class CoordinationService:
    def __init__(self):
        self._dispatcher = None
        self._ai_email_service = None
        self._notifications: list[Notification] = []
        self._schedule: list[ScheduleItem] = []
        self._daily_plan: Optional[AIDailyPlan] = None
        self._running = False
        self._coordination_task: Optional[asyncio.Task] = None
        self._ws_manager = None
        self._notification_callbacks: list = []
        self._last_user_interaction: float = time.time()
        self._user_online: bool = False

        self._context_aggregator = None
        self._user_profile = None
        self._context_window = None
        self._habit_learner = None
        self._behavior_predictor = None
        self._screen_handler = None
        self._notification_handler = None
        self._proactive_scheduler = None
        self._service_registry = None
        self._channel_router = None
        self._content_generator = None
        self._conversational_service = None
        self._multimodal_understanding = None
        self._workflow_engine = None
        self._agent_coordinator = None
        self._environment_rules = None
        self._activity_handoff = None
        self._context_sync = None
        self._privacy_guard = None
        self._consent_manager = None
        self._local_first = None

    def _init_submodules(self):
        from app.core.coordination.agent_team.coordinator import get_agent_coordinator
        from app.core.coordination.automation.environment_rules import get_environment_rules_engine
        from app.core.coordination.context.aggregator import get_context_aggregator
        from app.core.coordination.context.context_window import SlidingContextWindow
        from app.core.coordination.context.habit_learner import get_habit_learner
        from app.core.coordination.context.multimodal import get_multimodal_understanding
        from app.core.coordination.context.notification_handler import get_notification_handler
        from app.core.coordination.context.predictor import get_behavior_predictor
        from app.core.coordination.context.screen_handler import get_screen_handler
        from app.core.coordination.context.user_profile import get_user_profile
        from app.core.coordination.handoff.activity_handoff import get_activity_handoff, get_context_sync
        from app.core.coordination.privacy.privacy_guard import get_consent_manager, get_local_first, get_privacy_guard
        from app.core.coordination.proactive.channel_router import get_channel_router
        from app.core.coordination.proactive.content_generator import get_content_generator
        from app.core.coordination.proactive.conversational import get_conversational_service
        from app.core.coordination.proactive.scheduler import get_proactive_scheduler
        from app.core.coordination.proactive.service_registry import get_service_registry
        from app.core.coordination.workflow.workflow_engine import get_workflow_engine

        self._context_aggregator = get_context_aggregator()
        self._user_profile = get_user_profile()
        self._context_window = SlidingContextWindow()
        self._habit_learner = get_habit_learner()
        self._behavior_predictor = get_behavior_predictor()
        self._screen_handler = get_screen_handler()
        self._notification_handler = get_notification_handler()
        self._proactive_scheduler = get_proactive_scheduler()
        self._service_registry = get_service_registry()
        self._channel_router = get_channel_router()
        self._content_generator = get_content_generator()
        self._conversational_service = get_conversational_service()
        self._multimodal_understanding = get_multimodal_understanding()
        self._workflow_engine = get_workflow_engine()
        self._agent_coordinator = get_agent_coordinator()
        self._environment_rules = get_environment_rules_engine()
        self._activity_handoff = get_activity_handoff()
        self._context_sync = get_context_sync()
        self._privacy_guard = get_privacy_guard()
        self._consent_manager = get_consent_manager()
        self._local_first = get_local_first()

    def _get_dispatcher(self):
        if self._dispatcher is None:
            from app.core.llm.dispatcher import ModelDispatcher
            self._dispatcher = ModelDispatcher()
        return self._dispatcher

    def _get_ai_email_service(self):
        if self._ai_email_service is None:
            from app.services.email.ai_service import get_ai_email_service
            self._ai_email_service = get_ai_email_service()
        return self._ai_email_service

    def set_ws_manager(self, ws_manager):
        self._ws_manager = ws_manager

    def on_notification(self, callback):
        self._notification_callbacks.append(callback)

    def update_user_status(self, online: bool):
        self._user_online = online
        if online:
            self._last_user_interaction = time.time()
        if self._user_profile:
            self._user_profile.record_interaction()

    def record_user_interaction(self):
        self._last_user_interaction = time.time()
        if self._user_profile:
            self._user_profile.record_interaction()

    async def push_notification(self, notification: Notification):
        self._notifications.insert(0, notification)
        if len(self._notifications) > 200:
            self._notifications = self._notifications[:200]

        for cb in self._notification_callbacks:
            try:
                await cb(notification)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")

        if self._ws_manager:
            try:
                await self._ws_manager.broadcast(json.dumps({
                    "type": "notification",
                    "data": {
                        "id": notification.id,
                        "notification_type": notification.type.value,
                        "title": notification.title,
                        "content": notification.content,
                        "priority": notification.priority,
                        "source": notification.source,
                        "action_required": notification.action_required,
                        "action_data": notification.action_data,
                    }
                }))
            except Exception as e:
                logger.error(f"WebSocket push failed: {e}")

    async def ingest_context(self, source: str, data: dict, priority: str = "normal") -> None:
        if not self._context_aggregator:
            self._init_submodules()
        from app.core.coordination.context.aggregator import ContextEvent, ContextSource
        try:
            source_enum = ContextSource(source)
        except ValueError:
            source_enum = ContextSource.USER_INTERACTION
        event = ContextEvent(source=source_enum, data=data, priority=priority)
        await self._context_aggregator.ingest(event)
        if self._context_window:
            evt = {
                "source": source, "data": data,
                "timestamp": time.time(), "priority": priority,
            }
            self._context_window.add_event(evt)
        if self._user_profile:
            self._user_profile.record_interaction()

    async def process_screen_data(self, screen_data: dict) -> Optional[dict]:
        if not self._screen_handler:
            self._init_submodules()
        result = await self._screen_handler.process_screen_data(screen_data)
        if result:
            return {"app": result.app_name, "activity": result.activity_name, "is_sensitive": result.is_sensitive}
        return None

    async def process_notification_data(self, notif_data: dict) -> Optional[dict]:
        if not self._notification_handler:
            self._init_submodules()
        result = await self._notification_handler.process_notification(notif_data)
        return {
            "category": result.category.value,
            "urgency": result.urgency.value,
            "action_items": result.action_items,
            "summary": result.summary,
            "suggested_action": result.suggested_action,
            "time_sensitive": result.time_sensitive,
        }

    async def get_full_context(self) -> dict:
        if not self._context_aggregator:
            self._init_submodules()
        context = await self._context_aggregator.get_current_context()
        profile = self._user_profile.get_current() if self._user_profile else {}
        window = self._context_window.get_full_context() if self._context_window else {}
        return {
            "context": context,
            "user_profile": profile,
            "context_window": window,
        }

    async def get_proactive_services(self) -> list[dict]:
        if not self._service_registry:
            self._init_submodules()
        return self._service_registry.list_services()

    async def toggle_proactive_service(self, name: str, enabled: bool) -> bool:
        if not self._service_registry:
            self._init_submodules()
        return self._service_registry.toggle_service(name, enabled)

    async def trigger_proactive_service(self, service_name: str) -> Optional[dict]:
        if not self._proactive_scheduler:
            self._init_submodules()
        result = await self._proactive_scheduler.manual_trigger(service_name)
        return result.to_dict() if result else None

    async def get_proactive_stats(self) -> dict:
        if not self._proactive_scheduler:
            self._init_submodules()
        return self._proactive_scheduler.get_stats()

    async def get_proactive_history(self, limit: int = 50) -> list[dict]:
        if not self._proactive_scheduler:
            self._init_submodules()
        return self._proactive_scheduler.get_history(limit)

    async def record_proactive_feedback(self, service_id: str, feedback: str) -> bool:
        if not self._proactive_scheduler:
            self._init_submodules()
        result = self._proactive_scheduler.record_feedback(service_id, feedback)
        if result and self._service_registry:
            parts = service_id.split("_")
            if len(parts) >= 3:
                self._service_registry.record_feedback(parts[-1], feedback)
        return result

    async def detect_scene(self) -> Optional[dict]:
        if not self._multimodal_understanding:
            self._init_submodules()
        context = await self._context_aggregator.get_current_context() if self._context_aggregator else {}
        profile = self._user_profile.get_current() if self._user_profile else {}
        result = await self._multimodal_understanding.understand(context, profile)
        return result

    async def start_conversation(self, topic: str, reason: str) -> Optional[dict]:
        if not self._conversational_service:
            self._init_submodules()
        context = await self._context_aggregator.get_current_context() if self._context_aggregator else {}
        result = await self._conversational_service.initiate_conversation(topic, reason, context)
        return result

    async def continue_conversation(self, conv_id: str, user_response: str) -> Optional[dict]:
        if not self._conversational_service:
            self._init_submodules()
        return await self._conversational_service.continue_conversation(conv_id, user_response)

    async def create_workflow(self, template_name: str, params: Optional[dict] = None) -> Optional[dict]:
        if not self._workflow_engine:
            self._init_submodules()
        wf = self._workflow_engine.create_from_template(template_name, params)
        return wf.to_dict() if wf else None

    async def execute_workflow(self, workflow_id: str) -> Optional[dict]:
        if not self._workflow_engine:
            self._init_submodules()
        return await self._workflow_engine.execute(workflow_id)

    async def evaluate_automation(self) -> list[dict]:
        if not self._environment_rules:
            self._init_submodules()
        context = await self._context_aggregator.get_current_context() if self._context_aggregator else {}
        profile = self._user_profile.get_current() if self._user_profile else {}
        return await self._environment_rules.evaluate(context, profile)

    async def get_habit_patterns(self, pattern_type: Optional[str] = None) -> list[dict]:
        if not self._habit_learner:
            self._init_submodules()
        return self._habit_learner.get_patterns(pattern_type)

    async def get_prediction(self) -> Optional[dict]:
        if not self._behavior_predictor:
            self._init_submodules()
        context = await self._context_aggregator.get_current_context() if self._context_aggregator else {}
        profile = self._user_profile.get_current() if self._user_profile else {}
        prediction = self._behavior_predictor.predict_next_action(context, profile)
        return prediction.to_dict()

    async def get_privacy_status(self) -> dict:
        if not self._privacy_guard:
            self._init_submodules()
        return {
            "preferences": self._privacy_guard.get_preferences(),
            "consents": self._consent_manager.list_consents(),
            "local_ratio": self._local_first.get_local_ratio(),
        }

    async def set_privacy_preference(self, key: str, value) -> None:
        if not self._privacy_guard:
            self._init_submodules()
        self._privacy_guard.set_preference(key, value)

    async def grant_consent(self, service_name: str, data_types: list[str], channels: list[str]) -> dict:
        if not self._consent_manager:
            self._init_submodules()
        record = self._consent_manager.grant_consent(service_name, data_types, channels)
        return record.to_dict()

    async def revoke_consent(self, service_name: str) -> bool:
        if not self._consent_manager:
            self._init_submodules()
        return self._consent_manager.revoke_consent(service_name)

    async def get_proactive_config(self) -> dict:
        if not self._proactive_scheduler:
            self._init_submodules()
        config: dict = {
            "enabled": self._running,
            "scheduler": {
                "check_interval": self._proactive_scheduler._check_interval,
                "default_cooldown": self._proactive_scheduler._default_cooldown,
                "memory_build_interval": self._proactive_scheduler._memory_build_interval,
                "optimize_interval": self._proactive_scheduler._optimize_interval,
            },
            "delivery": {
                "meeting_quiet_mode": getattr(self._proactive_scheduler, '_meeting_quiet_mode', True),
                "focus_filter": getattr(self._proactive_scheduler, '_focus_filter', True),
                "mood_aware": getattr(self._proactive_scheduler, '_mood_aware', True),
            },
        }
        return config

    async def set_proactive_config(
        self,
        enabled: Optional[bool] = None,
        scheduler: Optional[dict] = None,
        delivery: Optional[dict] = None,
    ) -> None:
        if not self._proactive_scheduler:
            self._init_submodules()
        if enabled is not None:
            if enabled and not self._running:
                await self.start()
            elif not enabled and self._running:
                await self.stop()
        if scheduler:
            if "check_interval" in scheduler:
                self._proactive_scheduler._check_interval = max(10, int(scheduler["check_interval"]))
            if "default_cooldown" in scheduler:
                self._proactive_scheduler._default_cooldown = max(30, int(scheduler["default_cooldown"]))
            if "memory_build_interval" in scheduler:
                self._proactive_scheduler._memory_build_interval = max(30, int(scheduler["memory_build_interval"]))
            if "optimize_interval" in scheduler:
                self._proactive_scheduler._optimize_interval = max(600, int(scheduler["optimize_interval"]))
        if delivery:
            if "meeting_quiet_mode" in delivery:
                self._proactive_scheduler._meeting_quiet_mode = bool(delivery["meeting_quiet_mode"])
            if "focus_filter" in delivery:
                self._proactive_scheduler._focus_filter = bool(delivery["focus_filter"])
            if "mood_aware" in delivery:
                self._proactive_scheduler._mood_aware = bool(delivery["mood_aware"])

    async def toggle_automation_rule(self, rule_name: str, enabled: bool) -> bool:
        if not self._environment_rules:
            self._init_submodules()
        rule_id = f"rule_{rule_name}"
        return self._environment_rules.toggle_rule(rule_id, enabled)

    async def handle_email_decision(self, decision, record):
        action = decision.action if isinstance(decision.action, str) else decision.action.value
        priority = decision.priority if isinstance(decision.priority, str) else decision.priority.value

        if action == "notify_user":
            notification = Notification(
                id=f"notif_{int(time.time())}_{decision.email_id}",
                type=NotificationType.EMAIL_ALERT,
                title=f"New email: {record.subject}",
                content=decision.notification_message or decision.reason,
                priority=priority,
                source="ai_email",
                created_at=time.time(),
                action_required=priority in ("urgent", "high"),
                action_data={"email_id": decision.email_id, "sender": record.sender},
            )
            await self.push_notification(notification)

        elif action == "forward_to_user":
            notification = Notification(
                id=f"notif_{int(time.time())}_fwd_{decision.email_id}",
                type=NotificationType.EMAIL_ALERT,
                title=f"Email needs your attention: {record.subject}",
                content=decision.notification_message or f"From {record.sender}: {decision.reason}",
                priority=priority,
                source="ai_email",
                created_at=time.time(),
                action_required=True,
                action_data={"email_id": decision.email_id, "action": "forward"},
            )
            await self.push_notification(notification)

        elif action == "auto_reply" and record.auto_replied:
            notification = Notification(
                id=f"notif_{int(time.time())}_auto_{decision.email_id}",
                type=NotificationType.AI_ACTION_REPORT,
                title=f"Auto-replied to: {record.subject}",
                content=f"AI auto-replied to {record.sender}. Reason: {decision.reason}",
                priority="low",
                source="ai_email",
                created_at=time.time(),
                action_required=False,
            )
            await self.push_notification(notification)

        elif action == "extract_task" and record.tasks_created:
            notification = Notification(
                id=f"notif_{int(time.time())}_task_{decision.email_id}",
                type=NotificationType.TASK_REMINDER,
                title=f"Tasks extracted from: {record.subject}",
                content=f"AI extracted {len(record.tasks_created)} task(s) from {record.sender}'s email.",
                priority=priority,
                source="ai_email",
                created_at=time.time(),
                action_required=True,
                action_data={"email_id": decision.email_id, "tasks": record.tasks_created},
            )
            await self.push_notification(notification)

        elif action == "schedule_event":
            notification = Notification(
                id=f"notif_{int(time.time())}_sched_{decision.email_id}",
                type=NotificationType.SCHEDULE_REMINDER,
                title=f"Meeting from email: {record.subject}",
                content=decision.reason,
                priority=priority,
                source="ai_email",
                created_at=time.time(),
                action_required=True,
                action_data={"email_id": decision.email_id, "schedule": decision.schedule_info},
            )
            await self.push_notification(notification)

    async def generate_daily_plan(self) -> AIDailyPlan:
        from app.core.llm.dispatcher import TaskCategory
        dispatcher = self._get_dispatcher()

        email_svc = self._get_ai_email_service()
        email_stats = email_svc.get_stats()

        pending_notifs = [n for n in self._notifications if not n.read and n.action_required]
        pending_schedule = [s for s in self._schedule if not s.executed]

        now = time.localtime()
        date_str = time.strftime("%Y-%m-%d", now)

        prompt = """You are an AI coordination assistant. Generate a daily plan for the AI agent.

Based on the current state, plan:
1. Email check schedule (when to check for new emails)
2. Scheduled reminders (what to remind the user about)
3. Proactive actions (when to proactively reach out to the user)
4. Pending tasks to follow up on

Return JSON:
{
  "email_checks": [{"time": "HH:MM", "reason": "..."}],
  "scheduled_reminders": [{"time": "HH:MM", "title": "...", "content": "...", "priority": "high/medium/low"}],
  "proactive_actions": [{"time": "HH:MM", "action": "greeting/reminder/suggestion", "content": "..."}],
  "pending_tasks": [{"title": "...", "priority": "high/medium/low", "due_hint": "..."}],
  "summary": "Brief summary of today's plan"
}"""

        extra_context = {}
        if self._user_profile:
            extra_context["user_profile"] = self._user_profile.get_current()
        if self._habit_learner:
            extra_context["habit_patterns"] = len(self._habit_learner.get_patterns())

        context = json.dumps({
            "date": date_str,
            "current_hour": now.tm_hour,
            "email_stats": email_stats,
            "pending_notifications": len(pending_notifs),
            "pending_schedule_items": len(pending_schedule),
            "user_online": self._user_online,
            "hours_since_last_interaction": (time.time() - self._last_user_interaction) / 3600,
            **extra_context,
        }, ensure_ascii=False)

        try:
            response = await dispatcher.dispatch(TaskCategory.INTENT, messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": context},
            ])
            content = response.choices[0].message.content
            result = json.loads(content)
            plan = AIDailyPlan(
                date=date_str,
                email_checks=result.get("email_checks", []),
                scheduled_reminders=result.get("scheduled_reminders", []),
                proactive_actions=result.get("proactive_actions", []),
                pending_tasks=result.get("pending_tasks", []),
                summary=result.get("summary", ""),
            )
            self._daily_plan = plan
            return plan
        except Exception as e:
            logger.error(f"Daily plan generation failed: {e}")
            return AIDailyPlan(date=date_str, summary=f"Plan generation failed: {e}")

    async def check_proactive_outreach(self):
        idle_hours = (time.time() - self._last_user_interaction) / 3600
        if idle_hours < 0.5:
            return

        from app.core.llm.dispatcher import TaskCategory
        dispatcher = self._get_dispatcher()

        prompt = """You are an AI assistant deciding whether to proactively reach out to the user.

Consider:
- How long since last interaction
- Whether there are pending notifications
- Whether there are important emails or tasks
- Time of day appropriateness

Return JSON:
{
  "should_reach_out": true/false,
  "message": "the message to send if should_reach_out is true",
  "reason": "why you decided this"
}"""

        context_data = {
            "idle_hours": round(idle_hours, 1),
            "pending_notifications": len([n for n in self._notifications if not n.read]),
            "urgent_notifications": len([n for n in self._notifications if not n.read and n.priority == "urgent"]),
            "current_hour": time.localtime().tm_hour,
            "user_online": self._user_online,
        }
        if self._user_profile:
            context_data["user_activity"] = self._user_profile.get_current().get("activity", "unknown")
            context_data["user_mood"] = self._user_profile.get_current().get("mood", "unknown")

        context = json.dumps(context_data, ensure_ascii=False)

        try:
            response = await dispatcher.dispatch(TaskCategory.DAILY, messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": context},
            ])
            content = response.choices[0].message.content
            result = json.loads(content)

            if result.get("should_reach_out") and result.get("message"):
                notification = Notification(
                    id=f"notif_{int(time.time())}_proactive",
                    type=NotificationType.PROACTIVE_GREETING,
                    title="AI Assistant",
                    content=result["message"],
                    priority="normal",
                    source="coordination",
                    created_at=time.time(),
                    action_required=False,
                )
                await self.push_notification(notification)
        except Exception as e:
            logger.error(f"Proactive outreach check failed: {e}")

    async def start(self):
        if self._running:
            return
        self._running = True
        self._init_submodules()

        ai_email = self._get_ai_email_service()
        ai_email.on_decision(self.handle_email_decision)
        await ai_email.start_monitoring(poll_interval=60)

        from app.core.agent.cron import CronJob, CronPayload, CronSchedule, CronScheduleKind, CronService
        self._cron = CronService()

        proactive_job = CronJob(
            name="proactive_outreach",
            schedule=CronSchedule(kind=CronScheduleKind.EVERY, every_ms=300000),
            payload=CronPayload(kind="systemEvent", text="check_proactive_outreach"),
        )
        proactive_job._callback = lambda p: self.check_proactive_outreach()
        self._cron.add_job(proactive_job)

        plan_job = CronJob(
            name="daily_plan_refresh",
            schedule=CronSchedule(kind=CronScheduleKind.EVERY, every_ms=1800000),
            payload=CronPayload(kind="systemEvent", text="generate_daily_plan"),
        )
        plan_job._callback = lambda p: self.generate_daily_plan()
        self._cron.add_job(plan_job)

        habit_job = CronJob(
            name="habit_learning",
            schedule=CronSchedule(kind=CronScheduleKind.EVERY, every_ms=600000),
            payload=CronPayload(kind="systemEvent", text="habit_learning_cycle"),
        )
        habit_job._callback = lambda p: self._habit_learning_cycle()
        self._cron.add_job(habit_job)

        await self._cron.start()

        if self._proactive_scheduler:
            self._proactive_scheduler.set_ws_manager(self._ws_manager)
            await self._proactive_scheduler.start()

        logger.info("Coordination service started (enhanced with proactive modules)")

    async def _habit_learning_cycle(self):
        try:
            if self._context_aggregator and self._habit_learner:
                context = await self._context_aggregator.get_current_context()
                hour = time.localtime().tm_hour
                sources = context.get("sources", {})
                if "screen" in sources:
                    app = sources["screen"].get("latest", {}).get("app", "")
                    if app:
                        self._habit_learner.observe_app_usage(app, hour)
                if self._user_profile:
                    activity = self._user_profile.get_current().get("activity", "unknown")
                    self._habit_learner.observe_time_pattern(hour, activity)
        except Exception as e:
            logger.error(f"Habit learning cycle error: {e}")

    async def stop(self):
        self._running = False
        ai_email = self._get_ai_email_service()
        await ai_email.stop_monitoring()
        if hasattr(self, "_cron") and self._cron:
            await self._cron.stop()
        if self._proactive_scheduler:
            await self._proactive_scheduler.stop()
        if self._coordination_task:
            self._coordination_task.cancel()
            try:
                await self._coordination_task
            except asyncio.CancelledError:
                pass
            self._coordination_task = None
        logger.info("Coordination service stopped")

    async def _coordination_loop(self):
        cycle = 0
        while self._running:
            try:
                cycle += 1
                if cycle % 10 == 0:
                    await self.check_proactive_outreach()
                if cycle % 60 == 0:
                    await self.generate_daily_plan()
                if cycle % 20 == 0:
                    await self._habit_learning_cycle()
            except Exception as e:
                logger.error(f"Coordination loop error: {e}")
            await asyncio.sleep(30)

    def get_notifications(self, unread_only: bool = False, limit: int = 50) -> list[dict]:
        notifs = self._notifications
        if unread_only:
            notifs = [n for n in notifs if not n.read]
        return [
            {
                "id": n.id,
                "type": n.type.value,
                "title": n.title,
                "content": n.content,
                "priority": n.priority,
                "source": n.source,
                "created_at": n.created_at,
                "read": n.read,
                "action_required": n.action_required,
                "action_data": n.action_data,
                "dismissed": n.dismissed,
            }
            for n in notifs[:limit]
        ]

    def mark_notification_read(self, notif_id: str) -> bool:
        for n in self._notifications:
            if n.id == notif_id:
                n.read = True
                return True
        return False

    def dismiss_notification(self, notif_id: str) -> bool:
        for n in self._notifications:
            if n.id == notif_id:
                n.dismissed = True
                n.read = True
                return True
        return False

    def get_daily_plan(self) -> Optional[dict]:
        if not self._daily_plan:
            return None
        return {
            "date": self._daily_plan.date,
            "email_checks": self._daily_plan.email_checks,
            "scheduled_reminders": self._daily_plan.scheduled_reminders,
            "proactive_actions": self._daily_plan.proactive_actions,
            "pending_tasks": self._daily_plan.pending_tasks,
            "summary": self._daily_plan.summary,
        }

    async def get_current_context_for_agent(self) -> dict:
        if not self._context_aggregator:
            self._init_submodules()
        return await self._context_aggregator.get_current_context_for_agent()

    async def search_context(self, query: str, limit: int = 5) -> list[dict]:
        if not self._context_aggregator:
            self._init_submodules()
        return await self._context_aggregator.search_context(query, limit)

    def get_recent_activity_summaries(self, limit: int = 10) -> list[dict]:
        if not self._context_aggregator:
            self._init_submodules()
        return self._context_aggregator.get_recent_summaries(limit)

    def get_activity_windows(self, limit: int = 10) -> list[dict]:
        if not self._context_window:
            self._init_submodules()
        return self._context_window.get_activity_windows(limit)

    def get_primary_activity(self) -> dict:
        if not self._context_window:
            self._init_submodules()
        return self._context_window.get_primary_activity()

    def get_recent_memories(self, limit: int = 10) -> list[dict]:
        if not self._proactive_scheduler:
            self._init_submodules()
        return self._proactive_scheduler.get_recent_memories(limit)

    def search_memories(self, query: str, limit: int = 5) -> list[dict]:
        if not self._proactive_scheduler:
            self._init_submodules()
        return self._proactive_scheduler.search_memories(query, limit)

    def get_latest_memory(self) -> Optional[dict]:
        if not self._proactive_scheduler:
            self._init_submodules()
        return self._proactive_scheduler._memory_builder.get_latest_memory()

    def get_status(self) -> dict:
        ai_email = self._get_ai_email_service()
        status = {
            "running": self._running,
            "user_online": self._user_online,
            "unread_notifications": len([n for n in self._notifications if not n.read]),
            "urgent_notifications": len([n for n in self._notifications if not n.read and n.priority == "urgent"]),
            "email_monitoring": ai_email._monitoring,
            "email_stats": ai_email.get_stats(),
            "daily_plan": self.get_daily_plan(),
            "last_user_interaction": self._last_user_interaction,
        }
        if self._proactive_scheduler:
            status["proactive_stats"] = self._proactive_scheduler.get_stats()
        if self._service_registry:
            status["proactive_services_count"] = len(self._service_registry.list_services())
            status["proactive_services_enabled"] = len(self._service_registry.list_services(enabled_only=True))
        if self._user_profile:
            status["user_profile"] = self._user_profile.get_current()
        if self._habit_learner:
            status["habit_patterns_count"] = len(self._habit_learner.get_patterns())
        return status


_coordination_service: Optional[CoordinationService] = None


def get_coordination_service() -> CoordinationService:
    global _coordination_service
    if _coordination_service is None:
        _coordination_service = CoordinationService()
    return _coordination_service
