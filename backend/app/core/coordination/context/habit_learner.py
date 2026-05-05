import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class HabitPattern:
    pattern_type: str
    pattern_data: dict
    confidence: float = 0.0
    observed_count: int = 0
    last_observed: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "pattern_data": self.pattern_data,
            "confidence": self.confidence,
            "observed_count": self.observed_count,
            "last_observed": self.last_observed,
        }


class HabitLearner:
    def __init__(self):
        self._patterns: dict[str, HabitPattern] = {}
        self._time_observations: list[dict] = []
        self._app_observations: list[dict] = []
        self._communication_observations: list[dict] = []
        self._work_rhythm_observations: list[dict] = []
        self._max_observations = 500
        self._min_confidence = 0.3
        self._confidence_increment = 0.05
        self._confidence_decay = 0.01

    def observe_time_pattern(self, hour: int, activity: str) -> None:
        obs = {"hour": hour, "activity": activity, "timestamp": time.time()}
        self._time_observations.append(obs)
        if len(self._time_observations) > self._max_observations:
            self._time_observations = self._time_observations[-self._max_observations:]
        self._update_time_patterns()

    def observe_app_usage(self, app: str, hour: int, duration_minutes: float = 0) -> None:
        obs = {"app": app, "hour": hour, "duration": duration_minutes, "timestamp": time.time()}
        self._app_observations.append(obs)
        if len(self._app_observations) > self._max_observations:
            self._app_observations = self._app_observations[-self._max_observations:]
        self._update_app_patterns()

    def observe_communication(self, contact: str, hour: int, channel: str, topic: str = "") -> None:
        obs = {"contact": contact, "hour": hour, "channel": channel, "topic": topic, "timestamp": time.time()}
        self._communication_observations.append(obs)
        if len(self._communication_observations) > self._max_observations:
            self._communication_observations = self._communication_observations[-self._max_observations:]
        self._update_communication_patterns()

    def observe_work_rhythm(self, rhythm_type: str, duration_minutes: float, hour: int) -> None:
        obs = {"type": rhythm_type, "duration": duration_minutes, "hour": hour, "timestamp": time.time()}
        self._work_rhythm_observations.append(obs)
        if len(self._work_rhythm_observations) > self._max_observations:
            self._work_rhythm_observations = self._work_rhythm_observations[-self._max_observations:]
        self._update_work_rhythm_patterns()

    def _update_time_patterns(self) -> None:
        hour_activity: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for obs in self._time_observations:
            hour_activity[obs["hour"]][obs["activity"]] += 1
        for hour, activities in hour_activity.items():
            total = sum(activities.values())
            if total < 3:
                continue
            dominant = max(activities, key=activities.get)
            confidence = activities[dominant] / total
            key = f"time_{hour}_{dominant}"
            if key in self._patterns:
                p = self._patterns[key]
                p.observed_count += 1
                p.confidence = min(1.0, p.confidence + self._confidence_increment)
                p.last_observed = time.time()
            else:
                self._patterns[key] = HabitPattern(
                    pattern_type="time",
                    pattern_data={"hour": hour, "activity": dominant, "frequency": total},
                    confidence=confidence,
                    observed_count=1,
                )

    def _update_app_patterns(self) -> None:
        hour_app: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for obs in self._app_observations:
            hour_app[obs["hour"]][obs["app"]] += 1
        for hour, apps in hour_app.items():
            total = sum(apps.values())
            if total < 3:
                continue
            dominant = max(apps, key=apps.get)
            key = f"app_{hour}_{dominant}"
            if key in self._patterns:
                p = self._patterns[key]
                p.observed_count += 1
                p.confidence = min(1.0, p.confidence + self._confidence_increment)
                p.last_observed = time.time()
            else:
                self._patterns[key] = HabitPattern(
                    pattern_type="app_usage",
                    pattern_data={"hour": hour, "app": dominant, "frequency": total},
                    confidence=total / (total + 5),
                    observed_count=1,
                )

    def _update_communication_patterns(self) -> None:
        contact_hour: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
        for obs in self._communication_observations:
            contact_hour[obs["contact"]][obs["hour"]] += 1
        for contact, hours in contact_hour.items():
            total = sum(hours.values())
            if total < 2:
                continue
            peak_hour = max(hours, key=hours.get)
            key = f"comm_{contact}_{peak_hour}"
            if key in self._patterns:
                p = self._patterns[key]
                p.observed_count += 1
                p.confidence = min(1.0, p.confidence + self._confidence_increment)
            else:
                self._patterns[key] = HabitPattern(
                    pattern_type="communication",
                    pattern_data={"contact": contact, "peak_hour": peak_hour, "frequency": total},
                    confidence=total / (total + 3),
                    observed_count=1,
                )

    def _update_work_rhythm_patterns(self) -> None:
        type_durations: dict[str, list[float]] = defaultdict(list)
        for obs in self._work_rhythm_observations:
            type_durations[obs["type"]].append(obs["duration"])
        for rhythm_type, durations in type_durations.items():
            if len(durations) < 3:
                continue
            avg_duration = sum(durations) / len(durations)
            key = f"rhythm_{rhythm_type}"
            if key in self._patterns:
                p = self._patterns[key]
                p.observed_count += 1
                p.pattern_data["avg_duration"] = avg_duration
                p.confidence = min(1.0, p.confidence + self._confidence_increment)
            else:
                self._patterns[key] = HabitPattern(
                    pattern_type="work_rhythm",
                    pattern_data={"type": rhythm_type, "avg_duration": avg_duration, "samples": len(durations)},
                    confidence=len(durations) / (len(durations) + 5),
                    observed_count=1,
                )

    def detect_anomaly(self, current_activity: str, current_hour: int) -> Optional[dict]:
        expected = self.predict_activity(current_hour)
        if not expected:
            return None
        if current_activity != expected.get("activity"):
            return {
                "expected": expected,
                "actual": {"activity": current_activity, "hour": current_hour},
                "deviation": True,
                "suggestion": f"Usually at this time you {expected['activity']}. Need help with {current_activity}?",
            }
        return None

    def predict_activity(self, hour: int) -> Optional[dict]:
        candidates = []
        for key, pattern in self._patterns.items():
            if pattern.pattern_type == "time" and pattern.pattern_data.get("hour") == hour:
                if pattern.confidence >= self._min_confidence:
                    candidates.append(pattern)
        if not candidates:
            return None
        best = max(candidates, key=lambda p: p.confidence)
        return {"activity": best.pattern_data["activity"], "confidence": best.confidence}

    def get_patterns(self, pattern_type: Optional[str] = None, min_confidence: float = 0.0) -> list[dict]:
        results = []
        for key, pattern in self._patterns.items():
            if pattern_type and pattern.pattern_type != pattern_type:
                continue
            if pattern.confidence < min_confidence:
                continue
            results.append({"key": key, **pattern.to_dict()})
        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    def decay_confidence(self) -> None:
        for key, pattern in self._patterns.items():
            pattern.confidence = max(0.0, pattern.confidence - self._confidence_decay)
        self._patterns = {k: v for k, v in self._patterns.items() if v.confidence > 0.01}


_learner: Optional[HabitLearner] = None


def get_habit_learner() -> HabitLearner:
    global _learner
    if _learner is None:
        _learner = HabitLearner()
    return _learner
