from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, HTTPException, Query, Depends

from app.services.clipboard_service import (
    ClipboardContentType,
    ClipboardCreateRequest,
    clipboard_service,
)

router = APIRouter()


@router.post("")
async def add_clipboard(req: ClipboardCreateRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        item = await clipboard_service.add(req)
        return item.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_clipboard(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    content_type: Optional[ClipboardContentType] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items = await clipboard_service.list_items(content_type=content_type, limit=limit, offset=offset)
    return {"items": [i.model_dump() for i in items], "total": len(items)}


@router.get("/{item_id}")
async def get_clipboard(item_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    item = await clipboard_service.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Clipboard item not found")
    return item.model_dump()


@router.delete("/{item_id}")
async def delete_clipboard(item_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    deleted = await clipboard_service.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Clipboard item not found")
    return {"status": "deleted"}


@router.delete("")
async def clear_clipboard(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    count = await clipboard_service.clear()
    return {"status": "cleared", "count": count}
