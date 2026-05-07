from __future__ import annotations

import asyncio
import json
import logging
import shutil
from typing import Any

from app.core.tool.base import BaseTool

logger = logging.getLogger(__name__)


class OpenCLIWebTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="opencli_web",
            description=(
                "Web operation tool powered by OpenCLI - browser control, "
                "page interaction, content extraction, site adapters, "
                "CDP communication, network capture"
            ),
        )
        self._opencli_path: str | None = None
        self._daemon_running = False

    async def _on_activate(self) -> None:
        self._opencli_path = shutil.which("opencli")
        if self._opencli_path:
            logger.info("OpenCLI found at: %s", self._opencli_path)
        else:
            logger.debug("OpenCLI not found in PATH. Web operations will be limited.")

    async def _on_call(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "")

        if action in ("open", "state", "click", "type", "select", "keys",
                       "wait", "extract", "screenshot", "scroll", "back",
                       "find", "eval", "network", "console", "tab_list",
                       "tab_new", "tab_select", "tab_close", "analyze"):
            return await self._handle_browser_action(action, **kwargs)
        elif action in ("site_command",):
            return await self._handle_site_command(**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}

    async def _handle_browser_action(self, action: str, **kwargs: Any) -> Any:
        if not self._opencli_path:
            return {"error": "OpenCLI not installed. Install: npm install -g @jackwener/opencli"}

        cmd = [self._opencli_path, "browser"]

        if action == "open":
            url = kwargs.get("url", "")
            cmd.extend(["open", url])
        elif action == "state":
            cmd.extend(["state"])
        elif action == "click":
            target = kwargs.get("target", "")
            cmd.extend(["click", target])
        elif action == "type":
            target = kwargs.get("target", "")
            text = kwargs.get("text", "")
            cmd.extend(["type", target, text])
        elif action == "select":
            target = kwargs.get("target", "")
            option = kwargs.get("option", "")
            cmd.extend(["select", target, option])
        elif action == "keys":
            key = kwargs.get("key", "")
            cmd.extend(["keys", key])
        elif action == "wait":
            wait_type = kwargs.get("wait_type", "navigation")
            value = kwargs.get("value", "")
            cmd.extend(["wait", wait_type])
            if value:
                cmd.append(value)
        elif action == "extract":
            cmd.extend(["extract"])
            selector = kwargs.get("selector", "")
            if selector:
                cmd.extend(["--selector", selector])
        elif action == "screenshot":
            path = kwargs.get("path", "")
            cmd.extend(["screenshot"])
            if path:
                cmd.append(path)
        elif action == "scroll":
            direction = kwargs.get("direction", "down")
            cmd.extend(["scroll", direction])
        elif action == "back":
            cmd.extend(["back"])
        elif action == "find":
            css = kwargs.get("css", "")
            cmd.extend(["find", "--css", css])
        elif action == "eval":
            js = kwargs.get("js", "")
            cmd.extend(["eval", js])
        elif action == "network":
            cmd.extend(["network"])
        elif action == "console":
            cmd.extend(["console"])
        elif action == "tab_list":
            cmd.extend(["tab", "list"])
        elif action == "tab_new":
            url = kwargs.get("url", "")
            cmd.extend(["tab", "new"])
            if url:
                cmd.append(url)
        elif action == "tab_select":
            target_id = kwargs.get("target_id", "")
            cmd.extend(["tab", "select", target_id])
        elif action == "tab_close":
            target_id = kwargs.get("target_id", "")
            cmd.extend(["tab", "close", target_id])
        elif action == "analyze":
            url = kwargs.get("url", "")
            cmd.extend(["analyze", url])

        cmd.extend(["--format", "json"])

        profile = kwargs.get("profile", "")
        if profile:
            cmd.extend(["--profile", profile])

        tab = kwargs.get("tab", "")
        if tab:
            cmd.extend(["--tab", str(tab)])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=kwargs.get("timeout", 30))

            if proc.returncode == 0:
                try:
                    return json.loads(stdout.decode())
                except json.JSONDecodeError:
                    return {"raw_output": stdout.decode(), "success": True}
            else:
                return {
                    "error": stderr.decode() if stderr else f"Command failed with code {proc.returncode}",
                    "exit_code": proc.returncode,
                }
        except asyncio.TimeoutError:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}

    async def _handle_site_command(self, **kwargs: Any) -> Any:
        site = kwargs.get("site", "")
        command = kwargs.get("command", "")
        args = kwargs.get("args", {})

        if not self._opencli_path:
            return {"error": "OpenCLI not installed"}

        if not site or not command:
            return {"error": "Both 'site' and 'command' are required"}

        cmd = [self._opencli_path, site, command, "--format", "json"]

        for key, value in args.items():
            cmd.extend([f"--{key}", str(value)])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

            if proc.returncode == 0:
                try:
                    return json.loads(stdout.decode())
                except json.JSONDecodeError:
                    return {"raw_output": stdout.decode(), "success": True}
            else:
                return {"error": stderr.decode() if stderr else "Command failed", "exit_code": proc.returncode}
        except asyncio.TimeoutError:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        self._opencli_path = None
        self._daemon_running = False
