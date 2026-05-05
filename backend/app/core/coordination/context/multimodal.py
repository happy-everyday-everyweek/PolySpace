import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Scene(str, Enum):
    DEEP_CODING = "deep_coding"
    DOCUMENT_WRITING = "document_writing"
    MEETING = "meeting"
    EMAIL_PROCESSING = "email_processing"
    READING = "reading"
    NOTE_TAKING = "note_taking"
    SEARCHING = "searching"
    SHOPPING = "shopping"
    SOCIAL = "social"
    ENTERTAINMENT = "entertainment"
    COMMUTING = "commuting"
    TRANSITION = "transition"
    IDLE = "idle"
    UNKNOWN = "unknown"


@dataclass
class SceneResult:
    scene: Scene
    confidence: float
    sub_scene: str = ""
    suggested_services: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "scene": self.scene.value,
            "confidence": self.confidence,
            "sub_scene": self.sub_scene,
            "suggested_services": self.suggested_services,
        }


SCENE_SERVICE_MAP = {
    Scene.DEEP_CODING: ["focus_protector", "idea_spark", "doc_suggestion"],
    Scene.DOCUMENT_WRITING: ["writing_coach", "doc_suggestion"],
    Scene.MEETING: ["meeting_prep", "focus_protector"],
    Scene.EMAIL_PROCESSING: ["smart_followup", "deadline_guard"],
    Scene.READING: ["learning_path", "context_news"],
    Scene.SEARCHING: ["doc_suggestion", "learning_path"],
    Scene.SHOPPING: ["expense_tracker"],
    Scene.SOCIAL: ["social_reminder", "smart_followup"],
    Scene.COMMUTING: ["commute_assistant", "context_news"],
    Scene.IDLE: ["daily_briefing", "proactive_greeting", "wellness_guard"],
}


class SceneDetector:
    def __init__(self, llm_dispatcher=None):
        self._dispatcher = llm_dispatcher
        self._current_scene: Optional[SceneResult] = None
        self._scene_history: list[SceneResult] = []
        self._max_history = 50

    async def detect(self, context: dict, user_profile: dict) -> SceneResult:
        activity = user_profile.get("activity", "unknown")
        attention = user_profile.get("attention", "none")
        sources = context.get("sources", {})
        scene = self._infer_scene(activity, attention, sources)
        confidence = self._compute_confidence(activity, attention, sources)
        suggested = SCENE_SERVICE_MAP.get(scene, [])
        result = SceneResult(
            scene=scene,
            confidence=confidence,
            suggested_services=suggested,
        )
        if self._current_scene and self._current_scene.scene != scene:
            result.sub_scene = f"transition_from_{self._current_scene.scene.value}"
        self._current_scene = result
        self._scene_history.append(result)
        if len(self._scene_history) > self._max_history:
            self._scene_history = self._scene_history[-self._max_history:]
        return result

    def _infer_scene(self, activity: str, attention: str, sources: dict) -> Scene:
        if attention == "code":
            return Scene.DEEP_CODING
        if attention == "document":
            return Scene.DOCUMENT_WRITING
        if activity == "in_meeting":
            return Scene.MEETING
        if attention == "email":
            return Scene.EMAIL_PROCESSING
        if attention == "browser":
            screen_data = sources.get("screen", {}).get("latest", {})
            app = screen_data.get("app", "") if screen_data else ""
            if any(s in app.lower() for s in ("taobao", "jd", "amazon")):
                return Scene.SHOPPING
            return Scene.SEARCHING
        if attention == "chat":
            return Scene.SOCIAL
        if activity == "idle":
            return Scene.IDLE
        return Scene.UNKNOWN

    def _compute_confidence(self, activity: str, attention: str, sources: dict) -> float:
        score = 0.3
        if activity != "unknown":
            score += 0.2
        if attention != "none":
            score += 0.2
        if len(sources) >= 2:
            score += 0.15
        if len(sources) >= 4:
            score += 0.15
        return min(1.0, score)

    def get_current_scene(self) -> Optional[dict]:
        return self._current_scene.to_dict() if self._current_scene else None

    def get_history(self, limit: int = 20) -> list[dict]:
        return [s.to_dict() for s in self._scene_history[-limit:]]


class MultimodalContextUnderstanding:
    def __init__(self, llm_dispatcher=None):
        self._dispatcher = llm_dispatcher
        self._scene_detector = SceneDetector(llm_dispatcher)

    async def understand(self, context: dict, user_profile: dict) -> dict:
        scene_result = await self._scene_detector.detect(context, user_profile)
        screen_understanding = self._understand_screen(context)
        communication_understanding = self._understand_communication(context)
        work_understanding = self._understand_work(context)
        life_understanding = self._understand_life(context, user_profile)
        return {
            "scene": scene_result.to_dict(),
            "screen": screen_understanding,
            "communication": communication_understanding,
            "work": work_understanding,
            "life": life_understanding,
            "timestamp": time.time(),
        }

    def _understand_screen(self, context: dict) -> dict:
        sources = context.get("sources", {})
        screen_data = sources.get("screen", {}).get("latest", {})
        if not screen_data:
            return {"understood": False, "reason": "no_screen_data"}
        return {
            "understood": True,
            "current_app": screen_data.get("app", "unknown"),
            "has_text": bool(screen_data.get("ocr_text")),
            "is_sensitive": screen_data.get("is_sensitive", False),
        }

    def _understand_communication(self, context: dict) -> dict:
        sources = context.get("sources", {})
        has_chat = "chat" in sources
        has_email = "email" in sources
        has_notification = "notification" in sources
        return {
            "channels_active": [],
            "has_pending": has_chat or has_email or has_notification,
            "chat_active": has_chat,
            "email_active": has_email,
            "notification_active": has_notification,
        }

    def _understand_work(self, context: dict) -> dict:
        sources = context.get("sources", {})
        return {
            "has_calendar": "calendar" in sources,
            "has_tasks": "notification" in sources,
            "has_files": "file_operation" in sources,
            "workload_indicators": len(sources),
        }

    def _understand_life(self, context: dict, user_profile: dict) -> dict:
        return {
            "activity": user_profile.get("activity", "unknown"),
            "mood": user_profile.get("mood", "unknown"),
            "attention": user_profile.get("attention", "none"),
        }


_understanding: Optional[MultimodalContextUnderstanding] = None


def get_multimodal_understanding() -> MultimodalContextUnderstanding:
    global _understanding
    if _understanding is None:
        _understanding = MultimodalContextUnderstanding()
    return _understanding
