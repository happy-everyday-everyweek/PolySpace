from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None


@dataclass
class MCPToolDef:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    server_name: str = ""


class MCPClient:
    def __init__(self) -> None:
        self._servers: dict[str, MCPServerConfig] = {}
        self._tools: dict[str, MCPToolDef] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._connected: set[str] = set()

    def register_server(self, config: MCPServerConfig) -> None:
        self._servers[config.name] = config

    def unregister_server(self, name: str) -> None:
        self._servers.pop(name, None)
        self._connected.discard(name)

    async def connect(self, server_name: str) -> bool:
        config = self._servers.get(server_name)
        if not config:
            return False

        try:
            import os
            env = dict(os.environ)
            env.update(config.env)

            process = await asyncio.create_subprocess_exec(
                config.command,
                *config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=config.cwd,
                env=env,
            )

            self._processes[server_name] = process

            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "PolySpace", "version": "1.0.0"},
                },
            }

            response = await self._send_request(server_name, init_request)
            if response and "result" in response:
                tools_response = await self._send_request(
                    server_name,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {},
                    },
                )
                if tools_response and "result" in tools_response:
                    for tool_def in tools_response["result"].get("tools", []):
                        mcp_tool = MCPToolDef(
                            name=tool_def["name"],
                            description=tool_def.get("description", ""),
                            input_schema=tool_def.get("inputSchema", {}),
                            server_name=server_name,
                        )
                        self._tools[mcp_tool.name] = mcp_tool

                self._connected.add(server_name)
                return True

            return False

        except Exception:
            return False

    async def disconnect(self, server_name: str) -> None:
        process = self._processes.pop(server_name, None)
        if process:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
        self._connected.discard(server_name)

    async def disconnect_all(self) -> None:
        for name in list(self._connected):
            await self.disconnect(name)

    async def list_tools(self) -> list[MCPToolDef]:
        return list(self._tools.values())

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        tool = self._tools.get(tool_name)
        if not tool:
            raise KeyError(f"MCP tool '{tool_name}' not found")

        if tool.server_name not in self._connected:
            raise RuntimeError(f"MCP server '{tool.server_name}' not connected")

        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }

        response = await self._send_request(tool.server_name, request)
        if response and "result" in response:
            content = response["result"].get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
            return response["result"]
        elif response and "error" in response:
            raise RuntimeError(f"MCP tool error: {response['error'].get('message', 'Unknown error')}")
        return None

    def get_connected_servers(self) -> list[str]:
        return list(self._connected)

    def get_registered_servers(self) -> list[str]:
        return list(self._servers.keys())

    async def _send_request(self, server_name: str, request: dict) -> dict | None:
        process = self._processes.get(server_name)
        if not process or not process.stdin or not process.stdout:
            return None

        try:
            message = json.dumps(request) + "\n"
            process.stdin.write(message.encode())
            await process.stdin.drain()

            response_line = await asyncio.wait_for(process.stdout.readline(), timeout=30.0)
            if response_line:
                return json.loads(response_line.decode())
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass

        return None


mcp_client = MCPClient()
