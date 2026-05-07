from __future__ import annotations

import asyncio
import logging
import os
import shutil
import signal
import subprocess
import sys
from enum import Enum
from typing import Any

import httpx

from app.core.tool.base import BaseTool

logger = logging.getLogger(__name__)

OPEN_DESIGN_DIR = os.environ.get(
    "OPEN_DESIGN_DIR",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "open-design-main")
    ),
)
if not os.path.isdir(OPEN_DESIGN_DIR):
    mobile_path = "/home/polyspace/open-design"
    if os.path.isdir(mobile_path):
        OPEN_DESIGN_DIR = mobile_path
OPEN_DESIGN_DEFAULT_PORT = 3838
OPEN_DESIGN_DEFAULT_HOST = "127.0.0.1"


class ProcessStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


class OpenDesignProcessManager:
    _instance: OpenDesignProcessManager | None = None

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._status = ProcessStatus.STOPPED
        self._port = OPEN_DESIGN_DEFAULT_PORT
        self._host = OPEN_DESIGN_DEFAULT_HOST
        self._base_url = f"http://{self._host}:{self._port}"
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def get_instance(cls) -> OpenDesignProcessManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def status(self) -> ProcessStatus:
        return self._status

    @property
    def base_url(self) -> str:
        return self._base_url

    def is_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None

    async def start(self, port: int | None = None) -> dict[str, Any]:
        if self.is_running():
            return {"status": "already_running", "base_url": self._base_url}

        if not os.path.isdir(OPEN_DESIGN_DIR):
            return {"error": f"Open Design directory not found: {OPEN_DESIGN_DIR}"}

        if port is not None:
            self._port = port
            self._base_url = f"http://{self._host}:{self._port}"

        self._status = ProcessStatus.STARTING

        node_path = shutil.which("node")
        if not node_path:
            self._status = ProcessStatus.ERROR
            return {"error": "Node.js not found in PATH"}

        daemon_cli = os.path.join(OPEN_DESIGN_DIR, "apps", "daemon", "dist", "cli.js")
        if not os.path.isfile(daemon_cli):
            daemon_cli_alt = os.path.join(OPEN_DESIGN_DIR, "apps", "daemon", "src", "cli.ts")
            if os.path.isfile(daemon_cli_alt):
                daemon_cli = daemon_cli_alt
            else:
                self._status = ProcessStatus.ERROR
                return {"error": f"Open Design daemon CLI not found at {daemon_cli}"}

        env = os.environ.copy()
        env["PORT"] = str(self._port)
        env["HOST"] = self._host
        env["OD_DATA_DIR"] = os.path.join(OPEN_DESIGN_DIR, ".od")
        env["POLYSPACE_API_URL"] = os.environ.get(
            "POLYSPACE_API_URL", f"http://127.0.0.1:{os.environ.get('POLYSPACE_PORT', '8000')}"
        )

        try:
            if sys.platform == "win32":
                self._process = subprocess.Popen(
                    [node_path, daemon_cli],
                    cwd=OPEN_DESIGN_DIR,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                self._process = subprocess.Popen(
                    [node_path, daemon_cli],
                    cwd=OPEN_DESIGN_DIR,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid,
                )
        except Exception as e:
            self._status = ProcessStatus.ERROR
            return {"error": f"Failed to start Open Design daemon: {str(e)}"}

        for _ in range(30):
            await asyncio.sleep(1)
            if not self.is_running():
                self._status = ProcessStatus.ERROR
                stderr_out = ""
                if self._process and self._process.stderr:
                    try:
                        stderr_out = self._process.stderr.read(2048).decode(errors="replace")
                    except Exception:
                        pass
                return {"error": "Open Design daemon exited prematurely", "stderr": stderr_out}

            if await self._health_check():
                self._status = ProcessStatus.RUNNING
                self._ensure_client()
                logger.info("Open Design daemon started on %s", self._base_url)
                return {"status": "running", "base_url": self._base_url}

        self._status = ProcessStatus.ERROR
        return {"error": "Open Design daemon health check timed out after 30s"}

    async def stop(self) -> dict[str, Any]:
        if not self.is_running():
            self._status = ProcessStatus.STOPPED
            return {"status": "already_stopped"}

        try:
            if sys.platform == "win32":
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self._process.terminate()

            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        except Exception as e:
            logger.warning("Error stopping Open Design daemon: %s", e)

        self._process = None
        self._status = ProcessStatus.STOPPED

        if self._client:
            await self._client.aclose()
            self._client = None

        return {"status": "stopped"}

    async def _health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self._base_url}/api/health")
                return resp.status_code == 200
        except Exception:
            return False

    def _ensure_client(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=60.0,
            )

    async def api_request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self._client:
            self._ensure_client()
        if self._client is None:
            return {"error": "Open Design client not available"}
        try:
            resp = await self._client.request(method, path, **kwargs)
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "")
            if ct.startswith("application/json"):
                return resp.json()
            return {"content_type": ct, "size": len(resp.content)}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request error: {str(e)}"}

    async def ensure_running(self) -> dict[str, Any]:
        if self.is_running() and self._status == ProcessStatus.RUNNING:
            return {"status": "running", "base_url": self._base_url}
        return await self.start()

    def get_status(self) -> dict[str, Any]:
        return {
            "status": self._status.value,
            "base_url": self._base_url,
            "port": self._port,
            "pid": self._process.pid if self._process and self.is_running() else None,
            "open_design_dir": OPEN_DESIGN_DIR,
        }


class OpenDesignTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="open_design",
            description=(
                "Open Design tool - AI-driven design with skills, design systems, "
                "project management, artifact creation, media generation, and export. "
                "Manages the Open Design daemon as a subprocess."
            ),
        )
        self._manager = OpenDesignProcessManager.get_instance()

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "")

        if action == "start_daemon":
            return await self._manager.start(kwargs.get("port"))
        elif action == "stop_daemon":
            return await self._manager.stop()
        elif action == "daemon_status":
            return self._manager.get_status()
        elif action == "ensure_running":
            return await self._manager.ensure_running()

        if action not in ("start_daemon", "stop_daemon", "daemon_status", "ensure_running"):
            if not self._manager.is_running():
                start_result = await self._manager.ensure_running()
                if start_result.get("status") not in ("running", "already_running"):
                    return {"error": "Open Design daemon is not running", "start_result": start_result}

        handlers = {
            "list_skills": self._list_skills,
            "get_skill": self._get_skill,
            "list_design_systems": self._list_design_systems,
            "get_design_system": self._get_design_system,
            "list_projects": self._list_projects,
            "create_project": self._create_project,
            "get_project": self._get_project,
            "delete_project": self._delete_project,
            "list_conversations": self._list_conversations,
            "create_conversation": self._create_conversation,
            "list_files": self._list_project_files,
            "read_file": self._read_project_file,
            "save_artifact": self._save_artifact,
            "lint_artifact": self._lint_artifact,
            "list_media_models": self._list_media_models,
            "generate_media": self._generate_media,
            "export_html": self._export_html,
            "export_pdf": self._export_pdf,
            "export_to_ppt": self._export_to_ppt,
            "export_to_dev": self._export_to_dev,
            "health": self._health,
        }

        handler = handlers.get(action)
        if handler:
            return await handler(**kwargs)
        return {"error": f"Unknown action: {action}. Available: {', '.join(handlers.keys())}"}

    async def _list_skills(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/skills")

    async def _get_skill(self, **kwargs: Any) -> Any:
        skill_id = kwargs.get("skill_id", "")
        return await self._manager.api_request("GET", f"/api/skills/{skill_id}")

    async def _list_design_systems(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/design-systems")

    async def _get_design_system(self, **kwargs: Any) -> Any:
        ds_id = kwargs.get("design_system_id", "")
        return await self._manager.api_request("GET", f"/api/design-systems/{ds_id}")

    async def _list_projects(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/projects")

    async def _create_project(self, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", "/api/projects", json=data)

    async def _get_project(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        return await self._manager.api_request("GET", f"/api/projects/{project_id}")

    async def _delete_project(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        return await self._manager.api_request("DELETE", f"/api/projects/{project_id}")

    async def _list_conversations(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        return await self._manager.api_request("GET", f"/api/projects/{project_id}/conversations")

    async def _create_conversation(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request(
            "POST", f"/api/projects/{project_id}/conversations", json=data
        )

    async def _list_project_files(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        return await self._manager.api_request("GET", f"/api/projects/{project_id}/files")

    async def _read_project_file(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        file_path = kwargs.get("file_path", "")
        return await self._manager.api_request("GET", f"/api/projects/{project_id}/files/{file_path}")

    async def _save_artifact(self, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", "/api/artifacts/save", json=data)

    async def _lint_artifact(self, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", "/api/artifacts/lint", json=data)

    async def _list_media_models(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/media/models")

    async def _generate_media(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request(
            "POST", f"/api/projects/{project_id}/media/generate", json=data
        )

    async def _export_html(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        return await self._manager.api_request("GET", f"/api/projects/{project_id}/archive")

    async def _export_pdf(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        return {
            "action": "export_pdf",
            "project_id": project_id,
            "method": "Open the HTML artifact in browser and use window.print() for PDF export",
        }

    async def _export_to_ppt(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        return {
            "action": "export_to_ppt",
            "project_id": project_id,
            "method": "Export design to PPT application for further editing",
            "format": "PPTX",
        }

    async def _export_to_dev(self, **kwargs: Any) -> Any:
        project_id = kwargs.get("project_id", "")
        return {
            "action": "export_to_dev",
            "project_id": project_id,
            "method": "Export design to Dev application for application development",
            "note": "AI will automatically enhance logic, backend, and interactivity",
        }

    async def _health(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/health")

    async def _on_hibernate(self) -> None:
        await self._manager.stop()
