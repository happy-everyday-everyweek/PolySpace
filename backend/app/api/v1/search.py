from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class SearchResult(BaseModel):
    id: str
    title: str
    description: str
    category: str
    icon: str
    action: str
    action_data: Optional[dict] = None
    score: float = 0.0


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str
    scope: str = "all"


@router.get("", response_model=SearchResponse)
async def unified_search(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[str] = Query(
        None,
        description="Filter by category: app,file,contact,command,setting,knowledge",
    ),
    limit: int = Query(20, ge=1, le=100),
    scope: Optional[str] = Query(
        None,
        description=(
            "Search scope: all,knowledge,notes,todo,"
            "document,calendar,chat,memory,command,app,setting,action,navigation"
        ),
    ),
):
    from app.services.search_service import search_service
    results = await search_service.search(q, category=category, limit=limit, scope=scope)
    return SearchResponse(results=results, total=len(results), query=q, scope=scope or "all")


@router.get("/suggestions")
async def search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
):
    from app.services.search_service import search_service
    suggestions = await search_service.suggest(q, limit=limit)
    return {"suggestions": suggestions}


@router.get("/recent")
async def recent_searches(limit: int = Query(10, ge=1, le=50)):
    from app.services.search_service import search_service
    return {"searches": await search_service.get_recent(limit=limit)}


@router.get("/commands")
async def list_commands():
    from app.services.search_service import search_service
    return {"commands": await search_service.get_all_commands()}
