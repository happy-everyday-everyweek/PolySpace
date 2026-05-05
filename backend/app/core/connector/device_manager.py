from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

from fastapi import WebSocket

from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class DevicePlatform(str, Enum):
    ANDROID = "android"
    WINDOWS = "windows"
    WEB = "web"
    LINUX = "linux"
    MACOS = "macos"


@dataclass
class DeviceCapability:
    name: str
    description: str = ""
    actions: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectedDevice:
    device_id: str
    device_name: str = ""
    platform: DevicePlatform = DevicePlatform.WEB
    status: DeviceStatus = DeviceStatus.ONLINE
    capabilities: list[DeviceCapability] = field(default_factory=list)
    websocket: Optional[WebSocket] = None
    connected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_heartbeat: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    _pending_requests: dict[str, asyncio.Future] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "platform": self.platform.value,
            "status": self.status.value,
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "actions": c.actions,
                    "parameters": c.parameters,
                }
                for c in self.capabilities
            ],
            "connected_at": self.connected_at,
            "last_heartbeat": self.last_heartbeat,
            "metadata": self.metadata,
        }

    def get_tool_names(self) -> list[str]:
        return [f"device_{self.device_id[:8]}_{c.name}" for c in self.capabilities]


class DeviceManager:
    def __init__(self, heartbeat_timeout: float = 30.0, heartbeat_interval: float = 10.0):
        self._devices: dict[str, ConnectedDevice] = {}
        self._heartbeat_timeout = heartbeat_timeout
        self._heartbeat_interval = heartbeat_interval
        self._on_device_connected: Optional[Callable[[ConnectedDevice], Awaitable[None]]] = None
        self._on_device_disconnected: Optional[Callable[[ConnectedDevice], Awaitable[None]]] = None
        self._on_capabilities_updated: Optional[Callable[[ConnectedDevice], Awaitable[None]]] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._status_subscribers: list[WebSocket] = []

    def set_callbacks(
        self,
        on_connected: Optional[Callable[[ConnectedDevice], Awaitable[None]]] = None,
        on_disconnected: Optional[Callable[[ConnectedDevice], Awaitable[None]]] = None,
        on_capabilities_updated: Optional[Callable[[ConnectedDevice], Awaitable[None]]] = None,
    ) -> None:
        self._on_device_connected = on_connected
        self._on_device_disconnected = on_disconnected
        self._on_capabilities_updated = on_capabilities_updated

    async def start_heartbeat_monitor(self) -> None:
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop_heartbeat_monitor(self) -> None:
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                now = time.time()
                to_remove = []
                for device_id, device in self._devices.items():
                    if device.status == DeviceStatus.OFFLINE:
                        to_remove.append(device_id)
                        continue
                    if now - device.last_heartbeat > self._heartbeat_timeout:
                        device.status = DeviceStatus.OFFLINE
                        to_remove.append(device_id)
                for device_id in to_remove:
                    device = self._devices.pop(device_id, None)
                    if device and self._on_device_disconnected:
                        await self._on_device_disconnected(device)
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def register_device(
        self,
        websocket: WebSocket,
        device_id: Optional[str] = None,
        device_name: str = "",
        platform: str = "web",
        capabilities: Optional[list[dict]] = None,
        metadata: Optional[dict] = None,
        skip_accept: bool = False,
    ) -> ConnectedDevice:
        if not skip_accept:
            await websocket.accept()

        if not device_id:
            device_id = str(uuid.uuid4())

        existing = self._devices.get(device_id)
        if existing and existing.websocket:
            try:
                await existing.websocket.close()
            except Exception:
                pass

        parsed_caps = []
        if capabilities:
            for cap_data in capabilities:
                parsed_caps.append(DeviceCapability(
                    name=cap_data.get("name", ""),
                    description=cap_data.get("description", ""),
                    actions=cap_data.get("actions", []),
                    parameters=cap_data.get("parameters", {}),
                ))

        device = ConnectedDevice(
            device_id=device_id,
            device_name=device_name or f"{platform}-{device_id[:8]}",
            platform=DevicePlatform(platform.lower()),
            status=DeviceStatus.ONLINE,
            capabilities=parsed_caps,
            websocket=websocket,
            metadata=metadata or {},
        )

        self._devices[device_id] = device

        await audit_service.record(
            category=AuditCategory.DEVICE_CONNECT,
            action="device_register",
            level=AuditLevel.INFO,
            actor_type="device",
            actor_id=device_id,
            source_device_id=device_id,
            source_platform=platform,
            status="success",
            detail=json.dumps({
                "device_name": device.device_name,
                "platform": platform,
                "capabilities": [c.name for c in parsed_caps],
            }, ensure_ascii=False),
        )

        if self._on_device_connected:
            await self._on_device_connected(device)

        await self._notify_status_change("connected", device)

        return device

    async def disconnect_device(self, device_id: str) -> None:
        device = self._devices.pop(device_id, None)
        if device:
            for fut in device._pending_requests.values():
                if not fut.done():
                    fut.set_result({"status": "error", "message": "Device disconnected"})
            if device.websocket:
                try:
                    await device.websocket.close()
                except Exception:
                    pass

            await audit_service.record(
                category=AuditCategory.DEVICE_DISCONNECT,
                action="device_disconnect",
                level=AuditLevel.INFO,
                actor_type="device",
                actor_id=device_id,
                source_device_id=device_id,
                source_platform=device.platform.value,
                status="success",
                detail=f"Device {device.device_name} disconnected",
            )

            if self._on_device_disconnected:
                await self._on_device_disconnected(device)

            await self._notify_status_change("disconnected", device)

    async def handle_message(self, device_id: str, message: dict) -> None:
        device = self._devices.get(device_id)
        if not device:
            return

        msg_type = message.get("type", "")

        if msg_type == "heartbeat":
            device.last_heartbeat = time.time()
            device.status = DeviceStatus.ONLINE
            if device.websocket:
                try:
                    await device.websocket.send_json({"type": "heartbeat_ack", "timestamp": time.time()})
                except Exception:
                    pass

        elif msg_type == "capability_update":
            caps_data = message.get("capabilities", [])
            parsed_caps = []
            for cap_data in caps_data:
                parsed_caps.append(DeviceCapability(
                    name=cap_data.get("name", ""),
                    description=cap_data.get("description", ""),
                    actions=cap_data.get("actions", []),
                    parameters=cap_data.get("parameters", {}),
                ))
            device.capabilities = parsed_caps

            await audit_service.record(
                category=AuditCategory.DEVICE_CAPABILITY,
                action="capability_update",
                level=AuditLevel.INFO,
                actor_type="device",
                actor_id=device_id,
                source_device_id=device_id,
                source_platform=device.platform.value,
                detail=json.dumps({
                    "capabilities": [c.name for c in parsed_caps],
                }, ensure_ascii=False),
            )

            if self._on_capabilities_updated:
                await self._on_capabilities_updated(device)

        elif msg_type == "tool_result":
            request_id = message.get("request_id", "")
            fut = device._pending_requests.pop(request_id, None)
            if fut and not fut.done():
                fut.set_result(message.get("result", {}))

        elif msg_type == "tool_error":
            request_id = message.get("request_id", "")
            fut = device._pending_requests.pop(request_id, None)
            if fut and not fut.done():
                fut.set_result({
                    "status": "error",
                    "message": message.get("error", "Unknown error"),
                })

        elif msg_type == "status_update":
            status_str = message.get("status", "online")
            try:
                device.status = DeviceStatus(status_str)
            except ValueError:
                device.status = DeviceStatus.ONLINE

    async def execute_on_device(
        self,
        device_id: str,
        tool_name: str,
        action: str,
        params: dict[str, Any],
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        device = self._devices.get(device_id)
        if not device:
            return {"status": "error", "message": f"Device not found: {device_id}"}
        if device.status == DeviceStatus.OFFLINE:
            return {"status": "error", "message": f"Device is offline: {device_id}"}
        if not device.websocket:
            return {"status": "error", "message": f"Device has no active connection: {device_id}"}

        start_time = time.monotonic()
        request_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        device._pending_requests[request_id] = future

        command = {
            "type": "tool_call",
            "request_id": request_id,
            "tool": tool_name,
            "action": action,
            "params": params,
            "timestamp": time.time(),
        }

        try:
            await device.websocket.send_json(command)
        except Exception as e:
            device._pending_requests.pop(request_id, None)
            if not future.done():
                future.cancel()
            await audit_service.record(
                category=AuditCategory.DEVICE_EXECUTE,
                action=f"remote_execute:{tool_name}.{action}",
                level=AuditLevel.ERROR,
                actor_type="server",
                target_device_id=device_id,
                target_platform=device.platform.value,
                resource_type="tool",
                resource_id=tool_name,
                status="error",
                duration_ms=round((time.monotonic() - start_time) * 1000, 2),
                detail=f"Failed to send command: {str(e)}",
            )
            return {"status": "error", "message": f"Failed to send command: {str(e)}"}

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            result_status = result.get("status", "ok") if isinstance(result, dict) else "ok"
            await audit_service.record(
                category=AuditCategory.DEVICE_EXECUTE,
                action=f"remote_execute:{tool_name}.{action}",
                level=AuditLevel.INFO,
                actor_type="server",
                target_device_id=device_id,
                target_platform=device.platform.value,
                resource_type="tool",
                resource_id=tool_name,
                status="success" if result_status != "error" else "error",
                duration_ms=duration_ms,
                request_summary=json.dumps({"action": action, "params_keys": list(params.keys())}, ensure_ascii=False),
                response_summary=str(result)[:500] if result else "",
            )
            return result if isinstance(result, dict) else {"status": "ok", "result": result}
        except asyncio.TimeoutError:
            device._pending_requests.pop(request_id, None)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            await audit_service.record(
                category=AuditCategory.DEVICE_EXECUTE,
                action=f"remote_execute:{tool_name}.{action}",
                level=AuditLevel.ERROR,
                actor_type="server",
                target_device_id=device_id,
                target_platform=device.platform.value,
                resource_type="tool",
                resource_id=tool_name,
                status="timeout",
                duration_ms=duration_ms,
                detail=f"Tool execution timed out after {timeout}s",
            )
            return {"status": "error", "message": f"Tool execution timed out after {timeout}s"}
        except Exception as e:
            device._pending_requests.pop(request_id, None)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            await audit_service.record(
                category=AuditCategory.DEVICE_EXECUTE,
                action=f"remote_execute:{tool_name}.{action}",
                level=AuditLevel.ERROR,
                actor_type="server",
                target_device_id=device_id,
                target_platform=device.platform.value,
                resource_type="tool",
                resource_id=tool_name,
                status="error",
                duration_ms=duration_ms,
                detail=str(e),
            )
            return {"status": "error", "message": str(e)}

    async def broadcast_to_devices(
        self,
        message: dict,
        platform: Optional[DevicePlatform] = None,
    ) -> dict[str, bool]:
        targets: list[tuple[str, WebSocket]] = []
        offline_results: dict[str, bool] = {}

        for device_id, device in self._devices.items():
            if device.status == DeviceStatus.OFFLINE or not device.websocket:
                offline_results[device_id] = False
                continue
            if platform and device.platform != platform:
                offline_results[device_id] = False
                continue
            targets.append((device_id, device.websocket))

        async def _send_single(did: str, ws: WebSocket) -> bool:
            try:
                await ws.send_json(message)
                return True
            except Exception:
                return False

        send_results = await asyncio.gather(
            *[_send_single(did, ws) for did, ws in targets],
            return_exceptions=False,
        )
        results = {did: ok for (did, _), ok in zip(targets, send_results)}
        results.update(offline_results)

        reached = sum(1 for v in results.values() if v)
        await audit_service.record(
            category=AuditCategory.DEVICE_BROADCAST,
            action="broadcast",
            level=AuditLevel.INFO,
            actor_type="server",
            status="success",
            detail=json.dumps({
                "msg_type": message.get("type", ""),
                "target_platform": platform.value if platform else "all",
                "total_devices": len(results),
                "reached": reached,
            }, ensure_ascii=False),
        )

        return results

    def get_device(self, device_id: str) -> Optional[ConnectedDevice]:
        return self._devices.get(device_id)

    def list_devices(self, platform: Optional[str] = None, status: Optional[str] = None) -> list[ConnectedDevice]:
        devices = list(self._devices.values())
        if platform:
            try:
                pf = DevicePlatform(platform.lower())
                devices = [d for d in devices if d.platform == pf]
            except ValueError:
                pass
        if status:
            try:
                st = DeviceStatus(status.lower())
                devices = [d for d in devices if d.status == st]
            except ValueError:
                pass
        return devices

    def find_device_for_tool(self, tool_name: str, action: Optional[str] = None) -> Optional[ConnectedDevice]:
        for device in self._devices.values():
            if device.status == DeviceStatus.OFFLINE:
                continue
            for cap in device.capabilities:
                if cap.name == tool_name:
                    if action and action not in cap.actions:
                        continue
                    return device
        return None

    def find_devices_by_capability(self, capability_name: str) -> list[ConnectedDevice]:
        result = []
        for device in self._devices.values():
            if device.status == DeviceStatus.OFFLINE:
                continue
            for cap in device.capabilities:
                if cap.name == capability_name:
                    result.append(device)
                    break
        return result

    @property
    def device_count(self) -> int:
        return len(self._devices)

    @property
    def online_count(self) -> int:
        return sum(1 for d in self._devices.values() if d.status != DeviceStatus.OFFLINE)

    def subscribe_status(self, ws: WebSocket) -> None:
        self._status_subscribers.append(ws)

    def unsubscribe_status(self, ws: WebSocket) -> None:
        try:
            self._status_subscribers.remove(ws)
        except ValueError:
            pass

    async def _notify_status_change(self, event: str, device: ConnectedDevice) -> None:
        if not self._status_subscribers:
            return
        message = json.dumps({
            "type": "device_status",
            "event": event,
            "device": device.to_dict(),
            "total": self.device_count,
            "online": self.online_count,
        }, ensure_ascii=False)
        to_remove = []
        for ws in self._status_subscribers:
            try:
                await ws.send_text(message)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self._status_subscribers.remove(ws)


device_manager = DeviceManager()
