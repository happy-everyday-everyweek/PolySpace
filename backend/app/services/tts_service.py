from __future__ import annotations

import asyncio
import io
import logging
import os
import wave
from typing import Optional

logger = logging.getLogger(__name__)

VIBEVOICE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "VibeVoice-main", "VibeVoice-main"
)


class TTSService:
    def __init__(self) -> None:
        self._vibevoice_service = None
        self._vibevoice_loaded = False
        self._vibevoice_available: Optional[bool] = None

    def _check_vibevoice(self) -> bool:
        if self._vibevoice_available is not None:
            return self._vibevoice_available
        app_path = os.path.join(VIBEVOICE_DIR, "demo", "web", "app.py")
        self._vibevoice_available = os.path.exists(app_path)
        if not self._vibevoice_available:
            logger.info("VibeVoice not found at %s, TTS will use fallback", VIBEVOICE_DIR)
        return self._vibevoice_available

    async def _load_vibevoice(self):
        if self._vibevoice_loaded:
            return self._vibevoice_service is not None
        self._vibevoice_loaded = True

        if not self._check_vibevoice():
            return False

        try:
            import sys
            vv_path = VIBEVOICE_DIR
            if vv_path not in sys.path:
                sys.path.insert(0, vv_path)

            from demo.web.app import StreamingTTSService

            model_path = os.environ.get("VIBEVOICE_MODEL_PATH", "VibeVoice/VibeVoice")
            device = os.environ.get("VIBEVOICE_DEVICE", "cpu")
            steps = int(os.environ.get("VIBEVOICE_STEPS", "5"))

            self._vibevoice_service = StreamingTTSService(
                model_path=model_path,
                device=device,
                inference_steps=steps,
            )
            self._vibevoice_service.load()
            logger.info("VibeVoice TTS service loaded successfully")
            return True
        except Exception as e:
            logger.warning("Failed to load VibeVoice: %s", e)
            self._vibevoice_service = None
            return False

    async def generate(self, text: str, voice: str = "en-Carter_man") -> bytes:
        vv_ok = await self._load_vibevoice()
        if vv_ok and self._vibevoice_service:
            return await self._generate_vibevoice(text, voice)
        return self._generate_silence_wav(len(text))

    async def _generate_vibevoice(self, text: str, voice: str) -> bytes:
        loop = asyncio.get_event_loop()

        def _sync_generate():
            audio_chunks = []
            try:
                for chunk in self._vibevoice_service.stream(
                    text=text,
                    voice_key=voice,
                    cfg_scale=1.5,
                    do_sample=False,
                ):
                    if chunk is not None:
                        audio_chunks.append(chunk)
            except Exception as e:
                logger.error("VibeVoice streaming error: %s", e)

            if not audio_chunks:
                return self._generate_silence_wav(len(text))

            import numpy as np
            all_audio = np.concatenate(audio_chunks)
            return self._numpy_to_wav(all_audio, self._vibevoice_service.sample_rate)

        return await loop.run_in_executor(None, _sync_generate)

    def _numpy_to_wav(self, audio_data, sample_rate: int) -> bytes:
        import numpy as np

        if isinstance(audio_data, np.ndarray):
            if audio_data.dtype in (np.float32, np.float64):
                audio_data = np.clip(audio_data, -1.0, 1.0)
                audio_data = (audio_data * 32767).astype(np.int16)
            elif audio_data.dtype != np.int16:
                audio_data = audio_data.astype(np.int16)

        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
        return buf.getvalue()

    def _generate_silence_wav(self, char_count: int) -> bytes:
        duration_ms = max(500, char_count * 60)
        sample_rate = 22050
        num_samples = int(sample_rate * duration_ms / 1000)
        audio_data = b'\x00\x00' * num_samples

        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        return buf.getvalue()


tts_service = TTSService()
