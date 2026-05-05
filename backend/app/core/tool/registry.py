from __future__ import annotations

import json
import time
from typing import Any, Optional

from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service
from app.core.connector.bridge_tool import DeviceBridgeFactory, DeviceBridgeTool
from app.core.connector.device_manager import ConnectedDevice, DeviceManager, device_manager
from app.core.tool.base import BaseTool


class ToolRegistry:
    def __init__(self, device_manager: Optional[DeviceManager] = None):
        self._tools: dict[str, BaseTool] = {}
        self._device_manager = device_manager
        self._bridge_factory: Optional[DeviceBridgeFactory] = None
        if device_manager:
            self._bridge_factory = DeviceBridgeFactory(device_manager)

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")
        del self._tools[name]

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "state": tool.state.value,
                "definition": tool.get_definition(),
                "is_remote": isinstance(tool, DeviceBridgeTool),
            }
            for tool in self._tools.values()
        ]

    async def call_tool(self, name: str, **kwargs) -> Any:
        start_time = time.monotonic()
        tool = self._tools.get(name)
        is_remote = isinstance(tool, DeviceBridgeTool) if tool else False
        target_device_id = tool._device_id if is_remote else None

        try:
            if tool is None:
                routed_result = await self._try_device_route(name, **kwargs)
                if routed_result is not None:
                    await audit_service.record(
                        category=AuditCategory.TOOL_CALL,
                        action=f"tool_call:{name}",
                        level=AuditLevel.INFO,
                        actor_type="agent",
                        resource_type="tool",
                        resource_id=name,
                        target_device_id=target_device_id,
                        status="success",
                        duration_ms=round((time.monotonic() - start_time) * 1000, 2),
                        detail=f"Routed to device for tool {name}",
                    )
                    return routed_result
                raise KeyError(f"Tool '{name}' is not registered")

            result = await tool.call(**kwargs)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            await audit_service.record(
                category=AuditCategory.TOOL_CALL,
                action=f"tool_call:{name}",
                level=AuditLevel.INFO,
                actor_type="agent",
                resource_type="tool",
                resource_id=name,
                target_device_id=target_device_id,
                target_platform=tool._device_manager.get_device(target_device_id).platform.value if is_remote and target_device_id and tool._device_manager.get_device(target_device_id) else None,
                status="success",
                duration_ms=duration_ms,
                request_summary=json.dumps({"kwargs_keys": list(kwargs.keys())}, ensure_ascii=False)[:500],
            )
            return result
        except Exception as e:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            await audit_service.record(
                category=AuditCategory.TOOL_CALL,
                action=f"tool_call:{name}",
                level=AuditLevel.ERROR,
                actor_type="agent",
                resource_type="tool",
                resource_id=name,
                target_device_id=target_device_id,
                status="error",
                duration_ms=duration_ms,
                detail=str(e),
            )
            raise

    async def _try_device_route(self, tool_name: str, **kwargs) -> Optional[Any]:
        if not self._device_manager:
            return None

        action = kwargs.get("action", "execute")
        params = {k: v for k, v in kwargs.items() if k != "action"}

        device = self._device_manager.find_device_for_tool(tool_name, action)
        if not device:
            return None

        result = await self._device_manager.execute_on_device(
            device_id=device.device_id,
            tool_name=tool_name,
            action=action,
            params=params,
        )
        return result

    async def activate_tool(self, name: str) -> None:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' is not registered")
        await tool.activate()

    async def hibernate_tool(self, name: str) -> None:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' is not registered")
        await tool.hibernate()

    async def hibernate_all(self) -> None:
        for tool in self._tools.values():
            try:
                await tool.hibernate()
            except Exception:
                pass

    def get_definitions(self) -> list[dict]:
        return [tool.get_definition() for tool in self._tools.values()]

    def get_local_definitions(self) -> list[dict]:
        return [
            tool.get_definition()
            for tool in self._tools.values()
            if not isinstance(tool, DeviceBridgeTool)
        ]

    def get_remote_definitions(self) -> list[dict]:
        return [
            tool.get_definition()
            for tool in self._tools.values()
            if isinstance(tool, DeviceBridgeTool)
        ]

    async def register_device_tools(self, device: ConnectedDevice) -> list[str]:
        if not self._bridge_factory:
            return []
        tools = self._bridge_factory.create_tools_for_device(device)
        registered = []
        for tool in tools:
            try:
                self.register(tool)
                registered.append(tool.name)
            except ValueError:
                existing = self._tools.get(tool.name)
                if existing:
                    self.unregister(tool.name)
                    self.register(tool)
                    registered.append(tool.name)

        if registered:
            await audit_service.record(
                category=AuditCategory.TOOL_REGISTER,
                action="register_device_tools",
                level=AuditLevel.INFO,
                actor_type="device",
                actor_id=device.device_id,
                source_device_id=device.device_id,
                source_platform=device.platform.value,
                status="success",
                detail=json.dumps({"tools": registered}, ensure_ascii=False),
            )

        return registered

    async def unregister_device_tools(self, device_id: str) -> list[str]:
        if not self._bridge_factory:
            return []
        tool_names = self._bridge_factory.remove_tools_for_device(device_id)
        for name in tool_names:
            try:
                self.unregister(name)
            except KeyError:
                pass

        if tool_names:
            await audit_service.record(
                category=AuditCategory.TOOL_UNREGISTER,
                action="unregister_device_tools",
                level=AuditLevel.INFO,
                actor_type="device",
                actor_id=device_id,
                source_device_id=device_id,
                status="success",
                detail=json.dumps({"tools": tool_names}, ensure_ascii=False),
            )

        return tool_names

    def get_device_bridge_tools(self, device_id: str) -> list[DeviceBridgeTool]:
        return [
            tool for tool in self._tools.values()
            if isinstance(tool, DeviceBridgeTool) and tool._device_id == device_id
        ]


tool_registry = ToolRegistry(device_manager=device_manager)
