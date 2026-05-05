import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ConversationGoal:
    goal_id: str
    description: str
    status: str = "active"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"goal_id": self.goal_id, "description": self.description, "status": self.status}


class ConversationalProactiveService:
    def __init__(self, llm_dispatcher=None):
        self._dispatcher = llm_dispatcher
        self._active_conversations: dict[str, dict] = {}
        self._goals: list[ConversationGoal] = []
        self._max_goals = 5
        self._conversation_history: list[dict] = []
        self._max_history = 100

    async def initiate_conversation(self, topic: str, reason: str, context: dict) -> dict:
        conv_id = f"conv_{int(time.time())}_{hash(topic) % 1000}"
        goal = ConversationGoal(goal_id=conv_id, description=topic)
        self._goals.append(goal)
        if len(self._goals) > self._max_goals:
            self._goals = self._goals[-self._max_goals:]
        opening = await self._generate_opening(topic, reason, context)
        conversation = {
            "conv_id": conv_id,
            "topic": topic,
            "reason": reason,
            "opening": opening,
            "status": "active",
            "started_at": time.time(),
            "messages": [{"role": "assistant", "content": opening, "timestamp": time.time()}],
        }
        self._active_conversations[conv_id] = conversation
        self._conversation_history.append({"type": "initiated", "conv_id": conv_id, "topic": topic})
        return conversation

    async def _generate_opening(self, topic: str, reason: str, context: dict) -> str:
        if self._dispatcher:
            from app.core.llm.dispatcher import TaskCategory
            prompt = (
                f"Generate a natural, non-intrusive opening message for a proactive conversation.\n"
                f"Topic: {topic}\nReason: {reason}\n"
                f"Rules: Be brief (1-2 sentences). Sound natural, not robotic. Do not use emojis."
            )
            try:
                response = await self._dispatcher.dispatch(TaskCategory.DAILY, messages=[{"role": "user", "content": prompt}])
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Opening generation failed: {e}")
        return f"I noticed something about {topic}. Would you like to discuss it?"

    async def continue_conversation(self, conv_id: str, user_response: str) -> Optional[dict]:
        conv = self._active_conversations.get(conv_id)
        if not conv:
            return None
        conv["messages"].append({"role": "user", "content": user_response, "timestamp": time.time()})
        reply = await self._generate_reply(conv, user_response)
        conv["messages"].append({"role": "assistant", "content": reply, "timestamp": time.time()})
        return {"conv_id": conv_id, "reply": reply}

    async def _generate_reply(self, conv: dict, user_response: str) -> str:
        if self._dispatcher:
            from app.core.llm.dispatcher import TaskCategory
            history = "\n".join([f"{m['role']}: {m['content']}" for m in conv["messages"][-6:]])
            prompt = (
                f"Continue this proactive conversation naturally.\n"
                f"Topic: {conv['topic']}\nHistory:\n{history}\n"
                f"Rules: Be helpful and concise. Guide toward the goal. Do not use emojis."
            )
            try:
                response = await self._dispatcher.dispatch(TaskCategory.DAILY, messages=[{"role": "user", "content": prompt}])
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Reply generation failed: {e}")
        return "I understand. Let me know if you need anything else."

    def end_conversation(self, conv_id: str, outcome: str = "completed") -> bool:
        conv = self._active_conversations.get(conv_id)
        if conv:
            conv["status"] = outcome
            self._conversation_history.append({"type": "ended", "conv_id": conv_id, "outcome": outcome})
            del self._active_conversations[conv_id]
            for goal in self._goals:
                if goal.goal_id == conv_id:
                    goal.status = outcome
            return True
        return False

    def track_outcome(self, conv_id: str, user_adopted: bool) -> None:
        self._conversation_history.append({
            "type": "outcome_tracked",
            "conv_id": conv_id,
            "user_adopted": user_adopted,
        })

    def get_active_conversations(self) -> list[dict]:
        return [
            {"conv_id": k, "topic": v["topic"], "status": v["status"], "message_count": len(v["messages"])}
            for k, v in self._active_conversations.items()
        ]

    def get_history(self, limit: int = 20) -> list[dict]:
        return self._conversation_history[-limit:]


_service: Optional[ConversationalProactiveService] = None


def get_conversational_service() -> ConversationalProactiveService:
    global _service
    if _service is None:
        _service = ConversationalProactiveService()
    return _service
