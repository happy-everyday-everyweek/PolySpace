import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ProactiveContentSchema:
    title: str = ""
    summary: str = ""
    action_items: list[str] = field(default_factory=list)
    tone: str = "friendly"
    urgency_hint: str = "normal"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "action_items": self.action_items,
            "tone": self.tone,
            "urgency_hint": self.urgency_hint,
        }

    def to_text(self) -> str:
        parts = []
        if self.title:
            parts.append(self.title)
        if self.summary:
            parts.append(self.summary)
        if self.action_items:
            for i, item in enumerate(self.action_items, 1):
                parts.append(f"{i}. {item}")
        return "\n".join(parts)


TEMPLATE_ONLY_SERVICES = frozenset({
    "focus_protector", "wellness_guard", "proactive_greeting",
    "clipboard_insight", "commute_assistant", "device_health",
})

LLM_SERVICES = frozenset({
    "daily_briefing", "meeting_prep", "deadline_guard",
    "smart_followup", "context_news", "doc_suggestion",
    "learning_path", "expense_tracker", "social_reminder",
    "weather_advisor", "security_guard", "idea_spark",
    "writing_coach", "data_insight",
})

SERVICE_SCHEMAS: dict[str, dict] = {
    "daily_briefing": {
        "title_max_len": 60, "summary_sentences": (2, 4),
        "action_items_range": (2, 5), "urgency_hint": "normal",
    },
    "meeting_prep": {
        "title_max_len": 80, "summary_sentences": (2, 3),
        "action_items_range": (1, 3), "urgency_hint": "important",
    },
    "deadline_guard": {
        "title_max_len": 60, "summary_sentences": (1, 2),
        "action_items_range": (1, 2), "urgency_hint": "urgent",
    },
    "focus_protector": {
        "title_max_len": 40, "summary_sentences": (1, 1),
        "action_items_range": (0, 1), "urgency_hint": "normal",
    },
    "smart_followup": {
        "title_max_len": 60, "summary_sentences": (1, 2),
        "action_items_range": (1, 2), "urgency_hint": "normal",
    },
    "wellness_guard": {
        "title_max_len": 40, "summary_sentences": (1, 1),
        "action_items_range": (1, 2), "urgency_hint": "normal",
    },
    "weather_advisor": {
        "title_max_len": 60, "summary_sentences": (1, 2),
        "action_items_range": (1, 2), "urgency_hint": "normal",
    },
    "security_guard": {
        "title_max_len": 60, "summary_sentences": (1, 2),
        "action_items_range": (1, 3), "urgency_hint": "urgent",
    },
    "proactive_greeting": {
        "title_max_len": 40, "summary_sentences": (1, 1),
        "action_items_range": (0, 1), "urgency_hint": "low",
    },
}

DEFAULT_SCHEMA = {
    "title_max_len": 60, "summary_sentences": (1, 2),
    "action_items_range": (1, 2), "urgency_hint": "normal",
}


