from __future__ import annotations

import asyncio
import logging
import os
import shlex
import shutil
from dataclasses import dataclass, field
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

_ALLOWED_COMMANDS = {
    "git", "docker", "npm", "pip", "curl", "wget", "python", "node",
    "ls", "cat", "echo", "pwd", "mkdir", "rm", "cp", "mv",
    "grep", "head", "tail", "wc", "sort", "uniq"
}

_PREDEFINED_TOOLS: dict[str, dict[str, Any]] = {
    "git": {
        "display_name": "Git",
        "description": "分布式版本控制系统",
        "category": CapabilityCategory.DEVELOPMENT,
        "actions": [
            "clone", "commit", "push", "pull",
            "checkout", "branch", "merge",
            "log", "diff", "status", "add", "stash",
        ],
    },
    "docker": {
        "display_name": "Docker",
        "description": "容器化平台",
        "category": CapabilityCategory.AUTOMATION,
        "actions": ["build", "run", "stop", "rm", "ps", "images", "exec", "logs", "compose"],
    },
    "npm": {
        "display_name": "NPM",
        "description": "Node.js包管理器",
        "category": CapabilityCategory.DEVELOPMENT,
        "actions": ["install", "uninstall", "update", "run", "init", "list", "audit"],
    },
    "pip": {
        "display_name": "Pip",
        "description": "Python包管理器",
        "category": CapabilityCategory.DEVELOPMENT,
        "actions": ["install", "uninstall", "list", "show", "freeze", "search"],
    },
    "curl": {
        "display_name": "Curl",
        "description": "URL数据传输工具",
        "category": CapabilityCategory.NETWORK,
        "actions": ["get", "post", "put", "delete", "head", "download"],
    },
    "wget": {
        "display_name": "Wget",
        "description": "网络下载工具",
        "category": CapabilityCategory.NETWORK,
        "actions": ["download", "mirror", "recursive"],
    },
    "python": {
        "display_name": "Python",
        "description": "Python解释器",
        "category": CapabilityCategory.DEVELOPMENT,
        "actions": ["execute", "script", "module", "pip"],
    },
    "node": {
        "display_name": "Node.js",
        "description": "Node.js运行时",
        "category": CapabilityCategory.DEVELOPMENT,
        "actions": ["execute", "script", "repl"],
    },
}


@dataclass
class CLIToolDef:
    name: str
    path: str = ""
    version: str = ""
    help_text: str = ""
    commands: list[str] = field(default_factory=list)


