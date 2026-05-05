import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    name: str
    display_name: str
    description: str
    category: str
    enabled: bool = True
    cooldown_seconds: float = 300.0
    max_fires_per_day: int = 10
    priority: str = "normal"
    channels: list[str] = field(default_factory=lambda: ["notification", "websocket"])
    trigger_conditions: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    fire_count: int = 0
    accept_count: int = 0
    ignore_count: int = 0
    negative_count: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "enabled": self.enabled,
            "cooldown_seconds": self.cooldown_seconds,
            "max_fires_per_day": self.max_fires_per_day,
            "priority": self.priority,
            "channels": self.channels,
            "fire_count": self.fire_count,
            "accept_count": self.accept_count,
            "ignore_count": self.ignore_count,
            "negative_count": self.negative_count,
            "accept_rate": self.accept_count / self.fire_count if self.fire_count > 0 else 0.0,
        }


class ProactiveServiceRegistry:
    def __init__(self):
        self._services: dict[str, ServiceConfig] = {}
        self._register_built_in_services()

    def _register_built_in_services(self) -> None:
        built_in = [
            ServiceConfig(
                name="daily_briefing", display_name="每日简报",
                description="早间/午间/晚间简报推送",
                category="work", cooldown_seconds=3600.0,
                max_fires_per_day=3, priority="important",
            ),
            ServiceConfig(
                name="meeting_prep", display_name="会议准备",
                description="会议前推送相关信息",
                category="work", cooldown_seconds=600.0,
                max_fires_per_day=5, priority="important",
            ),
            ServiceConfig(
                name="deadline_guard", display_name="截止日期守护",
                description="截止日期临近提醒",
                category="work", cooldown_seconds=1800.0,
                max_fires_per_day=8, priority="urgent",
            ),
            ServiceConfig(
                name="focus_protector", display_name="专注守护",
                description="深度工作时过滤非紧急通知",
                category="work", cooldown_seconds=600.0,
                max_fires_per_day=6, priority="important",
            ),
            ServiceConfig(
                name="smart_followup", display_name="智能跟进",
                description="检测未执行承诺和未回复消息",
                category="work", cooldown_seconds=900.0,
                max_fires_per_day=5, priority="suggested",
            ),
            ServiceConfig(
                name="context_news", display_name="上下文新闻",
                description="根据工作内容推荐相关新闻",
                category="info", cooldown_seconds=7200.0,
                max_fires_per_day=3, priority="suggested",
            ),
            ServiceConfig(
                name="doc_suggestion", display_name="文档建议",
                description="根据当前内容推荐相关文档",
                category="info", cooldown_seconds=1800.0,
                max_fires_per_day=5, priority="suggested",
            ),
            ServiceConfig(
                name="learning_path", display_name="学习路径",
                description="检测知识盲区推荐学习资源",
                category="info", cooldown_seconds=14400.0,
                max_fires_per_day=2, priority="suggested",
            ),
            ServiceConfig(
                name="wellness_guard", display_name="健康守护",
                description="久坐/用眼/饮水/作息提醒",
                category="life", cooldown_seconds=1800.0,
                max_fires_per_day=8, priority="suggested",
            ),
            ServiceConfig(
                name="commute_assistant", display_name="通勤助手",
                description="通勤时间和路况提醒",
                category="life", cooldown_seconds=3600.0,
                max_fires_per_day=4, priority="suggested",
            ),
            ServiceConfig(
                name="expense_tracker", display_name="消费追踪",
                description="消费识别和趋势分析",
                category="life", cooldown_seconds=7200.0,
                max_fires_per_day=3, priority="suggested",
            ),
            ServiceConfig(
                name="social_reminder", display_name="社交提醒",
                description="生日/纪念日/久未联系人提醒",
                category="life", cooldown_seconds=86400.0,
                max_fires_per_day=2, priority="suggested",
            ),
            ServiceConfig(
                name="weather_advisor", display_name="天气顾问",
                description="恶劣天气预警和建议",
                category="env", cooldown_seconds=3600.0,
                max_fires_per_day=4, priority="important",
            ),
            ServiceConfig(
                name="device_health", display_name="设备健康",
                description="电量/存储/网络异常提醒",
                category="env", cooldown_seconds=1800.0,
                max_fires_per_day=5, priority="important",
            ),
            ServiceConfig(
                name="security_guard", display_name="安全守护",
                description="异常登录/可疑链接预警",
                category="env", cooldown_seconds=300.0,
                max_fires_per_day=10, priority="urgent",
            ),
            ServiceConfig(
                name="idea_spark", display_name="灵感火花",
                description="基于工作内容生成创意建议",
                category="creative", cooldown_seconds=7200.0,
                max_fires_per_day=3, priority="suggested",
            ),
            ServiceConfig(
                name="writing_coach", display_name="写作教练",
                description="文档编辑改进建议",
                category="creative", cooldown_seconds=1800.0,
                max_fires_per_day=5, priority="suggested",
            ),
            ServiceConfig(
                name="data_insight", display_name="数据洞察",
                description="数据异常和趋势发现",
                category="creative", cooldown_seconds=3600.0,
                max_fires_per_day=3, priority="suggested",
            ),
            ServiceConfig(
                name="proactive_greeting", display_name="主动问候",
                description="空闲时主动发起友好问候",
                category="social", cooldown_seconds=3600.0,
                max_fires_per_day=5, priority="chitchat",
            ),
            ServiceConfig(
                name="clipboard_insight", display_name="剪贴板洞察",
                description="剪贴板内容智能分析",
                category="info", cooldown_seconds=300.0,
                max_fires_per_day=10, priority="suggested",
            ),
        ]
        for svc in built_in:
            self._services[svc.name] = svc

    def register(self, config: ServiceConfig) -> None:
        self._services[config.name] = config

    def unregister(self, name: str) -> bool:
        if name in self._services:
            del self._services[name]
            return True
        return False

    def get_service(self, name: str) -> Optional[dict]:
        svc = self._services.get(name)
        return svc.to_dict() if svc else None

    def toggle_service(self, name: str, enabled: bool) -> bool:
        svc = self._services.get(name)
        if svc:
            svc.enabled = enabled
            return True
        return False

    def record_fire(self, name: str) -> None:
        svc = self._services.get(name)
        if svc:
            svc.fire_count += 1

    def record_feedback(self, name: str, feedback: str) -> None:
        svc = self._services.get(name)
        if svc:
            if feedback == "accepted":
                svc.accept_count += 1
            elif feedback == "ignored":
                svc.ignore_count += 1
            elif feedback == "negative":
                svc.negative_count += 1

    def list_services(self, category: Optional[str] = None, enabled_only: bool = False) -> list[dict]:
        results = []
        for svc in self._services.values():
            if category and svc.category != category:
                continue
            if enabled_only and not svc.enabled:
                continue
            results.append(svc.to_dict())
        return results

    def get_categories(self) -> list[dict]:
        cats = {}
        for svc in self._services.values():
            if svc.category not in cats:
                cats[svc.category] = {"count": 0, "enabled": 0}
            cats[svc.category]["count"] += 1
            if svc.enabled:
                cats[svc.category]["enabled"] += 1
        return [{"category": k, **v} for k, v in cats.items()]

    def auto_optimize(self) -> list[str]:
        adjustments = []
        for svc in self._services.values():
            if svc.fire_count < 5:
                continue
            accept_rate = svc.accept_count / svc.fire_count
            if accept_rate < 0.2 and svc.enabled:
                svc.cooldown_seconds *= 1.5
                adjustments.append(f"{svc.display_name}: cooldown increased (low accept rate {accept_rate:.1%})")
            elif accept_rate > 0.7 and svc.enabled:
                svc.cooldown_seconds = max(60.0, svc.cooldown_seconds * 0.8)
                adjustments.append(f"{svc.display_name}: cooldown decreased (high accept rate {accept_rate:.1%})")
            if svc.negative_count > svc.fire_count * 0.3:
                svc.enabled = False
                adjustments.append(f"{svc.display_name}: auto-disabled (too many negative feedbacks)")
        return adjustments


_registry: Optional[ProactiveServiceRegistry] = None


def get_service_registry() -> ProactiveServiceRegistry:
    global _registry
    if _registry is None:
        _registry = ProactiveServiceRegistry()
    return _registry
