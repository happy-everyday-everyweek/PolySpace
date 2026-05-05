from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class ActionType(str, Enum):
    DIRECT_REPLY = "direct_reply"
    SEND_NEW_MESSAGE = "send_new_message"
    FETCH_KNOWLEDGE = "fetch_knowledge"
    WAIT = "wait"
    LISTENING = "listening"
    RETHINK_GOAL = "rethink_goal"
    END_CONVERSATION = "end_conversation"
    SAY_GOODBYE = "say_goodbye"
    BLOCK_AND_IGNORE = "block_and_ignore"
    FOLLOW_UP = "follow_up"
    PROACTIVE_REMIND = "proactive_remind"
    CONCERN_CHECK = "concern_check"


@dataclass
class Goal:
    description: str
    method: str
    reasoning: str
    created_at: datetime = field(default_factory=datetime.now)
    priority: int = 1
    status: str = "active"


@dataclass
class AttentionFocus:
    primary_topic: str = ""
    secondary_topics: list[str] = field(default_factory=list)
    topic_stack: list[str] = field(default_factory=list)
    last_shift: datetime = field(default_factory=datetime.now)

    def shift_to(self, topic: str):
        if self.primary_topic and self.primary_topic != topic:
            if self.primary_topic not in self.secondary_topics:
                self.secondary_topics.insert(0, self.primary_topic)
                if len(self.secondary_topics) > 3:
                    self.secondary_topics.pop()
        self.primary_topic = topic
        self.last_shift = datetime.now()

    def pop_topic(self) -> Optional[str]:
        if self.secondary_topics:
            old_primary = self.primary_topic
            self.primary_topic = self.secondary_topics.pop(0)
            self.last_shift = datetime.now()
            return old_primary
        return None


@dataclass
class ConversationState:
    last_user_message_time: Optional[datetime] = None
    consecutive_no_reply: int = 0
    total_messages: int = 0
    conversation_start: datetime = field(default_factory=datetime.now)
    topics: list[str] = field(default_factory=list)


@dataclass
class ThinkingChain:
    steps: list[str] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.5

    def to_display_text(self) -> str:
        if not self.steps:
            return ""
        parts = []
        for i, step in enumerate(self.steps, 1):
            parts.append(f"{i}. {step}")
        if self.conclusion:
            parts.append(f"=> {self.conclusion}")
        return "\n".join(parts)


COLD_FIELD_THRESHOLD = timedelta(seconds=60)
NO_REPLY_THRESHOLD = 3
REFLECTION_QUALITY_THRESHOLD = 0.6


class GoalAnalyzer:
    def __init__(self, llm_dispatcher):
        self._dispatcher = llm_dispatcher
        self._goals: list[Goal] = []
        self._max_goals = 3

    async def analyze_goal(self, conversation_info: str, observation_info: str) -> tuple[str, str, str]:
        messages = [
            {
                "role": "system",
                "content": (
                    "分析对话并确定当前目标。"
                    "考虑现有目标，决定是继续、修改还是开始新目标。"
                    "返回JSON: {goal, method, reasoning, action: continue|modify|new|complete}"
                ),
            },
            {
                "role": "user",
                "content": f"对话: {conversation_info}\n观察: {observation_info}\n"
                          f"当前目标: {[g.description for g in self._goals]}",
            },
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.DAILY, messages=messages)
        content = response.choices[0].message.content
        return content, "analyzed", "goal analysis"

    async def update_goals(self, new_goal: str, method: str, reasoning: str) -> None:
        goal = Goal(description=new_goal, method=method, reasoning=reasoning)
        if len(self._goals) >= self._max_goals:
            self._goals.sort(key=lambda g: g.priority)
            self._goals.pop(0)
        self._goals.append(goal)

    def get_all_goals(self) -> list[Goal]:
        return self._goals.copy()

    def get_active_goals(self) -> list[Goal]:
        return [g for g in self._goals if g.status == "active"]

    def complete_goal(self, description: str) -> None:
        for g in self._goals:
            if g.description == description:
                g.status = "completed"

    def clear_goals(self) -> None:
        self._goals.clear()


