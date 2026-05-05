from __future__ import annotations

from typing import Any, Optional

from app.core.connector.device_manager import ConnectedDevice, DeviceCapability, DeviceManager
from app.core.tool.base import BaseTool


class DeviceBridgeTool(BaseTool):
    def __init__(
        self,
        device_manager: DeviceManager,
        device_id: str,
        capability: DeviceCapability,
    ):
        self._device_manager = device_manager
        self._device_id = device_id
        self._capability = capability

        tool_name = f"device_{device_id[:8]}_{capability.name}"
        description = (
            f"[{capability.name}] on device {device_id[:8]} - {capability.description}"
        )

        parameters = self._build_parameters(capability)
        super().__init__(name=tool_name, description=description, parameters=parameters)

    @staticmethod
    def _build_parameters(capability: DeviceCapability) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "action": {
                "type": "string",
                "enum": capability.actions if capability.actions else ["execute"],
                "description": f"Action to perform on {capability.name}",
            },
        }
        if capability.parameters:
            for param_name, param_schema in capability.parameters.items():
                if param_name != "action":
                    properties[param_name] = param_schema
        else:
            properties["params"] = {
                "type": "object",
                "description": f"Parameters for the {capability.name} action",
                "properties": {},
            }

        return {
            "type": "object",
            "properties": properties,
            "required": ["action"],
        }

    async def _on_activate(self) -> None:
        device = self._device_manager.get_device(self._device_id)
        if not device or device.status.value == "offline":
            raise RuntimeError(f"Device {self._device_id} is not available")

    async def _on_call(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "execute")
        params = {k: v for k, v in kwargs.items() if k != "action"}

        result = await self._device_manager.execute_on_device(
            device_id=self._device_id,
            tool_name=self._capability.name,
            action=action,
            params=params,
        )
        return result

    async def _on_hibernate(self) -> None:
        pass

    def is_device_available(self) -> bool:
        device = self._device_manager.get_device(self._device_id)
        return device is not None and device.status.value != "offline"


class DeviceBridgeFactory:
    def __init__(self, device_manager: DeviceManager):
        self._device_manager = device_manager
        self._registered_tools: dict[str, str] = {}

    def create_tools_for_device(self, device: ConnectedDevice) -> list[DeviceBridgeTool]:
        tools = []
        for capability in device.capabilities:
            tool = DeviceBridgeTool(
                device_manager=self._device_manager,
                device_id=device.device_id,
                capability=capability,
            )
            tools.append(tool)
            self._registered_tools[tool.name] = device.device_id
        return tools

    def remove_tools_for_device(self, device_id: str) -> list[str]:
        removed = []
        to_remove = [
            name for name, did in self._registered_tools.items() if did == device_id
        ]
        for name in to_remove:
            del self._registered_tools[name]
            removed.append(name)
        return removed

    def get_device_id_for_tool(self, tool_name: str) -> Optional[str]:
        return self._registered_tools.get(tool_name)

    def get_all_tool_names(self) -> list[str]:
        return list(self._registered_tools.keys())

    def get_tools_for_device(self, device_id: str) -> list[str]:
        return [name for name, did in self._registered_tools.items() if did == device_id]
