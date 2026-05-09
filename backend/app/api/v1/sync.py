from typing import Any, Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel

from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service
from app.services.sync_service import CONFLICT_STRATEGIES, SYNC_SCOPES, sync_service

router = APIRouter()


class SyncRegisterRequest(BaseModel):
    device_id: str
    device_name: str = ""
    platform: str = ""
    sync_scopes: list[str] | None = None


class SyncPushRequest(BaseModel):
    device_id: str
    changes: list[dict[str, Any]] = []


class SyncPullRequest(BaseModel):
    device_id: str
    since: Optional[str] = None
    scopes: list[str] | None = None


class SyncGitHubRequest(BaseModel):
    device_id: str
    repo: str
    token: str
    encryption_key: str = ""


class SyncConflictResolveRequest(BaseModel):
    conflict_id: str
    resolution: str = "local"
    content: Optional[str] = None


class SyncScopesUpdateRequest(BaseModel):
    device_id: str
    scopes: list[str]


class HandoffSyncRequest(BaseModel):
    source_device_id: str
    target_device_id: str


@router.post("/register")
async def register_device(request: SyncRegisterRequest, http_request: Request, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    device = await sync_service.register_device(
        device_id=request.device_id,
        device_name=request.device_name,
        platform=request.platform,
        sync_scopes=request.sync_scopes,
    )
    await audit_service.record(
        category=AuditCategory.SYNC_PUSH,
        action="sync_register",
        level=AuditLevel.INFO,
        actor_type="device",
        actor_id=request.device_id,
        source_device_id=request.device_id,
        actor_ip=http_request.client.host if http_request.client else "",
        status="success",
        detail=f"Device {request.device_id} registered for sync on branch {device.branch}",
    )
    return {
        "status": "ok",
        "device_id": device.device_id,
        "branch": device.branch,
        "is_main_branch": device.branch == "main",
        "sync_scopes": device.sync_scopes,
    }


@router.post("/push")
async def push_changes(request: SyncPushRequest, http_request: Request, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await sync_service.push_changes(
        device_id=request.device_id,
        changes=request.changes,
    )
    await audit_service.record(
        category=AuditCategory.SYNC_PUSH,
        action="sync_push",
        level=AuditLevel.INFO,
        actor_type="device",
        actor_id=request.device_id,
        source_device_id=request.device_id,
        actor_ip=http_request.client.host if http_request.client else "",
        status="success" if "error" not in result else "error",
        detail=f"Device {request.device_id} pushed {result.get('pushed', 0)} changes",
    )
    return result


@router.post("/pull")
async def pull_changes(request: SyncPullRequest, http_request: Request, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await sync_service.pull_changes(
        device_id=request.device_id,
        since=request.since,
        scopes=request.scopes,
    )
    await audit_service.record(
        category=AuditCategory.SYNC_PULL,
        action="sync_pull",
        level=AuditLevel.INFO,
        actor_type="device",
        actor_id=request.device_id,
        source_device_id=request.device_id,
        actor_ip=http_request.client.host if http_request.client else "",
        status="success" if "error" not in result else "error",
        detail=f"Device {request.device_id} pulled {result.get('count', 0)} changes",
    )
    return result


@router.get("/status/{device_id}")
async def sync_status(device_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await sync_service.get_status(device_id)


@router.get("/devices")
async def all_devices_status(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "devices": await sync_service.get_all_devices_status(),
        "count": len(sync_service._devices),
    }


@router.get("/conflicts/{device_id}")
async def detect_conflicts(device_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    conflicts = await sync_service.detect_conflicts(device_id)
    return {
        "device_id": device_id,
        "conflicts": [c.to_dict() for c in conflicts],
        "count": len(conflicts),
    }


@router.post("/resolve-conflict")
async def resolve_conflict(request: SyncConflictResolveRequest, http_request: Request = None, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await sync_service.resolve_conflict(
        conflict_id=request.conflict_id,
        resolution=request.resolution,
        content=request.content,
    )
    await audit_service.record(
        category=AuditCategory.SYNC_CONFLICT,
        action="sync_resolve_conflict",
        level=AuditLevel.WARN,
        actor_type="device",
        actor_id="server",
        actor_ip=http_request.client.host if http_request and http_request.client else "",
        status="success",
        detail=f"Resolved conflict {request.conflict_id} with strategy: {request.resolution}",
    )
    return result


@router.post("/github")
async def sync_to_github(request: SyncGitHubRequest, http_request: Request, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await sync_service.encrypt_and_sync_to_github(
        device_id=request.device_id,
        repo=request.repo,
        token=request.token,
        encryption_key=request.encryption_key,
    )
    await audit_service.record(
        category=AuditCategory.SYNC_PUSH,
        action="sync_github",
        level=AuditLevel.INFO,
        actor_type="device",
        actor_id=request.device_id,
        source_device_id=request.device_id,
        actor_ip=http_request.client.host if http_request.client else "",
        status="success" if "error" not in result else "error",
        detail=f"GitHub sync for device {request.device_id}: {result.get('status', 'unknown')}",
    )
    return result


@router.put("/scopes")
async def update_sync_scopes(request: SyncScopesUpdateRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await sync_service.update_device_scopes(
        device_id=request.device_id,
        scopes=request.scopes,
    )
    return result


@router.post("/handoff")
async def handoff_sync(request: HandoffSyncRequest, http_request: Request, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await sync_service.trigger_handoff_sync(
        source_device_id=request.source_device_id,
        target_device_id=request.target_device_id,
    )
    await audit_service.record(
        category=AuditCategory.SYNC_PUSH,
        action="sync_handoff",
        level=AuditLevel.INFO,
        actor_type="system",
        actor_id="server",
        source_device_id=request.source_device_id,
        actor_ip=http_request.client.host if http_request.client else "",
        status="success" if "error" not in result else "error",
        detail=f"Handoff sync: {request.source_device_id} -> {request.target_device_id}",
    )
    return result


@router.post("/auto-sync/start")
async def start_auto_sync(interval_sec: int = 300, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await sync_service.start_auto_sync(interval_sec)
    return {"status": "ok", "interval_sec": interval_sec}


@router.post("/auto-sync/stop")
async def stop_auto_sync(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await sync_service.stop_auto_sync()
    return {"status": "ok"}


@router.get("/meta")
async def sync_meta(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "sync_scopes": SYNC_SCOPES,
        "conflict_strategies": CONFLICT_STRATEGIES,
        "auto_sync_running": sync_service._auto_sync_running,
        "auto_sync_interval": sync_service._auto_sync_interval,
        "conflict_strategy": sync_service.get_conflict_strategy(),
    }
