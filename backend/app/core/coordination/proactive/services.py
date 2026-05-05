import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class ProactiveServiceBase:
    service_name: str = ""
    display_name: str = ""
    description: str = ""
    category: str = ""

    def __init__(self, llm_dispatcher=None):
        self._dispatcher = llm_dispatcher

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return f"[{self.service_name}] Notification"

    def _get_dispatcher(self):
        if self._dispatcher is None:
            from app.core.llm.dispatcher import get_model_dispatcher
            self._dispatcher = get_model_dispatcher()
        return self._dispatcher


class DailyBriefingService(ProactiveServiceBase):
    service_name = "daily_briefing"
    display_name = "每日简报"
    category = "work"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        hour = time.localtime().tm_hour
        if hour in (8, 12, 18):
            return {"should_fire": True, "period": "morning" if hour == 8 else "noon" if hour == 12 else "evening"}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        hour = time.localtime().tm_hour
        period = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        summary = context.get("summary", {})
        sources = context.get("sources", {})
        period_label = (
            "Morning" if period == "morning"
            else "Afternoon" if period == "afternoon"
            else "Evening"
        )
        parts = [f"{period_label} briefing:"]
        if "calendar" in sources:
            parts.append("- You have upcoming calendar events")
        if "email" in sources:
            parts.append("- You have unread emails")
        if "notification" in sources:
            urgent = summary.get("urgent_event_count", 0)
            if urgent:
                parts.append(f"- {urgent} urgent notification(s) need attention")
        parts.append(f"- Active context sources: {len(sources)}")
        return "\n".join(parts)


class MeetingPrepService(ProactiveServiceBase):
    service_name = "meeting_prep"
    display_name = "会议准备"
    category = "work"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        sources = context.get("sources", {})
        cal_data = sources.get("calendar", {}).get("latest", {})
        if cal_data and cal_data.get("is_meeting"):
            start_time = cal_data.get("start_time", 0)
            if 0 < (start_time - time.time()) < 900:
                return {"should_fire": True, "meeting_title": cal_data.get("title", "Meeting")}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        sources = context.get("sources", {})
        cal_data = sources.get("calendar", {}).get("latest", {})
        title = cal_data.get("title", "Upcoming meeting")
        return f"Your meeting '{title}' starts in 15 minutes. Prepare your notes and materials."


class DeadlineGuardService(ProactiveServiceBase):
    service_name = "deadline_guard"
    display_name = "截止日期守护"
    category = "work"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        sources = context.get("sources", {})
        if "notification" in sources:
            notif_data = sources["notification"].get("latest", {})
            if notif_data.get("urgency") in ("urgent", "high"):
                return {"should_fire": True, "urgency": notif_data["urgency"]}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "You have approaching deadlines. Review your task list and prioritize accordingly."


class FocusProtectorService(ProactiveServiceBase):
    service_name = "focus_protector"
    display_name = "专注守护"
    category = "work"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        if user_profile.get("activity") == "focused":
            return {"should_fire": True, "duration": "extended"}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        summary = context.get("summary", {})
        urgent = summary.get("urgent_event_count", 0)
        if urgent > 0:
            return f"You are in focus mode. {urgent} urgent notification(s) are being held."
        return "You are in focus mode. Non-urgent notifications are being held."


class SmartFollowupService(ProactiveServiceBase):
    service_name = "smart_followup"
    display_name = "智能跟进"
    category = "work"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        sources = context.get("sources", {})
        if "chat" in sources:
            chat_data = sources["chat"].get("latest", {})
            if chat_data.get("has_pending_reply"):
                return {"should_fire": True, "contact": chat_data.get("contact", "someone")}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "You have messages that may need follow-up. Check your recent conversations."


class ContextNewsService(ProactiveServiceBase):
    service_name = "context_news"
    display_name = "上下文新闻"
    category = "info"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        if user_profile.get("attention") in ("document", "browser"):
            return {"should_fire": True}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "Based on your current work, here are some relevant articles you might find useful."


class DocSuggestionService(ProactiveServiceBase):
    service_name = "doc_suggestion"
    display_name = "文档建议"
    category = "info"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        if user_profile.get("attention") == "document":
            return {"should_fire": True}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "Based on your current document, you might find these related resources helpful."


class LearningPathService(ProactiveServiceBase):
    service_name = "learning_path"
    display_name = "学习路径"
    category = "info"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "I noticed some knowledge gaps in your recent work. Here are some learning resources."


class WellnessGuardService(ProactiveServiceBase):
    service_name = "wellness_guard"
    display_name = "健康守护"
    category = "life"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        if user_profile.get("activity") == "focused":
            return {"should_fire": True, "type": "sedentary"}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "You have been working for a while. Consider taking a short break to stretch and rest your eyes."


