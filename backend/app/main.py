import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    ai_coordination,
    ai_workspace,
    artifacts,
    audit,
    auth,
    chat,
    clipboard,
    dashboard,
    devices,
    doc_conversion,
    email,
    files,
    im,
    inference,
    kanban,
    marketplace,
    models,
    overview,
    pdf,
    recordings,
    research,
    search,
    sync,
    tasks,
    todo,
    tools,
    voice,
    webhooks,
    workspace,
)
from app.api.v1 import (
    settings as settings_api,
)
from app.api.websocket import chat_ws
from app.config import settings
from app.core.audit.middleware import AuditMiddleware
from app.core.audit.models import init_audit_db
from app.core.audit.service import audit_service
from app.core.connector.device_manager import device_manager
from app.core.exceptions import register_exception_handlers
from app.core.observability.metrics import router as metrics_router
from app.db.database import check_db_health, close_db, init_db
from app.dependencies import container, init_services

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PolySpace starting up...")
    await init_db()
    await init_audit_db()
    init_services()
    await container.start_all()
    await audit_service.start()
    from app.core.tool.interaction_tools import async_task_manager
    await async_task_manager.start_worker()
    await device_manager.start_heartbeat_monitor()
    chat_ws.start_heartbeat_monitor()
    logger.info("PolySpace started successfully")
    yield
    logger.info("PolySpace shutting down...")
    chat_ws.stop_heartbeat_monitor()
    await device_manager.stop_heartbeat_monitor()
    from app.core.tool.interaction_tools import async_task_manager
    await async_task_manager.stop_worker()
    await audit_service.stop()
    await container.stop_all()
    await close_db()
    logger.info("PolySpace shut down complete")


app = FastAPI(
    title="PolySpace API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else (["*"] if settings.DEBUG else []),
    allow_credentials=bool(settings.CORS_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(workspace.router, prefix="/api/v1/workspace", tags=["workspace"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
app.include_router(settings_api.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(email.router, prefix="/api/v1/email", tags=["email"])
app.include_router(kanban.router, prefix="/api/v1/kanban", tags=["kanban"])
app.include_router(todo.router, prefix="/api/v1/todo", tags=["todo"])
app.include_router(ai_workspace.router, prefix="/api/v1/ai/workspace", tags=["ai-workspace"])
app.include_router(ai_coordination.router, prefix="/api/v1/ai/coordination", tags=["ai-coordination"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(inference.router, prefix="/api/v1/inference", tags=["inference"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(overview.router, prefix="/api/v1/overview", tags=["overview"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(recordings.router, prefix="/api/v1/recordings", tags=["recordings"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["artifacts"])
app.include_router(research.router, prefix="/api/v1/ai/research", tags=["research"])
app.include_router(clipboard.router, prefix="/api/v1/clipboard", tags=["clipboard"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(im.router, prefix="/api/v1/im", tags=["im"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(marketplace.router, prefix="/api/v1/marketplace", tags=["marketplace"])
app.include_router(pdf.router, prefix="/api/v1/pdf", tags=["pdf"])
app.include_router(doc_conversion.router, prefix="/api/v1/documents", tags=["doc-conversion"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(chat_ws.router, prefix="/ws", tags=["websocket"])
app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])


@app.get("/health")
async def health_check():
    db_ok = await check_db_health()
    return {
        "status": "ok" if db_ok else "degraded",
        "version": settings.APP_VERSION,
        "database": "ok" if db_ok else "unavailable",
        "services": container.list_services(),
        "devices": {
            "total": device_manager.device_count,
            "online": device_manager.online_count,
        },
    }
