from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.webhook_service import (
    APIKeyCreateRequest,
    WebhookCreateRequest,
    WebhookEvent,
    WebhookStatus,
    api_key_service,
    webhook_service,
)

router = APIRouter()


@router.post("/api-keys")
async def create_api_key(req: APIKeyCreateRequest):
    api_key, raw_key = await api_key_service.create_key(req)
    result = api_key.model_dump()
    result["key"] = raw_key
    return result


@router.get("/api-keys")
async def list_api_keys():
    keys = await api_key_service.list_keys()
    return {"keys": [k.model_dump() for k in keys]}


@router.post("/api-keys/{key_id}/revoke")
async def revoke_api_key(key_id: str):
    revoked = await api_key_service.revoke_key(key_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "revoked"}


@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    deleted = await api_key_service.delete_key(key_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "deleted"}


@router.post("/webhooks")
async def create_webhook(req: WebhookCreateRequest):
    webhook = await webhook_service.create_webhook(req)
    return webhook.model_dump()


@router.get("/webhooks")
async def list_webhooks():
    webhooks = await webhook_service.list_webhooks()
    return {"webhooks": [w.model_dump() for w in webhooks]}


@router.get("/webhooks/{webhook_id}")
async def get_webhook(webhook_id: str):
    webhook = await webhook_service.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook.model_dump()


class WebhookUpdateRequest(BaseModel):
    events: Optional[list[WebhookEvent]] = None
    status: Optional[WebhookStatus] = None


@router.patch("/webhooks/{webhook_id}")
async def update_webhook(webhook_id: str, req: WebhookUpdateRequest):
    webhook = await webhook_service.update_webhook(webhook_id, events=req.events, status=req.status)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook.model_dump()


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str):
    deleted = await webhook_service.delete_webhook(webhook_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "deleted"}


@router.post("/webhooks/trigger")
async def trigger_webhook(event: WebhookEvent, payload: dict[str, Any]):
    deliveries = await webhook_service.trigger(event, payload)
    return {"deliveries": [d.model_dump() for d in deliveries]}


@router.get("/webhooks/deliveries")
async def list_deliveries(webhook_id: Optional[str] = None, limit: int = Query(50, ge=1, le=200)):
    deliveries = await webhook_service.get_deliveries(webhook_id=webhook_id, limit=limit)
    return {"deliveries": deliveries}
