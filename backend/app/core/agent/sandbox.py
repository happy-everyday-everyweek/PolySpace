from __future__ import annotations

import asyncio
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    error: str | None = None


class BaseSandbox(ABC):
    @abstractmethod
    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        working_dir: str | None = None,
    ) -> SandboxResult:
        ...

    @abstractmethod
    async def execute_command(
        self,
        command: str,
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        working_dir: str | None = None,
    ) -> SandboxResult:
        ...


class LocalSandbox(BaseSandbox):
    LANGUAGE_COMMANDS: dict[str, list[str]] = {
        "python": ["python", "-c"],
        "python3": ["python", "-c"],
        "javascript": ["node", "-e"],
        "js": ["node", "-e"],
        "bash": ["bash", "-c"],
        "sh": ["sh", "-c"],
    }

    def __init__(self, allowed_commands: list[str] | None = None) -> None:
        self._allowed_commands = allowed_commands

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        working_dir: str | None = None,
    ) -> SandboxResult:
        lang = language.lower()
        if lang not in self.LANGUAGE_COMMANDS:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Unsupported language: {language}",
                error=f"Unsupported language: {language}",
            )

        cmd_parts = self.LANGUAGE_COMMANDS[lang] + [code]
        return await self._run_subprocess(cmd_parts, timeout, env, working_dir)

    async def execute_command(
        self,
        command: str,
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        working_dir: str | None = None,
    ) -> SandboxResult:
        if self._allowed_commands:
            base_cmd = command.split()[0] if command.split() else ""
            if base_cmd not in self._allowed_commands:
                return SandboxResult(
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command not allowed: {base_cmd}",
                    error=f"Command not allowed: {base_cmd}",
                )

        cmd_parts = ["bash", "-c", command]
        return await self._run_subprocess(cmd_parts, timeout, env, working_dir)

    async def _run_subprocess(
        self,
        cmd_parts: list[str],
        timeout: float,
        env: dict[str, str] | None,
        working_dir: str | None,
    ) -> SandboxResult:
        process_env = dict(os.environ)
        if env:
            process_env.update(env)

        work_dir = working_dir or tempfile.gettempdir()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=process_env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                return SandboxResult(
                    exit_code=process.returncode or 0,
                    stdout=stdout_bytes.decode("utf-8", errors="replace"),
                    stderr=stderr_bytes.decode("utf-8", errors="replace"),
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return SandboxResult(
                    exit_code=-1,
                    stdout="",
                    stderr=f"Execution timed out after {timeout}s",
                    timed_out=True,
                )

        except FileNotFoundError as e:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                error=f"Command not found: {e}",
            )
        except Exception as e:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                error=str(e),
            )


class DockerSandbox(BaseSandbox):
    def __init__(
        self,
        image: str = "python:3.11-slim",
        container_timeout: float = 60.0,
    ) -> None:
        self._image = image
        self._container_timeout = container_timeout

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        working_dir: str | None = None,
    ) -> SandboxResult:
        lang = language.lower()
        if lang in ("python", "python3"):
            cmd = f'python -c {__import__("shlex").quote(code)}'
        elif lang in ("javascript", "js"):
            cmd = f'node -e {__import__("shlex").quote(code)}'
        elif lang in ("bash", "sh"):
            cmd = code
        else:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Unsupported language: {language}",
                error=f"Unsupported language: {language}",
            )

        return await self.execute_command(cmd, timeout, env, working_dir)

    async def execute_command(
        self,
        command: str,
        timeout: float = 30.0,
        env: dict[str, str] | None = None,
        working_dir: str | None = None,
    ) -> SandboxResult:
        docker_args = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "512m",
            "--cpus", "1",
        ]

        if env:
            for k, v in env.items():
                docker_args.extend(["-e", f"{k}={v}"])

        if working_dir:
            docker_args.extend(["-w", working_dir])

        docker_args.extend([self._image, "bash", "-c", command])

        local = LocalSandbox()
        return await local._run_subprocess(docker_args, timeout, None, None)


local_sandbox = LocalSandbox()
