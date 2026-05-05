import logging
import time
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TriggerOperator(str, Enum):
    AND = "and"
    OR = "or"
    NOT = "not"


class TriggerConditionType(str, Enum):
    CONTEXT_SOURCE_ACTIVE = "context_source_active"
    USER_ACTIVITY = "user_activity"
    IDLE_TIME = "idle_time"
    TIME_OF_DAY = "time_of_day"
    EVENT_COUNT = "event_count"
    CUSTOM = "custom"


@dataclass
class TriggerCondition:
    type: TriggerConditionType
    params: dict = field(default_factory=dict)
    operator: TriggerOperator = TriggerOperator.AND

    def evaluate(self, context: dict, user_profile: dict) -> bool:
        if self.type == TriggerConditionType.CONTEXT_SOURCE_ACTIVE:
            source = self.params.get("source", "")
            sources = context.get("sources", {})
            return source in sources and sources[source].get("latest") is not None
        elif self.type == TriggerConditionType.USER_ACTIVITY:
            activity = self.params.get("activity", "")
            current = user_profile.get("activity", "unknown")
            return activity == current
        elif self.type == TriggerConditionType.IDLE_TIME:
            min_idle = self.params.get("min_seconds", 0)
            max_idle = self.params.get("max_seconds", float("inf"))
            last_interaction = user_profile.get("last_interaction", time.time())
            idle = time.time() - last_interaction
            return min_idle <= idle <= max_idle
        elif self.type == TriggerConditionType.TIME_OF_DAY:
            hour = time.localtime().tm_hour
            from_hour = self.params.get("from_hour", 0)
            to_hour = self.params.get("to_hour", 24)
            return from_hour <= hour < to_hour
        elif self.type == TriggerConditionType.EVENT_COUNT:
            source = self.params.get("source", "")
            min_count = self.params.get("min_count", 0)
            sources = context.get("sources", {})
            count = sources.get(source, {}).get("count", 0)
            return count >= min_count
        elif self.type == TriggerConditionType.CUSTOM:
            check_fn = self.params.get("check_fn")
            if callable(check_fn):
                return check_fn(context, user_profile)
        return False


@dataclass
class TriggerResult:
    triggered: bool = False
    trigger_id: str = ""
    conditions_met: list[str] = field(default_factory=list)
    priority: str = "normal"


class ProactiveTrigger:
    def __init__(self):
        self._triggers: dict[str, dict] = {}
        self._last_fired: dict[str, float] = {}
        self._fire_counts: dict[str, int] = {}

    def register(
        self,
        trigger_id: str,
        conditions: list[TriggerCondition],
        operator: TriggerOperator = TriggerOperator.AND,
        priority: str = "normal",
        cooldown_seconds: float = 300.0,
        max_fires_per_day: int = 10,
    ) -> None:
        self._triggers[trigger_id] = {
            "conditions": conditions,
            "operator": operator,
            "priority": priority,
            "cooldown_seconds": cooldown_seconds,
            "max_fires_per_day": max_fires_per_day,
        }
        self._last_fired[trigger_id] = 0.0
        self._fire_counts[trigger_id] = 0

    def unregister(self, trigger_id: str) -> bool:
        if trigger_id in self._triggers:
            del self._triggers[trigger_id]
            self._last_fired.pop(trigger_id, None)
            self._fire_counts.pop(trigger_id, None)
            return True
        return False

    def evaluate(self, context: dict, user_profile: dict) -> list[TriggerResult]:
        results = []
        now = time.time()
        today = time.strftime("%Y-%m-%d")
        for trigger_id, config in self._triggers.items():
            last_day = self._last_fired.get(f"{trigger_id}_day", "")
            if last_day != today:
                self._fire_counts[trigger_id] = 0
                self._last_fired[f"{trigger_id}_day"] = today
            if self._fire_counts.get(trigger_id, 0) >= config.get("max_fires_per_day", 10):
                continue
            last_fire = self._last_fired.get(trigger_id, 0)
            if (now - last_fire) < config.get("cooldown_seconds", 300.0):
                continue
            conditions = config.get("conditions", [])
            operator = config.get("operator", TriggerOperator.AND)
            met = []
            for cond in conditions:
                if cond.evaluate(context, user_profile):
                    met.append(cond.type.value)
            if operator == TriggerOperator.AND:
                triggered = len(met) == len(conditions) and len(conditions) > 0
            elif operator == TriggerOperator.OR:
                triggered = len(met) > 0
            elif operator == TriggerOperator.NOT:
                triggered = len(met) == 0 and len(conditions) > 0
            else:
                triggered = False
            if triggered:
                self._last_fired[trigger_id] = now
                self._fire_counts[trigger_id] = self._fire_counts.get(trigger_id, 0) + 1
                results.append(TriggerResult(
                    triggered=True,
                    trigger_id=trigger_id,
                    conditions_met=met,
                    priority=config.get("priority", "normal"),
                ))
        results.sort(key=lambda r: {"critical": 0, "high": 1, "normal": 2, "low": 3}.get(r.priority, 2))
        return results

    def list_triggers(self) -> list[dict]:
        result = []
        for tid, config in self._triggers.items():
            result.append({
                "id": tid,
                "condition_count": len(config.get("conditions", [])),
                "operator": config.get("operator", TriggerOperator.AND).value,
                "priority": config.get("priority", "normal"),
                "cooldown_seconds": config.get("cooldown_seconds", 300.0),
                "max_fires_per_day": config.get("max_fires_per_day", 10),
                "fire_count_today": self._fire_counts.get(tid, 0),
                "last_fired": self._last_fired.get(tid, 0),
            })
        return result
