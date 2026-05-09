from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, HTTPException, Query, Depends

from app.services.skill_marketplace_service import (
    SkillCategory,
    SkillPublishRequest,
    SkillReviewRequest,
    skill_marketplace_service,
)

router = APIRouter()


@router.get("/skills")
async def list_marketplace_skills(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    category: Optional[SkillCategory] = None,
    search: Optional[str] = None,
    sort_by: str = Query("downloads", pattern="^(downloads|rating|newest)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    skills = await skill_marketplace_service.list_skills(category=category, search=search, sort_by=sort_by, limit=limit, offset=offset)
    return {"skills": [s.model_dump() for s in skills], "total": len(skills)}


@router.get("/skills/{skill_id}")
async def get_marketplace_skill(skill_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    skill = await skill_marketplace_service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill.model_dump()


@router.post("/skills")
async def publish_skill(req: SkillPublishRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    skill = await skill_marketplace_service.publish(req)
    return skill.model_dump()


@router.post("/skills/{skill_id}/install")
async def install_skill(skill_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    installed = await skill_marketplace_service.install(skill_id)
    if not installed:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "installed"}


@router.post("/skills/{skill_id}/uninstall")
async def uninstall_skill(skill_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    uninstalled = await skill_marketplace_service.uninstall(skill_id)
    if not uninstalled:
        raise HTTPException(status_code=404, detail="Skill not installed")
    return {"status": "uninstalled"}


@router.get("/installed")
async def list_installed_skills(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    skills = await skill_marketplace_service.list_installed()
    return {"skills": [s.model_dump() for s in skills]}


@router.post("/skills/{skill_id}/review")
async def review_skill(skill_id: str, req: SkillReviewRequest, user_id: str = "", user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    skill = await skill_marketplace_service.review(skill_id, user_id, req)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill.model_dump()


@router.delete("/skills/{skill_id}")
async def delete_marketplace_skill(skill_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    deleted = await skill_marketplace_service.delete_skill(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "deleted"}