class CommuteAssistantService(ProactiveServiceBase):
    service_name = "commute_assistant"
    display_name = "通勤助手"
    category = "life"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        hour = time.localtime().tm_hour
        if hour in (7, 8, 17, 18):
            return {"should_fire": True, "commute_hour": hour}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        hour = time.localtime().tm_hour
        direction = "morning" if hour < 12 else "evening"
        return f"Commute time approaching ({direction}). Check traffic conditions before you leave."


class ExpenseTrackerService(ProactiveServiceBase):
    service_name = "expense_tracker"
    display_name = "消费追踪"
    category = "life"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        sources = context.get("sources", {})
        if "notification" in sources:
            notif_data = sources["notification"].get("latest", {})
            if notif_data.get("category") == "finance":
                return {"should_fire": True}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "New transaction detected. Your spending summary has been updated."


class SocialReminderService(ProactiveServiceBase):
    service_name = "social_reminder"
    display_name = "社交提醒"
    category = "life"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "You have upcoming social events. Check your calendar for details."


class WeatherAdvisorService(ProactiveServiceBase):
    service_name = "weather_advisor"
    display_name = "天气顾问"
    category = "env"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "Weather advisory: Check today's weather conditions before heading out."


class DeviceHealthService(ProactiveServiceBase):
    service_name = "device_health"
    display_name = "设备健康"
    category = "env"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        sources = context.get("sources", {})
        if "device_state" in sources:
            device_data = sources["device_state"].get("latest", {})
            battery = device_data.get("battery_level", 100)
            if battery < 20:
                return {"should_fire": True, "battery": battery}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        sources = context.get("sources", {})
        device_data = sources.get("device_state", {}).get("latest", {})
        battery = device_data.get("battery_level", 0)
        return f"Your device battery is at {battery}%. Consider charging soon."


class SecurityGuardService(ProactiveServiceBase):
    service_name = "security_guard"
    display_name = "安全守护"
    category = "env"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "Security alert detected. Please review your recent activity."


class IdeaSparkService(ProactiveServiceBase):
    service_name = "idea_spark"
    display_name = "灵感火花"
    category = "creative"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        if user_profile.get("activity") in ("working", "focused"):
            return {"should_fire": True}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "Here is a creative idea based on your current work context."


class WritingCoachService(ProactiveServiceBase):
    service_name = "writing_coach"
    display_name = "写作教练"
    category = "creative"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        if user_profile.get("attention") == "document":
            return {"should_fire": True}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "Writing suggestion: Consider reviewing your document structure and clarity."


class DataInsightService(ProactiveServiceBase):
    service_name = "data_insight"
    display_name = "数据洞察"
    category = "creative"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "Data insight: Review your recent data for interesting patterns and trends."


class ProactiveGreetingService(ProactiveServiceBase):
    service_name = "proactive_greeting"
    display_name = "主动问候"
    category = "social"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        if user_profile.get("activity") == "idle":
            return {"should_fire": True}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        hour = time.localtime().tm_hour
        if hour < 12:
            return "Good morning! How can I help you today?"
        elif hour < 18:
            return "Good afternoon! Need any assistance?"
        else:
            return "Good evening! Wrapping up for the day?"


class ClipboardInsightService(ProactiveServiceBase):
    service_name = "clipboard_insight"
    display_name = "剪贴板洞察"
    category = "info"

    async def check(self, context: dict, user_profile: dict) -> Optional[dict]:
        sources = context.get("sources", {})
        if "clipboard" in sources:
            return {"should_fire": True}
        return None

    async def generate_content(self, context: dict, user_profile: dict) -> str:
        return "I noticed you copied some content. Here are some actions you might want to take."


BUILT_IN_SERVICES: list[type[ProactiveServiceBase]] = [
    DailyBriefingService,
    MeetingPrepService,
    DeadlineGuardService,
    FocusProtectorService,
    SmartFollowupService,
    ContextNewsService,
    DocSuggestionService,
    LearningPathService,
    WellnessGuardService,
    CommuteAssistantService,
    ExpenseTrackerService,
    SocialReminderService,
    WeatherAdvisorService,
    DeviceHealthService,
    SecurityGuardService,
    IdeaSparkService,
    WritingCoachService,
    DataInsightService,
    ProactiveGreetingService,
    ClipboardInsightService,
]


_service_instances: Optional[dict[str, ProactiveServiceBase]] = None


def get_service_instances() -> dict[str, ProactiveServiceBase]:
    global _service_instances
    if _service_instances is None:
        _service_instances = {cls.service_name: cls() for cls in BUILT_IN_SERVICES}
    return _service_instances
