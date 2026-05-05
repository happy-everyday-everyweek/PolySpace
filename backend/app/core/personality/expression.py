import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExpressionRecord:
    situation: str
    style: str
    count: int = 1
    last_active: datetime = field(default_factory=datetime.now)
    source_ids: list[str] = field(default_factory=list)
    quality_score: float = 1.0
    auto_check_status: str = "pending"
    jargon_type: str = ""


@dataclass
class FillerWordRule:
    word: str
    emotion_condition: str = ""
    position: str = "start"
    probability: float = 0.3


@dataclass
class RhythmPattern:
    name: str
    short_long_ratio: float = 0.5
    pause_frequency: float = 0.2
    exclamation_rate: float = 0.1


FILLER_WORDS_MAP: dict[str, list[FillerWordRule]] = {
    "warm": [
        FillerWordRule("嗯", "calm,happy,curious", "start", 0.4),
        FillerWordRule("啊", "excited,surprised", "start", 0.3),
        FillerWordRule("呢", "playful,curious", "end", 0.3),
        FillerWordRule("呀", "happy,excited", "end", 0.25),
        FillerWordRule("哦", "thoughtful,curious", "start", 0.3),
    ],
    "neutral": [
        FillerWordRule("嗯", "calm,thoughtful", "start", 0.2),
        FillerWordRule("那么", "neutral", "start", 0.15),
    ],
    "cool": [
        FillerWordRule("所以", "neutral,confident", "start", 0.2),
    ],
}

RHYTHM_MAP: dict[str, RhythmPattern] = {
    "energetic": RhythmPattern("energetic", 0.7, 0.1, 0.3),
    "balanced": RhythmPattern("balanced", 0.5, 0.2, 0.1),
    "calm": RhythmPattern("calm", 0.3, 0.3, 0.05),
    "thoughtful": RhythmPattern("thoughtful", 0.4, 0.35, 0.05),
}


