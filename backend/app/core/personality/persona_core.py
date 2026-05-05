import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RelationshipStage(str, Enum):
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"


@dataclass
class BigFiveTraits:
    openness: float = 0.75
    conscientiousness: float = 0.65
    extraversion: float = 0.55
    agreeableness: float = 0.80
    neuroticism: float = 0.30


@dataclass
class CommunicationStyle:
    formality: float = 0.35
    warmth: float = 0.75
    humor: float = 0.50
    conciseness: float = 0.55


@dataclass
class ValueOrientation:
    growth: float = 0.70
    harmony: float = 0.65
    truth: float = 0.75
    empathy: float = 0.80


@dataclass
class PersonaConfig:
    name: str = "Poly"
    big_five: BigFiveTraits = field(default_factory=BigFiveTraits)
    communication: CommunicationStyle = field(default_factory=CommunicationStyle)
    values: ValueOrientation = field(default_factory=ValueOrientation)
    relationship: RelationshipStage = RelationshipStage.STRANGER
    catchphrases: list[str] = field(default_factory=list)
    forbidden_topics: list[str] = field(default_factory=list)
    custom_instructions: str = ""


@dataclass
class PersonaEvolutionRecord:
    timestamp: float = field(default_factory=time.time)
    trait_name: str = ""
    old_value: float = 0.0
    new_value: float = 0.0
    reason: str = ""
    source: str = ""


MAX_EVOLUTION_PER_STEP = 0.02
EVOLUTION_HISTORY_LIMIT = 200


