from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, HTTPException, Query, Depends

from app.services.artifact_service import (
    ArtifactCreateRequest,
    ArtifactType,
    ArtifactUpdateRequest,
    artifact_service,
)

router = APIRouter()


@router.post("")
async def create_artifact(req: ArtifactCreateRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    artifact = await artifact_service.create(req)
    return artifact.model_dump()


@router.get("")
async def list_artifacts(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    type: Optional[ArtifactType] = None,
    session_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    artifacts = await artifact_service.list_artifacts(type=type, session_id=session_id, limit=limit, offset=offset)
    return {"items": [a.model_dump() for a in artifacts], "total": len(artifacts)}


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    artifact = await artifact_service.get(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.model_dump()


@router.get("/{artifact_id}/render")
async def render_artifact(artifact_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    rendered = await artifact_service.render(artifact_id)
    if not rendered:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return rendered


@router.patch("/{artifact_id}")
async def update_artifact(artifact_id: str, req: ArtifactUpdateRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    artifact = await artifact_service.update(artifact_id, req)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.model_dump()


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    deleted = await artifact_service.delete(artifact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"status": "deleted"}