class PFCManager:
    def __init__(self, llm_dispatcher):
        self._dispatcher = llm_dispatcher
        self._goal_analyzer = GoalAnalyzer(llm_dispatcher)
        self._conversation_state = ConversationState()
        self._attention = AttentionFocus()
        self._last_reflection_score: float = 0.0
        self._proactive_pending: bool = False

    @property
    def goal_analyzer(self) -> GoalAnalyzer:
        return self._goal_analyzer

    @property
    def conversation_state(self) -> ConversationState:
        return self._conversation_state

    @property
    def attention(self) -> AttentionFocus:
        return self._attention

    def update_user_message_time(self) -> None:
        self._conversation_state.last_user_message_time = datetime.now()
        self._conversation_state.consecutive_no_reply = 0
        self._conversation_state.total_messages += 1

    def update_attention(self, topic: str):
        if topic and topic != self._attention.primary_topic:
            self._attention.shift_to(topic)

    def is_cold_field(self) -> bool:
        if not self._conversation_state.last_user_message_time:
            return False
        elapsed = datetime.now() - self._conversation_state.last_user_message_time
        return elapsed > COLD_FIELD_THRESHOLD

    def should_be_proactive(self, emotion_context: dict = None,
                             relationship: str = "stranger",
                             has_pending_tasks: bool = False) -> bool:
        if not has_pending_tasks and not self.is_cold_field():
            return False
        rel_weight = {"stranger": 0.2, "acquaintance": 0.4, "friend": 0.7, "close_friend": 0.9}
        weight = rel_weight.get(relationship, 0.2)
        if emotion_context:
            intensity = emotion_context.get("intensity", 0.3)
            if intensity > 0.7:
                weight *= 0.5
        import random
        return random.random() < weight

    async def plan_action(self, observation_info: str, conversation_info: str,
                           emotion_context: dict = None,
                           relationship: str = "stranger") -> tuple[ActionType, str, ThinkingChain]:
        is_cold = self.is_cold_field()
        no_reply = self._conversation_state.consecutive_no_reply >= NO_REPLY_THRESHOLD
        active_goals = self._goal_analyzer.get_active_goals()
        thinking = ThinkingChain()

        thinking.steps.append(f"观察: 冷场={is_cold}, 无回复次数={self._conversation_state.consecutive_no_reply}")
        thinking.steps.append(f"注意力焦点: {self._attention.primary_topic or '无'}")
        if active_goals:
            thinking.steps.append(f"活跃目标: {[g.description for g in active_goals]}")

        context_parts = [
            f"观察: {observation_info}",
            f"对话: {conversation_info}",
            f"冷场: {is_cold}",
            f"连续无回复: {self._conversation_state.consecutive_no_reply}",
            f"活跃目标: {[g.description for g in active_goals]}",
            f"注意力焦点: {self._attention.primary_topic or '无'}",
            f"关系阶段: {relationship}",
        ]

        if is_cold and no_reply:
            prompt = (
                "对话已经冷场且用户多次未回复。"
                "决定: 1) say_goodbye 优雅结束, 2) send_new_message 重新吸引。"
                "返回JSON: {action_type, reason}"
            )
        elif is_cold:
            prompt = (
                "对话已经冷场。决定: "
                "1) send_new_message 用相关话题重新吸引, "
                "2) wait 再等等, "
                "3) end_conversation。"
                "返回JSON: {action_type, reason}"
            )
        elif active_goals:
            prompt = (
                "有活跃目标。决定下一步行动。"
                "考虑: direct_reply, follow_up, fetch_knowledge, rethink_goal。"
                "返回JSON: {action_type, reason}"
            )
        else:
            prompt = (
                "基于观察和对话，决定下一步行动。"
                "可选: direct_reply, send_new_message, fetch_knowledge, "
                "wait, listening, rethink_goal, end_conversation, say_goodbye, follow_up。"
                "返回JSON: {action_type, reason}"
            )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "\n".join(context_parts)},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.DAILY, messages=messages)
        content = response.choices[0].message.content
        try:
            import json
            data = json.loads(content)
            action_str = data.get("action_type", "direct_reply")
            reason = data.get("reason", "")
            thinking.conclusion = reason
            thinking.confidence = 0.7
            try:
                action = ActionType(action_str)
            except ValueError:
                action = ActionType.DIRECT_REPLY
            return action, reason, thinking
        except (json.JSONDecodeError, ValueError):
            thinking.conclusion = content[:100]
            return ActionType.DIRECT_REPLY, content, thinking

    def reflect_on_reply(self, reply: str, emotion_context: dict = None) -> tuple[float, str]:
        score = 0.7
        suggestion = ""
        if not reply or len(reply.strip()) < 5:
            score = 0.3
            suggestion = "回复太短，可能需要更详细的回答"
        elif len(reply) > 500 and emotion_context and emotion_context.get("intensity", 0) < 0.3:
            score = 0.5
            suggestion = "情绪平静时回复过长，可以更简洁"
        if "我不确定" in reply or "可能" in reply:
            score -= 0.1
        self._last_reflection_score = score
        return score, suggestion

    async def decide_farewell(self, conversation_summary: str) -> tuple[bool, str]:
        messages = [
            {
                "role": "system",
                "content": (
                    "在结束对话前，决定是否需要告别消息。"
                    "考虑: 这是一次有意义的对话吗？用户可能还会回来吗？"
                    "返回JSON: {should_farewell: bool, message: string}"
                ),
            },
            {"role": "user", "content": f"对话摘要: {conversation_summary}"},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.INTENT, messages=messages)
        content = response.choices[0].message.content
        try:
            import json
            data = json.loads(content)
            return data.get("should_farewell", False), data.get("message", "")
        except (json.JSONDecodeError, ValueError):
            return False, ""