class CLISniffer:
    def scan_path(self) -> list[str]:
        found: list[str] = []
        path_env = os.environ.get("PATH", "")
        separators = ";" if os.name == "nt" else ":"
        seen: set[str] = set()
        for directory in path_env.split(separators):
            if not directory or not os.path.isdir(directory):
                continue
            try:
                for entry in os.listdir(directory):
                    full_path = os.path.join(directory, entry)
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        name = os.path.splitext(entry)[0] if os.name == "nt" else entry
                        if name not in seen:
                            seen.add(name)
                            found.append(name)
            except PermissionError:
                continue
        return found

    async def analyze_tool(self, name: str) -> CLIToolDef:
        tool_path = shutil.which(name) or ""
        version = ""
        help_text = ""
        for flag in ("--version", "-V", "--version"):
            try:
                proc = await asyncio.create_subprocess_exec(
                    name, flag,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
                output = (stdout or b"").decode("utf-8", errors="replace").strip()
                if output:
                    version = output.split("\n")[0][:200]
                    break
            except Exception:
                continue

        try:
            proc = await asyncio.create_subprocess_exec(
                name, "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            help_text = (stdout or stderr or b"").decode("utf-8", errors="replace").strip()[:2000]
        except Exception:
            pass

        return CLIToolDef(
            name=name,
            path=tool_path,
            version=version,
            help_text=help_text,
        )

    async def scan(self) -> list[CLIToolDef]:
        names = self.scan_path()
        results: list[CLIToolDef] = []
        for name in names:
            try:
                tool_def = await self.analyze_tool(name)
                results.append(tool_def)
            except Exception:
                results.append(CLIToolDef(name=name))
        return results


class CLIProvider(CapabilityProvider):
    def __init__(self) -> None:
        self._tools: dict[str, CLIToolDef] = {}
        self._sniffer = CLISniffer()

    @property
    def name(self) -> str:
        return "cli"

    @property
    def source_type(self) -> CapabilitySource:
        return CapabilitySource.CLI

    async def discover(self) -> list[CapabilityMeta]:
        self._tools.clear()
        tool_defs = await self._sniffer.scan()
        metas: list[CapabilityMeta] = []
        for tool_def in tool_defs:
            cap_name = f"cli_{tool_def.name}"
            self._tools[cap_name] = tool_def
            predefined = _PREDEFINED_TOOLS.get(tool_def.name)
            if predefined:
                meta = CapabilityMeta(
                    name=cap_name,
                    display_name=predefined["display_name"],
                    description=predefined["description"],
                    source_type=CapabilitySource.CLI,
                    category=predefined["category"],
                    platforms=[CapabilityPlatform.BACKEND],
                    actions=predefined["actions"],
                    provider_name=self.name,
                    version=tool_def.version,
                )
            else:
                meta = CapabilityMeta(
                    name=cap_name,
                    display_name=tool_def.name,
                    description=tool_def.help_text[:200] if tool_def.help_text else f"CLI tool: {tool_def.name}",
                    source_type=CapabilitySource.CLI,
                    category=CapabilityCategory.AUTOMATION,
                    platforms=[CapabilityPlatform.BACKEND],
                    actions=["execute"],
                    provider_name=self.name,
                    version=tool_def.version,
                )
            metas.append(meta)
        return metas

    async def activate(self, capability_name: str) -> None:
        tool_def = self._tools.get(capability_name)
        if tool_def and tool_def.path:
            if not os.path.isfile(tool_def.path):
                tool_def.path = shutil.which(tool_def.name) or ""

    def _validate_command(self, tool_name: str, action: str, args: list) -> tuple[bool, str]:
        if tool_name not in _ALLOWED_COMMANDS:
            return False, f"Command '{tool_name}' is not allowed"
        
        if "\0" in tool_name or "\0" in action:
            return False, "Null byte detected"
        
        predefined = _PREDEFINED_TOOLS.get(tool_name)
        if predefined and action != "execute":
            allowed_actions = predefined.get("actions", [])
            if action not in allowed_actions:
                return False, f"Action '{action}' is not allowed for '{tool_name}'"
        
        for arg in args:
            arg_str = str(arg)
            if "\0" in arg_str:
                return False, "Null byte in arguments"
            if len(arg_str) > 1024:
                return False, "Argument too long"
        
        return True, ""

    async def execute(
        self,
        capability_name: str,
        params: dict[str, Any],
        context: CapabilityCallContext,
    ) -> CapabilityResult:
        tool_def = self._tools.get(capability_name)
        if not tool_def:
            return CapabilityResult(success=False, error=f"CLI tool '{capability_name}' not found")
        
        tool_name = tool_def.name
        action = params.get("action", "execute")
        args = params.get("args", [])
        
        if isinstance(args, str):
            args = shlex.split(args)
        elif not isinstance(args, list):
            args = []
        
        is_valid, error = self._validate_command(tool_name, action, args)
        if not is_valid:
            logger.warning(f"CLI command validation failed: {error}")
            return CapabilityResult(success=False, error=f"Command validation failed: {error}")
        
        cmd_args = [tool_name]
        if action != "execute":
            cmd_args.append(action)
        cmd_args.extend(args)
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=context.timeout_seconds,
            )
            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""
            if proc.returncode == 0:
                return CapabilityResult(
                    success=True,
                    data={"stdout": stdout_str, "stderr": stderr_str, "returncode": proc.returncode},
                )
            else:
                return CapabilityResult(
                    success=False,
                    error=stderr_str or f"Exit code: {proc.returncode}",
                    data={"stdout": stdout_str, "stderr": stderr_str, "returncode": proc.returncode},
                )
        except asyncio.TimeoutError:
            return CapabilityResult(
                success=False,
                error=f"CLI tool '{tool_name}' timed out after {context.timeout_seconds}s",
            )
        except FileNotFoundError:
            return CapabilityResult(
                success=False,
                error=f"CLI tool '{tool_name}' not found on system",
            )
        except Exception as e:
            return CapabilityResult(success=False, error=str(e))

    async def deactivate(self, capability_name: str) -> None:
        pass

    async def health_check(self, capability_name: str) -> bool:
        tool_def = self._tools.get(capability_name)
        if not tool_def:
            return False
        return shutil.which(tool_def.name) is not None

    def get_capability(self, name: str) -> Optional[CapabilityMeta]:
        tool_def = self._tools.get(name)
        if not tool_def:
            return None
        predefined = _PREDEFINED_TOOLS.get(tool_def.name)
        if predefined:
            return CapabilityMeta(
                name=name,
                display_name=predefined["display_name"],
                description=predefined["description"],
                source_type=CapabilitySource.CLI,
                category=predefined["category"],
                platforms=[CapabilityPlatform.BACKEND],
                actions=predefined["actions"],
                provider_name=self.name,
            )
        return CapabilityMeta(
            name=name,
            display_name=tool_def.name,
            description=f"CLI tool: {tool_def.name}",
            source_type=CapabilitySource.CLI,
            category=CapabilityCategory.AUTOMATION,
            platforms=[CapabilityPlatform.BACKEND],
            actions=["execute"],
            provider_name=self.name,
        )
