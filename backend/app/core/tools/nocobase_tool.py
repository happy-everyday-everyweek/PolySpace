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

NOCOBASE_DIR = os.environ.get(
    "NOCOBASE_DIR",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "nocobase")
    ),
)
if not os.path.isdir(NOCOBASE_DIR):
    mobile_path = "/home/polyspace/nocobase"
    if os.path.isdir(mobile_path):
        NOCOBASE_DIR = mobile_path
NOCOBASE_DEFAULT_PORT = 13000
NOCOBASE_DEFAULT_HOST = "127.0.0.1"


class ProcessStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


class NocoBaseProcessManager:
    _instance: NocoBaseProcessManager | None = None

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._status = ProcessStatus.STOPPED
        self._port = NOCOBASE_DEFAULT_PORT
        self._host = NOCOBASE_DEFAULT_HOST
        self._base_url = f"http://{self._host}:{self._port}"
        self._api_token: str = ""
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def get_instance(cls) -> NocoBaseProcessManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def status(self) -> ProcessStatus:
        return self._status

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def api_token(self) -> str:
        return self._api_token

    def is_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None

    async def start(self, port: int | None = None) -> dict[str, Any]:
        if self.is_running():
            return {"status": "already_running", "base_url": self._base_url}

        if not os.path.isdir(NOCOBASE_DIR):
            return {
                "status": "not_available",
                "base_url": self._base_url,
                "message": f"NocoBase directory not found: {NOCOBASE_DIR}. "
                "Please clone nocobase to the project root directory.",
            }

        if port is not None:
            self._port = port
            self._base_url = f"http://{self._host}:{self._port}"

        self._status = ProcessStatus.STARTING

        env = os.environ.copy()
        env["PORT"] = str(self._port)
        env["HOST"] = self._host
        env["NODE_ENV"] = "production"
        env["DB_DIALECT"] = "sqlite"
        env["DB_STORAGE"] = os.path.join(NOCOBASE_DIR, "storage", "db.sqlite")

        storage_dir = os.path.join(NOCOBASE_DIR, "storage")
        os.makedirs(storage_dir, exist_ok=True)

        npx_path = shutil.which("npx")
        if not npx_path:
            node_path = shutil.which("node")
            if not node_path:
                self._status = ProcessStatus.ERROR
                return {"error": "Node.js not found in PATH"}
            npx_path = node_path

        try:
            if sys.platform == "win32":
                self._process = subprocess.Popen(
                    [npx_path, "nocobase", "start"],
                    cwd=NOCOBASE_DIR,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                self._process = subprocess.Popen(
                    [npx_path, "nocobase", "start"],
                    cwd=NOCOBASE_DIR,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid,
                )
        except Exception as e:
            self._status = ProcessStatus.ERROR
            return {"error": f"Failed to start NocoBase: {str(e)}"}

        for _ in range(60):
            await asyncio.sleep(2)
            if not self.is_running():
                self._status = ProcessStatus.ERROR
                stderr_out = ""
                if self._process and self._process.stderr:
                    try:
                        stderr_out = self._process.stderr.read(2048).decode(errors="replace")
                    except Exception:
                        pass
                return {"error": "NocoBase exited prematurely", "stderr": stderr_out}

            if await self._health_check():
                self._status = ProcessStatus.RUNNING
                self._ensure_client()
                logger.info("NocoBase started on %s", self._base_url)
                return {"status": "running", "base_url": self._base_url}

        self._status = ProcessStatus.ERROR
        return {"error": "NocoBase health check timed out after 120s"}

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
                self._process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        except Exception as e:
            logger.warning("Error stopping NocoBase: %s", e)

        self._process = None
        self._status = ProcessStatus.STOPPED

        if self._client:
            await self._client.aclose()
            self._client = None

        return {"status": "stopped"}

    async def _health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/app")
                return resp.status_code == 200
        except Exception:
            return False

    def _ensure_client(self) -> None:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self._api_token:
                headers["Authorization"] = f"Bearer {self._api_token}"
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=30.0,
            )

    async def api_request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self._client:
            self._ensure_client()
        if self._client is None:
            return {"error": "NocoBase client not available"}
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
            "nocobase_dir": NOCOBASE_DIR,
            "dir_exists": os.path.isdir(NOCOBASE_DIR),
        }


class NocoBaseTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="nocobase",
            description=(
                "NocoBase tool - low-code platform for building applications. "
                "Manages NocoBase as a subprocess and provides full API access "
                "for collections, fields, records, roles, workflows, and plugins."
            ),
        )
        self._manager = NocoBaseProcessManager.get_instance()

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
                if start_result.get("status") not in ("running", "already_running", "not_available"):
                    return {"error": "NocoBase is not running", "start_result": start_result}
                if start_result.get("status") == "not_available":
                    return {"error": start_result.get("message", "NocoBase not available")}

        handlers = {
            "list_collections": self._list_collections,
            "create_collection": self._create_collection,
            "get_collection": self._get_collection,
            "update_collection": self._update_collection,
            "delete_collection": self._delete_collection,
            "list_fields": self._list_fields,
            "create_field": self._create_field,
            "update_field": self._update_field,
            "delete_field": self._delete_field,
            "list_records": self._list_records,
            "create_record": self._create_record,
            "get_record": self._get_record,
            "update_record": self._update_record,
            "delete_record": self._delete_record,
            "list_views": self._list_views,
            "create_view": self._create_view,
            "list_roles": self._list_roles,
            "create_role": self._create_role,
            "list_workflows": self._list_workflows,
            "create_workflow": self._create_workflow,
            "execute_workflow": self._execute_workflow,
            "list_pages": self._list_pages,
            "create_page": self._create_page,
            "list_menus": self._list_menus,
            "list_plugins": self._list_plugins,
            "install_plugin": self._install_plugin,
            "app_info": self._app_info,
            "health": self._health,
        }

        handler = handlers.get(action)
        if handler:
            return await handler(**kwargs)
        return {"error": f"Unknown action: {action}. Available: {', '.join(handlers.keys())}"}

    async def _list_collections(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/collections", params=kwargs.get("params", {}))

    async def _create_collection(self, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", "/api/collections", json=data)

    async def _get_collection(self, **kwargs: Any) -> Any:
        name = kwargs.get("name", "")
        return await self._manager.api_request("GET", f"/api/collections/{name}")

    async def _update_collection(self, **kwargs: Any) -> Any:
        name = kwargs.get("name", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request("PUT", f"/api/collections/{name}", json=data)

    async def _delete_collection(self, **kwargs: Any) -> Any:
        name = kwargs.get("name", "")
        return await self._manager.api_request("DELETE", f"/api/collections/{name}")

    async def _list_fields(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        return await self._manager.api_request("GET", f"/api/collections/{collection}/fields")

    async def _create_field(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", f"/api/collections/{collection}/fields", json=data)

    async def _update_field(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        field_name = kwargs.get("field_name", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request("PUT", f"/api/collections/{collection}/fields/{field_name}", json=data)

    async def _delete_field(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        field_name = kwargs.get("field_name", "")
        return await self._manager.api_request("DELETE", f"/api/collections/{collection}/fields/{field_name}")

    async def _list_records(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        params = kwargs.get("params", {})
        return await self._manager.api_request("GET", f"/api/collections/{collection}/records", params=params)

    async def _create_record(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", f"/api/collections/{collection}/records", json=data)

    async def _get_record(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        record_id = kwargs.get("record_id", "")
        return await self._manager.api_request("GET", f"/api/collections/{collection}/records/{record_id}")

    async def _update_record(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        record_id = kwargs.get("record_id", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request("PUT", f"/api/collections/{collection}/records/{record_id}", json=data)

    async def _delete_record(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        record_id = kwargs.get("record_id", "")
        return await self._manager.api_request("DELETE", f"/api/collections/{collection}/records/{record_id}")

    async def _list_views(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        return await self._manager.api_request("GET", f"/api/collections/{collection}/views")

    async def _create_view(self, **kwargs: Any) -> Any:
        collection = kwargs.get("collection", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", f"/api/collections/{collection}/views", json=data)

    async def _list_roles(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/roles")

    async def _create_role(self, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", "/api/roles", json=data)

    async def _list_workflows(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/workflows")

    async def _create_workflow(self, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", "/api/workflows", json=data)

    async def _execute_workflow(self, **kwargs: Any) -> Any:
        workflow_id = kwargs.get("workflow_id", "")
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", f"/api/workflows/{workflow_id}/execution", json=data)

    async def _list_pages(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/pages")

    async def _create_page(self, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", "/api/pages", json=data)

    async def _list_menus(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/menus")

    async def _list_plugins(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/plugins")

    async def _install_plugin(self, **kwargs: Any) -> Any:
        data = kwargs.get("data", {})
        return await self._manager.api_request("POST", "/api/plugins:install", json=data)

    async def _app_info(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/app")

    async def _health(self, **kwargs: Any) -> Any:
        return await self._manager.api_request("GET", "/api/app")

    async def _on_hibernate(self) -> None:
        await self._manager.stop()
