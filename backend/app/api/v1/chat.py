import json
import uuid
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.exceptions import ServiceUnavailableError
from app.dependencies import container

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: Optional[str] = "agent"
    operation_path: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: list[dict] = []
    cards: list[dict] = []
    emotion: dict = {}
    inner_voice: Optional[dict] = None
    action_type: str = "direct_reply"
    reflection: Optional[dict] = None


def _get_chat_service():
    return container.get("chat_service")


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    chat_service = _get_chat_service()

    if chat_service is None:
        return ChatResponse(
            session_id=session_id,
            reply=f"收到: {request.message}",
            tool_calls=[],
            cards=[],
            emotion={
                "label": "平淡中性", "discrete": "neutral",
                "valence": 0.5, "arousal": 0.3, "dominance": 0.5,
                "intensity": 0.0, "intensity_desc": "低",
            },
            inner_voice=None,
            action_type="direct_reply",
        )

    try:
        result = await chat_service.process_message(request.message, session_id)
        return ChatResponse(
            session_id=result["session_id"],
            reply=result["reply"],
            tool_calls=result.get("tool_calls", []),
            cards=result.get("cards", []),
            emotion=result.get("emotion", {}),
            inner_voice=result.get("inner_voice"),
            action_type=result.get("action_type", "direct_reply"),
            reflection=result.get("reflection"),
        )
    except Exception as e:
        raise ServiceUnavailableError(
            message=f"Chat service error: {str(e)}",
            service="chat_service",
        )


@router.post("/stream")
async def stream_message(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    chat_service = _get_chat_service()

    if chat_service is None:
        async def fallback():
            yield f"data: {json.dumps({'type': 'content', 'data': {'content': f'收到: {request.message}'}})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'data': {'session_id': session_id}})}\n\n"
        return StreamingResponse(fallback(), media_type="text/event-stream")

    async def event_generator():
        try:
            async for chunk in chat_service.process_message_stream(request.message, session_id):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_chunk = {
                "type": "error",
                "data": {"message": str(e)},
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    return {"session_id": session_id, "messages": []}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    return {"status": "ok", "session_id": session_id}


@router.get("/emotion")
async def get_current_emotion():
    chat_service = _get_chat_service()
    if chat_service is None:
        return {
            "label": "平淡中性", "discrete": "neutral",
            "valence": 0.5, "arousal": 0.3, "dominance": 0.5,
            "intensity": 0.0, "intensity_desc": "低",
        }
    if hasattr(chat_service, "get_emotion_context"):
        return chat_service.get_emotion_context()
    if hasattr(chat_service, "_heartflow"):
        return chat_service._heartflow.get_emotion_context()
    return {
        "label": "平淡中性", "discrete": "neutral",
        "valence": 0.5, "arousal": 0.3, "dominance": 0.5,
        "intensity": 0.0, "intensity_desc": "低",
    }


@router.get("/persona")
async def get_current_persona():
    chat_service = _get_chat_service()
    if chat_service is None:
        return {"name": "Poly", "relationship": "stranger"}
    if hasattr(chat_service, "get_persona_info"):
        return chat_service.get_persona_info()
    persona = getattr(chat_service, "_persona", None)
    if persona is None:
        return {"name": "Poly", "relationship": "stranger"}
    return {
        "name": persona.config.name,
        "relationship": persona.relationship.value,
        "big_five": {
            "openness": persona.config.big_five.openness,
            "conscientiousness": persona.config.big_five.conscientiousness,
            "extraversion": persona.config.big_five.extraversion,
            "agreeableness": persona.config.big_five.agreeableness,
            "neuroticism": persona.config.big_five.neuroticism,
        },
        "communication": {
            "formality": persona.config.communication.formality,
            "warmth": persona.config.communication.warmth,
            "humor": persona.config.communication.humor,
            "conciseness": persona.config.communication.conciseness,
        },
        "evolution_summary": persona.get_evolution_summary(),
    }
