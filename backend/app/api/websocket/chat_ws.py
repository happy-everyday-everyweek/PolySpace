import asyncio
import json
import logging
import time
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.core.connector.device_manager import device_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._last_heartbeat: dict[str, float] = {}
        self._lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def connect(self, client_id: str, websocket: WebSocket) -> bool:
        async with self._lock:
            if len(self._connections) >= settings.WS_MAX_CONNECTIONS:
                logger.warning(
                    "WebSocket connection rejected - max connections reached (%d)",
                    settings.WS_MAX_CONNECTIONS,
                )
                await websocket.close(code=1013, reason="Max connections reached")
                return False

            if client_id in self._connections:
                old_ws = self._connections[client_id]
                try:
                    await old_ws.close(code=1000, reason="Replaced by new connection")
                except Exception:
                    pass

            await websocket.accept()
            self._connections[client_id] = websocket
            self._last_heartbeat[client_id] = time.monotonic()
            logger.info(
                "WebSocket connected: %s (total: %d)",
                client_id,
                len(self._connections),
            )
            return True

    def disconnect(self, client_id: str) -> None:
        self._connections.pop(client_id, None)
        self._last_heartbeat.pop(client_id, None)
        logger.info(
            "WebSocket disconnected: %s (total: %d)",
            client_id,
            len(self._connections),
        )

    def update_heartbeat(self, client_id: str) -> None:
        self._last_heartbeat[client_id] = time.monotonic()

    def is_heartbeat_expired(self, client_id: str) -> bool:
        last = self._last_heartbeat.get(client_id, 0)
        return (time.monotonic() - last) > settings.WS_HEARTBEAT_TIMEOUT

    async def send_message(self, client_id: str, message: dict) -> bool:
        ws = self._connections.get(client_id)
        if not ws:
            return False
        try:
            await ws.send_json(message)
            return True
        except Exception:
            logger.warning("Failed to send message to %s, disconnecting", client_id)
            self.disconnect(client_id)
            return False

    async def broadcast(self, message: dict) -> None:
        disconnected = []
        for client_id, ws in self._connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)

    def get_connection(self, client_id: str) -> Optional[WebSocket]:
        return self._connections.get(client_id)


manager = ConnectionManager()


async def _heartbeat_checker() -> None:
    while True:
        await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
        expired = [
            cid for cid in list(manager._last_heartbeat.keys())
            if manager.is_heartbeat_expired(cid)
        ]
        for cid in expired:
            ws = manager._connections.get(cid)
            if ws:
                try:
                    await ws.close(code=1000, reason="Heartbeat timeout")
                except Exception:
                    pass
            manager.disconnect(cid)
            logger.info("WebSocket heartbeat timeout: %s", cid)


_heartbeat_task: Optional[asyncio.Task] = None


def start_heartbeat_monitor() -> None:
    global _heartbeat_task
    if _heartbeat_task is None or _heartbeat_task.done():
        _heartbeat_task = asyncio.create_task(_heartbeat_checker())
        logger.info("WebSocket heartbeat monitor started")


def stop_heartbeat_monitor() -> None:
    global _heartbeat_task
    if _heartbeat_task and not _heartbeat_task.done():
        _heartbeat_task.cancel()
        _heartbeat_task = None
        logger.info("WebSocket heartbeat monitor stopped")


async def _handle_websocket(websocket: WebSocket, client_id: str):
    connected = await manager.connect(client_id, websocket)
    if not connected:
        return

    try:
        while True:
            raw = await websocket.receive_text()

            if len(raw.encode("utf-8")) > settings.WS_MAX_MESSAGE_SIZE:
                await manager.send_message(client_id, {
                    "type": "error",
                    "data": {"message": "Message too large"},
                })
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                })
                continue

            message_type = data.get("type", "message")

            if message_type == "ping":
                manager.update_heartbeat(client_id)
                await manager.send_message(client_id, {
                    "type": "pong",
                    "data": {},
                })
                continue

            if message_type == "message":
                content = data.get("content", "")
                await manager.send_message(client_id, {
                    "type": "thinking",
                    "data": {"content": "Processing..."},
                })
                await manager.send_message(client_id, {
                    "type": "content",
                    "data": {"content": f"Echo: {content}"},
                })
                await manager.send_message(client_id, {
                    "type": "done",
                    "data": {},
                })

            elif message_type == "device_command":
                device_id = data.get("device_id", "")
                tool_name = data.get("tool_name", "")
                action = data.get("action", "")
                params = data.get("params", {})

                if not device_id or not tool_name:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "data": {"message": "Missing device_id or tool_name"},
                    })
                    continue

                try:
                    result = await device_manager.execute_on_device(
                        device_id=device_id,
                        tool_name=tool_name,
                        action=action,
                        params=params,
                    )
                    await manager.send_message(client_id, {
                        "type": "device_command_result",
                        "data": {
                            "device_id": device_id,
                            "tool_name": tool_name,
                            "action": action,
                            "result": result,
                        },
                    })
                except Exception as e:
                    logger.error("Device command failed for %s: %s", device_id, e)
                    await manager.send_message(client_id, {
                        "type": "error",
                        "data": {"message": f"Device command failed: {str(e)}"},
                    })

            elif message_type == "device_list":
                devices = device_manager.list_devices()
                await manager.send_message(client_id, {
                    "type": "device_list",
                    "data": {
                        "devices": [d.to_dict() for d in devices],
                        "total": len(devices),
                        "online": sum(1 for d in devices if d.status.value != "offline"),
                    },
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        logger.exception("WebSocket error for client %s", client_id)
        manager.disconnect(client_id)


@router.websocket("")
async def root_websocket(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await _handle_websocket(websocket, client_id)


@router.websocket("/unified")
async def unified_websocket(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await _handle_websocket(websocket, client_id)


@router.websocket("/chat/{client_id}")
async def chat_websocket(websocket: WebSocket, client_id: str):
    await _handle_websocket(websocket, client_id)
