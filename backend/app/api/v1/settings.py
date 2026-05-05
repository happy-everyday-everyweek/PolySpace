import json
import os
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.config import settings
from app.db.database import async_session
from app.models.settings import DistributedConfig, PersonaSettingsModel
from app.models.tables import SettingsRecord

router = APIRouter()

_SETTINGS_DEFAULTS = {
    "general": json.dumps({"language": "zh-CN", "theme": "auto"}),
    "agent": json.dumps({"agent_execution_mode": "auto"}),
    "app": json.dumps({
        "default_mode": "agent",
        "weather": {
            "city_id": None, "city_name": None, "country": None,
        },
        "email": {
            "auto_reply": True, "task_extraction": True,
            "notification": True, "monitoring": False,
        },
        "screen_recorder": {
            "source_type": "screen", "quality": "medium",
            "template": "", "change_detection": False,
            "include_audio": True, "include_cursor": True,
        },
        "ppt": {"theme": "light"},
        "pdf": {
            "watermark_text": "", "watermark_font_size": 36,
            "watermark_opacity": 0.3, "watermark_angle": -30,
            "watermark_position": "tile",
        },
        "video": {
            "export_format": "mp4", "export_quality": "medium",
            "export_resolution": "original", "include_subtitles": False,
        },
        "image": {
            "brightness": 100, "contrast": 100, "saturate": 100,
            "blur": 0, "grayscale": 0, "sepia": 0,
        },
        "document": {
            "font_family": "Default", "font_size": "Default", "heading": "p",
        },
        "focus_timer": {
            "mode": "pomodoro", "work_duration": 25,
            "break_duration": 5, "long_break_duration": 15,
            "sessions_before_long_break": 4,
        },
    }),
    "capability_providers": json.dumps({
        "internal_enabled": True,
        "mcp_enabled": True,
        "skill_enabled": True,
        "cli_enabled": True,
        "device_bridge_enabled": True,
    }),
    "memory": json.dumps({
        "dream_enabled": True,
        "auto_record_chat": True,
        "search_depth": "medium",
        "short_term_limit": 100,
        "long_term_retention_days": 90,
    }),
}


class GeneralSettingsUpdate(BaseModel):
    language: Optional[str] = None
    theme: Optional[str] = None


class AgentSettingsUpdate(BaseModel):
    agent_execution_mode: Optional[str] = None


class AppSettingsUpdate(BaseModel):
    default_mode: Optional[str] = None
    weather: Optional[dict] = None
    email: Optional[dict] = None
    screen_recorder: Optional[dict] = None
    ppt: Optional[dict] = None
    pdf: Optional[dict] = None
    video: Optional[dict] = None
    image: Optional[dict] = None
    document: Optional[dict] = None
    focus_timer: Optional[dict] = None


class ModelConfigUpdate(BaseModel):
    base_model: Optional[str] = None
    base_provider: Optional[str] = None
    base_api_key: Optional[str] = None
    base_api_base: Optional[str] = None
    strong_model: Optional[str] = None
    strong_provider: Optional[str] = None
    strong_api_key: Optional[str] = None
    strong_api_base: Optional[str] = None
    performance_model: Optional[str] = None
    performance_provider: Optional[str] = None
    performance_api_key: Optional[str] = None
    performance_api_base: Optional[str] = None
    cost_effective_model: Optional[str] = None
    cost_effective_provider: Optional[str] = None
    cost_effective_api_key: Optional[str] = None
    cost_effective_api_base: Optional[str] = None
    multimodal_model: Optional[str] = None
    multimodal_provider: Optional[str] = None
    multimodal_api_key: Optional[str] = None
    multimodal_api_base: Optional[str] = None
    multimodal_capabilities: Optional[list[str]] = None
    screen_model: Optional[str] = None
    screen_provider: Optional[str] = None
    screen_api_key: Optional[str] = None
    screen_api_base: Optional[str] = None


class CapabilityProviderSettingsUpdate(BaseModel):
    internal_enabled: Optional[bool] = None
    mcp_enabled: Optional[bool] = None
    skill_enabled: Optional[bool] = None
    cli_enabled: Optional[bool] = None
    device_bridge_enabled: Optional[bool] = None


class DistributedSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    auto_sync: Optional[bool] = None
    auto_sync_interval_sec: Optional[int] = None
    sync_on_startup: Optional[bool] = None
    sync_on_handoff: Optional[bool] = None
    conflict_strategy: Optional[str] = None
    github_token: Optional[str] = None
    sync_scopes: Optional[list[str]] = None
    local_first: Optional[bool] = None
    encrypt_transit: Optional[bool] = None


_distributed_config = DistributedConfig()


async def _get_setting(category: str) -> dict:
    async with async_session() as session:
        result = await session.scalar(
            select(SettingsRecord.value).where(SettingsRecord.key == category)
        )
        if result:
            return json.loads(result)
    default = _SETTINGS_DEFAULTS.get(category)
    return json.loads(default) if default else {}


