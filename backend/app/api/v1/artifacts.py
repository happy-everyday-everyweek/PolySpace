from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.artifact_service import (
    ArtifactCreateRequest,
    ArtifactType,
    ArtifactUpdateRequest,
    artifact_service,
)

router = APIRouter()


@router.post("")
async def create_artifact(req: ArtifactCreateRequest):
    artifact = await artifact_service.create(req)
    return artifact.model_dump()


@router.get("")
async def list_artifacts(
    type: Optional[ArtifactType] = None,
    session_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    artifacts = await artifact_service.list_artifacts(type=type, session_id=session_id, limit=limit, offset=offset)
    return {"items": [a.model_dump() for a in artifacts], "total": len(artifacts)}


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str):
    artifact = await artifact_service.get(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.model_dump()


@router.get("/{artifact_id}/render")
async def render_artifact(artifact_id: str):
    rendered = await artifact_service.render(artifact_id)
    if not rendered:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return rendered


@router.patch("/{artifact_id}")
async def update_artifact(artifact_id: str, req: ArtifactUpdateRequest):
    artifact = await artifact_service.update(artifact_id, req)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.model_dump()


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str):
    deleted = await artifact_service.delete(artifact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"status": "deleted"}
