import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DeviceActivity:
    device_id: str
    device_type: str
    current_activity: dict = field(default_factory=dict)
    last_active: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "current_activity": self.current_activity,
            "last_active": self.last_active,
        }


@dataclass
class HandoffRequest:
    source_device: str
    target_device: str
    activity_type: str
    activity_data: dict
    status: str = "pending"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "source_device": self.source_device,
            "target_device": self.target_device,
            "activity_type": self.activity_type,
            "activity_data": self.activity_data,
            "status": self.status,
            "created_at": self.created_at,
        }


class ActivityHandoff:
    def __init__(self):
        self._devices: dict[str, DeviceActivity] = {}
        self._handoff_history: list[HandoffRequest] = []
        self._max_history = 50
        self._sync_on_handoff: bool = True

    def set_sync_on_handoff(self, enabled: bool) -> None:
        self._sync_on_handoff = enabled

    def register_device(self, device_id: str, device_type: str) -> None:
        self._devices[device_id] = DeviceActivity(device_id=device_id, device_type=device_type)
        self._sync_from_device_manager(device_id)

    def _sync_from_device_manager(self, device_id: str) -> None:
        try:
            from app.core.connector.device_manager import device_manager
            connected = device_manager.get_device(device_id)
            if connected and hasattr(connected, "platform"):
                if device_id in self._devices:
                    platform = connected.platform
                    self._devices[device_id].device_type = (
                        platform.value if hasattr(platform, "value") else str(platform)
                    )
        except ImportError:
            pass

    def update_activity(self, device_id: str, activity: dict) -> None:
        if device_id in self._devices:
            self._devices[device_id].current_activity = activity
            self._devices[device_id].last_active = time.time()

    def detect_device_switch(self) -> Optional[HandoffRequest]:
        now = time.time()
        active_devices = [(d, dev) for d, dev in self._devices.items() if (now - dev.last_active) < 300]
        if len(active_devices) < 2:
            return None
        sorted_devices = sorted(active_devices, key=lambda x: x[1].last_active, reverse=True)
        newest = sorted_devices[0]
        previous = sorted_devices[1]
        if newest[1].current_activity and not previous[1].current_activity:
            return None
        if previous[1].current_activity:
            handoff = HandoffRequest(
                source_device=previous[0],
                target_device=newest[0],
                activity_type=previous[1].current_activity.get("type", "unknown"),
                activity_data=previous[1].current_activity,
            )
            self._handoff_history.append(handoff)
            if len(self._handoff_history) > self._max_history:
                self._handoff_history = self._handoff_history[-self._max_history:]

            if self._sync_on_handoff:
                self._trigger_handoff_sync(previous[0], newest[0])

            return handoff
        return None

    def _trigger_handoff_sync(self, source_device_id: str, target_device_id: str) -> None:
        try:
            import asyncio

            from app.services.sync_service import sync_service
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(
                    sync_service.trigger_handoff_sync(source_device_id, target_device_id)
                )
            else:
                loop.run_until_complete(
                    sync_service.trigger_handoff_sync(source_device_id, target_device_id)
                )
            logger.info(f"Handoff sync triggered: {source_device_id} -> {target_device_id}")
        except Exception as e:
            logger.error(f"Handoff sync trigger failed: {e}")

    def sync_devices_from_device_manager(self) -> int:
        try:
            from app.core.connector.device_manager import device_manager
            online = device_manager.get_online_devices()
            synced = 0
            for device_id in online:
                if device_id not in self._devices:
                    device_info = device_manager.get_device(device_id)
                    device_type = ""
                    if device_info and hasattr(device_info, "platform"):
                        platform = device_info.platform
                        device_type = (
                            platform.value if hasattr(platform, "value") else str(platform)
                        )
                    self._devices[device_id] = DeviceActivity(
                        device_id=device_id, device_type=device_type
                    )
                    synced += 1
            return synced
        except ImportError:
            return 0

    def get_device_status(self) -> list[dict]:
        return [d.to_dict() for d in self._devices.values()]

    def get_handoff_history(self, limit: int = 20) -> list[dict]:
        return [h.to_dict() for h in self._handoff_history[-limit:]]


class ContextSync:
    def __init__(self):
        self._sync_state: dict[str, dict] = {}
        self._conflict_log: list[dict] = []
        self._max_conflict_log = 50

    def sync_context(self, device_id: str, context: dict) -> dict:
        now = time.time()
        existing = self._sync_state.get(device_id, {})
        changes = {}
        for key, value in context.items():
            if existing.get(key) != value:
                changes[key] = {"old": existing.get(key), "new": value}
        self._sync_state[device_id] = {"context": context, "updated_at": now}
        return {"device_id": device_id, "changes": changes, "synced_at": now}

    def resolve_conflict(self, key: str, devices: list[str], resolution: str = "latest") -> dict:
        values = {}
        for device_id in devices:
            ctx = self._sync_state.get(device_id, {}).get("context", {})
            if key in ctx:
                values[device_id] = ctx[key]
        if resolution == "latest":
            latest_device = max(
                devices,
                key=lambda d: self._sync_state.get(d, {}).get("updated_at", 0),
            )
            resolved_value = values.get(latest_device)
        elif resolution == "merge":
            resolved_value = self._merge_values(values)
        else:
            resolved_value = values.get(devices[0]) if devices else None
        conflict_entry = {
            "key": key,
            "devices": devices,
            "values": values,
            "resolution": resolution,
            "resolved_value": resolved_value,
            "timestamp": time.time(),
        }
        self._conflict_log.append(conflict_entry)
        if len(self._conflict_log) > self._max_conflict_log:
            self._conflict_log = self._conflict_log[-self._max_conflict_log:]
        return conflict_entry

    def _merge_values(self, values: dict) -> any:
        if not values:
            return None
        first = list(values.values())[0]
        if isinstance(first, dict):
            merged = {}
            for v in values.values():
                if isinstance(v, dict):
                    merged.update(v)
            return merged
        return list(values.values())[-1]

    def get_sync_state(self) -> dict:
        return {k: {"updated_at": v["updated_at"]} for k, v in self._sync_state.items()}


_handoff: Optional[ActivityHandoff] = None
_sync: Optional[ContextSync] = None


def get_activity_handoff() -> ActivityHandoff:
    global _handoff
    if _handoff is None:
        _handoff = ActivityHandoff()
    return _handoff


def get_context_sync() -> ContextSync:
    global _sync
    if _sync is None:
        _sync = ContextSync()
    return _sync