async def _save_setting(category: str, data: dict) -> None:
    async with async_session() as session:
        result = await session.scalar(
            select(SettingsRecord).where(SettingsRecord.key == category)
        )
        value_str = json.dumps(data, ensure_ascii=False)
        if result:
            result.value = value_str
        else:
            session.add(SettingsRecord(key=category, value=value_str))
        await session.commit()


def _get_distributed_config() -> DistributedConfig:
    return _distributed_config


def _apply_distributed_update(update: DistributedSettingsUpdate) -> DistributedConfig:
    global _distributed_config
    data = update.model_dump(exclude_none=True)
    for key, value in data.items():
        if hasattr(_distributed_config, key):
            setattr(_distributed_config, key, value)

    from app.services.sync_service import sync_service
    if "conflict_strategy" in data:
        sync_service.set_conflict_strategy(data["conflict_strategy"])
    if "auto_sync" in data or "auto_sync_interval_sec" in data:
        import asyncio
        if _distributed_config.auto_sync:
            try:
                asyncio.ensure_future(sync_service.start_auto_sync(_distributed_config.auto_sync_interval_sec))
            except Exception:
                pass
        else:
            try:
                asyncio.ensure_future(sync_service.stop_auto_sync())
            except Exception:
                pass

    return _distributed_config


@router.get("/")
async def get_settings():
    config = _get_distributed_config()
    general = await _get_setting("general")
    agent = await _get_setting("agent")
    app = await _get_setting("app")
    return {
        "general": general,
        "agent": agent,
        "app": app,
        "distributed": {
            "enabled": config.enabled,
            "auto_sync": config.auto_sync,
            "auto_sync_interval_sec": config.auto_sync_interval_sec,
            "sync_on_startup": config.sync_on_startup,
            "sync_on_handoff": config.sync_on_handoff,
            "conflict_strategy": config.conflict_strategy,
            "github_token": "***" if config.github_token else None,
            "sync_scopes": config.sync_scopes,
            "local_first": config.local_first,
            "encrypt_transit": config.encrypt_transit,
        },
    }


@router.put("/general")
async def update_general_settings(update: GeneralSettingsUpdate):
    current = await _get_setting("general")
    updates = update.model_dump(exclude_none=True)
    current.update(updates)
    await _save_setting("general", current)
    return {"status": "ok", "category": "general"}


@router.put("/agent")
async def update_agent_settings(update: AgentSettingsUpdate):
    current = await _get_setting("agent")
    updates = update.model_dump(exclude_none=True)
    current.update(updates)
    await _save_setting("agent", current)
    return {"status": "ok", "category": "agent"}


@router.put("/app")
async def update_app_settings(update: AppSettingsUpdate):
    current = await _get_setting("app")
    updates = update.model_dump(exclude_none=True)
    current.update(updates)
    await _save_setting("app", current)
    return {"status": "ok", "category": "app"}


@router.get("/models")
async def get_model_settings():
    from app.core.llm.config_store import get_model_config_store
    store = get_model_config_store()
    result = store.get_flat_config()
    for tier in ["base", "strong", "performance", "cost_effective", "multimodal", "screen"]:
        model_key = f"{tier}_model"
        if model_key not in result or not result[model_key]:
            env_fallback = {
                "base": settings.LLM_BASE_MODEL,
                "strong": settings.LLM_STRONG_MODEL,
                "performance": settings.LLM_PERFORMANCE_MODEL,
                "cost_effective": settings.LLM_COST_EFFECTIVE_MODEL,
                "multimodal": settings.LLM_MULTIMODAL_MODEL,
                "screen": settings.LLM_SCREEN_MODEL,
            }
            result[model_key] = env_fallback.get(tier, "") or ""
    for tier in ["base", "strong", "performance", "cost_effective", "multimodal", "screen"]:
        for suffix in ["provider", "api_key", "api_base"]:
            key = f"{tier}_{suffix}"
            if key not in result:
                result[key] = ""
    if result.get("base_api_key"):
        result["base_api_key"] = "***"
    if result.get("strong_api_key"):
        result["strong_api_key"] = "***"
    if result.get("performance_api_key"):
        result["performance_api_key"] = "***"
    if result.get("cost_effective_api_key"):
        result["cost_effective_api_key"] = "***"
    if result.get("multimodal_api_key"):
        result["multimodal_api_key"] = "***"
    if result.get("screen_api_key"):
        result["screen_api_key"] = "***"
    if "multimodal_capabilities" not in result:
        result["multimodal_capabilities"] = []
    return result


@router.put("/models")
async def update_model_settings(update: ModelConfigUpdate):
    from app.core.llm.config_store import get_model_config_store
    from app.dependencies import container
    updates = update.model_dump(exclude_none=True)
    store = get_model_config_store()
    store.update_flat_config(updates)

    model_settings_map = {
        "base_model": "LLM_BASE_MODEL",
        "strong_model": "LLM_STRONG_MODEL",
        "performance_model": "LLM_PERFORMANCE_MODEL",
        "cost_effective_model": "LLM_COST_EFFECTIVE_MODEL",
        "multimodal_model": "LLM_MULTIMODAL_MODEL",
        "screen_model": "LLM_SCREEN_MODEL",
    }
    for config_key, settings_key in model_settings_map.items():
        if config_key in updates and updates[config_key]:
            os.environ[f"POLYSPACE_{settings_key}"] = updates[config_key]
            setattr(settings, settings_key, updates[config_key])

    new_config = store.get_dispatcher_config()
    from app.core.llm.dispatcher import ModelDispatcher
    new_dispatcher = ModelDispatcher(config=new_config)
    container.register("model_dispatcher", new_dispatcher)
    chat_service = container.get("chat_service")
    if chat_service and hasattr(chat_service, "update_dispatcher"):
        chat_service.update_dispatcher(new_dispatcher)
    return {"status": "ok", "category": "models", "updates": list(updates.keys())}


