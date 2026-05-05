from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.inference.local_engine import (
    InferenceBackend,
    InferenceConfig,
    local_inference_engine,
)

router = APIRouter()


class InferenceLoadRequest(BaseModel):
    backend: str = "ollama"
    model_path: str = ""
    model_name: str = ""
    n_ctx: int = 4096
    n_gpu_layers: int = -1
    temperature: float = 0.7
    max_tokens: int = 2048
    ollama_host: str = "http://localhost:11434"


class InferenceGenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False


class InferenceConfigUpdate(BaseModel):
    backend: Optional[str] = None
    model_path: Optional[str] = None
    model_name: Optional[str] = None
    n_ctx: Optional[int] = None
    n_gpu_layers: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    ollama_host: Optional[str] = None


@router.get("/status")
async def get_inference_status():
    return {
        "loaded": local_inference_engine.is_loaded,
        "backend": local_inference_engine.backend.value,
        "config": {
            "backend": local_inference_engine._config.backend.value,
            "model_path": local_inference_engine._config.model_path,
            "model_name": local_inference_engine._config.model_name,
            "n_ctx": local_inference_engine._config.n_ctx,
            "n_gpu_layers": local_inference_engine._config.n_gpu_layers,
            "temperature": local_inference_engine._config.temperature,
            "max_tokens": local_inference_engine._config.max_tokens,
            "ollama_host": local_inference_engine._config.ollama_host,
        },
    }


@router.get("/backends")
async def list_backends():
    return {"backends": local_inference_engine.get_available_backends()}


@router.post("/load")
async def load_model(request: InferenceLoadRequest):
    backend_map = {
        "llama_cpp": InferenceBackend.LLAMA_CPP,
        "ollama": InferenceBackend.OLLAMA,
    }
    backend = backend_map.get(request.backend, InferenceBackend.OLLAMA)
    config = InferenceConfig(
        backend=backend,
        model_path=request.model_path,
        model_name=request.model_name,
        n_ctx=request.n_ctx,
        n_gpu_layers=request.n_gpu_layers,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        ollama_host=request.ollama_host,
    )
    success = await local_inference_engine.load_model(config)
    return {
        "success": success,
        "loaded": local_inference_engine.is_loaded,
        "backend": local_inference_engine.backend.value,
    }


@router.post("/unload")
async def unload_model():
    await local_inference_engine.unload()
    return {"success": True, "loaded": False}


@router.post("/generate")
async def generate_text(request: InferenceGenerateRequest):
    if not local_inference_engine.is_loaded:
        return {
            "success": False,
            "error": "Model not loaded. Please load a model first.",
            "text": "",
        }
    kwargs = {}
    if request.model:
        kwargs["model"] = request.model
    if request.temperature is not None:
        kwargs["temperature"] = request.temperature
    if request.max_tokens is not None:
        kwargs["max_tokens"] = request.max_tokens

    result = await local_inference_engine.generate(request.prompt, **kwargs)
    return {
        "success": True,
        "text": result.text,
        "tokens_generated": result.tokens_generated,
        "time_taken": result.time_taken,
        "backend": result.backend,
    }


@router.put("/config")
async def update_inference_config(update: InferenceConfigUpdate):
    config = local_inference_engine._config
    data = update.model_dump(exclude_none=True)
    for key, value in data.items():
        if key == "backend":
            backend_map = {
                "llama_cpp": InferenceBackend.LLAMA_CPP,
                "ollama": InferenceBackend.OLLAMA,
                "none": InferenceBackend.NONE,
            }
            setattr(config, key, backend_map.get(value, InferenceBackend.NONE))
        elif hasattr(config, key):
            setattr(config, key, value)
    return {
        "success": True,
        "config": {
            "backend": config.backend.value,
            "model_path": config.model_path,
            "model_name": config.model_name,
            "n_ctx": config.n_ctx,
            "n_gpu_layers": config.n_gpu_layers,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "ollama_host": config.ollama_host,
        },
    }
