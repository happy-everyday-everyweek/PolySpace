from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any

from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service
from app.core.capability.base import (
    CapabilityCallContext,
    CapabilityResult,
    CapabilityState,
)
from app.core.capability.registry import CapabilityRegistry, capability_registry

logger = logging.getLogger(__name__)


class _RetryPolicy:
    __slots__ = ("max_retries", "delay_seconds", "backoff_factor")

    def __init__(self, max_retries: int = 0, delay_seconds: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self.backoff_factor = backoff_factor


class CapabilityExecutor:
    def __init__(self, registry: CapabilityRegistry | None = None) -> None:
        self._registry = registry or capability_registry

    async def execute(
        self,
        name: str,
        params: dict[str, Any],
        context: CapabilityCallContext | None = None,
    ) -> CapabilityResult:
        if context is None:
            context = CapabilityCallContext()

        entry = self._registry.get_entry(name)
        if not entry:
            return CapabilityResult(success=False, error=f"Capability '{name}' not found")

        meta = entry.meta
        provider = entry.provider
        audit_id = str(uuid.uuid4())
        start_time = time.monotonic()

        await audit_service.record(
            category=AuditCategory.TOOL_CALL,
            action=f"capability_call:{name}",
            level=AuditLevel.INFO,
            actor_type="agent",
            resource_type="capability",
            resource_id=name,
            trace_id=context.trace_id or None,
            span_id=context.span_id or None,
            status="started",
            detail=json.dumps({
                "source": meta.source_type.value,
                "provider": meta.provider_name,
                "params_keys": list(params.keys()),
            }, ensure_ascii=False)[:500],
        )

        try:
            if entry.state == CapabilityState.INACTIVE:
                await provider.activate(name)
                entry.state = CapabilityState.ACTIVE

            if entry.state not in (CapabilityState.ACTIVE, CapabilityState.CALLING):
                return CapabilityResult(
                    success=False,
                    error=f"Capability '{name}' is in state {entry.state.value}, cannot execute",
                    audit_id=audit_id,
                )

            entry.state = CapabilityState.CALLING
            result = await self._execute_with_timeout_and_retry(
                provider, name, params, context
            )
            entry.state = CapabilityState.ACTIVE

            duration_ms = (time.monotonic() - start_time) * 1000
            result.duration_ms = round(duration_ms, 2)
            result.audit_id = audit_id

            await audit_service.record(
                category=AuditCategory.TOOL_CALL,
                action=f"capability_call:{name}",
                level=AuditLevel.INFO,
                actor_type="agent",
                resource_type="capability",
                resource_id=name,
                trace_id=context.trace_id or None,
                span_id=context.span_id or None,
                status="success",
                duration_ms=result.duration_ms,
                detail=json.dumps({
                    "source": meta.source_type.value,
                    "success": result.success,
                    "result_type": type(result.data).__name__ if result.data is not None else "none",
                }, ensure_ascii=False)[:500],
            )

            return result

        except Exception as e:
            entry.state = CapabilityState.ERROR
            duration_ms = (time.monotonic() - start_time) * 1000

            await audit_service.record(
                category=AuditCategory.TOOL_CALL,
                action=f"capability_call:{name}",
                level=AuditLevel.ERROR,
                actor_type="agent",
                resource_type="capability",
                resource_id=name,
                trace_id=context.trace_id or None,
                span_id=context.span_id or None,
                status="error",
                duration_ms=round(duration_ms, 2),
                detail=str(e)[:500],
            )

            return CapabilityResult(
                success=False,
                error=str(e),
                duration_ms=round(duration_ms, 2),
                audit_id=audit_id,
            )

    async def _execute_with_timeout_and_retry(
        self,
        provider: Any,
        name: str,
        params: dict[str, Any],
        context: CapabilityCallContext,
    ) -> CapabilityResult:
        retry_policy = _RetryPolicy(
            max_retries=context.retry_count,
            delay_seconds=context.retry_delay_seconds,
        )

        last_result: CapabilityResult | None = None
        attempts = 1 + retry_policy.max_retries

        for attempt in range(attempts):
            try:
                result = await asyncio.wait_for(
                    provider.execute(name, params, context),
                    timeout=context.timeout_seconds,
                )
                if result.success or retry_policy.max_retries == 0:
                    return result
                last_result = result
                if attempt < attempts - 1:
                    delay = retry_policy.delay_seconds * (retry_policy.backoff_factor ** attempt)
                    await asyncio.sleep(delay)
            except asyncio.TimeoutError:
                last_result = CapabilityResult(
                    success=False,
                    error=f"Capability '{name}' timed out after {context.timeout_seconds}s",
                )
                if attempt < attempts - 1:
                    delay = retry_policy.delay_seconds * (retry_policy.backoff_factor ** attempt)
                    await asyncio.sleep(delay)
            except Exception as e:
                last_result = CapabilityResult(success=False, error=str(e))
                if attempt < attempts - 1:
                    delay = retry_policy.delay_seconds * (retry_policy.backoff_factor ** attempt)
                    await asyncio.sleep(delay)

        return last_result or CapabilityResult(success=False, error="No result after retries")

    async def activate(self, name: str) -> None:
        entry = self._registry.get_entry(name)
        if not entry:
            raise KeyError(f"Capability '{name}' not found")
        await entry.provider.activate(name)
        entry.state = CapabilityState.ACTIVE

    async def deactivate(self, name: str) -> None:
        entry = self._registry.get_entry(name)
        if not entry:
            raise KeyError(f"Capability '{name}' not found")
        await entry.provider.deactivate(name)
        entry.state = CapabilityState.INACTIVE

    async def health_check(self, name: str) -> bool:
        entry = self._registry.get_entry(name)
        if not entry:
            return False
        try:
            return await entry.provider.health_check(name)
        except Exception:
            return False


capability_executor = CapabilityExecutor()
