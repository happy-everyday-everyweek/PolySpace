import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ActivityState(str, Enum):
    WORKING = "working"
    RESTING = "resting"
    COMMUTING = "commuting"
    IN_MEETING = "in_meeting"
    FOCUSED = "focused"
    IDLE = "idle"
    UNKNOWN = "unknown"


class AttentionFocus(str, Enum):
    DOCUMENT = "document"
    CODE = "code"
    EMAIL = "email"
    CHAT = "chat"
    BROWSER = "browser"
    CALENDAR = "calendar"
    NONE = "none"


class MoodState(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    STRESSED = "stressed"
    TIRED = "tired"
    UNKNOWN = "unknown"


@dataclass
class UserProfileSnapshot:
    activity: ActivityState = ActivityState.UNKNOWN
    attention: AttentionFocus = AttentionFocus.NONE
    mood: MoodState = MoodState.UNKNOWN
    urgency_level: str = "normal"
    efficiency_curve: dict = field(default_factory=dict)
    confidence: float = 0.0
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "activity": self.activity.value,
            "attention": self.attention.value,
            "mood": self.mood.value,
            "urgency_level": self.urgency_level,
            "efficiency_curve": self.efficiency_curve,
            "confidence": self.confidence,
            "updated_at": self.updated_at,
        }


class DynamicUserProfile:
    def __init__(self):
        self._snapshot = UserProfileSnapshot()
        self._interaction_times: list[float] = []
        self._max_interaction_history = 50
        self._activity_history: list[dict] = []
        self._max_activity_history = 20

    @property
    def snapshot(self) -> UserProfileSnapshot:
        return self._snapshot

    def record_interaction(self) -> None:
        now = time.time()
        self._interaction_times.append(now)
        if len(self._interaction_times) > self._max_interaction_history:
            self._interaction_times = self._interaction_times[-self._max_interaction_history:]

    def update_from_context(self, context: dict) -> None:
        sources = context.get("sources", {})
        summary = context.get("summary", {})
        activity = self._infer_activity(sources)
        attention = self._infer_attention(sources)
        mood = self._infer_mood(sources)
        urgency = self._infer_urgency(summary)
        self._snapshot = UserProfileSnapshot(
            activity=activity,
            attention=attention,
            mood=mood,
            urgency_level=urgency,
            efficiency_curve=self._compute_efficiency_curve(),
            confidence=min(1.0, len(sources) * 0.15),
            updated_at=time.time(),
        )
        self._activity_history.append({
            "activity": activity.value,
            "attention": attention.value,
            "mood": mood.value,
            "timestamp": time.time(),
        })
        if len(self._activity_history) > self._max_activity_history:
            self._activity_history = self._activity_history[-self._max_activity_history:]

    def _infer_activity(self, sources: dict) -> ActivityState:
        now = time.time()
        recent_interactions = [t for t in self._interaction_times if (now - t) < 300]
        if len(recent_interactions) > 10:
            return ActivityState.FOCUSED
        if "calendar" in sources:
            cal_data = sources["calendar"].get("latest", {})
            if cal_data and cal_data.get("is_meeting"):
                return ActivityState.IN_MEETING
        if "screen" in sources:
            screen_data = sources["screen"].get("latest", {})
            app = screen_data.get("app", "")
            if app in ("vscode", "intellij", "android_studio"):
                return ActivityState.WORKING
        if len(recent_interactions) == 0:
            idle_time = (now - self._interaction_times[-1]) if self._interaction_times else 3600
            if idle_time > 1800:
                return ActivityState.IDLE
        return ActivityState.UNKNOWN

    def _infer_attention(self, sources: dict) -> AttentionFocus:
        if "screen" in sources:
            screen_data = sources["screen"].get("latest", {})
            app = screen_data.get("app", "")
            if app in ("vscode", "intellij"):
                return AttentionFocus.CODE
            if app in ("word", "wps", "notion"):
                return AttentionFocus.DOCUMENT
            if app in ("chrome", "firefox", "edge"):
                return AttentionFocus.BROWSER
        if "email" in sources:
            return AttentionFocus.EMAIL
        if "chat" in sources:
            return AttentionFocus.CHAT
        return AttentionFocus.NONE

    def _infer_mood(self, sources: dict) -> MoodState:
        now = time.time()
        recent = [t for t in self._interaction_times if (now - t) < 3600]
        if len(recent) > 30:
            return MoodState.STRESSED
        if len(recent) > 15:
            return MoodState.POSITIVE
        if len(recent) < 3 and self._interaction_times:
            return MoodState.TIRED
        return MoodState.NEUTRAL

    def _infer_urgency(self, summary: dict) -> str:
        urgent = summary.get("urgent_event_count", 0)
        if urgent > 3:
            return "critical"
        if urgent > 0:
            return "high"
        return "normal"

    def _compute_efficiency_curve(self) -> dict:
        if not self._interaction_times:
            return {}
        hourly = {}
        for t in self._interaction_times:
            hour = int((t % 86400) / 3600)
            hourly[hour] = hourly.get(hour, 0) + 1
        return hourly

    def get_activity_history(self, limit: int = 20) -> list[dict]:
        return self._activity_history[-limit:]

    def get_current(self) -> dict:
        return self._snapshot.to_dict()


_profile: Optional[DynamicUserProfile] = None


def get_user_profile() -> DynamicUserProfile:
    global _profile
    if _profile is None:
        _profile = DynamicUserProfile()
    return _profile
