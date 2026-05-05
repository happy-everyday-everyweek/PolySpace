from __future__ import annotations

import asyncio
from typing import Any

from app.core.tool.base import BaseTool


class ShellTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="shell",
            description="Execute shell commands in a sandboxed environment",
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs: Any) -> Any:
        command = kwargs.get("command", "")
        timeout = float(kwargs.get("timeout", 30.0))
        working_dir = kwargs.get("working_dir")

        if not command:
            return {"error": "No command provided"}

        try:
            process = await asyncio.create_subprocess_exec(
                "bash" if __import__("platform").system() != "Windows" else "cmd",
                "-c" if __import__("platform").system() != "Windows" else "/c",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                return {
                    "exit_code": process.returncode,
                    "stdout": stdout_bytes.decode("utf-8", errors="replace"),
                    "stderr": stderr_bytes.decode("utf-8", errors="replace"),
                }
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {"error": f"Command timed out after {timeout}s", "exit_code": -1}

        except FileNotFoundError as e:
            return {"error": f"Shell not found: {e}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass

    def get_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The shell command to execute"},
                        "timeout": {"type": "number", "description": "Timeout in seconds (default: 30)"},
                        "working_dir": {"type": "string", "description": "Working directory for the command"},
                    },
                    "required": ["command"],
                },
            },
        }
