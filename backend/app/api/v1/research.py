
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.agent.deep_research import deep_research_agent

router = APIRouter()


class ResearchRequest(BaseModel):
    query: str
    max_iterations: int = 3


class ResearchStepRequest(BaseModel):
    step_index: int


@router.post("")
async def start_research(req: ResearchRequest):
    result = await deep_research_agent.start_research(req.query)
    return result.to_dict()


@router.get("")
async def list_research(limit: int = Query(20, ge=1, le=100)):
    results = await deep_research_agent.list_research(limit=limit)
    return {"items": results, "total": len(results)}


@router.get("/{research_id}")
async def get_research(research_id: str):
    result = await deep_research_agent.get_status(research_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research not found")
    return result


@router.post("/{research_id}/step")
async def execute_step(research_id: str, req: ResearchStepRequest):
    result = await deep_research_agent.execute_step(research_id, req.step_index)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{research_id}/synthesize")
async def synthesize_research(research_id: str):
    try:
        result = await deep_research_agent.synthesize(research_id)
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
