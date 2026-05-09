from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.auth import get_current_user
from app.services.coordination_service import CoordinationService, get_coordination_service
from app.services.email.ai_service import AIEmailService, get_ai_email_service

router = APIRouter()


def _get_ai_email() -> AIEmailService:
    return get_ai_email_service()


def _get_coord() -> CoordinationService:
    return get_coordination_service()


class AnalyzeEmailRequest(BaseModel):
    email_data: dict


class SetConfigRequest(BaseModel):
    auto_reply: bool = True
    task_extraction: bool = True
    notification: bool = True


class StartMonitorRequest(BaseModel):
    poll_interval: int = 60


class MarkReadRequest(BaseModel):
    notification_id: str


# AI Email endpoints
@router.post("/ai-email/analyze")
async def ai_analyze_email(req: AnalyzeEmailRequest):
    decision = await _get_ai_email().analyze_email(req.email_data)
    return {
        "action": decision.action,
        "category": decision.category,
        "priority": decision.priority,
        "reason": decision.reason,
        "auto_reply_content": decision.auto_reply_content,
        "extracted_tasks": decision.extracted_tasks,
        "schedule_info": decision.schedule_info,
        "notification_message": decision.notification_message,
        "confidence": decision.confidence,
    }


@router.post("/ai-email/process")
async def ai_process_email(req: AnalyzeEmailRequest):
    account_id = req.email_data.get("account_id", 1)
    record = await _get_ai_email().process_new_email(req.email_data, account_id)
    result = {
        "email_id": record.email_id,
        "processed": record.processed,
        "auto_replied": record.auto_replied,
        "user_notified": record.user_notified,
        "tasks_created": record.tasks_created,
    }
    if record.decision:
        result["decision"] = {
            "action": record.decision.action,
            "category": record.decision.category,
            "priority": record.decision.priority,
            "reason": record.decision.reason,
        }
    return result


@router.post("/ai-email/check-new")
async def ai_check_new_emails():
    records = await _get_ai_email().check_new_emails()
    return {"new_emails_processed": len(records), "records": [
        {"email_id": r.email_id, "subject": r.subject, "auto_replied": r.auto_replied, "user_notified": r.user_notified}
        for r in records
    ]}


@router.post("/ai-email/monitor/start")
async def ai_email_monitor_start(req: StartMonitorRequest):
    await _get_ai_email().start_monitoring(poll_interval=req.poll_interval)
    return {"status": "monitoring_started", "poll_interval": req.poll_interval}


@router.post("/ai-email/monitor/stop")
async def ai_email_monitor_stop():
    await _get_ai_email().stop_monitoring()
    return {"status": "monitoring_stopped"}


@router.get("/ai-email/records")
async def ai_email_records(limit: int = 50):
    return {"records": _get_ai_email().get_records(limit=limit)}


@router.get("/ai-email/stats")
async def ai_email_stats():
    return _get_ai_email().get_stats()


@router.post("/ai-email/config")
async def ai_email_config(req: SetConfigRequest):
    _get_ai_email().set_config(auto_reply=req.auto_reply, task_extraction=req.task_extraction, notification=req.notification)
    return {"status": "config_updated"}


# Coordination endpoints
@router.post("/start")
async def coordination_start():
    coord = _get_coord()
    ai_email = _get_ai_email()
    ai_email.on_decision(coord.handle_email_decision)
    await coord.start()
    return {"status": "coordination_started"}


@router.post("/stop")
async def coordination_stop():
    await _get_coord().stop()
    return {"status": "coordination_stopped"}


@router.get("/status")
async def coordination_status():
    return _get_coord().get_status()


@router.get("/notifications")
async def coordination_notifications(unread_only: bool = False, limit: int = 50):
    return {"notifications": _get_coord().get_notifications(unread_only=unread_only, limit=limit)}


@router.post("/notifications/{notif_id}/read")
async def coordination_mark_read(notif_id: str):
    success = _get_coord().mark_notification_read(notif_id)
    return {"success": success}


@router.post("/notifications/{notif_id}/dismiss")
async def coordination_dismiss(notif_id: str):
    success = _get_coord().dismiss_notification(notif_id)
    return {"success": success}


