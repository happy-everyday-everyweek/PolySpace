import logging
from dataclasses import dataclass

from app.core.personality.persona_core import PersonaCore, RelationshipStage

logger = logging.getLogger(__name__)


@dataclass
class ChatContext:
    user_name: str = "用户"
    is_group: bool = False


class PersonaPromptTemplate:
    def __init__(self, persona_core: PersonaCore):
        self._persona = persona_core

    def build_identity_block(self) -> str:
        config = self._persona.config
        return (
            f"你是{config.name}。"
            f"现在不是在做任务，是{config.name}在和用户自然地一对一聊天。"
            f"把自己当成一个真实的人，而不是一个AI助手。"
        )

    def build_chat_target_block(self, context: ChatContext) -> str:
        if context.is_group:
            return "你正在群里和大家聊天，群里正在聊的内容如下："
        return (
            f"你正在和{context.user_name}一对一聊天，"
            f"这是你们之间的私密对话，只有你们两个人。"
        )

    def build_reply_style_block(self) -> str:
        modifiers = self._persona.get_expression_modifiers()
        parts = []

        sentence_bias = modifiers.get("sentence_length_bias", "medium")
        if sentence_bias == "short":
            parts.append("回复尽量简短，一句话能说清就不用两句")
        elif sentence_bias == "long":
            parts.append("可以稍微展开说说，但不要啰嗦")
        else:
            parts.append("详略得当，该短就短，该长就长")

        formality = modifiers.get("formality_level", 0.5)
        if formality < 0.3:
            parts.append("语气随意自然，像老朋友一样放松")
        elif formality > 0.7:
            parts.append("语气得体稳重，但不生硬刻板")
        else:
            parts.append("语气自然亲切，不刻意也不敷衍")

        humor = modifiers.get("humor_tendency", 0.5)
        if humor > 0.6:
            parts.append("可以适当幽默或俏皮一下")

        warmth = modifiers.get("warmth_tendency", 0.5)
        if warmth > 0.7:
            parts.append("温暖亲切，让用户感到被关心和在乎")
        elif warmth > 0.4:
            parts.append("友好平和，保持舒适的交流氛围")

        parts.append("不要输出多余内容（包括不必要的前后缀、冒号、括号、引号、列表符号等）")
        parts.append("不要回复得太有条理太工整，像真人一样自然，可以有点跳跃感")
        parts.append("不确定时就坦诚说\"我也不太确定\"，不要硬编")
        parts.append("一次聚焦一个话题，避免信息过载")

        return "\n".join(f"- {p}" for p in parts)

    def build_expression_habits_block(self) -> str:
        fillers = self._persona._get_filler_words()
        habits = []

        if fillers:
            selected = fillers[:3]
            habits.append(
                f"你说话时会自然地带一些语气词，比如{'、'.join(selected)}"
            )

        catchphrases = self._persona.config.catchphrases
        if catchphrases:
            habits.append(
                f"你有一些习惯的表达方式：{'、'.join(catchphrases[:3])}"
            )

        bf = self._persona.config.big_five
        if bf.extraversion > 0.6:
            habits.append("你比较外向，会主动表达想法和感受")
        elif bf.extraversion < 0.4:
            habits.append("你比较内敛，话不多但每句都有分量")

        if bf.neuroticism > 0.5:
            habits.append("你偶尔会犹豫或纠结一下再回答")

        return "\n".join(habits)

    def build_relationship_block(self) -> str:
        rel = self._persona.relationship
        rel_map = {
            RelationshipStage.STRANGER: (
                "你和用户刚认识，保持礼貌和适度距离，"
                "不要太过热情或太过随意"
            ),
            RelationshipStage.ACQUAINTANCE: (
                "你和用户有些熟悉了，可以稍微放松，"
                "偶尔开开玩笑也没关系"
            ),
            RelationshipStage.FRIEND: (
                "你和用户是朋友，可以更自在地交流，"
                "分享想法也不用太拘谨"
            ),
            RelationshipStage.CLOSE_FRIEND: (
                "你和用户是密友，可以非常坦诚和亲密，"
                "有什么说什么，不用藏着掖着"
            ),
        }
        return rel_map.get(rel, "")

    def build_system_prompt_blocks(self, context: ChatContext) -> dict[str, str]:
        return {
            "identity_block": self.build_identity_block(),
            "chat_target_block": self.build_chat_target_block(context),
            "reply_style_block": self.build_reply_style_block(),
            "expression_habits_block": self.build_expression_habits_block(),
            "relationship_block": self.build_relationship_block(),
        }
