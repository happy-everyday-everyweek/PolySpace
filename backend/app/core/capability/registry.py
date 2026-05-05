from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service
from app.core.capability.base import (
    CapabilityCategory,
    CapabilityMeta,
    CapabilityPlatform,
    CapabilityProvider,
    CapabilitySource,
    CapabilityState,
)

logger = logging.getLogger(__name__)


class _CapabilityEntry:
    __slots__ = ("meta", "provider", "state")

    def __init__(self, meta: CapabilityMeta, provider: CapabilityProvider):
        self.meta = meta
        self.provider = provider
        self.state = CapabilityState.INACTIVE


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, _CapabilityEntry] = {}
        self._providers: dict[str, CapabilityProvider] = {}
        self._change_callbacks: list[Callable[[str, str], Any]] = []
        self._initialized = False

    def register(self, meta: CapabilityMeta, provider: CapabilityProvider) -> None:
        if meta.name in self._capabilities:
            existing = self._capabilities[meta.name]
            if existing.meta.source_type == meta.source_type:
                logger.debug(f"Capability '{meta.name}' already registered by same source, updating")
            else:
                old_src = existing.meta.source_type.value
                new_src = meta.source_type.value
                logger.warning(
                    f"Capability '{meta.name}' already registered by "
                    f"{old_src}, overriding with {new_src}"
                )
        self._capabilities[meta.name] = _CapabilityEntry(meta, provider)
        self._notify_change(meta.name, "registered")

    def unregister(self, name: str) -> None:
        if name not in self._capabilities:
            return
        del self._capabilities[name]
        self._notify_change(name, "unregistered")

    def get(self, name: str) -> Optional[CapabilityMeta]:
        entry = self._capabilities.get(name)
        return entry.meta if entry else None

    def get_entry(self, name: str) -> Optional[_CapabilityEntry]:
        return self._capabilities.get(name)

    def has(self, name: str) -> bool:
        return name in self._capabilities

    def discover(
        self,
        source_type: Optional[CapabilitySource] = None,
        platform: Optional[CapabilityPlatform] = None,
        category: Optional[CapabilityCategory] = None,
        keyword: Optional[str] = None,
    ) -> list[CapabilityMeta]:
        results = []
        for entry in self._capabilities.values():
            meta = entry.meta
            if source_type and meta.source_type != source_type:
                continue
            if platform and not meta.is_available_on(platform):
                continue
            if category and meta.category != category:
                continue
            if keyword:
                kw = keyword.lower()
                in_name = kw in meta.name.lower()
                in_desc = kw in meta.description.lower()
                in_display = kw in meta.display_name.lower()
                if not (in_name or in_desc or in_display):
                    continue
            results.append(meta)
        return results

    def get_definitions(
        self,
        source_type: Optional[CapabilitySource] = None,
        platform: Optional[CapabilityPlatform] = None,
    ) -> list[dict]:
        metas = self.discover(source_type=source_type, platform=platform)
        return [m.to_openai_function() for m in metas]

    def get_local_definitions(self) -> list[dict]:
        return self.get_definitions(source_type=CapabilitySource.INTERNAL)

    def get_remote_definitions(self) -> list[dict]:
        remote_sources = {CapabilitySource.MCP, CapabilitySource.DEVICE, CapabilitySource.CLI}
        results = []
        for entry in self._capabilities.values():
            if entry.meta.source_type in remote_sources:
                results.append(entry.meta.to_openai_function())
        return results

    def list_capabilities(self) -> list[dict]:
        return [
            {
                "name": entry.meta.name,
                "display_name": entry.meta.display_name,
                "description": entry.meta.description,
                "source_type": entry.meta.source_type.value,
                "category": entry.meta.category.value,
                "state": entry.state.value,
                "provider": entry.meta.provider_name,
            }
            for entry in self._capabilities.values()
        ]

    def add_provider(self, provider: CapabilityProvider) -> None:
        self._providers[provider.name] = provider

    def remove_provider(self, provider_name: str) -> list[str]:
        provider = self._providers.pop(provider_name, None)
        if not provider:
            return []
        removed = []
        for name in list(self._capabilities.keys()):
            entry = self._capabilities.get(name)
            if entry and entry.provider is provider:
                del self._capabilities[name]
                removed.append(name)
                self._notify_change(name, "unregistered")
        return removed

    def on_change(self, callback: Callable[[str, str], Any]) -> None:
        self._change_callbacks.append(callback)

    def _notify_change(self, capability_name: str, action: str) -> None:
        for cb in self._change_callbacks:
            try:
                cb(capability_name, action)
            except Exception:
                pass

    async def initialize(self) -> list[str]:
        if self._initialized:
            return []
        all_registered: list[str] = []
        for provider in self._providers.values():
            try:
                metas = await provider.discover()
                for meta in metas:
                    meta.provider_name = provider.name
                    self.register(meta, provider)
                    all_registered.append(meta.name)
                logger.info(f"Provider '{provider.name}' registered {len(metas)} capabilities")
            except Exception as e:
                logger.error(f"Provider '{provider.name}' discovery failed: {e}")

        await audit_service.record(
            category=AuditCategory.TOOL_REGISTER,
            action="capability_registry_initialize",
            level=AuditLevel.INFO,
            actor_type="system",
            status="success",
            detail=f"Initialized with {len(all_registered)} capabilities from {len(self._providers)} providers",
        )
        self._initialized = True
        return all_registered

    def get_summary_by_source(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self._capabilities.values():
            key = entry.meta.source_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def get_summary_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self._capabilities.values():
            key = entry.meta.category.value
            counts[key] = counts.get(key, 0) + 1
        return counts


capability_registry = CapabilityRegistry()
