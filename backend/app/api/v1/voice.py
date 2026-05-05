from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.voice_service import STTRequest, TTSRequest, voice_service

router = APIRouter()


class VoiceSessionCreate(BaseModel):
    device_id: Optional[str] = None
    language: str = "zh"


@router.post("/sessions")
async def create_voice_session(req: VoiceSessionCreate):
    session = await voice_service.create_session(device_id=req.device_id, language=req.language)
    return session.model_dump()


@router.get("/sessions")
async def list_voice_sessions():
    sessions = await voice_service.list_sessions()
    return {"sessions": [s.model_dump() for s in sessions]}


@router.get("/sessions/{session_id}")
async def get_voice_session(session_id: str):
    session = await voice_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Voice session not found")
    return session.model_dump()


@router.delete("/sessions/{session_id}")
async def close_voice_session(session_id: str):
    closed = await voice_service.close_session(session_id)
    if not closed:
        raise HTTPException(status_code=404, detail="Voice session not found")
    return {"status": "closed"}


@router.post("/stt")
async def speech_to_text(session_id: str, req: STTRequest):
    result = await voice_service.speech_to_text(session_id, req.audio_data, req.language)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/tts")
async def text_to_speech(session_id: str, req: TTSRequest):
    result = await voice_service.text_to_speech(session_id, req.text, req.voice, req.speed)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/realtime/{session_id}/start")
async def start_realtime(session_id: str):
    result = await voice_service.start_realtime(session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/realtime/{session_id}/stop")
async def stop_realtime(session_id: str):
    result = await voice_service.stop_realtime(session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/voices")
async def list_voices():
    voices = await voice_service.get_voices()
    return {"voices": voices}