@router.post("/plan/generate")
async def coordination_generate_plan():
    plan = await _get_coord().generate_daily_plan()
    return {
        "date": plan.date,
        "email_checks": plan.email_checks,
        "scheduled_reminders": plan.scheduled_reminders,
        "proactive_actions": plan.proactive_actions,
        "pending_tasks": plan.pending_tasks,
        "summary": plan.summary,
    }


@router.get("/plan")
async def coordination_get_plan():
    plan = _get_coord().get_daily_plan()
    return {"plan": plan}


class UserStatusRequest(BaseModel):
    online: bool = True


@router.post("/user-status")
async def coordination_user_status(req: UserStatusRequest):
    _get_coord().update_user_status(req.online)
    return {"status": "updated"}


@router.post("/user-interaction")
async def coordination_user_interaction():
    _get_coord().record_user_interaction()
    return {"status": "recorded"}


@router.get("/cron/jobs")
async def cron_list_jobs():
    from app.core.agent.cron import get_cron_service
    return {"jobs": get_cron_service().list_jobs()}


@router.post("/cron/jobs")
async def cron_create_job(job_data: dict):
    from app.core.agent.cron import CronJob, CronPayload, CronSchedule, CronScheduleKind, get_cron_service
    sched_raw = job_data.get("schedule", {})
    schedule = CronSchedule(
        kind=CronScheduleKind(sched_raw.get("kind", "every")),
        at=sched_raw.get("at", ""),
        every_ms=sched_raw.get("every_ms", 60000),
        cron_expr=sched_raw.get("cron_expr", ""),
    )
    payload_raw = job_data.get("payload", {})
    payload = CronPayload(
        kind=payload_raw.get("kind", "systemEvent"),
        text=payload_raw.get("text", ""),
        message=payload_raw.get("message", ""),
    )
    job = CronJob(name=job_data.get("name", ""), schedule=schedule, payload=payload, enabled=job_data.get("enabled", True))
    job_id = get_cron_service().add_job(job)
    return {"id": job_id}


@router.delete("/cron/jobs/{job_id}")
async def cron_delete_job(job_id: str):
    from app.core.agent.cron import get_cron_service
    success = get_cron_service().remove_job(job_id)
    return {"success": success}


@router.get("/sessions")
async def session_list(agent_name: str | None = None):
    from app.core.agent.session import get_session_router
    return {"sessions": get_session_router().list_sessions(agent_name=agent_name)}


@router.post("/sessions")
async def session_create(data: dict):
    from app.core.agent.session import get_session_router
    session = get_session_router().create_session(
        agent_name=data.get("agent_name", "main"),
        channel=data.get("channel", "web"),
        session_key=data.get("session_key"),
        metadata=data.get("metadata"),
    )
    return {"id": session.id, "session_key": session.session_key, "agent_name": session.agent_name}


@router.get("/agents")
async def agent_list():
    from app.core.agent.mate.registry import agent_registry
    return {"agents": agent_registry.list_agents()}


@router.get("/memory/summary")
async def memory_summary():
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    return dual.get_combined_summary()


@router.get("/memory/search")
async def memory_search(query: str, limit: int = 20):
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    return dual.search_all(query, limit=limit)


@router.post("/memory/working/task")
async def memory_working_task(data: dict):
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    mid = dual.working.record_task(
        title=data.get("title", ""),
        status=data.get("status", "active"),
        priority=data.get("priority", "normal"),
        due=data.get("due", ""),
        source=data.get("source", ""),
    )
    return {"id": mid}


@router.post("/memory/working/file")
async def memory_working_file(data: dict):
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    mid = dual.working.record_file_operation(
        filename=data.get("filename", ""),
        operation=data.get("operation", "access"),
        summary=data.get("summary", ""),
    )
    return {"id": mid}


@router.post("/memory/interaction/conversation")
async def memory_interaction_conversation(data: dict):
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    mid = dual.interaction.record_conversation(
        topic=data.get("topic", ""),
        mood=data.get("mood", "neutral"),
        key_points=data.get("key_points", []),
    )
    return {"id": mid}


@router.post("/memory/interaction/emotion")
async def memory_interaction_emotion(data: dict):
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    mid = dual.interaction.record_emotion(
        emotion=data.get("emotion", ""),
        intensity=data.get("intensity", 0.5),
        trigger=data.get("trigger", ""),
    )
    return {"id": mid}


@router.post("/memory/interaction/preference")
async def memory_interaction_preference(data: dict):
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    mid = dual.interaction.record_preference(
        key=data.get("key", ""),
        value=data.get("value", ""),
        confidence=data.get("confidence", 0.8),
    )
    return {"id": mid}


