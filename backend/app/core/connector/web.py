from __future__ import annotations

from typing import Optional

from app.core.connector.base import BaseConnector, ConnectorType
from app.core.connector.device_manager import DeviceManager


class WebConnector(BaseConnector):
    def __init__(self, device_manager: DeviceManager):
        super().__init__(device_manager)

    async def activate(self) -> None:
        self._active = True

    async def execute(self, action: str, params: dict, device_id: Optional[str] = None) -> dict:
        if not self._active:
            raise RuntimeError("Web connector is not active")
        return await self.execute_on_device(
            tool_name="browser_automation",
            action=action,
            params=params,
            device_id=device_id,
        )

    async def hibernate(self) -> None:
        self._active = False

    def connector_type(self) -> ConnectorType:
        return ConnectorType.WEB
