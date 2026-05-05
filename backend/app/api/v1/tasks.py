from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.tool.interaction_tools import async_task_manager

router = APIRouter()


class TaskSupplementRequest(BaseModel):
    info: str
    source: str = "user"


class TaskResponse(BaseModel):
    id: str
    description: str
    goal: str
    status: str
    result: Optional[dict | str] = None
    error: str = ""
    progress: float = 0.0
    progress_message: str = ""
    supplements: list[dict] = []
    steps: list[dict] = []
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    session_id: str = ""


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    task = async_task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return TaskResponse(**task.to_dict())


@router.get("/", response_model=TaskListResponse)
async def list_tasks(session_id: str = "", limit: int = 50):
    tasks = async_task_manager.list_tasks(session_id=session_id, limit=limit)
    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks),
    )


@router.post("/{task_id}/supplement")
async def supplement_task(task_id: str, request: TaskSupplementRequest):
    result = async_task_manager.supplement_task(task_id, request.info, source=request.source)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    task = async_task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status.value in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Task is already {task.status.value}")
    from app.core.tool.interaction_tools import AsyncTaskStatus
    task.status = AsyncTaskStatus.CANCELLED
    return {"task_id": task_id, "status": "cancelled"}
