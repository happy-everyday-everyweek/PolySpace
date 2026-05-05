from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from app.core.connector.device_manager import ConnectedDevice, DeviceManager, DevicePlatform


class ConnectorType(str, Enum):
    ANDROID = "android"
    WINDOWS = "windows"
    WEB = "web"


class BaseConnector(ABC):
    def __init__(self, device_manager: DeviceManager):
        self._device_manager = device_manager
        self._active = False

    @abstractmethod
    async def activate(self) -> None:
        ...

    @abstractmethod
    async def execute(self, action: str, params: dict, device_id: Optional[str] = None) -> dict:
        ...

    @abstractmethod
    async def hibernate(self) -> None:
        ...

    @abstractmethod
    def connector_type(self) -> ConnectorType:
        ...

    def _get_platform(self) -> DevicePlatform:
        mapping = {
            ConnectorType.ANDROID: DevicePlatform.ANDROID,
            ConnectorType.WINDOWS: DevicePlatform.WINDOWS,
            ConnectorType.WEB: DevicePlatform.WEB,
        }
        return mapping[self.connector_type()]

    def find_device(self, device_id: Optional[str] = None) -> Optional[ConnectedDevice]:
        if device_id:
            device = self._device_manager.get_device(device_id)
            if device and device.platform == self._get_platform():
                return device
            return None
        devices = self._device_manager.list_devices(platform=self._get_platform().value)
        online = [d for d in devices if d.status.value != "offline"]
        return online[0] if online else None

    async def execute_on_device(
        self,
        tool_name: str,
        action: str,
        params: dict[str, Any],
        device_id: Optional[str] = None,
        timeout: float = 60.0,
    ) -> dict:
        device = self.find_device(device_id)
        if not device:
            return {"status": "error", "message": f"No online {self.connector_type().value} device available"}
        return await self._device_manager.execute_on_device(
            device_id=device.device_id,
            tool_name=tool_name,
            action=action,
            params=params,
            timeout=timeout,
        )
