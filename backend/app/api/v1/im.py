from typing import Any, Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.coordination.channels.im_channel import IMChannelType, get_im_channel

router = APIRouter()


class ChannelConfigRequest(BaseModel):
    channel_type: IMChannelType
    config: dict[str, Any]
    enabled: bool = True


class SendMessageRequest(BaseModel):
    channel_type: IMChannelType
    chat_id: str
    content: str


class ReceiveMessageRequest(BaseModel):
    channel_type: IMChannelType
    raw_data: dict[str, Any]


@router.get("/channels")
async def list_im_channels(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    im = get_im_channel()
    return {"channels": im.list_channels()}


@router.get("/channels/{channel_type}")
async def get_im_channel_config(channel_type: IMChannelType, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    im = get_im_channel()
    config = im.get_config(channel_type)
    return {"channel_type": config.channel_type.value, "enabled": config.enabled, "config": config.config}


@router.post("/channels/configure")
async def configure_channel(req: ChannelConfigRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    im = get_im_channel()
    config = im.configure(req.channel_type, req.config, req.enabled)
    return {"channel_type": config.channel_type.value, "enabled": config.enabled}


@router.post("/send")
async def send_im_message(req: SendMessageRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    im = get_im_channel()
    msg = await im.send(req.channel_type, req.chat_id, req.content)
    if not msg:
        raise HTTPException(status_code=400, detail="Channel not enabled or rate limited")
    return msg.to_dict()


@router.post("/receive")
async def receive_im_message(req: ReceiveMessageRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    im = get_im_channel()
    msg = await im.receive(req.channel_type, req.raw_data)
    return msg.to_dict()


@router.get("/messages")
async def list_im_messages(channel_type: Optional[IMChannelType] = None, limit: int = 50, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    im = get_im_channel()
    return {"messages": im.get_messages(channel_type=channel_type, limit=limit)}
