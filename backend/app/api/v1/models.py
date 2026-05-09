from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class ModelConfigRequest(BaseModel):
    name: str
    tier: str
    provider: str
    model_id: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    capabilities: list[str] = []
    scene_description: Optional[str] = None


@router.get("/config")
async def get_model_config(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "base_model": settings.LLM_BASE_MODEL,
        "strong_model": settings.LLM_STRONG_MODEL,
        "performance_model": settings.LLM_PERFORMANCE_MODEL,
        "cost_effective_model": settings.LLM_COST_EFFECTIVE_MODEL,
        "multimodal_model": settings.LLM_MULTIMODAL_MODEL,
        "screen_model": settings.LLM_SCREEN_MODEL,
    }


@router.post("/config")
async def update_model_config(request: ModelConfigRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"status": "ok", "model": request.name, "tier": request.tier}


@router.get("/tiers")
async def get_model_tiers(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "tiers": [
            {"name": "base", "description": "Base model (required)"},
            {"name": "strong", "description": "Strong capability model for planning"},
            {"name": "performance", "description": "High performance model for daily tasks"},
            {"name": "cost_effective", "description": "Cost-effective model for simple tasks"},
            {"name": "vertical_multimodal", "description": "Multimodal vertical model"},
            {"name": "vertical_screen", "description": "Screen operation vertical model"},
            {"name": "vertical_custom", "description": "Custom vertical model"},
        ]
    }
