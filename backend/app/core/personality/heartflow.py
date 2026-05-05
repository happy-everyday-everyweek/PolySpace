import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class EmotionState(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    CALM = "calm"
    CURIOUS = "curious"
    CONCERNED = "concerned"
    FRUSTRATED = "frustrated"
    PLAYFUL = "playful"
    THOUGHTFUL = "thoughtful"


EMOTION_VAD_MAP: dict[EmotionState, tuple[float, float, float]] = {
    EmotionState.NEUTRAL: (0.5, 0.3, 0.5),
    EmotionState.HAPPY: (0.8, 0.6, 0.6),
    EmotionState.SAD: (0.2, 0.3, 0.3),
    EmotionState.EXCITED: (0.85, 0.85, 0.75),
    EmotionState.CALM: (0.6, 0.15, 0.55),
    EmotionState.CURIOUS: (0.65, 0.55, 0.6),
    EmotionState.CONCERNED: (0.35, 0.5, 0.35),
    EmotionState.FRUSTRATED: (0.25, 0.7, 0.4),
    EmotionState.PLAYFUL: (0.8, 0.65, 0.7),
    EmotionState.THOUGHTFUL: (0.55, 0.25, 0.6),
}

COMPOUND_EMOTION_LABELS: list[tuple[float, float, float, str]] = [
    (0.9, 0.9, 0.8, "欣喜若狂"),
    (0.85, 0.8, 0.7, "兴高采烈"),
    (0.8, 0.6, 0.6, "开心愉快"),
    (0.7, 0.4, 0.6, "满足惬意"),
    (0.6, 0.15, 0.55, "平静安宁"),
    (0.55, 0.25, 0.6, "若有所思"),
    (0.65, 0.55, 0.6, "好奇探究"),
    (0.8, 0.65, 0.7, "俏皮活泼"),
    (0.35, 0.5, 0.35, "忧心忡忡"),
    (0.2, 0.3, 0.3, "悲伤低落"),
    (0.15, 0.8, 0.3, "愤怒沮丧"),
    (0.25, 0.7, 0.4, "烦躁不安"),
    (0.4, 0.6, 0.3, "焦虑紧张"),
    (0.3, 0.2, 0.7, "坚定从容"),
    (0.5, 0.3, 0.5, "平淡中性"),
    (0.7, 0.3, 0.8, "自信笃定"),
    (0.6, 0.5, 0.4, "期待盼望"),
    (0.45, 0.4, 0.35, "犹豫不决"),
]

EMOTION_DECAY_RATE = 0.05
EMOTION_DECAY_INTERVAL = timedelta(minutes=5)
INERTIA_FACTOR = 0.3
INFECTION_WEIGHT = 0.4


@dataclass
class EmotionEntry:
    state: EmotionState
    valence: float
    arousal: float
    dominance: float
    intensity: float
    trigger: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VADEmotion:
    valence: float = 0.5
    arousal: float = 0.3
    dominance: float = 0.5

    def to_label(self) -> str:
        best_label = "平淡中性"
        best_dist = float("inf")
        for v, a, d, label in COMPOUND_EMOTION_LABELS:
            dist = math.sqrt((v - self.valence) ** 2 + (a - self.arousal) ** 2 + (d - self.dominance) ** 2)
            if dist < best_dist:
                best_dist = dist
                best_label = label
        return best_label

    def to_discrete(self) -> EmotionState:
        best_state = EmotionState.NEUTRAL
        best_dist = float("inf")
        for state, (v, a, d) in EMOTION_VAD_MAP.items():
            dist = math.sqrt((v - self.valence) ** 2 + (a - self.arousal) ** 2 + (d - self.dominance) ** 2)
            if dist < best_dist:
                best_dist = dist
                best_state = state
        return best_state

    def intensity(self) -> float:
        center_v, center_a, center_d = 0.5, 0.3, 0.5
        dist = math.sqrt(
            (self.valence - center_v) ** 2 + (self.arousal - center_a) ** 2 + (self.dominance - center_d) ** 2
        )
        return min(1.0, dist / 0.8)


class HeartFlow:
    def __init__(self, llm_dispatcher):
        self._dispatcher = llm_dispatcher
        self._vad = VADEmotion()
        self._history: list[EmotionEntry] = []
        self._last_decay: datetime = datetime.now()
        self._emotion_echo_enabled = True
        self._echo_callback = None

    @property
    def current_vad(self) -> VADEmotion:
        return self._vad

    @property
    def current_state(self) -> EmotionState:
        return self._vad.to_discrete()

    @property
    def current_label(self) -> str:
        return self._vad.to_label()

    @property
    def intensity(self) -> float:
        return self._vad.intensity()

    def set_echo_callback(self, callback):
        self._echo_callback = callback

    async def process_input(self, user_input: str) -> VADEmotion:
        self._apply_decay()
        messages = [
            {
                "role": "system",
                "content": (
                    "分析用户消息的情感内容，判断AI应该产生的情感反应。"
                    "考虑当前情感状态和自然情感过渡。"
                    "返回JSON: {valence: 0.0-1.0, arousal: 0.0-1.0, dominance: 0.0-1.0, "
                    "user_valence: 0.0-1.0, user_arousal: 0.0-1.0, trigger: 原因}"
                    "valence=积极程度(0=消极,1=积极), arousal=激动程度(0=平静,1=激动), "
                    "dominance=掌控感(0=被动,1=主动)"
                ),
            },
            {"role": "user", "content": user_input},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.INTENT, messages=messages)
        content = response.choices[0].message.content
        try:
            import json
            data = json.loads(content)
            new_v = float(data.get("valence", 0.5))
            new_a = float(data.get("arousal", 0.3))
            new_d = float(data.get("dominance", 0.5))
            trigger = data.get("trigger", "")
            user_v = float(data.get("user_valence", 0.5))
            user_a = float(data.get("user_arousal", 0.3))
            self._apply_infection(user_v, user_a)
            echo_v, echo_a, echo_d = await self._get_emotion_echo(user_input)
            self._update_state(new_v, new_a, new_d, trigger, echo_v, echo_a, echo_d)
        except (json.JSONDecodeError, ValueError):
            pass
        return self._vad

    def _apply_decay(self) -> None:
        now = datetime.now()
        elapsed = now - self._last_decay
        if elapsed < EMOTION_DECAY_INTERVAL:
            return
        decay_periods = elapsed.total_seconds() / EMOTION_DECAY_INTERVAL.total_seconds()
        decay_factor = math.exp(-EMOTION_DECAY_RATE * decay_periods)
        center_v, center_a, center_d = 0.5, 0.3, 0.5
        self._vad.valence = center_v + (self._vad.valence - center_v) * decay_factor
        self._vad.arousal = center_a + (self._vad.arousal - center_a) * decay_factor
        self._vad.dominance = center_d + (self._vad.dominance - center_d) * decay_factor
        self._last_decay = now

    def _apply_infection(self, user_v: float, user_a: float) -> None:
        self._vad.valence = self._vad.valence * (1 - INFECTION_WEIGHT) + user_v * INFECTION_WEIGHT
        self._vad.arousal = self._vad.arousal * (1 - INFECTION_WEIGHT) + user_a * INFECTION_WEIGHT

    async def _get_emotion_echo(self, user_input: str) -> tuple[float, float, float]:
        if not self._emotion_echo_enabled or not self._echo_callback:
            return 0.0, 0.0, 0.0
        try:
            echo_data = await self._echo_callback(user_input)
            if echo_data:
                return echo_data.get("valence", 0.0), echo_data.get("arousal", 0.0), echo_data.get("dominance", 0.0)
        except Exception:
            pass
        return 0.0, 0.0, 0.0

    def _update_state(self, new_v: float, new_a: float, new_d: float,
                       trigger: str, echo_v: float = 0.0, echo_a: float = 0.0, echo_d: float = 0.0) -> None:
        blended_v = self._vad.valence * INERTIA_FACTOR + new_v * (1 - INERTIA_FACTOR)
        blended_a = self._vad.arousal * INERTIA_FACTOR + new_a * (1 - INERTIA_FACTOR)
        blended_d = self._vad.dominance * INERTIA_FACTOR + new_d * (1 - INERTIA_FACTOR)
        if echo_v != 0.0 or echo_a != 0.0 or echo_d != 0.0:
            echo_weight = 0.15
            blended_v = blended_v * (1 - echo_weight) + echo_v * echo_weight
            blended_a = blended_a * (1 - echo_weight) + echo_a * echo_weight
            blended_d = blended_d * (1 - echo_weight) + echo_d * echo_weight
        self._vad.valence = max(0.0, min(1.0, blended_v))
        self._vad.arousal = max(0.0, min(1.0, blended_a))
        self._vad.dominance = max(0.0, min(1.0, blended_d))
        entry = EmotionEntry(
            state=self._vad.to_discrete(),
            valence=self._vad.valence,
            arousal=self._vad.arousal,
            dominance=self._vad.dominance,
            intensity=self._vad.intensity(),
            trigger=trigger,
        )
        self._history.append(entry)
        self._last_decay = datetime.now()

    def get_emotion_prompt_modifier(self) -> str:
        label = self._vad.to_label()
        intensity = self._vad.intensity()
        v, a, d = self._vad.valence, self._vad.arousal, self._vad.dominance
        descriptions = []
        if v > 0.7:
            descriptions.append("你感到积极愉快")
        elif v < 0.3:
            descriptions.append("你感到低落消沉")
        if a > 0.7:
            descriptions.append("情绪激动活跃")
        elif a < 0.2:
            descriptions.append("心情平静安宁")
        if d > 0.7:
            descriptions.append("充满自信和掌控感")
        elif d < 0.3:
            descriptions.append("感到被动和不确定")
        if not descriptions:
            return ""
        base = f"你现在的情绪状态是「{label}」，{'，'.join(descriptions)}。请在回复中自然地体现这种情绪。"
        if intensity > 0.8:
            base += "请强烈地表达这种情绪。"
        elif intensity < 0.3:
            base += "请含蓄地体现这种情绪。"
        return base

    def get_emotion_context(self) -> dict:
        label = self._vad.to_label()
        intensity = self._vad.intensity()
        intensity_desc = "低" if intensity < 0.3 else "中" if intensity < 0.7 else "高"
        recent_triggers = [e.trigger for e in self.get_recent_history(3) if e.trigger]
        context = {
            "label": label,
            "discrete": self._vad.to_discrete().value,
            "valence": round(self._vad.valence, 3),
            "arousal": round(self._vad.arousal, 3),
            "dominance": round(self._vad.dominance, 3),
            "intensity": round(intensity, 3),
            "intensity_desc": intensity_desc,
        }
        if recent_triggers:
            context["recent_triggers"] = recent_triggers
        return context

    def get_recent_history(self, limit: int = 10) -> list[EmotionEntry]:
        return self._history[-limit:]