@router.post("/memory/dream/{phase}")
async def memory_dream(phase: str):
    from app.core.memory.dreaming import DreamPhase, get_memory_dreamer
    from app.core.memory.manager import get_memory_manager
    try:
        dream_phase = DreamPhase(phase)
    except ValueError:
        return {"error": f"Invalid phase: {phase}. Use light, deep, or rem."}
    dreamer = get_memory_dreamer()
    mgr = get_memory_manager()
    if dream_phase == DreamPhase.LIGHT:
        result = await dreamer.light_dream(mgr)
    elif dream_phase == DreamPhase.DEEP:
        result = await dreamer.deep_dream(mgr)
    elif dream_phase == DreamPhase.REM:
        result = await dreamer.rem_dream(mgr)
    else:
        return {"error": "Unknown phase"}
    return {
        "phase": result.phase.value,
        "insights": result.insights,
        "consolidated": result.consolidated,
        "pruned": result.pruned,
        "patterns": result.patterns,
        "report": result.report,
    }


@router.get("/memory/dream/results")
async def memory_dream_results(phase: str | None = None, limit: int = 20):
    from app.core.memory.dreaming import DreamPhase, get_memory_dreamer
    dreamer = get_memory_dreamer()
    dream_phase = DreamPhase(phase) if phase else None
    return {"results": dreamer.get_results(phase=dream_phase, limit=limit)}


@router.post("/memory/clear")
async def memory_clear():
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    dual.working._entries.clear()
    dual.working._active_tasks.clear()
    dual.working._file_contexts.clear()
    dual.working._schedule_cache.clear()
    dual.working._persist()
    dual.interaction._entries.clear()
    dual.interaction._user_preferences.clear()
    dual.interaction._emotion_history.clear()
    dual.interaction._conversation_topics.clear()
    dual.interaction._communication_style.clear()
    dual.interaction._persist()
    return {"status": "ok", "message": "All memory cleared"}


@router.delete("/memory/working/{entry_id}")
async def memory_delete_working(entry_id: str):
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    dual.working._entries = [e for e in dual.working._entries if e.id != entry_id]
    dual.working._active_tasks = [t for t in dual.working._active_tasks if t.get("id") != entry_id]
    dual.working._persist()
    return {"status": "ok", "entry_id": entry_id}


@router.delete("/memory/interaction/{entry_id}")
async def memory_delete_interaction(entry_id: str):
    from app.core.memory.dual_memory import get_dual_memory
    dual = get_dual_memory()
    dual.ensure_loaded()
    dual.interaction._entries = [e for e in dual.interaction._entries if e.id != entry_id]
    dual.interaction._persist()
    return {"status": "ok", "entry_id": entry_id}


@router.post("/agent/task")
async def agent_submit_task(data: dict):
    from app.core.agent.multi_agent import TaskPriority, get_orchestrator
    from app.core.agent.vertical_agents import register_built_in_agents
    orch = get_orchestrator()
    register_built_in_agents(orch)
    priority = TaskPriority(data.get("priority", "normal"))
    task = await orch.submit_task(
        description=data.get("description", ""),
        goal=data.get("goal", ""),
        priority=priority,
    )
    return {"task_id": task.id, "status": task.status.value}


@router.post("/agent/task/{task_id}/execute")
async def agent_execute_task(task_id: str):
    from app.core.agent.multi_agent import get_orchestrator
    from app.core.agent.vertical_agents import register_built_in_agents
    orch = get_orchestrator()
    register_built_in_agents(orch)
    result = await orch.execute_task(task_id)
    return result


@router.get("/agent/task/{task_id}")
async def agent_get_task(task_id: str):
    from app.core.agent.multi_agent import get_orchestrator
    return get_orchestrator().get_task(task_id) or {"error": "Task not found"}


@router.get("/agent/tasks")
async def agent_list_tasks(status: str | None = None, limit: int = 50):
    from app.core.agent.multi_agent import TaskStatus, get_orchestrator
    orch = get_orchestrator()
    task_status = TaskStatus(status) if status else None
    return {"tasks": orch.list_tasks(status=task_status, limit=limit)}


@router.get("/agent/status")
async def agent_orchestrator_status():
    from app.core.agent.multi_agent import get_orchestrator
    return get_orchestrator().get_status()