class ExpressionLearner:
    def __init__(self, llm_dispatcher):
        self._dispatcher = llm_dispatcher
        self._expressions: list[ExpressionRecord] = []
        self._similarity_threshold = 0.75
        self._auto_check_interval = 100
        self._message_count = 0
        self._own_filler_rules: list[FillerWordRule] = []
        self._own_rhythm: RhythmPattern = RHYTHM_MAP["balanced"]
        self._catchphrases: list[str] = []

    def configure_from_persona(self, persona_modifiers: dict):
        warmth = persona_modifiers.get("warmth_tendency", 0.5)
        humor = persona_modifiers.get("humor_tendency", 0.5)
        conciseness = persona_modifiers.get("conciseness", 0.5)
        persona_modifiers.get("formality_level", 0.5)

        if warmth >= 0.7:
            style_key = "warm"
        elif warmth >= 0.4:
            style_key = "neutral"
        else:
            style_key = "cool"
        self._own_filler_rules = FILLER_WORDS_MAP.get(style_key, FILLER_WORDS_MAP["neutral"]).copy()

        if warmth >= 0.7 and humor >= 0.6:
            self._own_rhythm = RHYTHM_MAP["energetic"]
        elif conciseness >= 0.7:
            self._own_rhythm = RHYTHM_MAP["calm"]
        elif warmth >= 0.5:
            self._own_rhythm = RHYTHM_MAP["balanced"]
        else:
            self._own_rhythm = RHYTHM_MAP["thoughtful"]

        self._own_rhythm.exclamation_rate = min(0.4, humor * 0.5)
        self._own_rhythm.pause_frequency = max(0.05, (1.0 - conciseness) * 0.3)

    async def learn_from_messages(self, messages: list[dict]) -> list[tuple[str, str, str]]:
        if not messages:
            return []
        messages_text = "\n".join(m.get("content", "") for m in messages)
        extraction_messages = [
            {
                "role": "system",
                "content": (
                    "从这些消息中提取独特的表达模式、俚语和行话。"
                    "返回JSON数组: [{situation, style, expression, jargon_type}]。"
                    "jargon_type可以是: abbreviation, pinyin, slang, dialect, internet_slang, 或空字符串。"
                    "关注独特的说话风格、俚语和沟通模式。"
                    "过滤掉: 机器人消息、图片标签、纯emoji内容、重复模式。"
                    "同时提取用户常用的语气词、口头禅、停顿习惯。"
                ),
            },
            {"role": "user", "content": messages_text},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.INTENT, messages=extraction_messages)
        content = response.choices[0].message.content
        results = []
        try:
            import json
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    situation = item.get("situation", "")
                    style = item.get("style", "")
                    expression = item.get("expression", "")
                    jargon_type = item.get("jargon_type", "")
                    source_id = hashlib.md5(f"{situation}:{style}".encode()).hexdigest()[:8]
                    if situation and style:
                        await self._upsert_expression(situation, style, source_id, jargon_type)
                        results.append((situation, style, expression))
        except Exception:
            pass
        self._message_count += len(messages)
        if self._message_count >= self._auto_check_interval:
            await self.auto_check_expressions()
            self._message_count = 0
        return results

    async def _upsert_expression(self, situation: str, style: str,
                                  source_id: str = "", jargon_type: str = "") -> None:
        for expr in self._expressions:
            if self._compute_similarity(expr.situation, situation) >= self._similarity_threshold:
                expr.count += 1
                expr.last_active = datetime.now()
                if source_id and source_id not in expr.source_ids:
                    expr.source_ids.append(source_id)
                if jargon_type and not expr.jargon_type:
                    expr.jargon_type = jargon_type
                return
        self._expressions.append(ExpressionRecord(
            situation=situation, style=style, source_ids=[source_id] if source_id else [],
            jargon_type=jargon_type
        ))

    def _compute_similarity(self, a: str, b: str) -> float:
        if a == b:
            return 1.0
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    async def select_expressions(self, context: str, max_num: int = 5) -> list[ExpressionRecord]:
        if not self._expressions:
            return []
        scored = []
        for expr in self._expressions:
            score = expr.count * expr.quality_score
            context_sim = self._compute_similarity(expr.situation, context)
            score *= (1.0 + context_sim * 0.5)
            if expr.auto_check_status == "rejected":
                score *= 0.1
            scored.append((score, expr))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [expr for _, expr in scored[:max_num]]

    async def auto_check_expressions(self) -> dict[str, int]:
        if not self._expressions:
            return {"checked": 0}
        unchecked = [e for e in self._expressions if e.auto_check_status == "pending"]
        if not unchecked:
            return {"checked": 0}
        batch_text = "\n".join(
            f"[{i}] Situation: {e.situation} | Style: {e.style} | Jargon: {e.jargon_type}"
            for i, e in enumerate(unchecked[:20])
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "评估这些学到的表达的质量和适当性。"
                    "对每个，返回JSON数组: [{index, suitable: bool, score: 0.0-1.0, reason}]。"
                    "拒绝: 冒犯性内容、无意义模式、机器人式短语。"
                    "接受: 自然的人类表达、俚语、个性模式。"
                ),
            },
            {"role": "user", "content": batch_text},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.INTENT, messages=messages)
        content = response.choices[0].message.content
        checked = 0
        try:
            import json
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    idx = item.get("index", -1)
                    if 0 <= idx < len(unchecked):
                        expr = unchecked[idx]
                        expr.quality_score = float(item.get("score", 0.5))
                        expr.auto_check_status = "suitable" if item.get("suitable", True) else "rejected"
                        checked += 1
        except Exception:
            pass
        return {"checked": checked}

    def apply_expression_style(self, text: str, emotion_label: str = "平淡中性",
                                emotion_intensity: float = 0.3) -> str:
        if not text:
            return text
        text = self._apply_filler_words(text, emotion_label)
        text = self._apply_rhythm(text, emotion_intensity)
        text = self._apply_emotional_punctuation(text, emotion_label, emotion_intensity)
        return text

    def _apply_filler_words(self, text: str, emotion_label: str) -> str:
        if not self._own_filler_rules:
            return text
        import random
        for rule in self._own_filler_rules:
            if rule.emotion_condition and emotion_label not in rule.emotion_condition:
                continue
            if random.random() > rule.probability:
                continue
            sentences = re.split(r'([。！？])', text)
            if len(sentences) < 2:
                continue
            if rule.position == "start" and sentences[0].strip():
                sentences[0] = f"{rule.word}，{sentences[0]}"
            elif rule.position == "end" and len(sentences) >= 2:
                sentences[0] = f"{sentences[0]}{rule.word}"
            text = "".join(sentences)
            break
        return text

    def _apply_rhythm(self, text: str, intensity: float) -> str:
        rhythm = self._own_rhythm
        if intensity > 0.7 and rhythm.exclamation_rate > 0.2:
            text = re.sub(r'。', '！', text, count=1)
        return text

    def _apply_emotional_punctuation(self, text: str, emotion_label: str, intensity: float) -> str:
        if intensity > 0.7:
            if any(k in emotion_label for k in ["兴奋", "欣喜", "激动", "愤怒"]):
                if "！" not in text and "。" in text:
                    text = text.replace("。", "！", 1)
            if any(k in emotion_label for k in ["犹豫", "思考", "不确定"]):
                if "……" not in text and "。" in text:
                    text = text.replace("。", "……", 1)
        elif intensity < 0.3:
            if "！" in text and "兴奋" not in emotion_label:
                text = text.replace("！", "。", 1)
        return text

    def get_all_expressions(self) -> list[ExpressionRecord]:
        return self._expressions.copy()

    def get_jargon_expressions(self) -> list[ExpressionRecord]:
        return [e for e in self._expressions if e.jargon_type]
