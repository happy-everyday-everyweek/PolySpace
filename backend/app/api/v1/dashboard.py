from app.api.v1.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException

from app.core.agent.dashboard import dashboard_manager

router = APIRouter()


@router.get("/traces")
async def list_traces(limit: int = 50, status: str | None = None, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    traces = dashboard_manager.list_traces(limit=limit, status=status)
    return {
        "traces": [
            {
                "trace_id": t.trace_id,
                "status": t.status,
                "agent_names": t.agent_names,
                "duration": t.duration,
                "created_at": t.created_at,
                "event_count": len(t.events),
            }
            for t in traces
        ]
    }


@router.get("/active")
async def get_active_traces(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    traces = dashboard_manager.get_active_traces()
    return {
        "active_traces": [
            {
                "trace_id": t.trace_id,
                "agent_names": t.agent_names,
                "duration": t.duration,
                "created_at": t.created_at,
            }
            for t in traces
        ]
    }


@router.get("/trace/{trace_id}")
async def get_trace(trace_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    trace = dashboard_manager.get_trace(trace_id)
    if not trace:
        from app.api.v1.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
        raise HTTPException(status_code=404, detail="Trace not found")
    return {
        "trace_id": trace.trace_id,
        "status": trace.status,
        "agent_names": trace.agent_names,
        "tool_calls": trace.tool_calls,
        "duration": trace.duration,
        "created_at": trace.created_at,
        "events": [
            {
                "agent_name": e.agent_name,
                "event_type": e.event_type,
                "data": e.data,
                "timestamp": e.timestamp,
            }
            for e in trace.events
        ],
    }


@router.get("/stats")
async def get_stats(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return dashboard_manager.get_stats()