@router.post("/agent/mode")
async def agent_set_mode(data: dict):
    from app.core.agent.multi_agent import get_orchestrator
    mode = data.get("mode", "auto")
    get_orchestrator().set_mode(mode)
    return {"execution_mode": mode}


@router.post("/agent/task/{task_id}/supplement")
async def agent_supplement_task(task_id: str, data: dict):
    from app.core.agent.multi_agent import get_orchestrator
    result = get_orchestrator().supplement_task(
        task_id=task_id,
        info=data.get("info", ""),
        source=data.get("source", "user"),
    )
    if result is None:
        return {"error": "Task not found"}
    return result


@router.get("/agent/vertical")
async def agent_list_vertical():
    from app.core.agent.multi_agent import get_orchestrator
    from app.core.agent.vertical_agents import register_built_in_agents
    orch = get_orchestrator()
    register_built_in_agents(orch)
    return {"agents": orch.list_vertical_agents()}


@router.post("/agent/vertical")
async def agent_create_vertical(data: dict):
    from app.core.agent.multi_agent import VerticalAgent, get_orchestrator
    agent = VerticalAgent(
        name=data.get("name", ""),
        domain=data.get("domain", ""),
        description=data.get("description", ""),
        system_prompt=data.get("system_prompt", ""),
        tools=data.get("tools", []),
    )
    agent._creator = "user"
    get_orchestrator().register_vertical_agent(agent)
    return {"name": agent.name, "domain": agent.domain}


@router.delete("/agent/vertical/{name}")
async def agent_delete_vertical(name: str):
    from app.core.agent.multi_agent import get_orchestrator
    success = get_orchestrator().unregister_vertical_agent(name)
    return {"success": success}


@router.get("/agent/supervisor/reports")
async def agent_supervisor_reports(limit: int = 50):
    from app.core.agent.multi_agent import get_orchestrator
    return {"reports": get_orchestrator().supervisor.get_reports(limit=limit)}


@router.get("/skills/animation/styles")
async def skills_animation_styles():
    from app.core.skills.animation import get_skill_engine
    return {"styles": get_skill_engine().list_styles()}


@router.post("/skills/animation/create")
async def skills_animation_create(data: dict):
    from app.core.skills.animation import get_skill_engine
    engine = get_skill_engine()
    project = engine.create_animation(
        svg_content=data.get("svg_content", ""),
        title=data.get("title", "Animation"),
        style=data.get("style", "standard"),
        width=data.get("width", 600),
        height=data.get("height", 600),
        bg_color=data.get("bg_color", "#f4f4f5"),
        duration=data.get("duration", 3.0),
    )
    html_path = engine.render_to_html(project.id)
    return {"project_id": project.id, "html_path": html_path}


@router.get("/skills/animation/projects")
async def skills_animation_projects():
    from app.core.skills.animation import get_skill_engine
    return {"projects": get_skill_engine().list_projects()}


@router.post("/skills/animation/export")
async def skills_animation_export(data: dict):
    return {"message": f"Animation export initiated: {data.get('frames', 0)} frames for '{data.get('title', '')}'"}


@router.get("/evolution/summary")
async def evolution_summary():
    from app.core.agent.evolution import get_evolution_engine
    return get_evolution_engine().get_evolution_summary()


@router.get("/evolution/learned")
async def evolution_learned(limit: int = 20):
    from app.core.agent.evolution import get_evolution_engine
    return {"behaviors": get_evolution_engine().get_learned_behaviors(limit=limit)}


@router.post("/evolution/feedback")
async def evolution_feedback(data: dict):
    from app.core.agent.evolution import get_evolution_engine
    engine = get_evolution_engine()
    entry = await engine.learn_from_feedback(
        task_desc=data.get("task", ""),
        result=data.get("result"),
        feedback=data.get("feedback", ""),
        score=data.get("score", 0.5),
    )
    return {"id": entry.id, "new_behavior": entry.new_behavior, "confidence": entry.confidence}


@router.post("/evolution/evolve-prompt")
async def evolution_evolve_prompt(data: dict):
    from app.core.agent.evolution import get_evolution_engine
    engine = get_evolution_engine()
    evolution = await engine.evolve_prompt(
        current_prompt=data.get("current_prompt", ""),
        performance_metrics=data.get("metrics", {}),
    )
    return {"id": evolution.id, "evolved_prompt": evolution.evolved_prompt[:500], "rationale": evolution.rationale}


