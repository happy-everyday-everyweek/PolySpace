from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.llm.dispatcher import TaskCategory, get_model_dispatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/llm", tags=["llm-proxy"])


class LLMProxyRequest(BaseModel):
    provider: str = "openai"
    model: Optional[str] = None
    messages: list[dict]
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    task_category: str = TaskCategory.DAILY


@router.post("/proxy/stream")
async def llm_proxy_stream(req: LLMProxyRequest):
    dispatcher = get_model_dispatcher()

    messages = list(req.messages)
    if req.system_prompt and (not messages or messages[0].get("role") != "system"):
        messages.insert(0, {"role": "system", "content": req.system_prompt})

    kwargs: dict = {}
    if req.max_tokens:
        kwargs["max_tokens"] = req.max_tokens
    if req.temperature is not None:
        kwargs["temperature"] = req.temperature

    async def generate():
        try:
            async for chunk in dispatcher.dispatch_stream(
                task_category=req.task_category,
                messages=messages,
                **kwargs,
            ):
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    data = {}
                    if hasattr(delta, "content") and delta.content:
                        data["delta"] = delta.content
                    if hasattr(delta, "tool_calls") and delta.tool_calls:
                        data["tool_calls"] = [
                            {
                                "id": tc.id if hasattr(tc, "id") else None,
                                "type": "function",
                                "function": {
                                    "name": (
                                        tc.function.name
                                        if hasattr(tc, "function") and hasattr(tc.function, "name")
                                        else None
                                    ),
                                    "arguments": (
                                        tc.function.arguments
                                        if hasattr(tc, "function") and hasattr(tc.function, "arguments")
                                        else None
                                    ),
                                },
                            }
                            for tc in delta.tool_calls
                        ]
                    if data:
                        yield f"data: {json.dumps(data)}\n\n"
                elif isinstance(chunk, dict):
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif isinstance(chunk, str):
                    yield f"data: {json.dumps({'delta': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("LLM proxy stream error: %s", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/proxy/anthropic/stream")
async def llm_proxy_anthropic_stream(req: LLMProxyRequest):
    req.provider = "anthropic"
    req.task_category = req.task_category or TaskCategory.PLANNING
    return await llm_proxy_stream(req)


@router.post("/proxy/openai/stream")
async def llm_proxy_openai_stream(req: LLMProxyRequest):
    req.provider = "openai"
    return await llm_proxy_stream(req)


@router.post("/proxy/azure/stream")
async def llm_proxy_azure_stream(req: LLMProxyRequest):
    req.provider = "azure"
    return await llm_proxy_stream(req)


@router.post("/proxy/google/stream")
async def llm_proxy_google_stream(req: LLMProxyRequest):
    req.provider = "google"
    req.task_category = req.task_category or TaskCategory.MULTIMODAL
    return await llm_proxy_stream(req)
