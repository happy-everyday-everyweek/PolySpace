import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from .models import EmailCategory, EmailPriority
from .service import get_email_service

logger = logging.getLogger(__name__)


@dataclass
class AIEmailDecision:
    email_id: int
    action: str
    category: str
    priority: str
    reason: str
    auto_reply_content: Optional[str] = None
    extracted_tasks: list[dict] = field(default_factory=list)
    schedule_info: Optional[dict] = None
    notification_message: Optional[str] = None
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "email_id": self.email_id,
            "action": self.action,
            "category": self.category,
            "priority": self.priority,
            "reason": self.reason,
            "auto_reply_content": self.auto_reply_content,
            "extracted_tasks": self.extracted_tasks,
            "schedule_info": self.schedule_info,
            "notification_message": self.notification_message,
            "confidence": self.confidence,
        }


@dataclass
class AIEmailRecord:
    email_id: int
    account_id: int
    subject: str
    sender: str
    decision: Optional[AIEmailDecision] = None
    processed: bool = False
    processed_at: Optional[float] = None
    user_notified: bool = False
    auto_replied: bool = False
    tasks_created: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "email_id": self.email_id,
            "account_id": self.account_id,
            "subject": self.subject,
            "sender": self.sender,
            "processed": self.processed,
            "processed_at": self.processed_at,
            "user_notified": self.user_notified,
            "auto_replied": self.auto_replied,
            "tasks_created": self.tasks_created,
        }
        if self.decision:
            d["decision"] = self.decision.to_dict()
        return d