@router.get("/prompts")
async def get_system_prompts():
    from app.core.agent.prompts import POLYSPACE_PLANNER_PROMPT, POLYSPACE_SUPERVISOR_PROMPT, POLYSPACE_SYSTEM_PROMPT
    return {
        "system": POLYSPACE_SYSTEM_PROMPT[:500] + "...",
        "planner": POLYSPACE_PLANNER_PROMPT[:300] + "...",
        "supervisor": POLYSPACE_SUPERVISOR_PROMPT[:300] + "...",
    }


class CalendarEventRequest(BaseModel):
    title: str = ""
    description: str = ""
    location: str = ""
    start_time: str = ""
    end_time: str = ""
    timezone: str = "UTC"
    source: str = ""
    system_event_id: str = ""
    category: str = ""


class CalendarEventUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    category: str | None = None


@router.get("/calendar/events")
async def list_calendar_events(start_date: str | None = None, end_date: str | None = None):
    from app.services.calendar_service import get_calendar_service
    svc = get_calendar_service()
    events = await svc.list_events(start_date=start_date, end_date=end_date)
    return {"events": [e.__dict__ if hasattr(e, "__dict__") else e for e in events]}


@router.post("/calendar/events")
async def create_calendar_event_from_sync(req: CalendarEventRequest):
    from app.services.calendar_service import get_calendar_service
    svc = get_calendar_service()
    event = await svc.create_event(
        title=req.title,
        description=req.description,
        start_time=req.start_time,
        end_time=req.end_time,
        location=req.location,
    )
    return {"status": "ok", "event": event.__dict__ if hasattr(event, "__dict__") else str(event)}


@router.patch("/calendar/events/{event_id}")
async def update_calendar_event(event_id: str, req: CalendarEventUpdateRequest):
    from app.services.calendar_service import get_calendar_service
    svc = get_calendar_service()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        return {"status": "ok", "message": "No updates provided"}
    event = await svc.update_event(event_id, **updates)
    if not event:
        return {"status": "error", "message": "Event not found"}
    return {"status": "ok", "event": event.__dict__ if hasattr(event, "__dict__") else str(event)}


@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str):
    from app.services.calendar_service import get_calendar_service
    svc = get_calendar_service()
    deleted = await svc.delete_event(event_id)
    if not deleted:
        return {"status": "error", "message": "Event not found"}
    return {"status": "ok"}


@router.post("/calendar/sync/from-system")
async def sync_from_system_calendar(events: list[dict]):
    from app.services.calendar_service import get_calendar_service
    svc = get_calendar_service()
    synced = 0
    for ev in events:
        try:
            await svc.create_event(
                title=ev.get("title", ""),
                description=ev.get("description", ""),
                start_time=ev.get("start_time", ""),
                end_time=ev.get("end_time", ""),
                location=ev.get("location", ""),
            )
            synced += 1
        except Exception:
            pass
    return {"status": "ok", "synced": synced}


class IncomingMessageRequest(BaseModel):
    source: str = ""
    source_name: str = ""
    title: str = ""
    text: str = ""
    sub_text: str = ""
    category: str = ""
    timestamp: int = 0
    is_group: bool = False


class MessageSuggestRequest(BaseModel):
    source: str = ""
    source_name: str = ""
    title: str = ""
    text: str = ""
    sub_text: str = ""
    category: str = ""
    timestamp: int = 0
    is_group: bool = False


@router.post("/messages/incoming")
async def receive_incoming_message(req: IncomingMessageRequest):
    from app.core.memory.manager import get_memory_manager
    mem = get_memory_manager()
    await mem.record_fact(
        f"[{req.source_name}] {req.title}: {req.text[:200]}",
        metadata={"type": "incoming_message", "source": req.source, "source_name": req.source_name, "is_group": req.is_group}
    )
    return {"status": "received", "source": req.source_name}


