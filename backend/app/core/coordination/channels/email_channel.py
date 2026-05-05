import logging
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str
    html_body: str = ""
    priority: str = "normal"
    sent_at: float = 0.0
    status: str = "pending"

    def to_dict(self) -> dict:
        return {
            "to": self.to,
            "subject": self.subject,
            "priority": self.priority,
            "sent_at": self.sent_at,
            "status": self.status,
        }


class EmailChannel:
    def __init__(self):
        self._sent: list[EmailMessage] = []
        self._max_sent = 100
        self._daily_count: dict[str, int] = {}
        self._max_daily = 5
        self._templates: dict[str, str] = {
            "daily_briefing": "<h2>Daily Briefing</h2><p>{content}</p>",
            "weekly_summary": "<h2>Weekly Summary</h2><p>{content}</p>",
            "urgent_alert": "<h2 style='color:red'>Urgent Alert</h2><p>{content}</p>",
        }

    async def send(self, to: str, subject: str, body: str, html_body: str = "", priority: str = "normal") -> EmailMessage:
        today = time.strftime("%Y-%m-%d")
        self._daily_count[today] = self._daily_count.get(today, 0) + 1
        if self._daily_count[today] > self._max_daily:
            logger.warning(f"Email daily limit reached ({self._max_daily})")
            return EmailMessage(to=to, subject=subject, body=body, html_body=html_body, priority=priority, status="rate_limited")
        msg = EmailMessage(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body or self._render_template("daily_briefing", content=body),
            priority=priority,
            sent_at=time.time(),
            status="sent",
        )
        self._sent.append(msg)
        if len(self._sent) > self._max_sent:
            self._sent = self._sent[-self._max_sent:]
        logger.info(f"Email sent to {to}: {subject}")
        return msg

    def _render_template(self, template_name: str, **kwargs) -> str:
        template = self._templates.get(template_name, "<p>{content}</p>")
        return template.format(**kwargs)

    def get_sent_history(self, limit: int = 20) -> list[dict]:
        return [m.to_dict() for m in self._sent[-limit:]]

    def get_daily_count(self) -> int:
        today = time.strftime("%Y-%m-%d")
        return self._daily_count.get(today, 0)


_channel: Optional[EmailChannel] = None


def get_email_channel() -> EmailChannel:
    global _channel
    if _channel is None:
        _channel = EmailChannel()
    return _channel
