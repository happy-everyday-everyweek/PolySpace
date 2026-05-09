from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from app.core.audit.models import AuditCategory
from app.core.audit.service import audit_service

router = APIRouter()


class AuditQueryParams(BaseModel):
    category: Optional[str] = None
    level: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
    source_device_id: Optional[str] = None
    target_device_id: Optional[str] = None
    trace_id: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100
    offset: int = 0


class IntegrityCheckParams(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@router.get("/logs")
async def query_audit_logs(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    category: Optional[str] = Query(None, description="Filter by category"),
    level: Optional[str] = Query(None, description="Filter by level"),
    actor_type: Optional[str] = Query(None, description="Filter by actor type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    source_device_id: Optional[str] = Query(None, description="Filter by source device"),
    target_device_id: Optional[str] = Query(None, description="Filter by target device"),
    trace_id: Optional[str] = Query(None, description="Filter by trace ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    parsed_start = None
    parsed_end = None
    if start_time:
        try:
            parsed_start = datetime.fromisoformat(start_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_time format")
    if end_time:
        try:
            parsed_end = datetime.fromisoformat(end_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_time format")

    logs = await audit_service.query(
        category=category,
        level=level,
        actor_type=actor_type,
        actor_id=actor_id,
        source_device_id=source_device_id,
        target_device_id=target_device_id,
        trace_id=trace_id,
        status=status,
        start_time=parsed_start,
        end_time=parsed_end,
        limit=limit,
        offset=offset,
    )
    return {"logs": logs, "count": len(logs), "offset": offset, "limit": limit}


@router.get("/trace/{trace_id}")
async def get_trace_chain(trace_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    chain = await audit_service.get_trace_chain(trace_id)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}")
    return {"trace_id": trace_id, "spans": chain, "span_count": len(chain)}


@router.post("/verify")
async def verify_integrity(params: IntegrityCheckParams, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    parsed_start = None
    parsed_end = None
    if params.start_time:
        try:
            parsed_start = datetime.fromisoformat(params.start_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_time format")
    if params.end_time:
        try:
            parsed_end = datetime.fromisoformat(params.end_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_time format")

    result = await audit_service.verify_integrity(
        start_time=parsed_start,
        end_time=parsed_end,
    )
    return result


@router.get("/stats")
async def get_audit_stats(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
):
    parsed_start = None
    parsed_end = None
    if start_time:
        try:
            parsed_start = datetime.fromisoformat(start_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_time format")
    if end_time:
        try:
            parsed_end = datetime.fromisoformat(end_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_time format")

    stats = await audit_service.get_stats(
        start_time=parsed_start,
        end_time=parsed_end,
    )
    return stats


@router.get("/categories")
async def list_audit_categories(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "categories": [
            {"value": c.value, "name": c.name}
            for c in AuditCategory
        ]
    }