class ProactiveContentGenerator:
    def __init__(self, llm_dispatcher=None):
        self._dispatcher = llm_dispatcher
        self._templates: dict[str, dict] = {
            "daily_briefing": {
                "morning": "Good morning! Here is your daily briefing for today.",
                "noon": "Mid-day update: Here is how your morning went.",
                "evening": "End of day summary: Here is what you accomplished today.",
            },
            "meeting_prep": "Your meeting starts in 15 minutes. Here is what you need to know.",
            "deadline_guard": "Reminder: A task is due soon. Please check your deadlines.",
            "focus_protector": "You have been focused for a while. Holding non-urgent notifications.",
            "smart_followup": "You mentioned something earlier but haven't followed up yet.",
            "wellness_guard": {
                "sedentary": "You have been sitting for a while. Consider taking a short break.",
                "eye_rest": "Time for a 20-20-20 break: look at something 20 feet away for 20 seconds.",
                "water": "Stay hydrated! Have you had water recently?",
            },
            "weather_advisor": "Weather alert detected. Consider adjusting your plans.",
            "security_guard": "Security alert detected. Please review immediately.",
            "proactive_greeting": "Hey! It has been a while. How are things going?",
            "clipboard_insight": "New clipboard content detected for analysis.",
            "commute_assistant": "Commute time reminder: check traffic before heading out.",
            "device_health": "Device status alert: please check your device.",
        }

    async def generate(self, service_name: str, context: dict, user_profile: dict, trigger_reason: str = "") -> str:
        schema = await self.generate_structured(service_name, context, user_profile, trigger_reason)
        return schema.to_text()

    async def generate_structured(
        self, service_name: str, context: dict,
        user_profile: dict, trigger_reason: str = "",
    ) -> ProactiveContentSchema:
        schema = self._get_schema(service_name)

        if service_name in TEMPLATE_ONLY_SERVICES or not self._dispatcher:
            text = self._generate_from_template(service_name, context, user_profile)
            return self._parse_to_schema(text, service_name, schema)

        if service_name not in LLM_SERVICES:
            text = self._generate_from_template(service_name, context, user_profile)
            return self._parse_to_schema(text, service_name, schema)

        return await self._generate_with_llm(service_name, context, user_profile, trigger_reason, schema)

    def _get_schema(self, service_name: str) -> dict:
        return SERVICE_SCHEMAS.get(service_name, DEFAULT_SCHEMA)

    async def _generate_with_llm(
        self, service_name: str, context: dict,
        user_profile: dict, trigger_reason: str, schema: dict,
    ) -> ProactiveContentSchema:
        from app.core.llm.dispatcher import TaskCategory
        tone = self._determine_tone(user_profile)
        context_summary = json.dumps(context.get("summary", {}), ensure_ascii=False)[:300]
        prompt = (
            f"Generate proactive message for '{service_name}'.\n"
            f"Tone: {tone}\nTrigger: {trigger_reason}\n"
            f"Activity: {user_profile.get('activity', 'unknown')}\n"
            f"Mood: {user_profile.get('mood', 'unknown')}\n"
            f"Context: {context_summary}\n"
            f"Output JSON: {{\"title\": \"...\", \"summary\": \"...\", "
            f"\"action_items\": [\"...\"], \"tone\": \"friendly\", \"urgency_hint\": \"normal\"}}\n"
            f"Rules: title max {schema['title_max_len']} chars, "
            f"summary {schema['summary_sentences'][0]}-{schema['summary_sentences'][1]} sentences, "
            f"action_items {schema['action_items_range'][0]}-{schema['action_items_range'][1]} items. "
            f"No emojis. Only valid JSON."
        )
        try:
            response = await self._dispatcher.dispatch(
                TaskCategory.DAILY,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()
            return self._parse_json_output(raw, service_name, schema)
        except Exception as e:
            logger.error(f"LLM content generation failed: {e}")
            text = self._generate_from_template(service_name, context, user_profile)
            return self._parse_to_schema(text, service_name, schema)

    def _parse_json_output(self, raw: str, service_name: str, schema: dict) -> ProactiveContentSchema:
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return ProactiveContentSchema(
                    title=str(data.get("title", ""))[:schema["title_max_len"]],
                    summary=str(data.get("summary", "")),
                    action_items=[str(a) for a in data.get("action_items", [])][:schema["action_items_range"][1]],
                    tone=str(data.get("tone", "friendly")),
                    urgency_hint=str(data.get("urgency_hint", schema.get("urgency_hint", "normal"))),
                )
            except json.JSONDecodeError:
                pass
        return self._parse_to_schema(raw, service_name, schema)

    def _parse_to_schema(self, text: str, service_name: str, schema: dict) -> ProactiveContentSchema:
        result = ProactiveContentSchema()
        lines = text.strip().split("\n")
        if lines:
            result.title = lines[0][:schema["title_max_len"]]
        if len(lines) > 1:
            result.summary = "\n".join(lines[1:])
        result.urgency_hint = schema.get("urgency_hint", "normal")
        return result

    def _generate_from_template(self, service_name: str, context: dict, user_profile: dict) -> str:
        template = self._templates.get(service_name, "")
        if isinstance(template, dict):
            hour = time.localtime().tm_hour
            if hour < 12:
                return template.get("morning", template.get("sedentary", str(template)))
            elif hour < 18:
                return template.get("noon", template.get("eye_rest", str(template)))
            else:
                return template.get("evening", template.get("water", str(template)))
        if isinstance(template, str):
            return template
        return f"[{service_name}] Proactive notification triggered."

    def _determine_tone(self, user_profile: dict) -> str:
        mood = user_profile.get("mood", "unknown")
        activity = user_profile.get("activity", "unknown")
        if mood == "stressed":
            return "gentle"
        if mood == "tired":
            return "encouraging"
        if activity == "in_meeting":
            return "formal"
        if activity == "focused":
            return "minimal"
        return "friendly"

    def generate_action_buttons(self, service_name: str) -> list[dict]:
        button_templates = {
            "daily_briefing": [
                {"label": "View Details", "action": "view_briefing"},
                {"label": "Dismiss", "action": "dismiss"},
            ],
            "meeting_prep": [
                {"label": "View Agenda", "action": "view_agenda"},
                {"label": "Join Meeting", "action": "join_meeting"},
                {"label": "Snooze", "action": "snooze_5min"},
            ],
            "deadline_guard": [
                {"label": "Mark In Progress", "action": "mark_in_progress"},
                {"label": "Request Extension", "action": "request_extension"},
                {"label": "Remind Later", "action": "remind_1hr"},
            ],
            "focus_protector": [
                {"label": "End Focus", "action": "end_focus"},
                {"label": "Continue", "action": "continue_focus"},
            ],
            "smart_followup": [
                {"label": "Follow Up Now", "action": "followup_now"},
                {"label": "Remind Later", "action": "remind_later"},
                {"label": "Mark Done", "action": "mark_done"},
            ],
            "wellness_guard": [
                {"label": "Take Break", "action": "take_break"},
                {"label": "Snooze 30min", "action": "snooze_30min"},
            ],
            "weather_advisor": [
                {"label": "Adjust Schedule", "action": "adjust_schedule"},
                {"label": "Dismiss", "action": "dismiss"},
            ],
            "security_guard": [
                {"label": "Review Now", "action": "review_now"},
                {"label": "Block", "action": "block"},
            ],
        }
        default = [
            {"label": "OK", "action": "acknowledge"},
            {"label": "Dismiss", "action": "dismiss"},
        ]
        return button_templates.get(service_name, default)


_generator: Optional[ProactiveContentGenerator] = None


def get_content_generator() -> ProactiveContentGenerator:
    global _generator
    if _generator is None:
        _generator = ProactiveContentGenerator()
    return _generator