@router.post("/messages/suggest")
async def suggest_message_response(req: MessageSuggestRequest):
    from app.core.llm.dispatcher import get_model_dispatcher
    dispatcher = get_model_dispatcher()

    prompt = f"""你是一个智能助手，收到了一条来自{req.source_name}的消息。请分析这条消息并给出建议。

消息来源: {req.source_name}
发送者: {req.title}
消息内容: {req.text}
是否群消息: {"是" if req.is_group else "否"}

请以JSON格式返回建议:
{{
    "suggested_replies": ["回复1", "回复2", "回复3"],
    "suggested_actions": [
        {{"action": "动作描述", "reason": "原因"}},
        {{"action": "动作描述", "reason": "原因"}}
    ],
    "priority": "high/medium/low",
    "summary": "消息摘要"
}}"""

    try:
        response = await dispatcher.dispatch(
            prompt=prompt,
            category="daily"
        )
        import json
        content = response.choices[0].message.content if hasattr(response, "choices") else str(response)
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(content[json_start:json_end])
        return {"suggested_replies": [], "suggested_actions": [], "priority": "medium", "summary": content[:200]}
    except Exception as e:
        return {"suggested_replies": [], "suggested_actions": [], "priority": "medium", "summary": str(e)[:200]}


class ContextIngestRequest(BaseModel):
    source: str
    data: dict
    priority: str = "normal"


class ScreenDataRequest(BaseModel):
    screen_data: dict


class NotificationDataRequest(BaseModel):
    notification_data: dict


class ProactiveToggleRequest(BaseModel):
    service_name: str
    enabled: bool


class ProactiveTriggerRequest(BaseModel):
    service_name: str


class ProactiveFeedbackRequest(BaseModel):
    service_id: str
    feedback: str


class ConversationStartRequest(BaseModel):
    topic: str
    reason: str = ""


class ConversationContinueRequest(BaseModel):
    conv_id: str
    user_response: str


class WorkflowCreateRequest(BaseModel):
    template_name: str
    params: dict = {}


class WorkflowExecuteRequest(BaseModel):
    workflow_id: str


class PrivacyPreferenceRequest(BaseModel):
    key: str
    value: Any = None


class ConsentRequest(BaseModel):
    service_name: str
    data_types: list[str] = []
    channels: list[str] = []


class ConsentRevokeRequest(BaseModel):
    service_name: str


class ProactiveConfigRequest(BaseModel):
    enabled: bool | None = None
    scheduler: dict | None = None
    delivery: dict | None = None


class AutomationRuleToggleRequest(BaseModel):
    rule_name: str
    enabled: bool


@router.get("/proactive/config")
async def proactive_config_get():
    coord = _get_coord()
    return await coord.get_proactive_config()


@router.post("/proactive/config")
async def proactive_config_set(req: ProactiveConfigRequest):
    coord = _get_coord()
    await coord.set_proactive_config(
        enabled=req.enabled,
        scheduler=req.scheduler,
        delivery=req.delivery,
    )
    return {"status": "updated"}


@router.post("/automation/rules/toggle")
async def automation_rules_toggle(req: AutomationRuleToggleRequest):
    coord = _get_coord()
    success = await coord.toggle_automation_rule(req.rule_name, req.enabled)
    return {"success": success}


@router.post("/context/ingest")
async def context_ingest(req: ContextIngestRequest):
    coord = _get_coord()
    await coord.ingest_context(req.source, req.data, req.priority)
    return {"status": "ingested"}


@router.get("/context")
async def context_get():
    coord = _get_coord()
    return await coord.get_full_context()


@router.get("/context/current")
async def context_current_for_agent():
    coord = _get_coord()
    return await coord.get_current_context_for_agent()


@router.get("/context/search")
async def context_search(query: str, limit: int = 5):
    coord = _get_coord()
    results = await coord.search_context(query, limit)
    return {"results": results}


@router.get("/context/summaries")
async def context_summaries(limit: int = 10):
    coord = _get_coord()
    return {"summaries": coord.get_recent_activity_summaries(limit)}


@router.get("/context/windows")
async def context_windows(limit: int = 10):
    coord = _get_coord()
    return {"windows": coord.get_activity_windows(limit)}


@router.get("/context/primary-activity")
async def context_primary_activity():
    coord = _get_coord()
    return coord.get_primary_activity()


@router.get("/memories/recent")
async def memories_recent(limit: int = 10):
    coord = _get_coord()
    return {"memories": coord.get_recent_memories(limit)}


@router.get("/memories/search")
async def memories_search(query: str, limit: int = 5):
    coord = _get_coord()
    results = coord.search_memories(query, limit)
    return {"results": results}


@router.get("/memories/latest")
async def memories_latest():
    coord = _get_coord()
    result = coord.get_latest_memory()
    return result or {"status": "no_memories"}


