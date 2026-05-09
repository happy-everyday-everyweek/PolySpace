from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.v1.auth import get_current_user
from app.services.workspace_service import workspace_service

router = APIRouter()


class CreateDocumentRequest(BaseModel):
    title: str
    doc_type: str = "note"
    content: str = ""
    metadata: dict = {}


class UpdateDocumentRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None
    metadata: Optional[dict] = None


class SmartEncouragementRequest(BaseModel):
    active_tool: str = ""
    work_context: str = ""
    emotion_state: str = ""
    recent_actions: list[str] = []
    work_duration_minutes: int = 0
    completed_tasks_count: int = 0


@router.get("/status")
async def workspace_status(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await workspace_service.get_status()


@router.post("/documents")
async def create_document(req: CreateDocumentRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doc = await workspace_service.create_document(
        title=req.title, doc_type=req.doc_type, content=req.content, **req.metadata
    )
    return {
        "doc_id": doc.doc_id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "content": doc.content,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }


@router.get("/documents")
async def list_documents(doc_type: Optional[str] = Query(None), user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    docs = await workspace_service.list_documents(doc_type)
    return {
        "items": [
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "doc_type": d.doc_type,
                "content": d.content,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
            }
            for d in docs
        ]
    }


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doc = await workspace_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "doc_id": doc.doc_id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "content": doc.content,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "metadata": doc.metadata,
    }


@router.put("/documents/{doc_id}")
async def update_document(doc_id: str, req: UpdateDocumentRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    doc = await workspace_service.update_document(doc_id, **updates)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "doc_id": doc.doc_id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "content": doc.content,
        "updated_at": doc.updated_at,
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    deleted = await workspace_service.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "ok", "doc_id": doc_id}


@router.post("/document/open")
async def open_document(path: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await workspace_service.open_document(path)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/presentation/open")
async def open_presentation(path: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await workspace_service.open_presentation(path)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/spreadsheet/open")
async def open_spreadsheet(path: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await workspace_service.open_spreadsheet(path)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/recommendations")
async def get_recommendations(mode: str = Query("normal"), user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    items = await workspace_service.get_recommendations(mode)
    return {
        "items": [
            {
                "title": r.title,
                "description": r.description,
                "action_type": r.action_type,
                "action_data": r.action_data,
            }
            for r in items
        ]
    }


@router.get("/encouragement")
async def get_encouragement(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await workspace_service.get_encouragement()
    return {
        "message": result.message,
        "category": result.category,
        "context_aware": result.context_aware,
        "related_tool": result.related_tool,
        "tone": result.tone,
    }


@router.post("/encouragement/smart")
async def get_smart_encouragement(req: SmartEncouragementRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await workspace_service.get_smart_encouragement(
        active_tool=req.active_tool,
        work_context=req.work_context,
        emotion_state=req.emotion_state,
        recent_actions=req.recent_actions,
        work_duration_minutes=req.work_duration_minutes,
        completed_tasks_count=req.completed_tasks_count,
    )
    return {
        "message": result.message,
        "category": result.category,
        "context_aware": result.context_aware,
        "related_tool": result.related_tool,
        "tone": result.tone,
    }
