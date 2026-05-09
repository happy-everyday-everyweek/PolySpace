import logging
from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...services.ai_workspace_service import AIWorkspaceService

router = APIRouter(tags=["ai-workspace"])
_ai_service: Optional[AIWorkspaceService] = None
logger = logging.getLogger(__name__)


def _get_service() -> AIWorkspaceService:
    global _ai_service
    if _ai_service is None:
        from app.core.llm.dispatcher import ModelDispatcher
        from app.core.llm.gateway import llm_gateway
        dispatcher = ModelDispatcher(gateway=llm_gateway)
        _ai_service = AIWorkspaceService(dispatcher)
    return _ai_service


class VideoAnalyzeRequest(BaseModel):
    video_info: dict


class SubtitleRequest(BaseModel):
    transcription: str
    language: str = "zh"


class DocumentAssistRequest(BaseModel):
    action: str
    content: str
    context: str = ""
    operation_path: str = ""


class PPTAssistRequest(BaseModel):
    action: str
    params: dict


class ExcelAssistRequest(BaseModel):
    action: str
    params: dict


class CalendarAssistRequest(BaseModel):
    action: str
    params: dict


class KnowledgeAssistRequest(BaseModel):
    action: str
    params: dict


class TodoAssistRequest(BaseModel):
    action: str
    params: dict


class EmailAssistRequest(BaseModel):
    action: str
    params: dict


class MemoAssistRequest(BaseModel):
    action: str
    params: dict


class KanbanAssistRequest(BaseModel):
    action: str
    params: dict


class RecorderAssistRequest(BaseModel):
    action: str
    params: dict


class WeatherAssistRequest(BaseModel):
    action: str
    params: dict


class WeatherSearchRequest(BaseModel):
    name: str
    count: int = 5
    language: str = "zh"


class WeatherDataRequest(BaseModel):
    latitude: float
    longitude: float
    forecast_days: int = 7


class AirQualityRequest(BaseModel):
    latitude: float
    longitude: float


class PPTSummaryRequest(BaseModel):
    slides: list[dict]


class MindMapAssistRequest(BaseModel):
    action: str
    params: dict


class NotesAssistRequest(BaseModel):
    action: str
    params: dict


class ContactsAssistRequest(BaseModel):
    action: str
    params: dict


class FocusAssistRequest(BaseModel):
    action: str
    params: dict


class ImageAssistRequest(BaseModel):
    action: str
    params: dict


class ReaderAssistRequest(BaseModel):
    action: str
    params: dict


class CodeAssistRequest(BaseModel):
    action: str
    params: dict


class FinanceAssistRequest(BaseModel):
    action: str
    params: dict


class CalculatorAssistRequest(BaseModel):
    action: str
    params: dict


class MusicAssistRequest(BaseModel):
    action: str
    params: dict


class VideoExportRequest(BaseModel):
    project: dict
    options: dict
    video_src: str = ""


class VideoProjectCreateRequest(BaseModel):
    title: str
    input_files: list[str] = []


class VideoProjectOperationRequest(BaseModel):
    operation: dict


class VideoProcessRequest(BaseModel):
    action: str
    file_path: str = ""
    file_paths: list[str] = []
    start_time: float = 0
    end_time: float = 0
    split_time: float = 0
    speed_factor: float = 1.0
    effect_name: str = ""
    text_content: str = ""
    text_position: str = "bottom"
    export_format: str = "mp4"
    quality: str = "medium"
    resolution: str = "original"


class AIErrorResponse(BaseModel):
    error: str
    detail: str = ""
    action: str = ""


def _handle_ai_error(action: str, e: Exception) -> dict:
    logger.error(f"AI action '{action}' failed: {type(e).__name__}: {e}")
    if isinstance(e, (ConnectionError, TimeoutError)):
        return {"result": "AI service is temporarily unavailable. Please try again later.", "error": "service_unavailable"}
    if "rate_limit" in str(e).lower() or "429" in str(e):
        return {"result": "AI service is busy. Please wait a moment and try again.", "error": "rate_limited"}
    if "api_key" in str(e).lower() or "401" in str(e) or "403" in str(e):
        return {"result": "AI service authentication error. Please check configuration.", "error": "auth_error"}
    return {"result": f"AI processing failed: {type(e).__name__}", "error": "processing_error"}


