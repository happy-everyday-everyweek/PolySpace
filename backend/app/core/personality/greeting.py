from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class GreetingConfig:
    enabled: bool = True
    min_idle_minutes: int = 30
    morning_hour: int = 8
    evening_hour: int = 20
    greeting_cooldown_minutes: int = 60
    max_greetings_per_day: int = 5


@dataclass
class GreetingRecord:
    greeting: str
    timestamp: datetime = field(default_factory=datetime.now)
    time_context: str = ""
    greeting_type: str = "scheduled"


@dataclass
class ActivityRhythm:
    hourly_activity: dict[int, int] = field(default_factory=lambda: {h: 0 for h in range(24)})
    total_samples: int = 0

    def record_activity(self, hour: int):
        self.hourly_activity[hour] = self.hourly_activity.get(hour, 0) + 1
        self.total_samples += 1

    def get_active_hours(self, threshold: float = 0.3) -> list[int]:
        if self.total_samples == 0:
            return [9, 10, 11, 14, 15, 16, 20, 21]
        max_count = max(self.hourly_activity.values()) if self.hourly_activity else 1
        return [h for h, c in self.hourly_activity.items() if c / max(1, max_count) >= threshold]

    def is_active_time(self, hour: int) -> bool:
        return hour in self.get_active_hours()


class GreetingManager:
    def __init__(self, llm_dispatcher, config: Optional[GreetingConfig] = None):
        self._dispatcher = llm_dispatcher
        self._config = config or GreetingConfig()
        self._last_interaction: Optional[datetime] = None
        self._last_greeting: Optional[datetime] = None
        self._greeting_history: list[GreetingRecord] = []
        self._daily_greeting_count: int = 0
        self._daily_count_date: Optional[str] = None
        self._activity_rhythm = ActivityRhythm()
        self._relationship_stage: str = "stranger"
        self._last_topics: list[str] = []
        self._concern_triggered: bool = False

    def update_interaction(self) -> None:
        now = datetime.now()
        self._last_interaction = now
        self._activity_rhythm.record_activity(now.hour)

    def update_relationship(self, stage: str):
        self._relationship_stage = stage

    def update_last_topics(self, topics: list[str]):
        self._last_topics = topics[-5:]

    def check_concern_trigger(self, message_gap_minutes: float = 0,
                               emotion_anomaly: bool = False) -> bool:
        if message_gap_minutes > 120 or emotion_anomaly:
            self._concern_triggered = True
            return True
        return False

    async def should_greet(self) -> bool:
        if not self._config.enabled:
            return False
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        if self._daily_count_date != today:
            self._daily_count_date = today
            self._daily_greeting_count = 0
        if self._daily_greeting_count >= self._config.max_greetings_per_day:
            return False
        if self._last_greeting and (now - self._last_greeting) < timedelta(minutes=self._config.greeting_cooldown_minutes):
            return False
        if self._last_interaction:
            idle_time = now - self._last_interaction
            if idle_time < timedelta(minutes=self._config.min_idle_minutes):
                return False
        return True

    async def generate_greeting(self, emotion_context: str = "",
                                 recent_topics: list[str] = None,
                                 person_name: str = "") -> Optional[str]:
        if not await self.should_greet():
            return None
        now = datetime.now()
        time_context = self._get_time_context(now)
        context_parts = [f"当前时段: {time_context}"]

        active_hours = self._activity_rhythm.get_active_hours()
        if active_hours:
            context_parts.append(f"用户通常活跃时段: {self._format_hours(active_hours)}")

        rel_map = {
            "stranger": "刚认识",
            "acquaintance": "有些熟悉",
            "friend": "是朋友",
            "close_friend": "是密友",
        }
        context_parts.append(f"你和用户的关系: {rel_map.get(self._relationship_stage, '刚认识')}")

        if emotion_context:
            context_parts.append(f"当前情绪状态: {emotion_context}")
        if recent_topics:
            context_parts.append(f"最近聊过的话题: {', '.join(recent_topics[-3:])}")
        elif self._last_topics:
            context_parts.append(f"上次聊到: {', '.join(self._last_topics[-3:])}")
        if person_name:
            context_parts.append(f"用户的名字: {person_name}")
        if self._greeting_history:
            last_greeting = self._greeting_history[-1]
            context_parts.append(f"上次问候是在{last_greeting.time_context}时段")

        if self._concern_triggered:
            context_parts.append("注意：用户可能状态不太好，请表达关心")
            greeting_type = "concern"
        elif self._last_topics and now.hour in [9, 10, 19, 20]:
            context_parts.append("可以自然地延续上次的话题")
            greeting_type = "followup"
        else:
            greeting_type = "scheduled"

        context_str = "。".join(context_parts)

        messages = [
            {
                "role": "system",
                "content": (
                    "生成一条自然、个性化的问候或关心消息。规则：\n"
                    "1. 匹配情绪基调——如果用户可能不太好，要温柔关心\n"
                    "2. 如果有上次话题，可以自然延续（如'对了，上次你说的那个项目怎么样了？'）\n"
                    "3. 用用户的名字（如果知道）\n"
                    "4. 简短（1-2句话）\n"
                    "5. 不要使用emoji\n"
                    "6. 风格多变——不要重复类似的问候\n"
                    "7. 考虑时段——早上问好、晚上关心休息\n"
                    "8. 如果是关心型问候，要真诚但不过分\n"
                    "9. 根据关系阶段调整亲密程度"
                ),
            },
            {"role": "user", "content": context_str},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.DAILY, messages=messages)
        greeting = response.choices[0].message.content.strip()
        self._last_greeting = now
        self._daily_greeting_count += 1
        self._concern_triggered = False
        self._greeting_history.append(GreetingRecord(
            greeting=greeting, timestamp=now, time_context=time_context, greeting_type=greeting_type
        ))
        return greeting

    def _get_time_context(self, now: datetime) -> str:
        hour = now.hour
        if 5 <= hour < 12:
            return "早上"
        elif 12 <= hour < 14:
            return "中午"
        elif 14 <= hour < 18:
            return "下午"
        elif 18 <= hour < 22:
            return "晚上"
        else:
            return "深夜"

    def _format_hours(self, hours: list[int]) -> str:
        if not hours:
            return ""
        ranges = []
        sorted_hours = sorted(hours)
        start = sorted_hours[0]
        end = sorted_hours[0]
        for h in sorted_hours[1:]:
            if h == end + 1:
                end = h
            else:
                ranges.append(f"{start}-{end}点" if start != end else f"{start}点")
                start = end = h
        ranges.append(f"{start}-{end}点" if start != end else f"{start}点")
        return ", ".join(ranges)

    def get_greeting_history(self, limit: int = 10) -> list[GreetingRecord]:
        return self._greeting_history[-limit:]
