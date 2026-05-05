from __future__ import annotations

import hashlib
import json
import os
import secrets
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class APIKeyPermission(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    key_hash: str = ""
    key_prefix: str = ""
    permissions: list[APIKeyPermission] = Field(default_factory=lambda: [APIKeyPermission.READ])
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    usage_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class APIKeyCreateRequest(BaseModel):
    name: str
    permissions: list[APIKeyPermission] = Field(default_factory=lambda: [APIKeyPermission.READ])
    expires_at: Optional[str] = None


class WebhookEvent(str, Enum):
    CHAT_MESSAGE = "chat.message"
    CHAT_SESSION = "chat.session"
    TOOL_CALL = "tool.call"
    AGENT_TASK = "agent.task"
    ARTIFACT_CREATED = "artifact.created"
    RESEARCH_COMPLETED = "research.completed"
    PROACTIVE_SERVICE = "proactive.service"
    DEVICE_STATUS = "device.status"


class WebhookStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


class Webhook(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    url: str
    events: list[WebhookEvent] = Field(default_factory=list)
    secret: str = Field(default_factory=lambda: secrets.token_hex(16))
    status: WebhookStatus = WebhookStatus.ACTIVE
    last_triggered_at: Optional[str] = None
    trigger_count: int = 0
    failure_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class WebhookCreateRequest(BaseModel):
    name: str
    url: str
    events: list[WebhookEvent]


class WebhookDelivery(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    webhook_id: str
    event: WebhookEvent
    payload: dict[str, Any] = Field(default_factory=dict)
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    success: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "api_keys")
_WEBHOOK_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "webhooks")


class APIKeyService:
    def __init__(self):
        self._keys: dict[str, APIKey] = {}
        self._load_all()

    def _load_all(self):
        try:
            if os.path.exists(_DATA_DIR):
                for fname in os.listdir(_DATA_DIR):
                    if fname.endswith(".json"):
                        with open(os.path.join(_DATA_DIR, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            key = APIKey(**data)
                            self._keys[key.id] = key
        except Exception:
            pass

    def _save(self, key: APIKey):
        os.makedirs(_DATA_DIR, exist_ok=True)
        path = os.path.join(_DATA_DIR, f"{key.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(key.model_dump(), f, ensure_ascii=False, indent=2)

    async def create_key(self, req: APIKeyCreateRequest) -> tuple[APIKey, str]:
        raw_key = f"poly_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:10]
        api_key = APIKey(
            name=req.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=req.permissions,
            expires_at=req.expires_at,
        )
        self._keys[api_key.id] = api_key
        self._save(api_key)
        return api_key, raw_key

    async def validate_key(self, raw_key: str) -> Optional[APIKey]:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        for key in self._keys.values():
            if key.key_hash == key_hash and key.status == APIKeyStatus.ACTIVE:
                key.usage_count += 1
                key.last_used_at = datetime.now().isoformat()
                self._save(key)
                return key
        return None

    async def list_keys(self) -> list[APIKey]:
        return list(self._keys.values())

    async def revoke_key(self, key_id: str) -> bool:
        key = self._keys.get(key_id)
        if key:
            key.status = APIKeyStatus.REVOKED
            self._save(key)
            return True
        return False

    async def delete_key(self, key_id: str) -> bool:
        if key_id in self._keys:
            del self._keys[key_id]
            path = os.path.join(_DATA_DIR, f"{key_id}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        return False


class WebhookService:
    def __init__(self):
        self._webhooks: dict[str, Webhook] = {}
        self._deliveries: list[WebhookDelivery] = []
        self._load_all()

    def _load_all(self):
        try:
            if os.path.exists(_WEBHOOK_DIR):
                for fname in os.listdir(_WEBHOOK_DIR):
                    if fname.endswith(".json"):
                        with open(os.path.join(_WEBHOOK_DIR, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            wh = Webhook(**data)
                            self._webhooks[wh.id] = wh
        except Exception:
            pass

    def _save(self, webhook: Webhook):
        os.makedirs(_WEBHOOK_DIR, exist_ok=True)
        path = os.path.join(_WEBHOOK_DIR, f"{webhook.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(webhook.model_dump(), f, ensure_ascii=False, indent=2)

    async def create_webhook(self, req: WebhookCreateRequest) -> Webhook:
        webhook = Webhook(name=req.name, url=req.url, events=req.events)
        self._webhooks[webhook.id] = webhook
        self._save(webhook)
        return webhook

    async def list_webhooks(self) -> list[Webhook]:
        return list(self._webhooks.values())

    async def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        return self._webhooks.get(webhook_id)

    async def update_webhook(self, webhook_id: str, events: Optional[list[WebhookEvent]] = None, status: Optional[WebhookStatus] = None) -> Optional[Webhook]:
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return None
        if events is not None:
            webhook.events = events
        if status is not None:
            webhook.status = status
        self._save(webhook)
        return webhook

    async def delete_webhook(self, webhook_id: str) -> bool:
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            path = os.path.join(_WEBHOOK_DIR, f"{webhook_id}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        return False

    async def trigger(self, event: WebhookEvent, payload: dict[str, Any]) -> list[WebhookDelivery]:
        deliveries = []
        for webhook in self._webhooks.values():
            if webhook.status != WebhookStatus.ACTIVE:
                continue
            if event not in webhook.events:
                continue
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event=event,
                payload=payload,
            )
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    sig = hashlib.hmac_new(
                        webhook.secret.encode(),
                        json.dumps(payload, ensure_ascii=False).encode(),
                        hashlib.sha256,
                    ).hexdigest()
                    resp = await client.post(
                        webhook.url,
                        json={"event": event.value, "payload": payload, "signature": sig},
                        headers={"X-PolySpace-Signature": sig, "Content-Type": "application/json"},
                        timeout=10.0,
                    )
                    delivery.status_code = resp.status_code
                    delivery.response_body = resp.text[:500]
                    delivery.success = 200 <= resp.status_code < 300
            except Exception as e:
                delivery.success = False
                delivery.response_body = str(e)[:500]
                webhook.failure_count += 1
            webhook.trigger_count += 1
            webhook.last_triggered_at = datetime.now().isoformat()
            self._save(webhook)
            deliveries.append(delivery)
        self._deliveries.extend(deliveries)
        return deliveries

    async def get_deliveries(self, webhook_id: Optional[str] = None, limit: int = 50) -> list[dict]:
        deliveries = self._deliveries
        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]
        deliveries = sorted(deliveries, key=lambda d: d.created_at, reverse=True)
        return [d.model_dump() for d in deliveries[:limit]]


api_key_service = APIKeyService()
webhook_service = WebhookService()