@router.put("/distributed")
async def update_distributed_settings(update: DistributedSettingsUpdate):
    config = _apply_distributed_update(update)
    return {
        "status": "ok",
        "category": "distributed",
        "distributed": {
            "enabled": config.enabled,
            "auto_sync": config.auto_sync,
            "auto_sync_interval_sec": config.auto_sync_interval_sec,
            "sync_on_startup": config.sync_on_startup,
            "sync_on_handoff": config.sync_on_handoff,
            "conflict_strategy": config.conflict_strategy,
            "sync_scopes": config.sync_scopes,
            "local_first": config.local_first,
            "encrypt_transit": config.encrypt_transit,
        },
    }


@router.get("/persona")
async def get_persona_settings():
    from app.core.personality.persona_core import get_persona_core
    persona = get_persona_core()
    config = persona.config
    return {
        "name": config.name,
        "big_five": {
            "openness": config.big_five.openness,
            "conscientiousness": config.big_five.conscientiousness,
            "extraversion": config.big_five.extraversion,
            "agreeableness": config.big_five.agreeableness,
            "neuroticism": config.big_five.neuroticism,
        },
        "communication": {
            "formality": config.communication.formality,
            "warmth": config.communication.warmth,
            "humor": config.communication.humor,
            "conciseness": config.communication.conciseness,
        },
        "values": {
            "growth": config.values.growth,
            "harmony": config.values.harmony,
            "truth": config.values.truth,
            "empathy": config.values.empathy,
        },
        "relationship": config.relationship.value,
        "catchphrases": config.catchphrases,
        "custom_instructions": config.custom_instructions,
    }


@router.put("/persona")
async def update_persona_settings(update: PersonaSettingsModel):
    from app.core.personality.persona_core import get_persona_core
    persona = get_persona_core()
    updates = update.model_dump(exclude_none=True)
    persona.update_config(updates)
    return {"status": "ok", "category": "persona", "updates": list(updates.keys())}


@router.get("/capabilities")
async def get_capability_settings():
    from app.core.capability.registry import capability_registry
    provider_settings = await _get_setting("capability_providers")
    source_summary = capability_registry.get_summary_by_source()
    category_summary = capability_registry.get_summary_by_category()
    return {
        "providers": {
            "internal_enabled": provider_settings.get("internal_enabled", True),
            "mcp_enabled": provider_settings.get("mcp_enabled", True),
            "skill_enabled": provider_settings.get("skill_enabled", True),
            "cli_enabled": provider_settings.get("cli_enabled", True),
            "device_bridge_enabled": provider_settings.get("device_bridge_enabled", True),
        },
        "summary": {
            "by_source": source_summary,
            "by_category": category_summary,
            "total": sum(source_summary.values()),
        },
    }


@router.put("/capabilities")
async def update_capability_settings(update: CapabilityProviderSettingsUpdate):
    current = await _get_setting("capability_providers")
    updates = update.model_dump(exclude_none=True)
    current.update(updates)
    await _save_setting("capability_providers", current)
    return {"status": "ok", "category": "capability_providers", "updates": list(updates.keys())}


@router.get("/env")
async def get_env_variables():
    from app.core.config.env_store import get_env_store
    store = get_env_store()
    return {
        "variables": store.get_by_group(),
        "definitions": store.get_definitions(),
    }


class EnvVariableUpdate(BaseModel):
    updates: dict[str, Any]


@router.put("/env")
async def update_env_variables(body: EnvVariableUpdate):
    from app.core.config.env_store import get_env_store
    store = get_env_store()
    changed = store.update(body.updates)
    for key in changed:
        if hasattr(settings, key):
            value = store._get_effective_value(key)
            if value is not None:
                setattr(settings, key, value)
    return {"status": "ok", "category": "env", "changed": changed}


class MemorySettingsUpdate(BaseModel):
    dream_enabled: Optional[bool] = None
    auto_record_chat: Optional[bool] = None
    search_depth: Optional[str] = None
    short_term_limit: Optional[int] = None
    long_term_retention_days: Optional[int] = None


@router.get("/memory")
async def get_memory_settings():
    return await _get_setting("memory")


@router.put("/memory")
async def update_memory_settings(update: MemorySettingsUpdate):
    current = await _get_setting("memory")
    updates = update.model_dump(exclude_none=True)
    current.update(updates)
    await _save_setting("memory", current)
    return {"status": "ok", "category": "memory", "updates": list(updates.keys())}
