from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CapabilitySource(str, Enum):
    INTERNAL = "internal"
    MCP = "mcp"
    SKILL = "skill"
    CLI = "cli"
    DEVICE = "device"


class CapabilityCategory(str, Enum):
    SYSTEM = "system"
    FILE = "file"
    COMMUNICATION = "communication"
    NETWORK = "network"
    MEDIA = "media"
    HARDWARE = "hardware"
    ACCESSIBILITY = "accessibility"
    AUTOMATION = "automation"
    BROWSER = "browser"
    STORAGE = "storage"
    PROCESS = "process"
    CLIPBOARD = "clipboard"
    WINDOW = "window"
    NOTIFICATION = "notification"
    SEARCH = "search"
    SCHEDULER = "scheduler"
    DOCUMENT = "document"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    COORDINATION = "coordination"
    PRODUCTIVITY = "productivity"
    CREATIVE = "creative"
    LIFESTYLE = "lifestyle"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    CONTENT = "content"
    ANALYTICS = "analytics"
    FINANCE = "finance"
    SECURITY = "security"
    DATABASE = "database"
    DEVELOPMENT = "development"


class CapabilityPlatform(str, Enum):
    ANDROID = "android"
    DESKTOP = "desktop"
    WEB = "web"
    LINUX = "linux"
    MACOS = "macos"
    BACKEND = "backend"


class CapabilityState(str, Enum):
    INACTIVE = "inactive"
    ACTIVATING = "activating"
    ACTIVE = "active"
    CALLING = "calling"
    HIBERNATING = "hibernating"
    ERROR = "error"


@dataclass
class CapabilityMeta:
    name: str
    display_name: str
    description: str
    source_type: CapabilitySource
    category: CapabilityCategory
    platforms: list[CapabilityPlatform] = field(default_factory=lambda: [CapabilityPlatform.BACKEND])
    actions: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    provider_name: str = ""
    availability_check: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "source_type": self.source_type.value,
            "category": self.category.value,
            "platforms": [p.value for p in self.platforms],
            "actions": self.actions,
            "parameters": self.parameters,
            "required_permissions": self.required_permissions,
            "version": self.version,
            "provider_name": self.provider_name,
        }

    def is_available_on(self, platform: CapabilityPlatform) -> bool:
        return platform in self.platforms

    def to_openai_function(self) -> dict:
        properties: dict[str, Any] = {
            "action": {
                "type": "string",
                "enum": self.actions if self.actions else ["execute"],
                "description": f"Action to perform on {self.name}",
            },
        }
        for param_name, param_schema in self.parameters.items():
            if param_name != "action":
                properties[param_name] = param_schema
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": ["action"],
                },
            },
        }


@dataclass
class CapabilityResult:
    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    audit_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.duration_ms > 0:
            result["duration_ms"] = self.duration_ms
        if self.audit_id:
            result["audit_id"] = self.audit_id
        return result


@dataclass
class CapabilityCallContext:
    caller_id: str = ""
    session_id: str = ""
    thread_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    timeout_seconds: float = 60.0
    retry_count: int = 0
    retry_delay_seconds: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class CapabilityProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def source_type(self) -> CapabilitySource:
        ...

    @abstractmethod
    async def discover(self) -> list[CapabilityMeta]:
        ...

    @abstractmethod
    async def activate(self, capability_name: str) -> None:
        ...

    @abstractmethod
    async def execute(
        self,
        capability_name: str,
        params: dict[str, Any],
        context: CapabilityCallContext,
    ) -> CapabilityResult:
        ...

    @abstractmethod
    async def deactivate(self, capability_name: str) -> None:
        ...

    @abstractmethod
    async def health_check(self, capability_name: str) -> bool:
        ...

    def get_capability(self, name: str) -> Optional[CapabilityMeta]:
        return None
