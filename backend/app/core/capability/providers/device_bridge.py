from __future__ import annotations

import logging
import time
from typing import Any, Optional

from app.core.capability.base import (
    CapabilityCallContext,
    CapabilityCategory,
    CapabilityMeta,
    CapabilityPlatform,
    CapabilityProvider,
    CapabilityResult,
    CapabilitySource,
)

logger = logging.getLogger(__name__)

_PLATFORM_MAP: dict[str, CapabilityPlatform] = {
    "android": CapabilityPlatform.ANDROID,
    "windows": CapabilityPlatform.DESKTOP,
    "web": CapabilityPlatform.WEB,
    "linux": CapabilityPlatform.LINUX,
    "macos": CapabilityPlatform.MACOS,
}

_CATEGORY_MAP: list[tuple[str, CapabilityCategory]] = [
    ("screen", CapabilityCategory.ACCESSIBILITY),
    ("file", CapabilityCategory.FILE),
    ("window", CapabilityCategory.WINDOW),
    ("clipboard", CapabilityCategory.CLIPBOARD),
    ("process", CapabilityCategory.PROCESS),
    ("audio", CapabilityCategory.MEDIA),
    ("communication", CapabilityCategory.COMMUNICATION),
    ("network", CapabilityCategory.NETWORK),
    ("hardware", CapabilityCategory.HARDWARE),
    ("location", CapabilityCategory.HARDWARE),
    ("battery", CapabilityCategory.HARDWARE),
    ("sensor", CapabilityCategory.HARDWARE),
    ("camera", CapabilityCategory.HARDWARE),
    ("notification", CapabilityCategory.NOTIFICATION),
    ("storage", CapabilityCategory.STORAGE),
    ("contact", CapabilityCategory.COMMUNICATION),
    ("sms", CapabilityCategory.COMMUNICATION),
    ("phone", CapabilityCategory.COMMUNICATION),
    ("app", CapabilityCategory.SYSTEM),
    ("wifi", CapabilityCategory.NETWORK),
    ("flashlight", CapabilityCategory.HARDWARE),
    ("vibration", CapabilityCategory.HARDWARE),
    ("tts", CapabilityCategory.MEDIA),
]


def _map_category(cap_name: str) -> CapabilityCategory:
    lower = cap_name.lower()
    for prefix, category in _CATEGORY_MAP:
        if lower.startswith(prefix):
            return category
    return CapabilityCategory.SYSTEM


class DeviceBridgeProvider(CapabilityProvider):
    def __init__(self) -> None:
        self._route: dict[str, tuple[str, str]] = {}
        self._dm = None

    @property
    def name(self) -> str:
        return "device_bridge"

    @property
    def source_type(self) -> CapabilitySource:
        return CapabilitySource.DEVICE

    def _get_dm(self):
        if self._dm is None:
            from app.core.connector.device_manager import device_manager
            self._dm = device_manager
        return self._dm

    async def discover(self) -> list[CapabilityMeta]:
        self._route.clear()
        dm = self._get_dm()
        metas: list[CapabilityMeta] = []
        devices = dm.list_devices() if hasattr(dm, "list_devices") else []
        for device in devices:
            device_id = device.device_id
            device_name = device.device_name
            platform_str = device.platform.value if hasattr(device.platform, "value") else str(device.platform)
            cap_platform = _PLATFORM_MAP.get(platform_str, CapabilityPlatform.WEB)
            capabilities = device.capabilities if hasattr(device, "capabilities") else []
            for cap in capabilities:
                cap_name = cap.name if hasattr(cap, "name") else str(cap)
                full_name = f"device_{device_id[:8]}_{cap_name}"
                self._route[full_name] = (device_id, cap_name)
                has_desc = hasattr(cap, "description") and cap.description
                desc = cap.description if has_desc else f"{cap_name} on {device_name}"
                actions = cap.actions if hasattr(cap, "actions") else ["execute"]
                parameters = cap.parameters if hasattr(cap, "parameters") else {}
                meta = CapabilityMeta(
                    name=full_name,
                    display_name=cap_name,
                    description=desc,
                    source_type=CapabilitySource.DEVICE,
                    category=_map_category(cap_name),
                    platforms=[cap_platform],
                    actions=actions,
                    parameters=parameters,
                    provider_name=self.name,
                )
                metas.append(meta)
        return metas

    async def activate(self, capability_name: str) -> None:
        route = self._route.get(capability_name)
        if not route:
            raise KeyError(f"Capability '{capability_name}' not found in device bridge routes")
        device_id, _ = route
        dm = self._get_dm()
        device = dm.get_device(device_id) if hasattr(dm, "get_device") else None
        if not device:
            raise RuntimeError(f"Device {device_id} not found")

    async def execute(
        self,
        capability_name: str,
        params: dict[str, Any],
        context: CapabilityCallContext,
    ) -> CapabilityResult:
        route = self._route.get(capability_name)
        if not route:
            msg = f"Capability '{capability_name}' not found in device bridge routes"
            return CapabilityResult(success=False, error=msg)
        device_id, tool_name = route
        dm = self._get_dm()
        action = params.get("action", "execute")
        call_params = {k: v for k, v in params.items() if k != "action"}
        start = time.monotonic()
        try:
            result = await dm.execute_on_device(
                device_id=device_id,
                tool_name=tool_name,
                action=action,
                params=call_params,
                timeout=context.timeout_seconds,
            )
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            if isinstance(result, dict) and result.get("status") == "error":
                return CapabilityResult(
                    success=False,
                    error=result.get("message", "Unknown device error"),
                    duration_ms=duration_ms,
                    data=result,
                )
            return CapabilityResult(success=True, data=result, duration_ms=duration_ms)
        except Exception as e:
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            return CapabilityResult(success=False, error=str(e), duration_ms=duration_ms)

    async def deactivate(self, capability_name: str) -> None:
        pass

    async def health_check(self, capability_name: str) -> bool:
        route = self._route.get(capability_name)
        if not route:
            return False
        device_id, _ = route
        dm = self._get_dm()
        device = dm.get_device(device_id) if hasattr(dm, "get_device") else None
        if not device:
            return False
        status = device.status if hasattr(device, "status") else None
        return status is not None and str(status) != "offline"

    def get_capability(self, name: str) -> Optional[CapabilityMeta]:
        route = self._route.get(name)
        if not route:
            return None
        device_id, cap_name = route
        dm = self._get_dm()
        device = dm.get_device(device_id) if hasattr(dm, "get_device") else None
        if not device:
            return None
        platform_str = device.platform.value if hasattr(device.platform, "value") else str(device.platform)
        cap_platform = _PLATFORM_MAP.get(platform_str, CapabilityPlatform.WEB)
        capabilities = device.capabilities if hasattr(device, "capabilities") else []
        for cap in capabilities:
            c_name = cap.name if hasattr(cap, "name") else str(cap)
            if c_name == cap_name:
                full_name = f"device_{device_id[:8]}_{cap_name}"
                has_desc = hasattr(cap, "description") and cap.description
                desc = cap.description if has_desc else f"{cap_name} on {device.device_name}"
                actions = cap.actions if hasattr(cap, "actions") else ["execute"]
                parameters = cap.parameters if hasattr(cap, "parameters") else {}
                return CapabilityMeta(
                    name=full_name,
                    display_name=cap_name,
                    description=desc,
                    source_type=CapabilitySource.DEVICE,
                    category=_map_category(cap_name),
                    platforms=[cap_platform],
                    actions=actions,
                    parameters=parameters,
                    provider_name=self.name,
                )
        return None
