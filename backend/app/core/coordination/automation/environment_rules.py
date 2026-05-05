import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AutomationRule:
    rule_id: str
    name: str
    condition: dict
    action: dict
    enabled: bool = True
    fire_count: int = 0
    last_fired: float = 0.0
    cooldown_seconds: float = 300.0
    created_at: float = field(default_factory=time.time)
    display_name: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "display_name": self.display_name or self.name,
            "description": self.description,
            "condition": self.condition,
            "action": self.action,
            "enabled": self.enabled,
            "fire_count": self.fire_count,
            "last_fired": self.last_fired,
        }


BUILTIN_TEMPLATES = [
    {
        "name": "arrive_office",
        "display_name": "到达办公室",
        "description": "到达办公室时自动静音、打开工作文档、显示待办",
        "condition": {"location": "office"},
        "action": {"mute_phone": True, "open_work_docs": True, "show_todos": True},
    },
    {
        "name": "leave_office",
        "display_name": "离开办公室",
        "description": "离开办公室时发送日报、启用通勤模式",
        "condition": {"location": "leaving_office"},
        "action": {"send_daily_summary": True, "enable_commute_mode": True},
    },
    {
        "name": "headphones_connected",
        "display_name": "耳机已连接",
        "description": "检测到耳机连接时询问是否播放媒体",
        "condition": {"device": "headphones_connected"},
        "action": {"ask_play_media": True},
    },
    {
        "name": "low_battery",
        "display_name": "低电量",
        "description": "电量低于20%时启用省电模式、暂停非紧急同步",
        "condition": {"battery_below": 20},
        "action": {"enable_power_saver": True, "pause_non_urgent_sync": True},
    },
    {
        "name": "meeting_started",
        "display_name": "会议开始",
        "description": "日历会议开始时自动静音、开始会议笔记",
        "condition": {"calendar": "meeting_start"},
        "action": {"mute_phone": True, "start_meeting_notes": True},
    },
    {
        "name": "flight_delayed",
        "display_name": "航班延误",
        "description": "检测到航班延误时搜索替代方案、通知接机人",
        "condition": {"notification": "flight_delay"},
        "action": {"search_alternatives": True, "notify_pickup": True},
    },
    {
        "name": "package_delivered",
        "display_name": "快递到达",
        "description": "检测到快递到达时提醒取件、更新待办",
        "condition": {"notification": "delivery"},
        "action": {"remind_pickup": True, "update_todo": True},
    },
    {
        "name": "bill_received",
        "display_name": "账单到达",
        "description": "检测到账单时自动分类消费、提醒付款",
        "condition": {"notification": "bill"},
        "action": {"categorize_expense": True, "remind_payment": True},
    },
]


class EnvironmentRulesEngine:
    def __init__(self):
        self._rules: dict[str, AutomationRule] = {}
        self._execution_log: list[dict] = []
        self._max_log = 100
        for tmpl in BUILTIN_TEMPLATES:
            rule_id = f"rule_{tmpl['name']}"
            self._rules[rule_id] = AutomationRule(
                rule_id=rule_id,
                name=tmpl["name"],
                condition=tmpl["condition"],
                action=tmpl["action"],
                display_name=tmpl.get("display_name", ""),
                description=tmpl.get("description", ""),
            )

    def add_rule(self, name: str, condition: dict, action: dict, cooldown: float = 300.0) -> str:
        rule_id = f"rule_custom_{int(time.time())}_{hash(name) % 1000}"
        rule = AutomationRule(rule_id=rule_id, name=name, condition=condition, action=action, cooldown_seconds=cooldown)
        self._rules[rule_id] = rule
        return rule_id

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def toggle_rule(self, rule_id: str, enabled: bool) -> bool:
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = enabled
            return True
        return False

    async def evaluate(self, context: dict, user_profile: dict) -> list[dict]:
        results = []
        now = time.time()
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if (now - rule.last_fired) < rule.cooldown_seconds:
                continue
            if self._matches(rule.condition, context, user_profile):
                rule.fire_count += 1
                rule.last_fired = now
                execution = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "action": rule.action,
                    "timestamp": now,
                }
                results.append(execution)
                self._execution_log.append(execution)
                if len(self._execution_log) > self._max_log:
                    self._execution_log = self._execution_log[-self._max_log:]
        return results

    def _matches(self, condition: dict, context: dict, user_profile: dict) -> bool:
        sources = context.get("sources", {})
        for key, value in condition.items():
            if key == "location":
                loc_data = sources.get("location", {}).get("latest", {})
                if loc_data.get("location") != value:
                    return False
            elif key == "device":
                device_data = sources.get("device_state", {}).get("latest", {})
                if not device_data.get(value, False):
                    return False
            elif key == "battery_below":
                device_data = sources.get("device_state", {}).get("latest", {})
                if device_data.get("battery_level", 100) >= value:
                    return False
            elif key == "calendar":
                cal_data = sources.get("calendar", {}).get("latest", {})
                if value == "meeting_start" and not cal_data.get("is_meeting"):
                    return False
            elif key == "notification":
                notif_data = sources.get("notification", {}).get("latest", {})
                if notif_data.get("category") != value:
                    return False
            elif key == "time_range":
                hour = time.localtime().tm_hour
                if not (value.get("from", 0) <= hour < value.get("to", 24)):
                    return False
        return True

    def list_rules(self, enabled_only: bool = False) -> list[dict]:
        rules = self._rules.values()
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return [r.to_dict() for r in rules]

    def get_execution_log(self, limit: int = 20) -> list[dict]:
        return self._execution_log[-limit:]


_engine: Optional[EnvironmentRulesEngine] = None


def get_environment_rules_engine() -> EnvironmentRulesEngine:
    global _engine
    if _engine is None:
        _engine = EnvironmentRulesEngine()
    return _engine
