from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DeviceMessageType(str, Enum):
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    REGISTER = "register"
    REGISTER_ACK = "register_ack"
    CAPABILITY_UPDATE = "capability_update"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"
    STATUS_UPDATE = "status_update"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"


@dataclass
class DeviceMessage:
    type: DeviceMessageType
    request_id: str = ""
    device_id: str = ""
    timestamp: float = 0.0
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = {"type": self.type.value}
        if self.request_id:
            result["request_id"] = self.request_id
        if self.device_id:
            result["device_id"] = self.device_id
        if self.timestamp:
            result["timestamp"] = self.timestamp
        if self.payload:
            result.update(self.payload)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceMessage:
        msg_type_str = data.get("type", "")
        try:
            msg_type = DeviceMessageType(msg_type_str)
        except ValueError:
            msg_type = DeviceMessageType.PING

        payload_keys = {"type", "request_id", "device_id", "timestamp"}
        payload = {k: v for k, v in data.items() if k not in payload_keys}

        return cls(
            type=msg_type,
            request_id=data.get("request_id", ""),
            device_id=data.get("device_id", ""),
            timestamp=data.get("timestamp", 0.0),
            payload=payload,
        )


def make_heartbeat() -> dict[str, Any]:
    import time
    return {"type": DeviceMessageType.HEARTBEAT.value, "timestamp": time.time()}


def make_heartbeat_ack() -> dict[str, Any]:
    import time
    return {"type": DeviceMessageType.HEARTBEAT_ACK.value, "timestamp": time.time()}


def make_register(
    device_id: str = "",
    device_name: str = "",
    platform: str = "web",
    capabilities: Optional[list[dict]] = None,
) -> dict[str, Any]:
    import time
    msg: dict[str, Any] = {
        "type": DeviceMessageType.REGISTER.value,
        "device_id": device_id,
        "device_name": device_name,
        "platform": platform,
        "timestamp": time.time(),
    }
    if capabilities:
        msg["capabilities"] = capabilities
    return msg


def make_register_ack(device_id: str, accepted: bool = True) -> dict[str, Any]:
    import time
    return {
        "type": DeviceMessageType.REGISTER_ACK.value,
        "device_id": device_id,
        "accepted": accepted,
        "timestamp": time.time(),
    }


def make_tool_call(
    request_id: str,
    tool: str,
    action: str,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    import time
    return {
        "type": DeviceMessageType.TOOL_CALL.value,
        "request_id": request_id,
        "tool": tool,
        "action": action,
        "params": params or {},
        "timestamp": time.time(),
    }


def make_tool_result(request_id: str, result: Any) -> dict[str, Any]:
    import time
    return {
        "type": DeviceMessageType.TOOL_RESULT.value,
        "request_id": request_id,
        "result": result,
        "timestamp": time.time(),
    }


def make_tool_error(request_id: str, error: str) -> dict[str, Any]:
    import time
    return {
        "type": DeviceMessageType.TOOL_ERROR.value,
        "request_id": request_id,
        "error": error,
        "timestamp": time.time(),
    }


def make_capability_update(capabilities: list[dict]) -> dict[str, Any]:
    import time
    return {
        "type": DeviceMessageType.CAPABILITY_UPDATE.value,
        "capabilities": capabilities,
        "timestamp": time.time(),
    }


def make_status_update(status: str) -> dict[str, Any]:
    import time
    return {
        "type": DeviceMessageType.STATUS_UPDATE.value,
        "status": status,
        "timestamp": time.time(),
    }


def make_disconnect(reason: str = "") -> dict[str, Any]:
    import time
    return {
        "type": DeviceMessageType.DISCONNECT.value,
        "reason": reason,
        "timestamp": time.time(),
    }