@router.post("/screen/process")
async def screen_process(req: ScreenDataRequest):
    coord = _get_coord()
    result = await coord.process_screen_data(req.screen_data)
    return result or {"status": "no_change"}


@router.post("/notification/process")
async def notification_process(req: NotificationDataRequest):
    coord = _get_coord()
    result = await coord.process_notification_data(req.notification_data)
    return result or {"status": "error"}


@router.get("/proactive/services")
async def proactive_services(category: str | None = None):
    coord = _get_coord()
    services = await coord.get_proactive_services()
    if category:
        services = [s for s in services if s.get("category") == category]
    return {"services": services}


@router.post("/proactive/services/toggle")
async def proactive_services_toggle(req: ProactiveToggleRequest):
    coord = _get_coord()
    success = await coord.toggle_proactive_service(req.service_name, req.enabled)
    return {"success": success}


@router.post("/proactive/trigger")
async def proactive_trigger(req: ProactiveTriggerRequest):
    coord = _get_coord()
    result = await coord.trigger_proactive_service(req.service_name)
    return result or {"status": "no_result"}


@router.get("/proactive/history")
async def proactive_history(limit: int = 50):
    coord = _get_coord()
    return {"history": await coord.get_proactive_history(limit)}


@router.post("/proactive/feedback")
async def proactive_feedback(req: ProactiveFeedbackRequest):
    coord = _get_coord()
    success = await coord.record_proactive_feedback(req.service_id, req.feedback)
    return {"success": success}


@router.get("/proactive/stats")
async def proactive_stats():
    coord = _get_coord()
    return await coord.get_proactive_stats()


@router.get("/scene")
async def scene_detect():
    coord = _get_coord()
    result = await coord.detect_scene()
    return result or {"scene": "unknown"}


@router.post("/conversation/start")
async def conversation_start(req: ConversationStartRequest):
    coord = _get_coord()
    result = await coord.start_conversation(req.topic, req.reason)
    return result or {"status": "error"}


@router.post("/conversation/continue")
async def conversation_continue(req: ConversationContinueRequest):
    coord = _get_coord()
    result = await coord.continue_conversation(req.conv_id, req.user_response)
    return result or {"status": "not_found"}


@router.get("/workflow/templates")
async def workflow_templates():
    from app.core.coordination.workflow.workflow_engine import get_workflow_engine
    return {"templates": get_workflow_engine().list_templates()}


@router.post("/workflow/create")
async def workflow_create(req: WorkflowCreateRequest):
    coord = _get_coord()
    result = await coord.create_workflow(req.template_name, req.params)
    return result or {"status": "template_not_found"}


@router.post("/workflow/execute")
async def workflow_execute(req: WorkflowExecuteRequest):
    coord = _get_coord()
    result = await coord.execute_workflow(req.workflow_id)
    return result or {"status": "workflow_not_found"}


@router.get("/automation/rules")
async def automation_rules(enabled_only: bool = False):
    from app.core.coordination.automation.environment_rules import get_environment_rules_engine
    return {"rules": get_environment_rules_engine().list_rules(enabled_only)}


@router.post("/automation/evaluate")
async def automation_evaluate():
    coord = _get_coord()
    results = await coord.evaluate_automation()
    return {"triggered": results}


@router.get("/habits/patterns")
async def habits_patterns(pattern_type: str | None = None):
    coord = _get_coord()
    return {"patterns": await coord.get_habit_patterns(pattern_type)}


@router.get("/prediction")
async def prediction():
    coord = _get_coord()
    result = await coord.get_prediction()
    return result or {"prediction": "none"}


@router.get("/privacy/status")
async def privacy_status():
    coord = _get_coord()
    return await coord.get_privacy_status()


@router.post("/privacy/preference")
async def privacy_set_preference(req: PrivacyPreferenceRequest):
    coord = _get_coord()
    await coord.set_privacy_preference(req.key, req.value)
    return {"status": "updated"}


@router.post("/privacy/consent/grant")
async def privacy_consent_grant(req: ConsentRequest):
    coord = _get_coord()
    result = await coord.grant_consent(req.service_name, req.data_types, req.channels)
    return result


@router.post("/privacy/consent/revoke")
async def privacy_consent_revoke(req: ConsentRevokeRequest):
    coord = _get_coord()
    success = await coord.revoke_consent(req.service_name)
    return {"success": success}
