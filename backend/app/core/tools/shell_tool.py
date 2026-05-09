from __future__ import annotations

import asyncio
import os
import shlex
from typing import Any

from app.core.tool.base import BaseTool


class ShellTool(BaseTool):
    _ALLOWED_COMMANDS = {
        "ls", "cat", "echo", "pwd", "mkdir", "rm", "cp", "mv", 
        "grep", "head", "tail", "wc", "sort", "uniq", "find",
        "git", "docker", "npm", "pip", "python", "node", "curl", "wget"
    }

    def __init__(self) -> None:
        super().__init__(
            name="shell",
            description="Execute shell commands in a sandboxed environment",
        )

    async def _on_activate(self) -> None:
        pass

    def _sanitize_command(self, command: str) -> tuple[bool, str]:
        if not command or len(command.strip()) > 4096:
            return False, "Command is empty or too long"
        
        if "\0" in command:
            return False, "Null byte in command"
        
        parts = shlex.split(command)
        if not parts:
            return False, "Empty command after parsing"
        
        base_cmd = parts[0]
        if base_cmd not in self._ALLOWED_COMMANDS:
            return False, f"Command '{base_cmd}' is not allowed"
        
        return True, ""

    def _validate_working_dir(self, working_dir: str | None) -> tuple[bool, str]:
        if working_dir is None:
            return True, ""
        
        if ".." in working_dir or working_dir.startswith("/") or working_dir.startswith("\\"):
            return False, "Invalid working directory path"
        
        try:
            abs_path = os.path.abspath(working_dir)
            if abs_path.startswith("/") and not abs_path.startswith("/workspace/"):
                return False, "Working directory must be within workspace"
        except Exception:
            return False, "Invalid working directory"
        
        return True, ""

    async def _on_call(self, **kwargs: Any) -> Any:
        command = kwargs.get("command", "")
        timeout = float(kwargs.get("timeout", 30.0))
        working_dir = kwargs.get("working_dir")

        if timeout < 1 or timeout > 300:
            return {"error": "Timeout must be between 1 and 300 seconds"}

        is_valid, error = self._sanitize_command(command)
        if not is_valid:
            return {"error": f"Command validation failed: {error}"}

        if working_dir:
            is_valid, error = self._validate_working_dir(working_dir)
            if not is_valid:
                return {"error": f"Working directory validation failed: {error}"}

        try:
            shell = "bash" if __import__("platform").system() != "Windows" else "cmd"
            flag = "-c" if __import__("platform").system() != "Windows" else "/c"
            
            process = await asyncio.create_subprocess_exec(
                shell, flag, command,
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
