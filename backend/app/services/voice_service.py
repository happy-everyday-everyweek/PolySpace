from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VoiceAction(str, Enum):
    STT = "stt"
    TTS = "tts"
    REALTIME_START = "realtime_start"
    REALTIME_STOP = "realtime_stop"
    WAKE_WORD_DETECT = "wake_word_detect"


class VoiceState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    REALTIME = "realtime"


class STTRequest(BaseModel):
    audio_data: str
    language: str = "zh"
    sample_rate: int = 16000


class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    speed: float = 1.0
    language: str = "zh"


class VoiceSession(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: VoiceState = VoiceState.IDLE
    language: str = "zh"
    wake_word_enabled: bool = False
    wake_word: str = "你好聚境"
    auto_tts: bool = True
    device_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class VoiceService:
    def __init__(self):
        self._sessions: dict[str, VoiceSession] = {}
        self._tts_cache: dict[str, str] = {}

    async def create_session(self, device_id: Optional[str] = None, language: str = "zh") -> VoiceSession:
        session = VoiceSession(device_id=device_id, language=language)
        self._sessions[session.id] = session
        return session

    async def get_session(self, session_id: str) -> Optional[VoiceSession]:
        return self._sessions.get(session_id)

    async def list_sessions(self) -> list[VoiceSession]:
        return list(self._sessions.values())

    async def close_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def speech_to_text(self, session_id: str, audio_data: str, language: str = "zh") -> dict:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        session.state = VoiceState.PROCESSING
        try:
            from app.core.llm.gateway import llm_gateway
            prompt = f"""Transcribe the following audio data. Language: {language}
If the audio data is base64 encoded, decode and transcribe it.
Return a JSON object with: {{"text": "transcribed text", "confidence": 0.0-1.0, "language": "detected language"}}
If unable to transcribe, return: {{"text": "", "confidence": 0.0, "language": "{language}"}}"""
            response = await llm_gateway.acompletion(
                messages=[{"role": "user", "content": prompt}],
                task_category="daily",
            )
            content = response.get("content", "{}")
            try:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    result = json.loads(content[start:end])
                else:
                    result = {"text": "", "confidence": 0.0, "language": language}
            except json.JSONDecodeError:
                result = {"text": content, "confidence": 0.5, "language": language}
            session.state = VoiceState.IDLE
            return result
        except Exception as e:
            session.state = VoiceState.IDLE
            return {"error": str(e), "text": "", "confidence": 0.0}

    async def text_to_speech(self, session_id: str, text: str, voice: str = "default", speed: float = 1.0) -> dict:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        session.state = VoiceState.SPEAKING
        try:
            cache_key = f"{text}:{voice}:{speed}"
            if cache_key in self._tts_cache:
                session.state = VoiceState.IDLE
                return {"audio_data": self._tts_cache[cache_key], "cached": True}
            session.state = VoiceState.IDLE
            return {"audio_data": "", "text": text, "voice": voice, "speed": speed, "status": "tts_ready"}
        except Exception as e:
            session.state = VoiceState.IDLE
            return {"error": str(e)}

    async def start_realtime(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        session.state = VoiceState.REALTIME
        return {"status": "realtime_started", "session_id": session_id}

    async def stop_realtime(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        session.state = VoiceState.IDLE
        return {"status": "realtime_stopped", "session_id": session_id}

    async def detect_wake_word(self, session_id: str, audio_data: str) -> dict:
        session = self._sessions.get(session_id)
        if not session or not session.wake_word_enabled:
            return {"detected": False}
        return {"detected": False, "wake_word": session.wake_word}

    async def get_voices(self) -> list[dict]:
        return [
            {"id": "default", "name": "默认", "language": "zh", "gender": "neutral"},
            {"id": "female_gentle", "name": "温柔女声", "language": "zh", "gender": "female"},
            {"id": "male_professional", "name": "专业男声", "language": "zh", "gender": "male"},
            {"id": "child", "name": "童声", "language": "zh", "gender": "neutral"},
            {"id": "en_default", "name": "English Default", "language": "en", "gender": "neutral"},
        ]


voice_service = VoiceService()
