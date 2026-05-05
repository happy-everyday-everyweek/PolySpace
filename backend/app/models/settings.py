from typing import Optional

from pydantic import BaseModel


class DistributedConfig(BaseModel):
    enabled: bool = True
    auto_sync: bool = True
    auto_sync_interval_sec: int = 300
    sync_on_startup: bool = True
    sync_on_handoff: bool = True
    conflict_strategy: str = "latest"
    github_token: Optional[str] = None
    sync_scopes: list[str] = ["settings", "persona", "mode", "workspace", "memory"]
    local_first: bool = True
    encrypt_transit: bool = True


class SettingsModel(BaseModel):
    language: str = "zh-CN"
    theme: str = "auto"
    agent_execution_mode: str = "auto"
    default_mode: str = "agent"
    distributed: DistributedConfig = DistributedConfig()


class PersonaSettingsModel(BaseModel):
    name: Optional[str] = None
    big_five: Optional[dict] = None
    communication: Optional[dict] = None
    values: Optional[dict] = None
    catchphrases: Optional[list[str]] = None
    custom_instructions: Optional[str] = None
