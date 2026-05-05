import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class VoiceAnnouncement:
    text: str
    priority: str = "normal"
    played: bool = False
    played_at: float = 0.0
    queued_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "priority": self.priority,
            "played": self.played,
            "queued_at": self.queued_at,
        }


class VoiceChannel:
    def __init__(self):
        self._queue: list[VoiceAnnouncement] = []
        self._history: list[VoiceAnnouncement] = []
        self._max_history = 50
        self._headphones_connected: bool = False
        self._in_call: bool = False
        self._enabled: bool = True
        self._max_daily = 10
        self._daily_count: dict[str, int] = {}

    def set_headphones_status(self, connected: bool) -> None:
        self._headphones_connected = connected

    def set_call_status(self, in_call: bool) -> None:
        self._in_call = in_call

    async def announce(self, text: str, priority: str = "normal") -> Optional[VoiceAnnouncement]:
        if not self._enabled:
            return None
        if self._in_call:
            logger.info("Voice announcement skipped: user in call")
            return None
        if not self._headphones_connected and priority != "urgent":
            logger.info("Voice announcement skipped: no headphones and not urgent")
            return None
        today = time.strftime("%Y-%m-%d")
        self._daily_count[today] = self._daily_count.get(today, 0) + 1
        if self._daily_count[today] > self._max_daily:
            return None
        if len(text) > 200:
            text = text[:197] + "..."
        announcement = VoiceAnnouncement(text=text, priority=priority)
        self._queue.append(announcement)
        return announcement

    async def process_queue(self) -> list[VoiceAnnouncement]:
        played = []
        while self._queue:
            ann = self._queue.pop(0)
            if self._in_call and ann.priority != "urgent":
                self._queue.append(ann)
                break
            ann.played = True
            ann.played_at = time.time()
            self._history.append(ann)
            played.append(ann)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        return played

    def get_history(self, limit: int = 20) -> list[dict]:
        return [a.to_dict() for a in self._history[-limit:]]

    def get_queue(self) -> list[dict]:
        return [a.to_dict() for a in self._queue]


_channel: Optional[VoiceChannel] = None


def get_voice_channel() -> VoiceChannel:
    global _channel
    if _channel is None:
        _channel = VoiceChannel()
    return _channel
