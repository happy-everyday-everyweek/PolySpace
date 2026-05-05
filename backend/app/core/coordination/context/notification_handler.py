import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.core.coordination.context.aggregator import (
    ContextAggregator,
    ContextEvent,
    ContextSource,
    get_context_aggregator,
)

logger = logging.getLogger(__name__)


class NotificationCategory(str, Enum):
    SOCIAL = "social"
    WORK = "work"
    SHOPPING = "shopping"
    TRAVEL = "travel"
    FINANCE = "finance"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class NotificationUrgency(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class ProcessedNotification:
    original_id: str
    category: NotificationCategory
    urgency: NotificationUrgency
    action_items: list[str]
    summary: str
    related_to: list[str]
    time_sensitive: bool
    suggested_action: str
    timestamp: float = field(default_factory=time.time)


class NotificationHandler:
    def __init__(self, aggregator: Optional[ContextAggregator] = None):
        self._aggregator = aggregator or get_context_aggregator()
        self._processed: list[ProcessedNotification] = []
        self._max_processed = 200
        self._dedup_cache: dict[str, float] = {}
        self._dedup_ttl = 60.0

    async def process_notification(self, notif_data: dict) -> ProcessedNotification:
        notif_id = notif_data.get("id", str(time.time()))
        content = notif_data.get("text", notif_data.get("content", ""))
        source = notif_data.get("source", notif_data.get("package", ""))
        if self._is_duplicate(notif_id, content):
            return self._make_default(notif_id, content)
        category = self._classify(source, content)
        urgency = self._assess_urgency(source, content, category)
        action_items = self._extract_actions(content)
        time_sensitive = self._check_time_sensitive(content)
        related = self._find_related(content, category)
        suggested = self._suggest_action(urgency, category, time_sensitive)
        summary = content[:100] if len(content) > 100 else content
        processed = ProcessedNotification(
            original_id=notif_id,
            category=category,
            urgency=urgency,
            action_items=action_items,
            summary=summary,
            related_to=related,
            time_sensitive=time_sensitive,
            suggested_action=suggested,
        )
        self._processed.append(processed)
        if len(self._processed) > self._max_processed:
            self._processed = self._processed[-self._max_processed:]
        self._dedup_cache[notif_id] = time.time()
        event = ContextEvent(
            source=ContextSource.NOTIFICATION,
            data={
                "id": notif_id,
                "category": category.value,
                "urgency": urgency.value,
                "summary": summary,
                "action_items": action_items,
                "time_sensitive": time_sensitive,
                "suggested_action": suggested,
                "source_app": source,
            },
            priority=urgency.value,
        )
        await self._aggregator.ingest(event)
        return processed

    def _is_duplicate(self, notif_id: str, content: str) -> bool:
        now = time.time()
        self._dedup_cache = {k: v for k, v in self._dedup_cache.items() if (now - v) < self._dedup_ttl}
        return notif_id in self._dedup_cache

    def _classify(self, source: str, content: str) -> NotificationCategory:
        source_lower = source.lower()
        social_apps = ("wechat", "whatsapp", "telegram", "qq", "dingtalk", "feishu", "slack", "discord")
        finance_apps = ("bank", "alipay", "wechat_pay", "paypal")
        shopping_apps = ("taobao", "jd", "amazon", "pinduoduo")
        travel_apps = ("ctrip", "didi", "uber", "fligy")
        for app in social_apps:
            if app in source_lower:
                return NotificationCategory.SOCIAL
        for app in finance_apps:
            if app in source_lower:
                return NotificationCategory.FINANCE
        for app in shopping_apps:
            if app in source_lower:
                return NotificationCategory.SHOPPING
        for app in travel_apps:
            if app in source_lower:
                return NotificationCategory.TRAVEL
        work_keywords = ("meeting", "deadline", "project", "task", "review", "approval")
        content_lower = content.lower()
        for kw in work_keywords:
            if kw in content_lower:
                return NotificationCategory.WORK
        return NotificationCategory.UNKNOWN

    def _assess_urgency(self, source: str, content: str, category: NotificationCategory) -> NotificationUrgency:
        urgent_keywords = ("urgent", "emergency", "asap", "immediately", "critical", "breaking")
        content_lower = content.lower()
        for kw in urgent_keywords:
            if kw in content_lower:
                return NotificationUrgency.URGENT
        if category == NotificationCategory.FINANCE:
            return NotificationUrgency.HIGH
        if category == NotificationCategory.WORK:
            high_keywords = ("deadline", "meeting in", "reminder", "due today")
            for kw in high_keywords:
                if kw in content_lower:
                    return NotificationUrgency.HIGH
        return NotificationUrgency.NORMAL

    def _extract_actions(self, content: str) -> list[str]:
        actions = []
        action_patterns = [
            ("please review", "Review requested"),
            ("please approve", "Approval needed"),
            ("meeting at", "Join meeting"),
            ("due by", "Complete before deadline"),
            ("please respond", "Response needed"),
            ("payment required", "Payment needed"),
            ("confirm your", "Confirmation needed"),
        ]
        content_lower = content.lower()
        for pattern, action in action_patterns:
            if pattern in content_lower:
                actions.append(action)
        return actions

    def _check_time_sensitive(self, content: str) -> bool:
        time_keywords = ("today", "now", "asap", "immediately", "in 1 hour", "in 30 min", "urgent", "deadline")
        content_lower = content.lower()
        return any(kw in content_lower for kw in time_keywords)

    def _find_related(self, content: str, category: NotificationCategory) -> list[str]:
        related = []
        for proc in self._processed[-20:]:
            if proc.category == category:
                related.append(proc.original_id)
        return related[:5]

    def _suggest_action(self, urgency: NotificationUrgency, category: NotificationCategory, time_sensitive: bool) -> str:
        if urgency == NotificationUrgency.URGENT:
            return "respond_immediately"
        if time_sensitive:
            return "handle_soon"
        if category == NotificationCategory.WORK:
            return "schedule_time"
        if category == NotificationCategory.SOCIAL:
            return "reply_when_convenient"
        return "review_later"

    async def generate_summary(self, hours: float = 1.0) -> dict:
        now = time.time()
        cutoff = now - hours * 3600
        recent = [p for p in self._processed if p.timestamp >= cutoff]
        by_category = {}
        for p in recent:
            cat = p.category.value
            by_category.setdefault(cat, []).append(p)
        urgent_count = sum(1 for p in recent if p.urgency == NotificationUrgency.URGENT)
        return {
            "period_hours": hours,
            "total_notifications": len(recent),
            "urgent_count": urgent_count,
            "by_category": {cat: len(items) for cat, items in by_category.items()},
            "action_items": [a for p in recent for a in p.action_items],
            "suggested_priority_order": sorted(
                by_category.keys(),
                key=lambda c: sum(1 for p in by_category[c] if p.urgency in (NotificationUrgency.URGENT, NotificationUrgency.HIGH)),
                reverse=True,
            ),
        }

    def _make_default(self, notif_id: str, content: str) -> ProcessedNotification:
        return ProcessedNotification(
            original_id=notif_id,
            category=NotificationCategory.UNKNOWN,
            urgency=NotificationUrgency.LOW,
            action_items=[],
            summary=content[:100],
            related_to=[],
            time_sensitive=False,
            suggested_action="review_later",
        )


_handler: Optional[NotificationHandler] = None


def get_notification_handler() -> NotificationHandler:
    global _handler
    if _handler is None:
        _handler = NotificationHandler()
    return _handler
