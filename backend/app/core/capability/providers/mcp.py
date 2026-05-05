from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.capability.base import (
    CapabilityCallContext,
    CapabilityCategory,
    CapabilityMeta,
    CapabilityPlatform,
    CapabilityProvider,
    CapabilityResult,
    CapabilitySource,
)

logger = logging.getLogger(__name__)


class MCPProvider(CapabilityProvider):
    def __init__(self) -> None:
        self._route: dict[str, tuple[str, str]] = {}
        self._client = None

    @property
    def name(self) -> str:
        return "mcp"

    @property
    def source_type(self) -> CapabilitySource:
        return CapabilitySource.MCP

    def _get_client(self):
        if self._client is None:
            from app.core.mcp.client import mcp_client
            self._client = mcp_client
        return self._client

    async def discover(self) -> list[CapabilityMeta]:
        self._route.clear()
        client = self._get_client()
        metas: list[CapabilityMeta] = []
        try:
            tools = await client.list_tools()
            for tool_def in tools:
                server_name = getattr(tool_def, "server_name", "default")
                tool_name = getattr(tool_def, "name", str(tool_def))
                cap_name = f"mcp_{server_name}_{tool_name}"
                self._route[cap_name] = (server_name, tool_name)
                description = getattr(tool_def, "description", "")
                input_schema = getattr(tool_def, "input_schema", {}) or {}
                parameters = input_schema.get("properties", {})
                meta = CapabilityMeta(
                    name=cap_name,
                    display_name=tool_name,
                    description=description or f"MCP tool: {tool_name}",
                    source_type=CapabilitySource.MCP,
                    category=CapabilityCategory.INTEGRATION,
                    platforms=[CapabilityPlatform.BACKEND],
                    parameters=parameters,
                    provider_name=self.name,
                )
                metas.append(meta)
        except Exception as e:
            logger.error(f"MCP discovery failed: {e}")
        return metas

    async def activate(self, capability_name: str) -> None:
        route = self._route.get(capability_name)
        if not route:
            return
        server_name, _ = route
        client = self._get_client()
        try:
            await client.connect(server_name)
        except Exception as e:
            logger.error(f"MCP activate '{capability_name}' failed: {e}")

    async def execute(
        self,
        capability_name: str,
        params: dict[str, Any],
        context: CapabilityCallContext,
    ) -> CapabilityResult:
        route = self._route.get(capability_name)
        if not route:
            return CapabilityResult(success=False, error=f"MCP capability '{capability_name}' not found")
        server_name, tool_name = route
        client = self._get_client()
        try:
            result = await client.call_tool(server_name, tool_name, params)
            return CapabilityResult(success=True, data=result)
        except Exception as e:
            return CapabilityResult(success=False, error=str(e))

    async def deactivate(self, capability_name: str) -> None:
        pass

    async def health_check(self, capability_name: str) -> bool:
        route = self._route.get(capability_name)
        if not route:
            return False
        server_name, _ = route
        client = self._get_client()
        connected = getattr(client, "connected_servers", set())
        return server_name in connected

    def get_capability(self, name: str) -> Optional[CapabilityMeta]:
        route = self._route.get(name)
        if not route:
            return None
        server_name, tool_name = route
        return CapabilityMeta(
            name=name,
            display_name=tool_name,
            description=f"MCP tool: {tool_name} from {server_name}",
            source_type=CapabilitySource.MCP,
            category=CapabilityCategory.INTEGRATION,
            platforms=[CapabilityPlatform.BACKEND],
            provider_name=self.name,
        )
