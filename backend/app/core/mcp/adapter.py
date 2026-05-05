from __future__ import annotations

from typing import Any

from app.core.mcp.client import MCPClient, MCPToolDef, mcp_client
from app.core.tool.base import BaseTool, ToolState


class MCPToolAdapter(BaseTool):
    def __init__(self, tool_def: MCPToolDef, client: MCPClient | None = None) -> None:
        super().__init__(
            name=f"mcp_{tool_def.server_name}_{tool_def.name}",
            description=tool_def.description,
        )
        self._tool_def = tool_def
        self._client = client or mcp_client
        self._state = ToolState.INACTIVE

    @property
    def tool_def(self) -> MCPToolDef:
        return self._tool_def

    async def _on_activate(self) -> None:
        if self._tool_def.server_name not in self._client.get_connected_servers():
            connected = await self._client.connect(self._tool_def.server_name)
            if not connected:
                raise RuntimeError(f"Failed to connect to MCP server: {self._tool_def.server_name}")

    async def _on_call(self, **kwargs: Any) -> Any:
        return await self._client.call_tool(self._tool_def.name, kwargs)

    async def _on_hibernate(self) -> None:
        pass

    def get_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._tool_def.input_schema,
            },
        }
