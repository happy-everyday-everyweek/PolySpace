import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.core.coordination.context.habit_learner import HabitLearner, get_habit_learner

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    predicted_action: str
    predicted_tool: str
    predicted_info: str
    best_timing_hour: int
    confidence: float
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "predicted_action": self.predicted_action,
            "predicted_tool": self.predicted_tool,
            "predicted_info": self.predicted_info,
            "best_timing_hour": self.best_timing_hour,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


class BehaviorPredictor:
    def __init__(self, habit_learner: Optional[HabitLearner] = None):
        self._learner = habit_learner or get_habit_learner()
        self._prediction_history: list[dict] = []
        self._max_history = 100
        self._ab_groups: dict[str, str] = {}

    def predict_next_action(self, current_context: dict, user_profile: dict) -> Prediction:
        hour = time.localtime().tm_hour
        activity = user_profile.get("activity", "unknown")
        attention = user_profile.get("attention", "none")
        habit_prediction = self._learner.predict_activity(hour)
        predicted_action = self._infer_action(activity, attention, current_context)
        predicted_tool = self._infer_tool(attention, current_context)
        predicted_info = self._infer_info(current_context)
        best_hour = self._infer_best_timing(habit_prediction, hour)
        confidence = 0.3
        if habit_prediction:
            confidence = max(confidence, habit_prediction.get("confidence", 0.3) * 0.8)
        reasoning = f"Based on current activity={activity}, attention={attention}, hour={hour}"
        if habit_prediction:
            reasoning += f", habit suggests {habit_prediction['activity']}"
        prediction = Prediction(
            predicted_action=predicted_action,
            predicted_tool=predicted_tool,
            predicted_info=predicted_info,
            best_timing_hour=best_hour,
            confidence=confidence,
            reasoning=reasoning,
        )
        self._prediction_history.append({
            "prediction": prediction.to_dict(),
            "context_snapshot": {"activity": activity, "attention": attention, "hour": hour},
            "timestamp": time.time(),
        })
        if len(self._prediction_history) > self._max_history:
            self._prediction_history = self._prediction_history[-self._max_history:]
        return prediction

    def _infer_action(self, activity: str, attention: str, context: dict) -> str:
        if attention == "code":
            return "continue_coding"
        if attention == "document":
            return "continue_writing"
        if attention == "email":
            return "process_emails"
        if attention == "chat":
            return "respond_messages"
        if activity == "in_meeting":
            return "meeting_notes"
        if activity == "idle":
            return "suggest_task"
        return "general_assistance"

    def _infer_tool(self, attention: str, context: dict) -> str:
        tool_map = {
            "code": "code_editor",
            "document": "document_editor",
            "email": "email_client",
            "chat": "chat_panel",
            "browser": "browser",
            "calendar": "calendar",
        }
        return tool_map.get(attention, "workspace")

    def _infer_info(self, context: dict) -> str:
        sources = context.get("sources", {})
        if "email" in sources:
            return "unread_emails_summary"
        if "calendar" in sources:
            return "upcoming_events"
        if "notification" in sources:
            return "pending_notifications"
        return "daily_briefing"

    def _infer_best_timing(self, habit_prediction: Optional[dict], current_hour: int) -> int:
        if habit_prediction and habit_prediction.get("confidence", 0) > 0.5:
            return current_hour
        productive_hours = [9, 10, 11, 14, 15, 16]
        for h in productive_hours:
            if h > current_hour:
                return h
        return current_hour

    def record_outcome(self, prediction_id: str, actual_action: str, was_helpful: bool) -> None:
        for entry in self._prediction_history:
            if entry.get("prediction", {}).get("predicted_action") == prediction_id:
                entry["actual_action"] = actual_action
                entry["was_helpful"] = was_helpful
                break

    def get_prediction_accuracy(self) -> dict:
        if not self._prediction_history:
            return {"accuracy": 0.0, "total": 0, "correct": 0}
        evaluated = [e for e in self._prediction_history if "was_helpful" in e]
        correct = sum(1 for e in evaluated if e["was_helpful"])
        return {
            "accuracy": correct / len(evaluated) if evaluated else 0.0,
            "total": len(evaluated),
            "correct": correct,
        }

    def assign_ab_group(self, user_id: str) -> str:
        if user_id not in self._ab_groups:
            self._ab_groups[user_id] = "A" if hash(user_id) % 2 == 0 else "B"
        return self._ab_groups[user_id]

    def get_history(self, limit: int = 20) -> list[dict]:
        return self._prediction_history[-limit:]


_predictor: Optional[BehaviorPredictor] = None


def get_behavior_predictor() -> BehaviorPredictor:
    global _predictor
    if _predictor is None:
        _predictor = BehaviorPredictor()
    return _predictor
