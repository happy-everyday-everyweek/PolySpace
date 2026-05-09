from __future__ import annotations

from typing import Any, Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

from app.core.connector.device_manager import DeviceStatus, device_manager
from app.core.tool.registry import tool_registry

router = APIRouter()


class DeviceRegisterRequest(BaseModel):
    device_id: Optional[str] = None
    device_name: str = ""
    platform: str = "web"
    capabilities: Optional[list[dict]] = None
    metadata: Optional[dict] = None


class DeviceToolCallRequest(BaseModel):
    tool_name: str
    action: str = "execute"
    params: dict[str, Any] = {}
    timeout: float = 60.0


class DeviceBroadcastRequest(BaseModel):
    message: dict[str, Any]
    platform: Optional[str] = None


@router.get("/list")
async def list_devices(platform: Optional[str] = None, status: Optional[str] = None, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    devices = device_manager.list_devices(platform=platform, status=status)
    return {
        "devices": [d.to_dict() for d in devices],
        "total": len(devices),
        "online": sum(1 for d in devices if d.status != DeviceStatus.OFFLINE),
    }


@router.get("/{device_id}")
async def get_device(device_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return device.to_dict()


@router.get("/{device_id}/capabilities")
async def get_device_capabilities(device_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return {
        "device_id": device_id,
        "capabilities": [
            {
                "name": c.name,
                "description": c.description,
                "actions": c.actions,
                "parameters": c.parameters,
            }
            for c in device.capabilities
        ],
    }


@router.post("/{device_id}/execute")
async def execute_on_device(device_id: str, request: DeviceToolCallRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    if device.status == DeviceStatus.OFFLINE:
        raise HTTPException(status_code=400, detail=f"Device is offline: {device_id}")

    result = await device_manager.execute_on_device(
        device_id=device_id,
        tool_name=request.tool_name,
        action=request.action,
        params=request.params,
        timeout=request.timeout,
    )
    return result


@router.post("/broadcast")
async def broadcast_to_devices(request: DeviceBroadcastRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    results = await device_manager.broadcast_to_devices(
        message=request.message,
        platform=request.platform,
    )
    return {"results": results, "reached": sum(1 for v in results.values() if v)}


@router.delete("/{device_id}")
async def disconnect_device(device_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    removed_tools = await tool_registry.unregister_device_tools(device_id)
    await device_manager.disconnect_device(device_id)
    return {"status": "ok", "removed_tools": removed_tools}


@router.websocket("/ws/{device_id}")
async def device_websocket(websocket: WebSocket, device_id: str):
    try:
        await websocket.accept()

        init_data = await websocket.receive_json()
        device_name = init_data.get("device_name", "")
        platform = init_data.get("platform", "web")
        capabilities = init_data.get("capabilities")
        metadata = init_data.get("metadata")

        device = await device_manager.register_device(
            websocket=websocket,
            device_id=device_id,
            device_name=device_name,
            platform=platform,
            capabilities=capabilities,
            metadata=metadata,
            skip_accept=True,
        )

        registered_tools = await tool_registry.register_device_tools(device)

        await websocket.send_json({
            "type": "register_ack",
            "device_id": device_id,
            "accepted": True,
            "registered_tools": registered_tools,
        })

        while True:
            data = await websocket.receive_json()
            await device_manager.handle_message(device_id, data)

    except WebSocketDisconnect:
        await tool_registry.unregister_device_tools(device_id)
        await device_manager.disconnect_device(device_id)
    except Exception:
        await tool_registry.unregister_device_tools(device_id)
        await device_manager.disconnect_device(device_id)


@router.websocket("/status/ws")
async def device_status_websocket(websocket: WebSocket):
    await websocket.accept()

    devices = device_manager.list_devices()
    await websocket.send_json({
        "type": "initial",
        "devices": [d.to_dict() for d in devices],
        "total": len(devices),
        "online": sum(1 for d in devices if d.status != DeviceStatus.OFFLINE),
    })

    device_manager.subscribe_status(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        device_manager.unsubscribe_status(websocket)
