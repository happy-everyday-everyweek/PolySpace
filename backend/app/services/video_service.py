from __future__ import annotations

import asyncio
import json
import os
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiosqlite


@dataclass
class VideoProject:
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    input_files: list[str] = field(default_factory=list)
    output_file: str = ""
    operations: list[dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


def _check_ffmpeg() -> str | None:
    path = shutil.which("ffmpeg")
    if path is None:
        return None
    return path


def _sanitize_path(path: str) -> str:
    resolved = os.path.realpath(path)
    return resolved


class FFmpegRunner:
    def __init__(self, ffmpeg_path: str | None = None) -> None:
        self._ffmpeg = ffmpeg_path or _check_ffmpeg()

    @property
    def available(self) -> bool:
        return self._ffmpeg is not None

    async def run(
        self,
        args: list[str],
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        if not self._ffmpeg:
            return {"error": "ffmpeg not found. Install ffmpeg to use video editing features."}

        cmd = [self._ffmpeg] + args
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            if process.returncode == 0:
                return {"success": True, "stdout": stdout.decode(errors="replace")}
            else:
                return {"error": f"ffmpeg error: {stderr.decode(errors='replace')}"}
        except FileNotFoundError:
            return {"error": "ffmpeg not found"}
        except asyncio.TimeoutError:
            process.kill()
            return {"error": "Video processing timed out"}
        except Exception as e:
            return {"error": str(e)}

    async def probe(self, input_file: str) -> dict[str, Any]:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            return {"error": "ffprobe not found"}
        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            _sanitize_path(input_file),
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30.0)
            if process.returncode == 0:
                return json.loads(stdout.decode())
            return {"error": "ffprobe failed"}
        except Exception as e:
            return {"error": str(e)}


class VideoService:
    def __init__(self, data_dir: str | None = None) -> None:
        if data_dir is None:
            data_dir = os.path.join(os.getcwd(), "data", "video")
        self._data_dir = data_dir
        self._projects: dict[str, VideoProject] = {}
        self._ffmpeg = FFmpegRunner()
        self._db_path = os.path.join(data_dir, "video_projects.db")
        os.makedirs(data_dir, exist_ok=True)

    @property
    def ffmpeg_available(self) -> bool:
        return self._ffmpeg.available

    async def _init_db(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS video_projects (
                    project_id TEXT PRIMARY KEY,
                    title TEXT DEFAULT '',
                    input_files TEXT DEFAULT '[]',
                    output_file TEXT DEFAULT '',
                    operations TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'draft',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            await db.commit()

    async def create_project(self, title: str, input_files: list[str] | None = None) -> VideoProject:
        project = VideoProject(title=title, input_files=input_files or [])
        self._projects[project.project_id] = project
        await self._save_project(project)
        return project

    async def get_project(self, project_id: str) -> VideoProject | None:
        if project_id in self._projects:
            return self._projects[project_id]
        return await self._load_project(project_id)

    async def _save_project(self, project: VideoProject) -> None:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO video_projects
                       (project_id, title, input_files, output_file, operations, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        project.project_id,
                        project.title,
                        json.dumps(project.input_files),
                        project.output_file,
                        json.dumps(project.operations),
                        project.status,
                        project.created_at,
                        project.updated_at,
                    ),
                )
                await db.commit()
        except Exception:
            pass

    async def _load_project(self, project_id: str) -> VideoProject | None:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM video_projects WHERE project_id = ?", (project_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row is None:
                        return None
                    project = VideoProject(
                        project_id=row["project_id"],
                        title=row["title"],
                        input_files=json.loads(row["input_files"]),
                        output_file=row["output_file"],
                        operations=json.loads(row["operations"]),
                        status=row["status"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    self._projects[project_id] = project
                    return project
        except Exception:
            return None

    async def add_operation(self, project_id: str, operation: dict[str, Any]) -> VideoProject | None:
        project = await self.get_project(project_id)
        if not project:
            return None
        project.operations.append(operation)
        project.updated_at = datetime.now().isoformat()
        await self._save_project(project)
        return project

    async def trim(
        self,
        input_file: str,
        start_time: float,
        end_time: float,
        output_file: str | None = None,
    ) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}

        out = output_file or os.path.join(self._data_dir, f"trim_{uuid.uuid4().hex[:8]}.mp4")
        args = [
            "-i", safe_input,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy",
            "-y",
            _sanitize_path(out),
        ]
        result = await self._ffmpeg.run(args, timeout=120.0)
        if result.get("success"):
            result["output_file"] = out
        return result

    async def merge(
        self,
        input_files: list[str],
        output_file: str | None = None,
    ) -> dict[str, Any]:
        if len(input_files) < 2:
            return {"error": "Need at least 2 input files to merge"}

        out = output_file or os.path.join(self._data_dir, f"merge_{uuid.uuid4().hex[:8]}.mp4")
        list_file = os.path.join(self._data_dir, f"filelist_{uuid.uuid4().hex[:8]}.txt")

        try:
            safe_files = []
            for f in input_files:
                safe = _sanitize_path(f)
                if not os.path.isfile(safe):
                    return {"error": f"Input file not found: {f}"}
                safe_files.append(safe)

            with open(list_file, "w", encoding="utf-8") as f:
                for safe_path in safe_files:
                    f.write(f"file '{safe_path}'\n")

            args = [
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                "-y",
                _sanitize_path(out),
            ]
            result = await self._ffmpeg.run(args, timeout=300.0)
            if result.get("success"):
                result["output_file"] = out
            return result
        finally:
            if os.path.exists(list_file):
                os.unlink(list_file)

    async def split(
        self,
        input_file: str,
        split_time: float,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}

        out_dir = output_dir or self._data_dir
        os.makedirs(out_dir, exist_ok=True)
        part1 = os.path.join(out_dir, f"split_{uuid.uuid4().hex[:8]}_part1.mp4")
        part2 = os.path.join(out_dir, f"split_{uuid.uuid4().hex[:8]}_part2.mp4")

        args1 = [
            "-i", safe_input,
            "-t", str(split_time),
            "-c", "copy",
            "-y",
            _sanitize_path(part1),
        ]
        args2 = [
            "-i", safe_input,
            "-ss", str(split_time),
            "-c", "copy",
            "-y",
            _sanitize_path(part2),
        ]

        r1 = await self._ffmpeg.run(args1, timeout=120.0)
        if not r1.get("success"):
            return r1

        r2 = await self._ffmpeg.run(args2, timeout=120.0)
        if not r2.get("success"):
            return r2

        return {
            "success": True,
            "parts": [part1, part2],
        }

    async def change_speed(
        self,
        input_file: str,
        speed_factor: float,
        output_file: str | None = None,
    ) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}

        if speed_factor <= 0 or speed_factor > 10:
            return {"error": "Speed factor must be between 0 and 10"}

        out = output_file or os.path.join(self._data_dir, f"speed_{uuid.uuid4().hex[:8]}.mp4")
        video_filter = f"setpts={1.0 / speed_factor}*PTS"
        audio_filter = f"atempo={min(max(speed_factor, 0.5), 2.0)}"

        args = [
            "-i", safe_input,
            "-filter:v", video_filter,
            "-filter:a", audio_filter,
            "-y",
            _sanitize_path(out),
        ]
        result = await self._ffmpeg.run(args, timeout=300.0)
        if result.get("success"):
            result["output_file"] = out
        return result

    async def add_text_overlay(
        self,
        input_file: str,
        text: str,
        position: str = "bottom",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}

        out = output_file or os.path.join(self._data_dir, f"text_{uuid.uuid4().hex[:8]}.mp4")

        pos_map = {
            "top": "x=(w-text_w)/2:y=20",
            "center": "x=(w-text_w)/2:y=(h-text_h)/2",
            "bottom": "x=(w-text_w)/2:y=h-text_h-30",
        }
        pos_expr = pos_map.get(position, pos_map["bottom"])

        safe_text = text.replace("'", "'\\''").replace(":", "\\:")
        drawtext = f"drawtext=text='{safe_text}':fontsize=24:fontcolor=white:{pos_expr}"

        args = [
            "-i", safe_input,
            "-vf", drawtext,
            "-c:a", "copy",
            "-y",
            _sanitize_path(out),
        ]
        result = await self._ffmpeg.run(args, timeout=300.0)
        if result.get("success"):
            result["output_file"] = out
        return result

    async def apply_effect(
        self,
        input_file: str,
        effect: str,
        output_file: str | None = None,
    ) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}

        out = output_file or os.path.join(self._data_dir, f"effect_{uuid.uuid4().hex[:8]}.mp4")

        effect_filters = {
            "grayscale": "colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3",
            "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
            "blur": "boxblur=5:1",
            "vignette": "vignette=angle=PI/4",
            "noise": "noise=alls=20:allf=t",
        }

        vf = effect_filters.get(effect)
        if not vf:
            return {"error": f"Unknown effect: {effect}. Available: {', '.join(effect_filters.keys())}"}

        args = [
            "-i", safe_input,
            "-vf", vf,
            "-c:a", "copy",
            "-y",
            _sanitize_path(out),
        ]
        result = await self._ffmpeg.run(args, timeout=300.0)
        if result.get("success"):
            result["output_file"] = out
        return result

    async def extract_audio(
        self,
        input_file: str,
        output_file: str | None = None,
        audio_format: str = "mp3",
    ) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}

        out = output_file or os.path.join(self._data_dir, f"audio_{uuid.uuid4().hex[:8]}.{audio_format}")
        args = [
            "-i", safe_input,
            "-vn",
            "-acodec", "libmp3lame" if audio_format == "mp3" else "copy",
            "-y",
            _sanitize_path(out),
        ]
        result = await self._ffmpeg.run(args, timeout=120.0)
        if result.get("success"):
            result["output_file"] = out
        return result

    async def generate_thumbnail(
        self,
        input_file: str,
        time_offset: float = 1.0,
        output_file: str | None = None,
    ) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}

        out = output_file or os.path.join(self._data_dir, f"thumb_{uuid.uuid4().hex[:8]}.jpg")
        args = [
            "-i", safe_input,
            "-ss", str(time_offset),
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            _sanitize_path(out),
        ]
        result = await self._ffmpeg.run(args, timeout=30.0)
        if result.get("success"):
            result["output_file"] = out
        return result

    async def get_info(self, input_file: str) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}
        return await self._ffmpeg.probe(safe_input)

    async def convert(
        self,
        input_file: str,
        format: str = "mp4",
        quality: str = "medium",
        output_file: str | None = None,
    ) -> dict[str, Any]:
        safe_input = _sanitize_path(input_file)
        if not os.path.isfile(safe_input):
            return {"error": f"Input file not found: {input_file}"}

        out = output_file or os.path.join(self._data_dir, f"convert_{uuid.uuid4().hex[:8]}.{format}")

        quality_presets = {
            "low": ["-crf", "28", "-preset", "fast", "-b:v", "1M"],
            "medium": ["-crf", "23", "-preset", "medium", "-b:v", "3M"],
            "high": ["-crf", "18", "-preset", "slow", "-b:v", "8M"],
        }

        extra_args = quality_presets.get(quality, quality_presets["medium"])

        if format == "mp4":
            args = [
                "-i", safe_input,
                "-c:v", "libx264",
                "-c:a", "aac",
                *extra_args,
                "-y",
                _sanitize_path(out),
            ]
        elif format == "webm":
            args = [
                "-i", safe_input,
                "-c:v", "libvpx-vp9",
                "-c:a", "libopus",
                *extra_args,
                "-y",
                _sanitize_path(out),
            ]
        elif format == "gif":
            args = [
                "-i", safe_input,
                "-vf", "fps=10,scale=480:-1:flags=lanczos",
                "-y",
                _sanitize_path(out),
            ]
        else:
            return {"error": f"Unsupported format: {format}"}

        result = await self._ffmpeg.run(args, timeout=600.0)
        if result.get("success"):
            result["output_file"] = out
        return result

    async def generate_narration(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> dict[str, Any]:
        try:
            from app.services.voice_service import voice_service
            audio_data = await voice_service.synthesize(text, voice=voice)
            if audio_data:
                out = os.path.join(self._data_dir, f"narration_{uuid.uuid4().hex[:8]}.mp3")
                with open(out, "wb") as f:
                    f.write(audio_data)
                return {"success": True, "output_file": out}
            return {"error": "TTS synthesis failed"}
        except Exception as e:
            return {"error": str(e)}

    async def list_projects(self) -> list[VideoProject]:
        return sorted(self._projects.values(), key=lambda p: p.updated_at, reverse=True)

    async def delete_project(self, project_id: str) -> bool:
        if project_id in self._projects:
            del self._projects[project_id]
            try:
                async with aiosqlite.connect(self._db_path) as db:
                    await db.execute("DELETE FROM video_projects WHERE project_id = ?", (project_id,))
                    await db.commit()
            except Exception:
                pass
            return True
        return False


video_service = VideoService()
