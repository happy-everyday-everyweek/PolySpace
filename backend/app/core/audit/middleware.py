from __future__ import annotations

import json
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service, new_span, new_trace_id

_SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}
_MAX_BODY_SIZE = 4096


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        k: ("***" if k.lower() in _SENSITIVE_HEADERS else v)
        for k, v in headers.items()
    }


def _summarize_body(body: bytes, max_len: int = _MAX_BODY_SIZE) -> str:
    if not body:
        return ""
    text = body[:max_len].decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            for key in list(parsed.keys()):
                if key.lower() in {"password", "token", "secret", "key", "credential"}:
                    parsed[key] = "***"
            return json.dumps(parsed, ensure_ascii=False)[:max_len]
    except (json.JSONDecodeError, ValueError):
        pass
    return text


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        exclude_paths: set[str] | None = None,
        exclude_prefixes: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._exclude_paths = exclude_paths or {"/health", "/docs", "/openapi.json", "/redoc"}
        self._exclude_prefixes = exclude_prefixes or []

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in self._exclude_paths:
            return await call_next(request)

        for prefix in self._exclude_prefixes:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        new_trace_id()
        new_span(parent=False)

        start_time = time.monotonic()

        request_body = b""
        try:
            request_body = await request.body()
        except Exception:
            pass

        request_summary = _summarize_body(request_body)
        request_headers = dict(request.headers)

        source_device_id = request_headers.get("x-device-id", "")
        source_platform = request_headers.get("x-platform", "")

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            await audit_service.record(
                category=AuditCategory.API_REQUEST,
                action=f"{request.method} {request.url.path}",
                level=AuditLevel.ERROR,
                actor_type="user",
                actor_ip=request.client.host if request.client else "",
                source_device_id=source_device_id or None,
                source_platform=source_platform or None,
                status="error",
                duration_ms=round(duration_ms, 2),
                request_summary=request_summary,
                detail=str(exc),
            )
            raise

        duration_ms = (time.monotonic() - start_time) * 1000

        response_body = b""
        if response.status_code >= 400:
            try:
                chunks = []
                async for chunk in response.body_iterator:
                    chunks.append(chunk)
                response_body = b"".join(chunks)

                async def replay_body():
                    yield response_body

                response.body_iterator = replay_body()
            except Exception:
                pass

        response_summary = _summarize_body(response_body) if response_body else ""

        level = AuditLevel.INFO
        if response.status_code >= 500:
            level = AuditLevel.ERROR
        elif response.status_code >= 400:
            level = AuditLevel.WARN

        await audit_service.record(
            category=AuditCategory.API_REQUEST,
            action=f"{request.method} {request.url.path}",
            level=level,
            actor_type="user",
            actor_ip=request.client.host if request.client else "",
            source_device_id=source_device_id or None,
            source_platform=source_platform or None,
            status="success" if response.status_code < 400 else "error",
            duration_ms=round(duration_ms, 2),
            request_summary=request_summary,
            response_summary=response_summary,
            detail=json.dumps({
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
            }, ensure_ascii=False),
        )

        return response


class WebSocketAuditHook:
    def __init__(self) -> None:
        self._on_connect_handlers: list[Callable] = []
        self._on_disconnect_handlers: list[Callable] = []
        self._on_message_handlers: list[Callable] = []

    def on_connect(self, handler: Callable) -> Callable:
        self._on_connect_handlers.append(handler)
        return handler

    def on_disconnect(self, handler: Callable) -> Callable:
        self._on_disconnect_handlers.append(handler)
        return handler

    def on_message(self, handler: Callable) -> Callable:
        self._on_message_handlers.append(handler)
        return handler

    async def emit_connect(self, device_id: str, platform: str, **kwargs) -> None:
        for handler in self._on_connect_handlers:
            try:
                await handler(device_id, platform, **kwargs)
            except Exception:
                pass

    async def emit_disconnect(self, device_id: str, reason: str = "", **kwargs) -> None:
        for handler in self._on_disconnect_handlers:
            try:
                await handler(device_id, reason, **kwargs)
            except Exception:
                pass

    async def emit_message(self, device_id: str, msg_type: str, **kwargs) -> None:
        for handler in self._on_message_handlers:
            try:
                await handler(device_id, msg_type, **kwargs)
            except Exception:
                pass


ws_audit_hook = WebSocketAuditHook()


@ws_audit_hook.on_connect
async def _audit_ws_connect(device_id: str, platform: str, **kwargs):
    await audit_service.record(
        category=AuditCategory.WEBSOCKET,
        action="ws_connect",
        level=AuditLevel.INFO,
        actor_type="device",
        actor_id=device_id,
        source_device_id=device_id,
        source_platform=platform,
        status="success",
        detail=f"Device {device_id} connected via WebSocket from platform {platform}",
    )


@ws_audit_hook.on_disconnect
async def _audit_ws_disconnect(device_id: str, reason: str = "", **kwargs):
    await audit_service.record(
        category=AuditCategory.WEBSOCKET,
        action="ws_disconnect",
        level=AuditLevel.INFO,
        actor_type="device",
        actor_id=device_id,
        source_device_id=device_id,
        status="success",
        detail=f"Device {device_id} disconnected. Reason: {reason or 'unknown'}",
    )


@ws_audit_hook.on_message
async def _audit_ws_message(device_id: str, msg_type: str, **kwargs):
    if msg_type == "tool_call":
        tool_name = kwargs.get("tool_name", "")
        action = kwargs.get("action", "")
        await audit_service.record(
            category=AuditCategory.DEVICE_EXECUTE,
            action=f"remote_tool_call:{tool_name}",
            level=AuditLevel.INFO,
            actor_type="device",
            actor_id=device_id,
            source_device_id=device_id,
            resource_type="tool",
            resource_id=tool_name,
            detail=f"Remote tool call: {tool_name}.{action}",
        )
    elif msg_type == "tool_result":
        request_id = kwargs.get("request_id", "")
        await audit_service.record(
            category=AuditCategory.DEVICE_EXECUTE,
            action="remote_tool_result",
            level=AuditLevel.INFO,
            actor_type="device",
            actor_id=device_id,
            source_device_id=device_id,
            resource_type="tool_result",
            resource_id=request_id,
            status=kwargs.get("status", "success"),
        )
    elif msg_type == "tool_error":
        error_msg = kwargs.get("error", "")
        await audit_service.record(
            category=AuditCategory.DEVICE_EXECUTE,
            action="remote_tool_error",
            level=AuditLevel.ERROR,
            actor_type="device",
            actor_id=device_id,
            source_device_id=device_id,
            resource_type="tool_error",
            resource_id=kwargs.get("request_id", ""),
            status="error",
            detail=error_msg,
        )