class AIEmailService:
    def __init__(self):
        self._dispatcher = None
        self._records: dict[int, AIEmailRecord] = {}
        self._processed_ids: set[int] = set()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._poll_interval = 60
        self._on_decision_callbacks: list = []
        self._auto_reply_enabled = True
        self._task_extraction_enabled = True
        self._notification_enabled = True

    def _get_dispatcher(self):
        if self._dispatcher is None:
            from app.core.llm.dispatcher import ModelDispatcher
            self._dispatcher = ModelDispatcher()
        return self._dispatcher

    def on_decision(self, callback):
        self._on_decision_callbacks.append(callback)

    async def _notify_decision(self, decision: AIEmailDecision, record: AIEmailRecord):
        for cb in self._on_decision_callbacks:
            try:
                await cb(decision, record)
            except Exception as e:
                logger.error(f"Decision callback error: {e}")

    async def analyze_email(self, email_data: dict) -> AIEmailDecision:
        email_id = email_data.get("id", 0)
        subject = email_data.get("subject", "")
        sender = email_data.get("sender", "") or ""
        body = email_data.get("text", "") or email_data.get("body_text", "") or email_data.get("html", "") or ""

        try:
            decision = await self._llm_analyze(email_id, subject, sender, body)
            if decision.confidence < 0.3:
                fallback = self._keyword_analyze(email_id, subject, sender, body)
                decision.category = fallback.category
                decision.priority = fallback.priority
                decision.confidence = max(decision.confidence, fallback.confidence)
            return decision
        except Exception as e:
            logger.error(f"AI email analysis failed, using keyword fallback: {e}")
            return self._keyword_analyze(email_id, subject, sender, body)

    async def _llm_analyze(self, email_id: int, subject: str, sender: str, body: str) -> AIEmailDecision:
        from app.core.llm.dispatcher import TaskCategory
        dispatcher = self._get_dispatcher()
        body_preview = body[:2000] if body else ""

        prompt = """You are an AI email assistant. Analyze the email and decide what action to take.

Available actions: auto_reply, extract_task, notify_user, schedule_event, forward_to_user, archive, ignore
Categories: work, personal, promotional, social, financial, travel, shopping, notification, system, unknown
Priorities: urgent, high, normal, low

Return JSON:
{
  "action": "one of the actions above",
  "category": "one of the categories above",
  "priority": "one of the priorities above",
  "reason": "brief explanation",
  "auto_reply_content": "reply text if action is auto_reply, else null",
  "extracted_tasks": [{"title": "...", "description": "...", \
"priority": "high/medium/low", "due_hint": "optional due date hint"}],
  "schedule_info": {"title": "...", "suggested_time": "...", "duration_minutes": 60} or null,
  "notification_message": "brief notification for user if action is notify_user or forward_to_user",
  "confidence": 0.0-1.0
}"""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Subject: {subject}\nFrom: {sender}\n\n{body_preview}"},
        ]

        response = await dispatcher.dispatch(TaskCategory.INTENT, messages=messages)
        content = response.choices[0].message.content
        result = json.loads(content)
        return AIEmailDecision(
            email_id=email_id,
            action=result.get("action", "notify_user"),
            category=result.get("category", "unknown"),
            priority=result.get("priority", "normal"),
            reason=result.get("reason", ""),
            auto_reply_content=result.get("auto_reply_content"),
            extracted_tasks=result.get("extracted_tasks", []),
            schedule_info=result.get("schedule_info"),
            notification_message=result.get("notification_message"),
            confidence=result.get("confidence", 0.5),
        )

    def _keyword_analyze(self, email_id: int, subject: str, sender: str, body: str) -> AIEmailDecision:
        all_text = f"{subject} {sender} {body}".lower()

        category = self._keyword_categorize(all_text)
        priority = self._keyword_priority(all_text)
        action = self._keyword_action(all_text, category, priority)

        auto_reply_content = None
        if action == "auto_reply":
            auto_reply_content = "Thank you for your email. I will review it and respond shortly."

        extracted_tasks = []
        if action in ("extract_task", "notify_user"):
            extracted_tasks = self._extract_action_items(body)

        notification_message = None
        if action in ("notify_user", "forward_to_user"):
            notification_message = f"New {priority} priority email from {sender}: {subject[:80]}"

        return AIEmailDecision(
            email_id=email_id,
            action=action,
            category=category,
            priority=priority,
            reason=f"Keyword-based classification: {category}/{priority}",
            auto_reply_content=auto_reply_content,
            extracted_tasks=extracted_tasks,
            notification_message=notification_message,
            confidence=0.6,
        )

    def _keyword_categorize(self, text: str) -> str:
        keywords_map = {
            EmailCategory.WORK.value: [
                "meeting", "project", "report", "deadline",
                "会议", "项目", "报告", "工作", "任务",
            ],
            EmailCategory.PROMOTIONAL.value: [
                "sale", "discount", "offer", "deal",
                "优惠", "促销", "折扣",
            ],
            EmailCategory.SOCIAL.value: [
                "invite", "party", "friend", "邀请", "朋友", "聚会",
            ],
            EmailCategory.FINANCIAL.value: [
                "bill", "payment", "bank", "invoice",
                "账单", "支付", "银行", "发票",
            ],
            EmailCategory.TRAVEL.value: [
                "flight", "hotel", "booking", "航班", "酒店", "预订",
            ],
            EmailCategory.SHOPPING.value: [
                "order", "delivery", "purchase", "shipping",
                "订单", "配送", "购买",
            ],
            EmailCategory.NOTIFICATION.value: [
                "notification", "alert", "reminder", "通知", "提醒", "验证",
            ],
            EmailCategory.SYSTEM.value: [
                "noreply", "no-reply", "automated", "系统", "自动",
            ],
        }
        for cat, keywords in keywords_map.items():
            if any(kw in text for kw in keywords):
                return cat
        return EmailCategory.UNKNOWN.value

    def _keyword_priority(self, text: str) -> str:
        urgent_kw = ["urgent", "immediately", "asap", "critical", "紧急", "立即", "重要"]
        high_kw = ["important", "please reply", "soon", "today", "重要", "请回复", "尽快"]
        if any(kw in text for kw in urgent_kw):
            return EmailPriority.URGENT.value
        if any(kw in text for kw in high_kw):
            return EmailPriority.HIGH.value
        return EmailPriority.NORMAL.value

    def _keyword_action(self, text: str, category: str, priority: str) -> str:
        if priority == EmailPriority.URGENT.value:
            return "notify_user"
        if category == EmailCategory.PROMOTIONAL.value:
            return "archive"
        if category == EmailCategory.SYSTEM.value:
            return "archive"
        if category == EmailCategory.WORK.value:
            return "extract_task"
        if priority == EmailPriority.HIGH.value:
            return "forward_to_user"
        return "notify_user"

    def _extract_action_items(self, text: str) -> list[dict]:
        items = []
        patterns = [
            r"请(.+?)[。\n]",
            r"需要(.+?)[。\n]",
            r"务必(.+?)[。\n]",
            r"Please (.+?)[.\n]",
            r"Need to (.+?)[.\n]",
            r"Must (.+?)[.\n]",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if 5 < len(match) < 200:
                    items.append({"title": match.strip(), "priority": "medium"})
        return items[:5]

    async def process_new_email(self, email_data: dict, account_id: int) -> AIEmailRecord:
        email_id = email_data.get("id", 0)
        if email_id in self._processed_ids:
            return self._records.get(email_id, AIEmailRecord(
                email_id=email_id, account_id=account_id,
                subject=email_data.get("subject", ""), sender=email_data.get("sender", ""),
            ))

        record = AIEmailRecord(
            email_id=email_id, account_id=account_id,
            subject=email_data.get("subject", ""), sender=email_data.get("sender", ""),
        )
        self._records[email_id] = record
        self._processed_ids.add(email_id)

        decision = await self.analyze_email(email_data)
        record.decision = decision

        email_svc = get_email_service()
        await email_svc.update_email_category_priority(
            email_id, category=decision.category, priority=decision.priority
        )

        if decision.action == "auto_reply" and self._auto_reply_enabled and decision.auto_reply_content:
            await self._execute_auto_reply(account_id, email_data, decision.auto_reply_content)
            record.auto_replied = True

        if decision.action == "extract_task" and self._task_extraction_enabled and decision.extracted_tasks:
            task_ids = await self._execute_task_extraction(decision.extracted_tasks)
            record.tasks_created = task_ids

        if decision.action == "schedule_event" and decision.schedule_info:
            await self._execute_schedule(decision.schedule_info)

        if decision.action in ("notify_user", "forward_to_user") and self._notification_enabled:
            record.user_notified = True

        record.processed = True
        record.processed_at = time.time()

        await self._notify_decision(decision, record)
        return record

    async def _execute_auto_reply(self, account_id: int, original_email: dict, reply_content: str):
        try:
            from .models import SendMessageInput
            email_svc = get_email_service()
            sender = original_email.get("sender", "")
            if isinstance(sender, str) and "<" in sender:
                import re
                match = re.search(r'<(.+?)>', sender)
                sender = match.group(1) if match else sender
            await email_svc.send_email(
                account_id,
                SendMessageInput(
                    to=sender,
                    subject=f"Re: {original_email.get('subject', '')}",
                    body=reply_content,
                    in_reply_to=original_email.get("message_id", ""),
                )
            )
            logger.info(f"Auto-replied to email from {sender}")
        except Exception as e:
            logger.error(f"Auto-reply failed: {e}")

    async def _execute_task_extraction(self, tasks: list[dict]) -> list[str]:
        task_ids = []
        for task in tasks:
            task_id = f"task_{int(time.time())}_{len(task_ids)}"
            task_ids.append(task_id)
            logger.info(f"Extracted task: {task.get('title')} (priority: {task.get('priority')})")
        return task_ids

    async def _execute_schedule(self, schedule_info: dict):
        logger.info(f"Schedule event: {schedule_info.get('title')} at {schedule_info.get('suggested_time')}")

    async def check_new_emails(self) -> list[AIEmailRecord]:
        try:
            email_svc = get_email_service()
            accounts = await email_svc.list_accounts()
            new_records = []
            for account in accounts:
                account_id = account.get("id")
                if not account_id:
                    continue
                try:
                    await email_svc.sync_emails(account_id)
                    emails = await email_svc.fetch_emails(account_id, folder="INBOX", limit=10)
                    for em in emails:
                        if em.get("id") not in self._processed_ids and not em.get("is_read", False):
                            record = await self.process_new_email(em, account_id)
                            new_records.append(record)
                except Exception as e:
                    logger.error(f"Error checking account {account_id}: {e}")
            return new_records
        except Exception as e:
            logger.error(f"Email check failed: {e}")
            return []

    async def start_monitoring(self, poll_interval: int = 60):
        if self._monitoring:
            return
        self._monitoring = True
        self._poll_interval = poll_interval
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"AI email monitoring started (interval: {poll_interval}s)")

    async def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        logger.info("AI email monitoring stopped")

    async def _monitor_loop(self):
        while self._monitoring:
            try:
                await self.check_new_emails()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
            await asyncio.sleep(self._poll_interval)

    def get_records(self, limit: int = 50) -> list[dict]:
        records = sorted(self._records.values(), key=lambda r: r.processed_at or 0, reverse=True)
        return [r.to_dict() for r in records[:limit]]

    def get_stats(self) -> dict:
        total = len(self._records)
        auto_replied = sum(1 for r in self._records.values() if r.auto_replied)
        tasks_extracted = sum(len(r.tasks_created) for r in self._records.values())
        user_notified = sum(1 for r in self._records.values() if r.user_notified)
        categories = {}
        for r in self._records.values():
            if r.decision:
                cat = r.decision.category
                categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_processed": total,
            "auto_replied": auto_replied,
            "tasks_extracted": tasks_extracted,
            "user_notified": user_notified,
            "monitoring": self._monitoring,
            "categories": categories,
        }

    def set_config(self, auto_reply: bool = True, task_extraction: bool = True, notification: bool = True):
        self._auto_reply_enabled = auto_reply
        self._task_extraction_enabled = task_extraction
        self._notification_enabled = notification


_ai_email_service: Optional[AIEmailService] = None


def get_ai_email_service() -> AIEmailService:
    global _ai_email_service
    if _ai_email_service is None:
        _ai_email_service = AIEmailService()
    return _ai_email_service