@router.post("/video/analyze")
async def ai_video_analyze(req: VideoAnalyzeRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_video_analyze(req.video_info)
    except Exception as e:
        return _handle_ai_error("video_analyze", e)


@router.post("/video/subtitles")
async def ai_generate_subtitles(req: SubtitleRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_generate_subtitles(req.transcription, req.language)
    except Exception as e:
        return _handle_ai_error("video_subtitles", e)


@router.post("/document/assist")
async def ai_document_assist(req: DocumentAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_document_assist(
            req.action, req.content, req.context, req.operation_path
        )
    except Exception as e:
        return _handle_ai_error("document_assist", e)


@router.post("/ppt/assist")
async def ai_ppt_assist(req: PPTAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_ppt_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("ppt_assist", e)


@router.post("/excel/assist")
async def ai_excel_assist(req: ExcelAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_excel_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("excel_assist", e)


@router.post("/calendar/assist")
async def ai_calendar_assist(req: CalendarAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_calendar_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("calendar_assist", e)


@router.post("/knowledge/assist")
async def ai_knowledge_assist(req: KnowledgeAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_knowledge_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("knowledge_assist", e)


@router.post("/todo/assist")
async def ai_todo_assist(req: TodoAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_todo_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("todo_assist", e)


@router.post("/email/assist")
async def ai_email_assist(req: EmailAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_email_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("email_assist", e)


@router.post("/memo/assist")
async def ai_memo_assist(req: MemoAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_memo_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("memo_assist", e)


@router.post("/kanban/assist")
async def ai_kanban_assist(req: KanbanAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_kanban_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("kanban_assist", e)


@router.post("/recorder/assist")
async def ai_recorder_assist(req: RecorderAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_recorder_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("recorder_assist", e)


class TTSGenerateRequest(BaseModel):
    text: str
    voice: str = "en-Carter_man"


@router.post("/tts/generate")
async def tts_generate(req: TTSGenerateRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.services.tts_service import tts_service
        audio_data = await tts_service.generate(req.text, req.voice)
        from fastapi.responses import Response
        return Response(content=audio_data, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weather/assist")
async def ai_weather_assist(req: WeatherAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_weather_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("weather_assist", e)


@router.post("/weather/search")
async def weather_search_city(req: WeatherSearchRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.services.weather_service import weather_service
        results = await weather_service.search_city(req.name, req.count, req.language)
        return {"results": results}
    except Exception as e:
        return _handle_ai_error("weather_search", e)


@router.post("/weather/forecast")
async def weather_forecast(req: WeatherDataRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.services.weather_service import weather_service
        return await weather_service.get_forecast(req.latitude, req.longitude, req.forecast_days)
    except Exception as e:
        return _handle_ai_error("weather_forecast", e)


@router.post("/weather/current")
async def weather_current(req: WeatherDataRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.services.weather_service import weather_service
        return await weather_service.get_current_weather(req.latitude, req.longitude)
    except Exception as e:
        return _handle_ai_error("weather_current", e)


@router.post("/weather/air-quality")
async def weather_air_quality(req: AirQualityRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.services.weather_service import weather_service
        return await weather_service.get_air_quality(req.latitude, req.longitude)
    except Exception as e:
        return _handle_ai_error("weather_air_quality", e)


@router.post("/ppt/summary")
async def ai_ppt_summary(req: PPTSummaryRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_ppt_summary(req.slides)
    except Exception as e:
        return _handle_ai_error("ppt_summary", e)


@router.post("/mindmap/assist")
async def ai_mindmap_assist(req: MindMapAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_mindmap_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("mindmap_assist", e)


@router.post("/notes/assist")
async def ai_notes_assist(req: NotesAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_notes_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("notes_assist", e)


@router.post("/contacts/assist")
async def ai_contacts_assist(req: ContactsAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_contacts_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("contacts_assist", e)


@router.post("/focus/assist")
async def ai_focus_assist(req: FocusAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_focus_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("focus_assist", e)


@router.post("/image/assist")
async def ai_image_assist(req: ImageAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_image_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("image_assist", e)


@router.post("/reader/assist")
async def ai_reader_assist(req: ReaderAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_reader_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("reader_assist", e)


@router.post("/code/assist")
async def ai_code_assist(req: CodeAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_code_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("code_assist", e)


@router.post("/dev/assist")
async def ai_dev_assist(req: CodeAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_dev_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("dev_assist", e)


@router.post("/design/assist")
async def ai_design_assist(req: CodeAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_design_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("design_assist", e)


@router.post("/finance/assist")
async def ai_finance_assist(req: FinanceAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_finance_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("finance_assist", e)


@router.post("/calculator/assist")
async def ai_calculator_assist(req: CalculatorAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_calculator_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("calculator_assist", e)


@router.post("/music/assist")
async def ai_music_assist(req: MusicAssistRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return await _get_service().ai_music_assist(req.action, req.params)
    except Exception as e:
        return _handle_ai_error("music_assist", e)


@router.post("/video/export")
async def video_export(req: VideoExportRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from ...services.video_service import video_service
        if not video_service.ffmpeg_available:
            return {"error": "ffmpeg not available on server"}

        input_files = req.project.get("input_files", [])
        if not input_files:
            return {"error": "No input files in project"}

        input_file = input_files[0]
        options = req.options
        fmt = options.get("format", "mp4")
        quality = options.get("quality", "medium")

        result = await video_service.convert(
            input_file=input_file,
            format=fmt,
            quality=quality,
        )
        if result.get("success"):
            return {"download_url": f"/api/v1/files/download?path={result['output_file']}"}
        return result
    except Exception as e:
        return _handle_ai_error("video_export", e)


@router.post("/video/projects")
async def create_video_project(req: VideoProjectCreateRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from ...services.video_service import video_service
        project = await video_service.create_project(req.title, req.input_files)
        return {
            "project_id": project.project_id,
            "title": project.title,
            "status": project.status,
            "created_at": project.created_at,
        }
    except Exception as e:
        return _handle_ai_error("video_project_create", e)


@router.get("/video/projects")
async def list_video_projects(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from ...services.video_service import video_service
        projects = await video_service.list_projects()
        return {
            "projects": [
                {
                    "project_id": p.project_id,
                    "title": p.title,
                    "status": p.status,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                }
                for p in projects
            ]
        }
    except Exception as e:
        return _handle_ai_error("video_project_list", e)


@router.get("/video/projects/{project_id}")
async def get_video_project(project_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from ...services.video_service import video_service
        project = await video_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {
            "project_id": project.project_id,
            "title": project.title,
            "input_files": project.input_files,
            "output_file": project.output_file,
            "operations": project.operations,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        return _handle_ai_error("video_project_get", e)


@router.delete("/video/projects/{project_id}")
async def delete_video_project(project_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from ...services.video_service import video_service
        deleted = await video_service.delete_project(project_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        return _handle_ai_error("video_project_delete", e)


@router.post("/video/projects/{project_id}/operations")
async def add_video_operation(project_id: str, req: VideoProjectOperationRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from ...services.video_service import video_service
        project = await video_service.add_operation(project_id, req.operation)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "operation_count": len(project.operations)}
    except HTTPException:
        raise
    except Exception as e:
        return _handle_ai_error("video_operation_add", e)


@router.post("/video/process")
async def video_process(req: VideoProcessRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from ...services.video_service import video_service
        if not video_service.ffmpeg_available:
            return {"error": "ffmpeg not available on server"}

        if req.action == "trim":
            return await video_service.trim(req.file_path, req.start_time, req.end_time)
        elif req.action == "merge":
            return await video_service.merge(req.file_paths)
        elif req.action == "split":
            return await video_service.split(req.file_path, req.split_time)
        elif req.action == "speed":
            return await video_service.change_speed(req.file_path, req.speed_factor)
        elif req.action == "effect":
            return await video_service.apply_effect(req.file_path, req.effect_name)
        elif req.action == "add_text":
            return await video_service.add_text_overlay(req.file_path, req.text_content, req.text_position)
        elif req.action == "audio_extract":
            return await video_service.extract_audio(req.file_path)
        elif req.action == "thumbnail":
            return await video_service.generate_thumbnail(req.file_path, req.start_time or 1.0)
        elif req.action == "info":
            return await video_service.get_info(req.file_path)
        elif req.action == "convert":
            return await video_service.convert(req.file_path, req.export_format, req.quality)
        else:
            return {"error": f"Unknown action: {req.action}"}
    except Exception as e:
        return _handle_ai_error("video_process", e)


class DesignExportRequest(BaseModel):
    project_id: str
    export_format: str = "html"
    target_app: Optional[str] = None


@router.post("/design/export")
async def design_export(req: DesignExportRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.core.tools.open_design_tool import OpenDesignProcessManager

        manager = OpenDesignProcessManager.get_instance()
        if not manager.is_running():
            start_result = await manager.ensure_running()
            if start_result.get("status") not in ("running", "already_running"):
                return {"error": "Design engine not available", "detail": start_result}

        if req.export_format == "html":
            result = await manager.api_request("GET", f"/api/projects/{req.project_id}/archive")
            return {"format": "html", "data": result}
        elif req.export_format == "pdf":
            return {
                "format": "pdf",
                "method": "Use browser print on the HTML artifact",
                "project_id": req.project_id,
            }
        elif req.export_format == "ppt":
            return {
                "format": "ppt",
                "target": "ppt_app",
                "project_id": req.project_id,
                "message": "Design exported to PPT application for further editing",
            }
        elif req.export_format == "dev":
            return {
                "format": "dev",
                "target": "dev_app",
                "project_id": req.project_id,
                "message": "Design exported to Dev application - AI will enhance with logic and backend",
            }
        else:
            return {"error": f"Unsupported export format: {req.export_format}"}
    except Exception as e:
        return _handle_ai_error("design_export", e)


@router.post("/design/daemon/start")
async def design_daemon_start(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.core.tools.open_design_tool import OpenDesignProcessManager

        manager = OpenDesignProcessManager.get_instance()
        result = await manager.start()
        return result
    except Exception as e:
        return _handle_ai_error("design_daemon_start", e)


@router.get("/design/daemon/status")
async def design_daemon_status(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.core.tools.open_design_tool import OpenDesignProcessManager

        manager = OpenDesignProcessManager.get_instance()
        return manager.get_status()
    except Exception as e:
        return _handle_ai_error("design_daemon_status", e)


@router.post("/dev/daemon/start")
async def dev_daemon_start(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.core.tools.nocobase_tool import NocoBaseProcessManager

        manager = NocoBaseProcessManager.get_instance()
        result = await manager.start()
        return result
    except Exception as e:
        return _handle_ai_error("dev_daemon_start", e)


@router.get("/dev/daemon/status")
async def dev_daemon_status(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from app.core.tools.nocobase_tool import NocoBaseProcessManager

        manager = NocoBaseProcessManager.get_instance()
        return manager.get_status()
    except Exception as e:
        return _handle_ai_error("dev_daemon_status", e)
