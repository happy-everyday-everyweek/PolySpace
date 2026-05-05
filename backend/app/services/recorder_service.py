from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import subprocess
from typing import Optional

from app.models.tables import Recording

logger = logging.getLogger(__name__)


class RecorderService:
    def __init__(self) -> None:
        self._ffmpeg_available: Optional[bool] = None

    def _check_ffmpeg(self) -> bool:
        if self._ffmpeg_available is not None:
            return self._ffmpeg_available
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=5,
            )
            self._ffmpeg_available = result.returncode == 0
        except Exception:
            self._ffmpeg_available = False
            logger.warning("FFmpeg not available, video processing features disabled")
        return self._ffmpeg_available

    async def analyze_recording(self, recording: Recording, action: str, params: dict) -> dict:
        key_frames = self._load_key_frames(recording)

        if action == "summarize_recording":
            return await self._analyze_with_vision(recording, key_frames, action, params)
        elif action == "extract_highlights":
            return await self._analyze_with_vision(recording, key_frames, action, params)
        elif action == "suggest_title":
            return await self._analyze_with_vision(recording, key_frames, action, params)
        elif action == "generate_chapters":
            return await self._analyze_with_vision(recording, key_frames, action, params)
        elif action == "extract_text":
            return await self._ocr_analysis(recording, key_frames, params)
        else:
            return await self._analyze_with_vision(recording, key_frames, action, params)

    def _load_key_frames(self, recording: Recording) -> list[str]:
        frames: list[str] = []
        if not recording.key_frames_dir or not os.path.exists(recording.key_frames_dir):
            return frames
        try:
            for fname in sorted(os.listdir(recording.key_frames_dir)):
                fpath = os.path.join(recording.key_frames_dir, fname)
                if fname.endswith((".jpg", ".jpeg", ".png")):
                    with open(fpath, "rb") as f:
                        data = base64.b64encode(f.read()).decode("utf-8")
                        frames.append(f"data:image/jpeg;base64,{data}")
        except Exception as e:
            logger.warning("Failed to load key frames: %s", e)
        return frames

    async def _analyze_with_vision(
        self, recording: Recording, key_frames: list[str], action: str, params: dict
    ) -> dict:
        from app.core.llm.dispatcher import ModelDispatcher, TaskCategory
        from app.core.llm.gateway import llm_gateway
        from app.dependencies import container

        prompt_map = {
            "summarize_recording": (
                "Analyze these screen recording frames and provide a comprehensive summary. "
                "Return JSON: {summary, key_points, topics, duration_estimate}. "
                "Describe what the user was doing based on the visual content."
            ),
            "extract_highlights": (
                "Analyze these screen recording frames and extract highlight moments. "
                "Return JSON: {highlights: [{timestamp_estimate, description, importance}]}. "
                "Focus on important actions, transitions, and key moments."
            ),
            "suggest_title": (
                "Analyze these screen recording frames and suggest descriptive titles. "
                "Return JSON: {titles: [{text, confidence}]}. "
                "Titles should be concise and descriptive of the recorded content."
            ),
            "generate_chapters": (
                "Analyze these screen recording frames and generate chapter markers. "
                "Return JSON: {chapters: [{title, start_time_estimate, description}]}. "
                "Divide the recording into logical sections based on content changes."
            ),
        }

        prompt = prompt_map.get(action, f"Analyze these screen recording frames for: {action}. Return JSON result.")

        duration_info = f"Duration: {recording.duration}s, Source: {recording.source_type}"
        if params.get("duration"):
            duration_info = f"Duration: {params['duration']}s, Source: {params.get('source_type', recording.source_type)}"

        messages = [{"role": "user", "content": []}]
        text_content = {"type": "text", "text": f"{prompt}\n\nRecording info: {duration_info}\nNumber of key frames: {len(key_frames)}"}
        messages[0]["content"].append(text_content)

        max_frames = min(len(key_frames), 10)
        for i in range(0, max_frames, max(1, max_frames // 5)):
            frame = key_frames[i]
            if frame.startswith("data:image/jpeg;base64,"):
                b64_data = frame.split(",", 1)[1]
            else:
                b64_data = frame
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"},
            })

        try:
            dispatcher = container.get("model_dispatcher")
            if not dispatcher:
                from app.config import settings
                from app.core.llm.models import ModelConfig, ModelDispatcherConfig, ModelTier
                base_model = ModelConfig(
                    name="base",
                    tier=ModelTier.BASE,
                    provider="",
                    model_id=settings.LLM_BASE_MODEL,
                )
                dispatcher = ModelDispatcher(ModelDispatcherConfig(base_model=base_model))

            model_config = dispatcher.resolve_model(TaskCategory.MULTIMODAL)
            model_id = llm_gateway.get_model_id(model_config)
            response = await llm_gateway.acompletion(
                model=model_id,
                messages=messages,
            )
            result_text = ""
            if isinstance(response, dict):
                choices = response.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    result_text = msg.get("content", "")
            elif hasattr(response, 'choices') and response.choices:
                result_text = response.choices[0].message.content or ""
            else:
                result_text = str(response)

            parsed = self._parse_json_result(result_text)

            if action == "summarize_recording" and parsed:
                from app.db.database import async_session
                async with async_session() as session:
                    rec = await session.get(Recording, recording.id)
                    if rec:
                        rec.ai_summary = parsed.get("summary", result_text)
                        await session.commit()

            if action == "extract_highlights" and parsed:
                from app.db.database import async_session
                async with async_session() as session:
                    rec = await session.get(Recording, recording.id)
                    if rec:
                        rec.ai_highlights = parsed.get("highlights", [])
                        await session.commit()

            if action == "generate_chapters" and parsed:
                from app.db.database import async_session
                async with async_session() as session:
                    rec = await session.get(Recording, recording.id)
                    if rec:
                        rec.ai_chapters = parsed.get("chapters", [])
                        await session.commit()

            return parsed if parsed else {"result": result_text}

        except Exception as e:
            logger.error("Vision analysis failed, falling back to text: %s", e)
            return await self._fallback_text_analysis(recording, action, params)

    async def _ocr_analysis(self, recording: Recording, key_frames: list[str], params: dict) -> dict:
        from app.core.llm.dispatcher import ModelDispatcher, TaskCategory
        from app.core.llm.gateway import llm_gateway
        from app.dependencies import container

        dispatcher = container.get("model_dispatcher")
        if not dispatcher:
            from app.config import settings
            from app.core.llm.models import ModelConfig, ModelDispatcherConfig, ModelTier
            base_model = ModelConfig(
                name="base",
                tier=ModelTier.BASE,
                provider="",
                model_id=settings.LLM_BASE_MODEL,
            )
            dispatcher = ModelDispatcher(ModelDispatcherConfig(base_model=base_model))

        prompt = (
            "Extract all visible text from these screen recording frames. "
            "Return JSON: {text: full extracted text, sections: [{time_estimate, text}]}. "
            "Focus on readable text, code, labels, and content visible on screen."
        )

        messages = [{"role": "user", "content": []}]
        messages[0]["content"].append({"type": "text", "text": prompt})

        max_frames = min(len(key_frames), 8)
        for i in range(0, max_frames, max(1, max_frames // 4)):
            frame = key_frames[i]
            if frame.startswith("data:image/jpeg;base64,"):
                b64_data = frame.split(",", 1)[1]
            else:
                b64_data = frame
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"},
            })

        try:
            model_config = dispatcher.resolve_model(TaskCategory.MULTIMODAL)
            model_id = llm_gateway.get_model_id(model_config)
            response = await llm_gateway.acompletion(
                model=model_id,
                messages=messages,
            )
            result_text = ""
            if isinstance(response, dict):
                choices = response.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    result_text = msg.get("content", "")
            elif hasattr(response, 'choices') and response.choices:
                result_text = response.choices[0].message.content or ""
            else:
                result_text = str(response)
            parsed = self._parse_json_result(result_text)

            if parsed and parsed.get("text"):
                from app.db.database import async_session
                async with async_session() as session:
                    rec = await session.get(Recording, recording.id)
                    if rec:
                        rec.ai_ocr_text = parsed.get("text", "")
                        await session.commit()

            return parsed if parsed else {"text": result_text}
        except Exception as e:
            logger.error("OCR analysis failed: %s", e)
            return {"error": str(e)}

    async def _fallback_text_analysis(self, recording: Recording, action: str, params: dict) -> dict:
        from app.core.llm.dispatcher import ModelDispatcher
        from app.dependencies import container
        from app.services.ai_workspace_service import AIWorkspaceService

        dispatcher = container.get("model_dispatcher")
        if not dispatcher:
            from app.config import settings
            from app.core.llm.models import ModelConfig, ModelDispatcherConfig, ModelTier
            base_model = ModelConfig(
                name="base",
                tier=ModelTier.BASE,
                provider="",
                model_id=settings.LLM_BASE_MODEL,
            )
            dispatcher = ModelDispatcher(ModelDispatcherConfig(base_model=base_model))

        svc = AIWorkspaceService(dispatcher)
        return await svc.ai_recorder_assist(action, {
            "duration": recording.duration,
            "source_type": recording.source_type,
            **params,
        })

    async def trim_recording(self, recording: Recording, start_time: float, end_time: float, output_format: str = "mp4") -> dict:
        if not self._check_ffmpeg():
            return {"error": "FFmpeg not available"}

        input_path = recording.mp4_path or recording.file_path
        if not input_path or not os.path.exists(input_path):
            return {"error": "Source file not found"}

        rec_dir = os.path.dirname(input_path)
        output_filename = f"trimmed_{start_time:.0f}_{end_time:.0f}.{output_format}"
        output_path = os.path.join(rec_dir, output_filename)

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy" if output_format == os.path.splitext(input_path)[1].lstrip(".") else "libx264",
            output_path,
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await result.communicate()
            if result.returncode != 0:
                return {"error": f"FFmpeg failed: {stderr.decode()[:200]}"}

            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            return {
                "output_path": output_path,
                "file_size": file_size,
                "start_time": start_time,
                "end_time": end_time,
                "format": output_format,
            }
        except Exception as e:
            return {"error": str(e)}

    async def convert_recording(self, recording: Recording, output_format: str = "mp4", quality: str = "high") -> dict:
        if not self._check_ffmpeg():
            return {"error": "FFmpeg not available"}

        input_path = recording.file_path
        if not input_path or not os.path.exists(input_path):
            return {"error": "Source file not found"}

        rec_dir = os.path.dirname(input_path)
        output_path = os.path.join(rec_dir, f"converted.{output_format}")

        quality_presets = {
            "low": ["-crf", "28", "-preset", "fast"],
            "medium": ["-crf", "23", "-preset", "medium"],
            "high": ["-crf", "18", "-preset", "slow"],
            "original": ["-crf", "15", "-preset", "veryslow"],
        }
        preset = quality_presets.get(quality, quality_presets["high"])

        cmd = ["ffmpeg", "-y", "-i", input_path]
        if output_format == "mp4":
            cmd.extend(["-c:v", "libx264", *preset, "-c:a", "aac", "-b:a", "128k"])
        elif output_format == "gif":
            cmd.extend(["-vf", "fps=10,scale=640:-1:flags=lanczos", "-loop", "0"])
        elif output_format == "avi":
            cmd.extend(["-c:v", "libx264", *preset])
        else:
            cmd.extend(["-c:v", "libx264", *preset])
        cmd.append(output_path)

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await result.communicate()
            if result.returncode != 0:
                return {"error": f"FFmpeg failed: {stderr.decode()[:200]}"}

            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

            from app.db.database import async_session
            async with async_session() as session:
                rec = await session.get(Recording, recording.id)
                if rec:
                    if output_format == "mp4":
                        rec.mp4_path = output_path
                    rec.status = "converted"
                    await session.commit()

            return {
                "output_path": output_path,
                "file_size": file_size,
                "format": output_format,
                "quality": quality,
            }
        except Exception as e:
            return {"error": str(e)}

    async def generate_thumbnail(self, recording: Recording) -> dict:
        if not self._check_ffmpeg():
            return {"error": "FFmpeg not available"}

        input_path = recording.mp4_path or recording.file_path
        if not input_path or not os.path.exists(input_path):
            return {"error": "Source file not found"}

        rec_dir = os.path.dirname(input_path)
        thumb_path = os.path.join(rec_dir, "thumbnail.jpg")

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ss", "1",
            "-vframes", "1",
            "-q:v", "2",
            "-vf", "scale=320:-1",
            thumb_path,
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await result.communicate()
            if result.returncode != 0:
                return {"error": f"FFmpeg failed: {stderr.decode()[:200]}"}

            from app.db.database import async_session
            async with async_session() as session:
                rec = await session.get(Recording, recording.id)
                if rec:
                    rec.thumbnail_path = thumb_path
                    await session.commit()

            return {"thumbnail_path": thumb_path}
        except Exception as e:
            return {"error": str(e)}

    def _parse_json_result(self, text: str) -> Optional[dict]:
        if not text:
            return None
        try:
            json_str = text
            if "```json" in text:
                json_str = text.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in text:
                json_str = text.split("```", 1)[1].split("```", 1)[0]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            return None


recorder_service = RecorderService()