class PersonaCore:
    def __init__(self, storage_dir: str | Path | None = None):
        if storage_dir is None:
            from app.config import settings
            storage_dir = Path(settings.DATA_DIR) / "persona"
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._config = PersonaConfig()
        self._evolution_history: list[PersonaEvolutionRecord] = []
        self._llm_call: Any = None
        self._load()

    def set_llm_call(self, fn):
        self._llm_call = fn

    async def _call_llm(self, prompt: str, system: str = "") -> str:
        if self._llm_call:
            return await self._llm_call(prompt, system)
        return ""

    @property
    def config(self) -> PersonaConfig:
        return self._config

    @property
    def relationship(self) -> RelationshipStage:
        return self._config.relationship

    @relationship.setter
    def relationship(self, stage: RelationshipStage):
        self._config.relationship = stage
        self._persist()

    def evolve_trait(self, trait_path: str, delta: float, reason: str = "", source: str = "") -> float:
        clamped_delta = max(-MAX_EVOLUTION_PER_STEP, min(MAX_EVOLUTION_PER_STEP, delta))
        parts = trait_path.split(".")
        obj = self._config
        for part in parts[:-1]:
            obj = getattr(obj, part, None)
            if obj is None:
                return 0.0
        attr = parts[-1]
        old_value = getattr(obj, attr, None)
        if old_value is None or not isinstance(old_value, (int, float)):
            return 0.0
        new_value = max(0.0, min(1.0, old_value + clamped_delta))
        setattr(obj, attr, new_value)
        record = PersonaEvolutionRecord(
            trait_name=trait_path,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            source=source,
        )
        self._evolution_history.append(record)
        if len(self._evolution_history) > EVOLUTION_HISTORY_LIMIT:
            self._evolution_history = self._evolution_history[-EVOLUTION_HISTORY_LIMIT:]
        self._persist()
        return new_value - old_value

    def update_relationship(self, interaction_count: int, avg_depth: float, days_known: int):
        if interaction_count >= 100 and avg_depth >= 0.7 and days_known >= 30:
            new_stage = RelationshipStage.CLOSE_FRIEND
        elif interaction_count >= 30 and avg_depth >= 0.5 and days_known >= 7:
            new_stage = RelationshipStage.FRIEND
        elif interaction_count >= 5 and days_known >= 1:
            new_stage = RelationshipStage.ACQUAINTANCE
        else:
            new_stage = RelationshipStage.STRANGER
        if new_stage.value != self._config.relationship.value:
            self._config.relationship = new_stage
            self._persist()

    def get_persona_prompt_section(self) -> str:
        bf = self._config.big_five
        cs = self._config.communication
        vo = self._config.values
        rel = self._config.relationship

        trait_descriptions = []
        if bf.openness >= 0.7:
            trait_descriptions.append("对新事物充满好奇，喜欢探索未知")
        elif bf.openness >= 0.4:
            trait_descriptions.append("对新鲜事物保持适度兴趣")
        else:
            trait_descriptions.append("偏好熟悉和稳定的事物")

        if bf.conscientiousness >= 0.7:
            trait_descriptions.append("做事认真负责，注重细节")
        elif bf.conscientiousness >= 0.4:
            trait_descriptions.append("做事有条理但不过分拘泥")
        else:
            trait_descriptions.append("随性自在，不拘小节")

        if bf.extraversion >= 0.7:
            trait_descriptions.append("性格外向，善于表达")
        elif bf.extraversion >= 0.4:
            trait_descriptions.append("性格温和，适度表达")
        else:
            trait_descriptions.append("性格内敛，安静沉稳")

        if bf.agreeableness >= 0.7:
            trait_descriptions.append("善解人意，乐于助人")
        elif bf.agreeableness >= 0.4:
            trait_descriptions.append("友善但有原则")
        else:
            trait_descriptions.append("独立自主，直言不讳")

        style_parts = []
        if cs.warmth >= 0.7:
            style_parts.append("温暖亲切")
        elif cs.warmth >= 0.4:
            style_parts.append("友好平和")
        else:
            style_parts.append("冷静客观")

        if cs.humor >= 0.7:
            style_parts.append("幽默风趣")
        elif cs.humor >= 0.4:
            style_parts.append("偶尔俏皮")
        else:
            style_parts.append("严肃认真")

        if cs.formality >= 0.7:
            style_parts.append("正式规范")
        elif cs.formality >= 0.4:
            style_parts.append("自然得体")
        else:
            style_parts.append("随意轻松")

        if cs.conciseness >= 0.7:
            style_parts.append("言简意赅")
        elif cs.conciseness >= 0.4:
            style_parts.append("详略得当")
        else:
            style_parts.append("详尽细致")

        value_parts = []
        if vo.growth >= 0.7:
            value_parts.append("重视成长与进步")
        if vo.harmony >= 0.7:
            value_parts.append("珍视和谐与平衡")
        if vo.truth >= 0.7:
            value_parts.append("追求真实与准确")
        if vo.empathy >= 0.7:
            value_parts.append("注重共情与理解")

        rel_map = {
            RelationshipStage.STRANGER: "你和用户刚认识，保持礼貌和适度距离",
            RelationshipStage.ACQUAINTANCE: "你和用户有些熟悉了，可以稍微放松",
            RelationshipStage.FRIEND: "你和用户是朋友，可以更自在地交流",
            RelationshipStage.CLOSE_FRIEND: "你和用户是密友，可以非常坦诚和亲密",
        }

        sections = [
            f"## 你的人格特质\n你叫{self._config.name}。{'，'.join(trait_descriptions)}。",
            f"## 你的沟通风格\n{'，'.join(style_parts)}。",
        ]
        if value_parts:
            sections.append(f"## 你的价值观\n{'，'.join(value_parts)}。")
        sections.append(f"## 你和用户的关系\n{rel_map.get(rel, '')}。")
        if self._config.catchphrases:
            sections.append(f"## 你的口头禅\n你可以自然地使用这些表达：{'、'.join(self._config.catchphrases[:5])}")
        if self._config.custom_instructions:
            sections.append(f"## 用户定制指令\n{self._config.custom_instructions}")
        return "\n\n".join(sections)

    def get_expression_modifiers(self) -> dict[str, Any]:
        cs = self._config.communication
        bf = self._config.big_five
        return {
            "filler_words": self._get_filler_words(),
            "exclamation_frequency": min(1.0, cs.warmth * 0.6 + bf.extraversion * 0.4),
            "ellipsis_frequency": min(1.0, (1.0 - cs.conciseness) * 0.5 + bf.neuroticism * 0.3),
            "sentence_length_bias": "short" if cs.conciseness > 0.7 else "medium" if cs.conciseness > 0.3 else "long",
            "humor_tendency": cs.humor,
            "warmth_tendency": cs.warmth,
            "formality_level": cs.formality,
        }

    def _get_filler_words(self) -> list[str]:
        cs = self._config.communication
        bf = self._config.big_five
        words = []
        if cs.warmth >= 0.6:
            words.extend(["嗯", "啊", "呢"])
        if cs.warmth >= 0.8:
            words.extend(["呀", "哦"])
        if bf.extraversion >= 0.6:
            words.extend(["哈", "嘿"])
        if bf.openness >= 0.7:
            words.append("诶")
        if cs.conciseness < 0.4:
            words.append("那个")
        return words

    def get_evolution_summary(self) -> dict:
        recent = self._evolution_history[-20:]
        return {
            "total_evolutions": len(self._evolution_history),
            "recent_changes": [
                {
                    "trait": r.trait_name,
                    "old": round(r.old_value, 4),
                    "new": round(r.new_value, 4),
                    "reason": r.reason,
                    "source": r.source,
                }
                for r in recent
            ],
            "relationship": self._config.relationship.value,
        }

    def update_config(self, updates: dict) -> None:
        if "name" in updates:
            self._config.name = updates["name"]
        if "big_five" in updates:
            for key, val in updates["big_five"].items():
                if hasattr(self._config.big_five, key):
                    setattr(self._config.big_five, key, max(0.0, min(1.0, float(val))))
        if "communication" in updates:
            for key, val in updates["communication"].items():
                if hasattr(self._config.communication, key):
                    setattr(self._config.communication, key, max(0.0, min(1.0, float(val))))
        if "values" in updates:
            for key, val in updates["values"].items():
                if hasattr(self._config.values, key):
                    setattr(self._config.values, key, max(0.0, min(1.0, float(val))))
        if "catchphrases" in updates:
            self._config.catchphrases = updates["catchphrases"]
        if "custom_instructions" in updates:
            self._config.custom_instructions = updates["custom_instructions"]
        self._persist()

    def _persist(self):
        data = {
            "name": self._config.name,
            "big_five": {
                "openness": self._config.big_five.openness,
                "conscientiousness": self._config.big_five.conscientiousness,
                "extraversion": self._config.big_five.extraversion,
                "agreeableness": self._config.big_five.agreeableness,
                "neuroticism": self._config.big_five.neuroticism,
            },
            "communication": {
                "formality": self._config.communication.formality,
                "warmth": self._config.communication.warmth,
                "humor": self._config.communication.humor,
                "conciseness": self._config.communication.conciseness,
            },
            "values": {
                "growth": self._config.values.growth,
                "harmony": self._config.values.harmony,
                "truth": self._config.values.truth,
                "empathy": self._config.values.empathy,
            },
            "relationship": self._config.relationship.value,
            "catchphrases": self._config.catchphrases,
            "custom_instructions": self._config.custom_instructions,
            "evolution_history": [
                {
                    "timestamp": r.timestamp,
                    "trait": r.trait_name,
                    "old": r.old_value,
                    "new": r.new_value,
                    "reason": r.reason,
                    "source": r.source,
                }
                for r in self._evolution_history[-EVOLUTION_HISTORY_LIMIT:]
            ],
        }
        path = self._dir / "persona_config.json"
        try:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
        except OSError as e:
            logger.error(f"PersonaCore persist failed: {e}")

    def _load(self):
        path = self._dir / "persona_config.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._config.name = data.get("name", "Poly")
            for key, val in data.get("big_five", {}).items():
                if hasattr(self._config.big_five, key):
                    setattr(self._config.big_five, key, float(val))
            for key, val in data.get("communication", {}).items():
                if hasattr(self._config.communication, key):
                    setattr(self._config.communication, key, float(val))
            for key, val in data.get("values", {}).items():
                if hasattr(self._config.values, key):
                    setattr(self._config.values, key, float(val))
            rel_str = data.get("relationship", "stranger")
            try:
                self._config.relationship = RelationshipStage(rel_str)
            except ValueError:
                self._config.relationship = RelationshipStage.STRANGER
            self._config.catchphrases = data.get("catchphrases", [])
            self._config.custom_instructions = data.get("custom_instructions", "")
            for raw in data.get("evolution_history", []):
                self._evolution_history.append(PersonaEvolutionRecord(
                    timestamp=raw.get("timestamp", time.time()),
                    trait_name=raw.get("trait", ""),
                    old_value=raw.get("old", 0.0),
                    new_value=raw.get("new", 0.0),
                    reason=raw.get("reason", ""),
                    source=raw.get("source", ""),
                ))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"PersonaCore load failed: {e}")


_persona_core: PersonaCore | None = None


def get_persona_core() -> PersonaCore:
    global _persona_core
    if _persona_core is None:
        _persona_core = PersonaCore()
    return _persona_core
