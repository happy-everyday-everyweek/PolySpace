import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ChannelPriority(str, Enum):
    SYSTEM_NOTIFICATION = "system_notification"
    POPUP = "popup"
    WIDGET = "widget"
    EMAIL = "email"
    CHAT_MESSAGE = "chat_message"
    WEBSOCKET = "websocket"
    VOICE = "voice"
    CALENDAR_INJECT = "calendar_inject"
    LOW_PRIORITY_NOTIFICATION = "low_priority_notification"
    TOAST = "toast"


URGENCY_CHANNEL_MAP = {
    "critical": [ChannelPriority.SYSTEM_NOTIFICATION, ChannelPriority.POPUP, ChannelPriority.WEBSOCKET],
    "urgent": [ChannelPriority.SYSTEM_NOTIFICATION, ChannelPriority.WEBSOCKET],
    "high": [ChannelPriority.SYSTEM_NOTIFICATION, ChannelPriority.WEBSOCKET],
    "important": [ChannelPriority.WIDGET, ChannelPriority.EMAIL, ChannelPriority.WEBSOCKET],
    "normal": [ChannelPriority.CHAT_MESSAGE, ChannelPriority.WEBSOCKET],
    "suggested": [ChannelPriority.CHAT_MESSAGE, ChannelPriority.LOW_PRIORITY_NOTIFICATION],
    "chitchat": [ChannelPriority.LOW_PRIORITY_NOTIFICATION, ChannelPriority.TOAST],
}

ACTIVITY_CHANNEL_FILTERS = {
    "in_meeting": [ChannelPriority.SYSTEM_NOTIFICATION, ChannelPriority.POPUP],
    "focused": [ChannelPriority.SYSTEM_NOTIFICATION, ChannelPriority.POPUP],
    "working": [ChannelPriority.SYSTEM_NOTIFICATION, ChannelPriority.WEBSOCKET, ChannelPriority.CHAT_MESSAGE],
    "resting": [ChannelPriority.CHAT_MESSAGE, ChannelPriority.LOW_PRIORITY_NOTIFICATION, ChannelPriority.TOAST],
    "idle": [ChannelPriority.WEBSOCKET, ChannelPriority.CHAT_MESSAGE, ChannelPriority.WIDGET],
}


@dataclass
class ChannelSelection:
    primary: ChannelPriority
    fallback: Optional[ChannelPriority] = None
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "primary": self.primary.value,
            "fallback": self.fallback.value if self.fallback else None,
            "reason": self.reason,
        }


class ChannelRouter:
    def __init__(self):
        self._channel_status: dict[ChannelPriority, bool] = {
            ch: True for ch in ChannelPriority
        }
        self._user_preferences: dict[str, list[str]] = {}

    def set_channel_available(self, channel: ChannelPriority, available: bool) -> None:
        self._channel_status[channel] = available

    def set_user_preference(self, urgency: str, channels: list[str]) -> None:
        self._user_preferences[urgency] = channels

    def select_channel(self, urgency: str, user_activity: str = "unknown", user_mood: str = "neutral") -> str:
        candidates = list(URGENCY_CHANNEL_MAP.get(urgency, [ChannelPriority.WEBSOCKET]))
        activity_filter = ACTIVITY_CHANNEL_FILTERS.get(user_activity)
        if activity_filter and urgency not in ("critical", "urgent"):
            filtered = [ch for ch in candidates if ch in activity_filter]
            if filtered:
                candidates = filtered
        if user_mood == "stressed" and urgency in ("suggested", "chitchat"):
            candidates = [ChannelPriority.LOW_PRIORITY_NOTIFICATION, ChannelPriority.TOAST]
        primary = self._find_available(candidates)
        if not primary:
            primary = ChannelPriority.WEBSOCKET
        return primary.value

    def _find_available(self, channels: list[ChannelPriority]) -> Optional[ChannelPriority]:
        for ch in channels:
            if self._channel_status.get(ch, True):
                return ch
        return None

    def select_multi_channel(self, urgency: str, user_activity: str = "unknown") -> list[str]:
        if urgency in ("critical", "urgent"):
            candidates = URGENCY_CHANNEL_MAP.get(urgency, [])
            return [ch.value for ch in candidates if self._channel_status.get(ch, True)]
        return [self.select_channel(urgency, user_activity)]

    def get_channel_status(self) -> dict:
        return {ch.value: available for ch, available in self._channel_status.items()}


_router: Optional[ChannelRouter] = None


def get_channel_router() -> ChannelRouter:
    global _router
    if _router is None:
        _router = ChannelRouter()
    return _router
