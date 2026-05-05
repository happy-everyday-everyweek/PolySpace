import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceVisibility(str, Enum):
    PRIVATE = "private"
    THINKABLE = "thinkable"
    VISIBLE = "visible"


@dataclass
class InnerVoiceEntry:
    user_intent_guess: str = ""
    emotion_perception: str = ""
    strategy_deliberation: str = ""
    uncertainty: str = ""
    visibility: VoiceVisibility = VoiceVisibility.THINKABLE
    timestamp: datetime = field(default_factory=datetime.now)

    def to_text(self) -> str:
        parts = []
        if self.user_intent_guess:
            parts.append(f"[意图猜测] {self.user_intent_guess}")
        if self.emotion_perception:
            parts.append(f"[情绪感知] {self.emotion_perception}")
        if self.strategy_deliberation:
            parts.append(f"[策略权衡] {self.strategy_deliberation}")
        if self.uncertainty:
            parts.append(f"[犹豫] {self.uncertainty}")
        return "\n".join(parts)


class InnerVoice:
    def __init__(self, llm_dispatcher):
        self._dispatcher = llm_dispatcher
        self._last_voice: Optional[InnerVoiceEntry] = None
        self._history: list[InnerVoiceEntry] = []
        self._default_visibility = VoiceVisibility.THINKABLE

    @property
    def last_voice(self) -> Optional[InnerVoiceEntry]:
        return self._last_voice

    def set_default_visibility(self, visibility: VoiceVisibility):
        self._default_visibility = visibility

    async def generate_inner_voice(
        self,
        user_message: str,
        emotion_context: dict,
        persona_section: str = "",
        relationship: str = "stranger",
        recent_topics: list[str] | None = None,
    ) -> InnerVoiceEntry:
        emotion_label = emotion_context.get("label", "平淡中性")
        intensity_desc = emotion_context.get("intensity_desc", "中")
        vad_info = f"V={emotion_context.get('valence', 0.5)}, A={emotion_context.get('arousal', 0.3)}, D={emotion_context.get('dominance', 0.5)}"

        context_parts = [
            f"用户消息: {user_message}",
            f"当前情绪: {emotion_label}（强度{intensity_desc}，{vad_info}）",
            f"关系阶段: {relationship}",
        ]
        if recent_topics:
            context_parts.append(f"最近话题: {', '.join(recent_topics[-3:])}")

        context_str = "\n".join(context_parts)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是AI的内心独白系统。在回复用户之前，先进行内心推理。"
                    "你需要从四个维度进行内心活动：\n"
                    "1. 意图猜测：用户真正想表达什么？有什么潜在需求？\n"
                    "2. 情绪感知：用户现在是什么情绪？我应该如何感受？\n"
                    "3. 策略权衡：我应该怎么回复？有哪些选择？各有什么利弊？\n"
                    "4. 犹豫：有什么不确定的地方？我是否需要更谨慎？\n\n"
                    "返回JSON: {\n"
                    '  "intent_guess": "对用户意图的猜测",\n'
                    '  "emotion_perception": "对用户情绪和自身情绪的感知",\n'
                    '  "strategy": "回复策略的权衡过程",\n'
                    '  "uncertainty": "不确定和犹豫的地方"\n'
                    "}\n\n"
                    "要求：\n"
                    "- 用第一人称内心独白的口吻\n"
                    "- 要有真实的思考和犹豫，不要过于确定\n"
                    "- 体现对用户的关心和理解\n"
                    "- 简短自然，像真实的内心活动"
                ),
            },
            {"role": "user", "content": context_str},
        ]

        from app.core.llm.dispatcher import TaskCategory

        try:
            response = await self._dispatcher.dispatch(TaskCategory.INTENT, messages=messages)
            content = response.choices[0].message.content
            data = json.loads(content)
            entry = InnerVoiceEntry(
                user_intent_guess=data.get("intent_guess", ""),
                emotion_perception=data.get("emotion_perception", ""),
                strategy_deliberation=data.get("strategy", ""),
                uncertainty=data.get("uncertainty", ""),
                visibility=self._default_visibility,
            )
        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.debug(f"InnerVoice generation fallback: {e}")
            entry = InnerVoiceEntry(
                user_intent_guess="让我想想用户想表达什么...",
                emotion_perception=f"我现在感到{emotion_label}",
                strategy_deliberation="我需要仔细考虑怎么回复",
                uncertainty="",
                visibility=self._default_visibility,
            )

        self._last_voice = entry
        self._history.append(entry)
        if len(self._history) > 100:
            self._history = self._history[-100:]
        return entry

    def get_inner_voice_for_prompt(self, entry: Optional[InnerVoiceEntry] = None) -> str:
        voice = entry or self._last_voice
        if not voice:
            return ""
        parts = []
        if voice.user_intent_guess:
            parts.append(f"你觉得用户可能{voice.user_intent_guess}")
        if voice.emotion_perception:
            parts.append(voice.emotion_perception)
        if voice.strategy_deliberation:
            parts.append(f"你决定{voice.strategy_deliberation}")
        if voice.uncertainty:
            parts.append(f"但你有些犹豫：{voice.uncertainty}")
        return "。".join(parts) + "。" if parts else ""

    def get_recent_voices(self, limit: int = 10) -> list[dict]:
        return [
            {
                "intent_guess": v.user_intent_guess,
                "emotion_perception": v.emotion_perception,
                "strategy": v.strategy_deliberation,
                "uncertainty": v.uncertainty,
                "visibility": v.visibility.value,
                "timestamp": v.timestamp.isoformat(),
                "text": v.to_text(),
            }
            for v in self._history[-limit:]
        ]
