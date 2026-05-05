import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.tables import Recording

logger = logging.getLogger(__name__)
router = APIRouter()

RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "recordings")


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _recording_dir(rec_id: str) -> str:
    d = os.path.join(RECORDINGS_DIR, rec_id)
    _ensure_dir(d)
    return d


@router.post("/upload")
async def upload_recording(
    file: UploadFile = File(...),
    duration: float = Form(0),
    source_type: str = Form("screen"),
    has_audio: bool = Form(True),
    quality: str = Form("high"),
    key_frames: str = Form(""),
    annotations: str = Form(""),
    template: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    rec_id = str(uuid.uuid4())
    rec_dir = _recording_dir(rec_id)

    file_path = os.path.join(rec_dir, f"original{os.path.splitext(file.filename or 'recording.webm')[1]}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        file_size = len(content)

    key_frames_dir = None
    if key_frames:
        try:
            frames = json.loads(key_frames)
            if frames and isinstance(frames, list):
                frames_dir = os.path.join(rec_dir, "frames")
                _ensure_dir(frames_dir)
                for i, frame_data in enumerate(frames):
                    if frame_data.startswith("data:image/jpeg;base64,"):
                        import base64
                        img_bytes = base64.b64decode(frame_data.split(",", 1)[1])
                        with open(os.path.join(frames_dir, f"frame_{i:04d}.jpg"), "wb") as img_f:
                            img_f.write(img_bytes)
                key_frames_dir = frames_dir
        except Exception as e:
            logger.warning("Failed to save key frames: %s", e)

    title = file.filename or f"Recording {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if len(title) > 100:
        title = title[:100]

    parsed_annotations = None
    if annotations:
        try:
            parsed_annotations = json.loads(annotations)
        except Exception:
            parsed_annotations = None

    recording = Recording(
        id=rec_id,
        title=title,
        file_path=file_path,
        duration=duration,
        file_size=file_size,
        source_type=source_type,
        has_audio=has_audio,
        quality=quality,
        format="webm",
        status="uploaded",
        key_frames_dir=key_frames_dir,
        tags={"template": template} if template else None,
        ai_highlights=parsed_annotations if parsed_annotations else None,
    )
    db.add(recording)
    await db.commit()
    await db.refresh(recording)

    return {"id": rec_id, "title": recording.title, "file_size": file_size}


@router.get("")
async def list_recordings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Recording).order_by(Recording.created_at.desc())
    if status:
        query = query.where(Recording.status == status)
    total_q = select(sa_func.count()).select_from(Recording)
    if status:
        total_q = total_q.where(Recording.status == status)

    total = (await db.execute(total_q)).scalar() or 0
    result = await db.execute(query.offset(offset).limit(limit))
    recordings = result.scalars().all()

    items = []
    for r in recordings:
        items.append({
            "id": r.id,
            "title": r.title,
            "duration": r.duration,
            "file_size": r.file_size,
            "source_type": r.source_type,
            "has_audio": r.has_audio,
            "quality": r.quality,
            "format": r.format,
            "status": r.status,
            "thumbnail_url": f"/api/v1/recordings/{r.id}/thumbnail" if r.thumbnail_path else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{recording_id}")
async def get_recording(recording_id: str, db: AsyncSession = Depends(get_db)):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    return {
        "id": recording.id,
        "title": recording.title,
        "description": recording.description,
        "duration": recording.duration,
        "resolution": recording.resolution,
        "file_size": recording.file_size,
        "source_type": recording.source_type,
        "has_audio": recording.has_audio,
        "quality": recording.quality,
        "fps": recording.fps,
        "format": recording.format,
        "status": recording.status,
        "tags": recording.tags,
        "ai_summary": recording.ai_summary,
        "ai_highlights": recording.ai_highlights,
        "ai_chapters": recording.ai_chapters,
        "ai_ocr_text": recording.ai_ocr_text,
        "thumbnail_url": f"/api/v1/recordings/{recording.id}/thumbnail" if recording.thumbnail_path else None,
        "created_at": recording.created_at.isoformat() if recording.created_at else None,
        "updated_at": recording.updated_at.isoformat() if recording.updated_at else None,
    }


@router.delete("/{recording_id}")
async def delete_recording(recording_id: str, db: AsyncSession = Depends(get_db)):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    rec_dir = _recording_dir(recording_id)
    if os.path.exists(rec_dir):
        import shutil
        shutil.rmtree(rec_dir, ignore_errors=True)

    await db.delete(recording)
    await db.commit()
    return {"deleted": True, "id": recording_id}


@router.get("/{recording_id}/download")
async def download_recording(recording_id: str, db: AsyncSession = Depends(get_db)):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    file_path = recording.mp4_path or recording.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Recording file not found")

    filename = f"{recording.title}.{os.path.splitext(file_path)[1].lstrip('.')}"
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)


@router.get("/{recording_id}/thumbnail")
async def get_thumbnail(recording_id: str, db: AsyncSession = Depends(get_db)):
    recording = await db.get(Recording, recording_id)
    if not recording or not recording.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    if not os.path.exists(recording.thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail file not found")

    return FileResponse(recording.thumbnail_path, media_type="image/jpeg")


class UpdateRecordingRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


@router.patch("/{recording_id}")
async def update_recording(
    recording_id: str,
    req: UpdateRecordingRequest = Body(default=UpdateRecordingRequest()),
    db: AsyncSession = Depends(get_db),
):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    if req.title is not None:
        recording.title = req.title
    if req.description is not None:
        recording.description = req.description
    if req.tags is not None:
        recording.tags = req.tags

    await db.commit()
    await db.refresh(recording)
    return {"id": recording.id, "title": recording.title}


class AnalyzeRecordingRequest(BaseModel):
    action: str = "summarize_recording"
    params: dict = {}


@router.post("/{recording_id}/analyze")
async def analyze_recording(
    recording_id: str,
    req: AnalyzeRecordingRequest = Body(default=AnalyzeRecordingRequest()),
    db: AsyncSession = Depends(get_db),
):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    try:
        from app.services.recorder_service import recorder_service
        result = await recorder_service.analyze_recording(recording, req.action, req.params)
        return result
    except Exception as e:
        logger.error("Recording analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class TrimRecordingRequest(BaseModel):
    start_time: float = 0
    end_time: float = 0
    output_format: str = "mp4"


@router.post("/{recording_id}/trim")
async def trim_recording(
    recording_id: str,
    req: TrimRecordingRequest = Body(default=TrimRecordingRequest()),
    db: AsyncSession = Depends(get_db),
):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    try:
        from app.services.recorder_service import recorder_service
        result = await recorder_service.trim_recording(recording, req.start_time, req.end_time, req.output_format)
        return result
    except Exception as e:
        logger.error("Recording trim failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class ConvertRecordingRequest(BaseModel):
    output_format: str = "mp4"
    quality: str = "high"


@router.post("/{recording_id}/convert")
async def convert_recording(
    recording_id: str,
    req: ConvertRecordingRequest = Body(default=ConvertRecordingRequest()),
    db: AsyncSession = Depends(get_db),
):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    try:
        from app.services.recorder_service import recorder_service
        result = await recorder_service.convert_recording(recording, req.output_format, req.quality)
        return result
    except Exception as e:
        logger.error("Recording convert failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{recording_id}/share")
async def share_recording(
    recording_id: str,
    expires_hours: int = 24,
    db: AsyncSession = Depends(get_db),
):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    token = secrets.token_urlsafe(32)
    recording.share_token = token
    recording.share_expires = datetime.utcnow() + timedelta(hours=expires_hours)
    await db.commit()

    return {"share_token": token, "expires_at": recording.share_expires.isoformat()}


@router.get("/shared/{token}")
async def get_shared_recording(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Recording).where(Recording.share_token == token)
    )
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status_code=404, detail="Shared recording not found")
    if recording.share_expires and recording.share_expires < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link expired")

    file_path = recording.mp4_path or recording.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Recording file not found")

    return FileResponse(file_path, media_type="video/webm", filename=f"{recording.title}.webm")


@router.post("/{recording_id}/mix-narration")
async def mix_narration(
    recording_id: str,
    narration: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    input_path = recording.mp4_path or recording.file_path
    if not input_path or not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="Recording file not found")

    rec_dir = os.path.dirname(input_path)
    narration_path = os.path.join(rec_dir, "narration.wav")
    output_path = os.path.join(rec_dir, "mixed.mp4")

    narration_content = await narration.read()
    with open(narration_path, "wb") as f:
        f.write(narration_content)

    try:
        from app.services.recorder_service import recorder_service
        if not recorder_service._check_ffmpeg():
            return {"error": "FFmpeg not available for mixing"}

        import asyncio
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-i", narration_path,
            "-filter_complex", "[1:a]adelay=0|0[narr];[0:a][narr]amix=inputs=2:duration=longest[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path,
        ]

        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await result.communicate()
        if result.returncode != 0:
            cmd_simple = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-i", narration_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-map", "0:v",
                "-map", "1:a",
                output_path,
            ]
            result2 = await asyncio.create_subprocess_exec(
                *cmd_simple,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr2 = await result2.communicate()
            if result2.returncode != 0:
                return {"error": f"FFmpeg mix failed: {stderr2.decode()[:200]}"}

        if os.path.exists(output_path):
            recording.mp4_path = output_path
            await db.commit()
            file_size = os.path.getsize(output_path)
            return {"output_path": output_path, "file_size": file_size}
        else:
            return {"error": "Mix output not found"}

    except Exception as e:
        logger.error("Narration mix failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
