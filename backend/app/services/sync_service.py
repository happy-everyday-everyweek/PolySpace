from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

SYNC_SCOPES = ["settings", "persona", "mode", "workspace", "memory", "todo"]

CONFLICT_STRATEGIES = ["latest", "local", "remote", "merge"]


@dataclass
class SyncDevice:
    device_id: str
    device_name: str = ""
    platform: str = ""
    last_sync: str = ""
    branch: str = "main"
    sync_scopes: list[str] = field(default_factory=lambda: list(SYNC_SCOPES))

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "platform": self.platform,
            "last_sync": self.last_sync,
            "branch": self.branch,
            "sync_scopes": self.sync_scopes,
        }


@dataclass
class SyncChange:
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str = ""
    change_type: str = ""
    path: str = ""
    content_hash: str = ""
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_content: bool = False) -> dict:
        d = {
            "change_id": self.change_id,
            "device_id": self.device_id,
            "type": self.change_type,
            "path": self.path,
            "content_hash": self.content_hash,
            "timestamp": self.timestamp,
        }
        if include_content:
            d["content"] = self.content
            d["metadata"] = self.metadata
        return d


@dataclass
class SyncConflict:
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    path: str = ""
    local_change: SyncChange | None = None
    remote_change: SyncChange | None = None
    auto_resolvable: bool = False
    resolved: bool = False

    def to_dict(self) -> dict:
        return {
            "conflict_id": self.conflict_id,
            "path": self.path,
            "local_hash": self.local_change.content_hash if self.local_change else None,
            "remote_hash": self.remote_change.content_hash if self.remote_change else None,
            "auto_resolvable": self.auto_resolvable,
            "resolved": self.resolved,
        }


class SyncService:
    def __init__(self, data_dir: str | None = None) -> None:
        if data_dir is None:
            data_dir = os.path.join(os.getcwd(), "data", "sync")
        self._data_dir = data_dir
        self._devices: dict[str, SyncDevice] = {}
        self._changes: dict[str, list[SyncChange]] = {}
        self._branches: dict[str, str] = {"main": "main"}
        self._conflict_strategy: str = "latest"
        self._auto_sync_task: Optional[asyncio.Task] = None
        self._auto_sync_interval: int = 300
        self._auto_sync_running: bool = False
        os.makedirs(data_dir, exist_ok=True)
        self._load_state()

    def _state_file(self) -> str:
        return os.path.join(self._data_dir, "sync_state.json")

    def _load_state(self) -> None:
        state_file = self._state_file()
        if not os.path.exists(state_file):
            return
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            for did, ddata in state.get("devices", {}).items():
                self._devices[did] = SyncDevice(
                    device_id=ddata["device_id"],
                    device_name=ddata.get("device_name", ""),
                    platform=ddata.get("platform", ""),
                    last_sync=ddata.get("last_sync", ""),
                    branch=ddata.get("branch", f"device/{did[:8]}"),
                    sync_scopes=ddata.get("sync_scopes", list(SYNC_SCOPES)),
                )
                self._branches[self._devices[did].branch] = did
            for did, clist in state.get("changes", {}).items():
                self._changes[did] = []
                for cdata in clist:
                    self._changes[did].append(SyncChange(
                        change_id=cdata.get("change_id", str(uuid.uuid4())),
                        device_id=cdata.get("device_id", did),
                        change_type=cdata.get("type", "update"),
                        path=cdata.get("path", ""),
                        content_hash=cdata.get("content_hash", ""),
                        content=cdata.get("content", ""),
                        timestamp=cdata.get("timestamp", ""),
                        metadata=cdata.get("metadata", {}),
                    ))
            self._conflict_strategy = state.get("conflict_strategy", "latest")
            total_changes = sum(len(v) for v in self._changes.values())
            logger.info(
                f"Sync state loaded: {len(self._devices)} devices, {total_changes} changes"
            )
        except Exception as e:
            logger.error(f"Failed to load sync state: {e}")

    def _save_state(self) -> None:
        state_file = self._state_file()
        try:
            state = {
                "devices": {did: d.to_dict() for did, d in self._devices.items()},
                "changes": {
                    did: [c.to_dict(include_content=True) for c in clist]
                    for did, clist in self._changes.items()
                },
                "conflict_strategy": self._conflict_strategy,
            }
            tmp = state_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            os.replace(tmp, state_file)
        except Exception as e:
            logger.error(f"Failed to save sync state: {e}")

    def set_conflict_strategy(self, strategy: str) -> None:
        if strategy in CONFLICT_STRATEGIES:
            self._conflict_strategy = strategy
            self._save_state()

    def get_conflict_strategy(self) -> str:
        return self._conflict_strategy

    async def register_device(
        self,
        device_id: str,
        device_name: str = "",
        platform: str = "",
        sync_scopes: list[str] | None = None,
    ) -> SyncDevice:
        if device_id in self._devices:
            device = self._devices[device_id]
            if device_name:
                device.device_name = device_name
            if platform:
                device.platform = platform
            if sync_scopes is not None:
                device.sync_scopes = [s for s in sync_scopes if s in SYNC_SCOPES]
            self._save_state()
            return device
        device = SyncDevice(
            device_id=device_id,
            device_name=device_name,
            platform=platform,
            branch=f"device/{device_id[:8]}",
            sync_scopes=sync_scopes if sync_scopes else list(SYNC_SCOPES),
        )
        self._devices[device_id] = device
        self._branches[device.branch] = device_id
        self._save_state()
        return device

    async def push_changes(self, device_id: str, changes: list[dict[str, Any]]) -> dict[str, Any]:
        device = self._devices.get(device_id)
        if not device:
            return {"error": f"Device not registered: {device_id}"}

        sync_changes = []
        for change_data in changes:
            path = change_data.get("path", "")
            if path and path not in device.sync_scopes:
                continue
            content = change_data.get("content", "")
            content_hash = hashlib.sha256(content.encode()).hexdigest() if content else ""
            change = SyncChange(
                device_id=device_id,
                change_type=change_data.get("type", "update"),
                path=path,
                content_hash=content_hash,
                content=content,
                metadata=change_data.get("metadata", {}),
            )
            sync_changes.append(change)

        if device_id not in self._changes:
            self._changes[device_id] = []
        self._changes[device_id].extend(sync_changes)

        max_per_device = 500
        if len(self._changes[device_id]) > max_per_device:
            self._changes[device_id] = self._changes[device_id][-max_per_device:]

        device.last_sync = datetime.now().isoformat()
        self._save_state()

        return {
            "pushed": len(sync_changes),
            "device_id": device_id,
            "branch": device.branch,
        }

    async def pull_changes(
        self,
        device_id: str,
        since: str | None = None,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        device = self._devices.get(device_id)
        if not device:
            return {"error": f"Device not registered: {device_id}"}

        effective_scopes = scopes if scopes else device.sync_scopes

        all_changes = []
        for did, changes in self._changes.items():
            if did == device_id:
                continue
            for change in changes:
                if since and change.timestamp <= since:
                    continue
                if change.path and change.path not in effective_scopes:
                    continue
                all_changes.append(change)

        all_changes.sort(key=lambda c: c.timestamp)

        return {
            "changes": [c.to_dict(include_content=True) for c in all_changes],
            "count": len(all_changes),
        }

    async def get_status(self, device_id: str) -> dict[str, Any]:
        device = self._devices.get(device_id)
        if not device:
            return {"error": f"Device not registered: {device_id}"}

        device_changes = self._changes.get(device_id, [])
        other_pending = 0
        for did, changes in self._changes.items():
            if did == device_id:
                continue
            for c in changes:
                if c.path in device.sync_scopes:
                    other_pending += 1

        return {
            "device_id": device_id,
            "device_name": device.device_name,
            "branch": device.branch,
            "last_sync": device.last_sync,
            "local_changes": len(device_changes),
            "remote_pending": other_pending,
            "registered_devices": len(self._devices),
            "sync_scopes": device.sync_scopes,
            "conflict_strategy": self._conflict_strategy,
        }

    async def detect_conflicts(self, device_id: str) -> list[SyncConflict]:
        device_changes = self._changes.get(device_id, [])
        if not device_changes:
            return []

        path_to_changes: dict[str, list[tuple[str, SyncChange]]] = {}
        for other_id, other_changes in self._changes.items():
            if other_id == device_id:
                continue
            for change in other_changes:
                if change.path not in path_to_changes:
                    path_to_changes[change.path] = []
                path_to_changes[change.path].append((other_id, change))

        conflicts = []
        for change in device_changes:
            other_entries = path_to_changes.get(change.path)
            if not other_entries:
                continue
            for other_id, other_change in other_entries:
                if change.content_hash != other_change.content_hash:
                    auto_resolvable = self._conflict_strategy in ("latest",)
                    conflict = SyncConflict(
                        path=change.path,
                        local_change=change,
                        remote_change=other_change,
                        auto_resolvable=auto_resolvable,
                    )
                    conflicts.append(conflict)

        return conflicts

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str = "local",
        content: str | None = None,
    ) -> dict[str, Any]:
        if resolution == "latest" and content:
            return {
                "conflict_id": conflict_id,
                "resolution": resolution,
                "resolved": True,
                "merged_content": content,
            }
        return {
            "conflict_id": conflict_id,
            "resolution": resolution,
            "resolved": True,
        }

    async def auto_sync_all(self) -> dict[str, Any]:
        results = {}
        for device_id, device in self._devices.items():
            try:
                conflicts = await self.detect_conflicts(device_id)
                auto_resolved = 0
                for c in conflicts:
                    if c.auto_resolvable:
                        await self.resolve_conflict(c.conflict_id, self._conflict_strategy)
                        auto_resolved += 1
                results[device_id] = {
                    "conflicts_detected": len(conflicts),
                    "auto_resolved": auto_resolved,
                    "status": "ok",
                }
            except Exception as e:
                results[device_id] = {"status": "error", "error": str(e)}
        self._save_state()
        return results

    async def start_auto_sync(self, interval_sec: int = 300) -> None:
        if self._auto_sync_running:
            return
        self._auto_sync_interval = interval_sec
        self._auto_sync_running = True
        self._auto_sync_task = asyncio.create_task(self._auto_sync_loop())
        logger.info(f"Auto-sync started with interval {interval_sec}s")

    async def stop_auto_sync(self) -> None:
        self._auto_sync_running = False
        if self._auto_sync_task:
            self._auto_sync_task.cancel()
            try:
                await self._auto_sync_task
            except asyncio.CancelledError:
                pass
            self._auto_sync_task = None
        logger.info("Auto-sync stopped")

    async def _auto_sync_loop(self) -> None:
        while self._auto_sync_running:
            try:
                await self.auto_sync_all()
            except Exception as e:
                logger.error(f"Auto-sync loop error: {e}")
            await asyncio.sleep(self._auto_sync_interval)

    async def trigger_handoff_sync(self, source_device_id: str, target_device_id: str) -> dict[str, Any]:
        source = self._devices.get(source_device_id)
        target = self._devices.get(target_device_id)
        if not source or not target:
            return {"error": "Device not found"}

        source_changes = self._changes.get(source_device_id, [])
        relevant = [c for c in source_changes if c.path in target.sync_scopes]

        return {
            "source_device": source_device_id,
            "target_device": target_device_id,
            "changes_available": len(relevant),
            "status": "ok",
        }

    async def get_all_devices_status(self) -> list[dict]:
        return [d.to_dict() for d in self._devices.values()]

    async def update_device_scopes(self, device_id: str, scopes: list[str]) -> dict[str, Any]:
        device = self._devices.get(device_id)
        if not device:
            return {"error": f"Device not registered: {device_id}"}
        device.sync_scopes = [s for s in scopes if s in SYNC_SCOPES]
        self._save_state()
        return {"status": "ok", "device_id": device_id, "sync_scopes": device.sync_scopes}

    @staticmethod
    def _aes_encrypt(data: bytes, key: bytes) -> bytes:
        try:
            import base64

            from cryptography.fernet import Fernet
            hashed_key = hashlib.sha256(key).digest()
            fernet_key = base64.urlsafe_b64encode(hashed_key)
            return Fernet(fernet_key).encrypt(data)
        except ImportError:
            import base64
            return base64.b64encode(data)

    @staticmethod
    def _aes_decrypt(data: bytes, key: bytes) -> bytes:
        try:
            import base64

            from cryptography.fernet import Fernet
            hashed_key = hashlib.sha256(key).digest()
            fernet_key = base64.urlsafe_b64encode(hashed_key)
            return Fernet(fernet_key).decrypt(data)
        except ImportError:
            import base64
            return base64.b64decode(data)

    async def encrypt_and_sync_to_github(
        self,
        device_id: str,
        repo: str,
        token: str,
        encryption_key: str = "",
    ) -> dict[str, Any]:
        device = self._devices.get(device_id)
        if not device:
            return {"error": f"Device not registered: {device_id}"}

        try:
            import httpx
            changes = self._changes.get(device_id, [])
            if not changes:
                return {"status": "no_changes", "message": "No changes to sync"}

            payload = json.dumps([
                {"path": c.path, "content": c.content, "hash": c.content_hash}
                for c in changes
            ], ensure_ascii=False)

            raw_bytes = payload.encode("utf-8")
            if encryption_key:
                encrypted = self._aes_encrypt(raw_bytes, encryption_key.encode())
                encoded_payload = encrypted.decode()
            else:
                import base64
                encoded_payload = base64.b64encode(raw_bytes).decode()

            github_file_size_limit = 50 * 1024 * 1024
            chunks = []
            current_chunk = ""
            for line in encoded_payload.split("\n"):
                if len(current_chunk.encode()) + len(line.encode()) > github_file_size_limit:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += "\n" + line if current_chunk else line
            if current_chunk:
                chunks.append(current_chunk)

            results = []
            async with httpx.AsyncClient() as client:
                for i, chunk in enumerate(chunks):
                    filename = f"sync/{device_id[:8]}_{i}.enc" if len(chunks) > 1 else f"sync/{device_id[:8]}.enc"
                    response = await client.put(
                        f"https://api.github.com/repos/{repo}/contents/{filename}",
                        headers={
                            "Authorization": f"token {token}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "message": f"PolySpace sync from {device.device_name} (chunk {i+1}/{len(chunks)})",
                            "content": chunk,
                        },
                        timeout=30.0,
                    )
                    if response.status_code in (200, 201):
                        results.append({"file": filename, "sha": response.json().get("content", {}).get("sha", "")})
                    else:
                        return {"error": f"GitHub API error: {response.status_code}"}

            device.last_sync = datetime.now().isoformat()
            self._save_state()
            return {"status": "ok", "files": results, "chunks": len(chunks)}

        except ImportError:
            return {"error": "httpx not installed"}
        except Exception as e:
            return {"error": str(e)}


sync_service = SyncService()
