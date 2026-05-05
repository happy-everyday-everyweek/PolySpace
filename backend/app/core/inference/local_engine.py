from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator


class InferenceBackend(str, Enum):
    LLAMA_CPP = "llama_cpp"
    OLLAMA = "ollama"
    NONE = "none"


@dataclass
class InferenceConfig:
    backend: InferenceBackend = InferenceBackend.NONE
    model_path: str = ""
    model_name: str = ""
    n_ctx: int = 4096
    n_gpu_layers: int = -1
    temperature: float = 0.7
    max_tokens: int = 2048
    ollama_host: str = "http://localhost:11434"


@dataclass
class InferenceResult:
    text: str
    tokens_generated: int = 0
    time_taken: float = 0.0
    backend: str = ""


class LocalInferenceEngine:
    def __init__(self, config: InferenceConfig | None = None) -> None:
        self._config = config or InferenceConfig()
        self._backend_instance: Any = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def backend(self) -> InferenceBackend:
        return self._config.backend

    async def load_model(self, config: InferenceConfig | None = None) -> bool:
        if config:
            self._config = config

        if self._config.backend == InferenceBackend.LLAMA_CPP:
            return await self._load_llama_cpp()
        elif self._config.backend == InferenceBackend.OLLAMA:
            return await self._load_ollama()
        else:
            return False

    async def _load_llama_cpp(self) -> bool:
        try:
            from llama_cpp import Llama
            self._backend_instance = Llama(
                model_path=self._config.model_path,
                n_ctx=self._config.n_ctx,
                n_gpu_layers=self._config.n_gpu_layers,
            )
            self._loaded = True
            return True
        except ImportError:
            return False
        except Exception:
            return False

    async def _load_ollama(self) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._config.ollama_host}/api/tags",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    self._loaded = True
                    return True
            return False
        except Exception:
            return False

    async def generate(self, prompt: str, **kwargs: Any) -> InferenceResult:
        if not self._loaded:
            return InferenceResult(text="[Local inference not loaded]", backend="none")

        import time
        start = time.time()

        if self._config.backend == InferenceBackend.LLAMA_CPP:
            result = await self._generate_llama_cpp(prompt, **kwargs)
        elif self._config.backend == InferenceBackend.OLLAMA:
            result = await self._generate_ollama(prompt, **kwargs)
        else:
            result = InferenceResult(text="[No backend configured]", backend="none")

        result.time_taken = time.time() - start
        return result

    async def _generate_llama_cpp(self, prompt: str, **kwargs: Any) -> InferenceResult:
        try:
            loop = asyncio.get_event_loop()
            temperature = kwargs.get("temperature", self._config.temperature)
            max_tokens = kwargs.get("max_tokens", self._config.max_tokens)

            output = await loop.run_in_executor(
                None,
                lambda: self._backend_instance(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
            )

            text = output["choices"][0]["text"] if output.get("choices") else ""
            tokens = output.get("usage", {}).get("completion_tokens", 0)
            return InferenceResult(text=text, tokens_generated=tokens, backend="llama_cpp")
        except Exception as e:
            return InferenceResult(text=f"[llama.cpp error: {e}]", backend="llama_cpp")

    async def _generate_ollama(self, prompt: str, **kwargs: Any) -> InferenceResult:
        try:
            import httpx
            model = kwargs.get("model", self._config.model_name or "llama3")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._config.ollama_host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": kwargs.get("temperature", self._config.temperature),
                            "num_predict": kwargs.get("max_tokens", self._config.max_tokens),
                        },
                    },
                    timeout=120.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return InferenceResult(
                        text=data.get("response", ""),
                        tokens_generated=data.get("eval_count", 0),
                        backend="ollama",
                    )
                return InferenceResult(text=f"[Ollama error: {response.status_code}]", backend="ollama")
        except Exception as e:
            return InferenceResult(text=f"[Ollama error: {e}]", backend="ollama")

    async def generate_stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        if not self._loaded or self._config.backend != InferenceBackend.OLLAMA:
            yield "[Streaming not available]"
            return

        try:
            import httpx
            model = kwargs.get("model", self._config.model_name or "llama3")
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self._config.ollama_host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": kwargs.get("temperature", self._config.temperature),
                        },
                    },
                    timeout=120.0,
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
        except Exception as e:
            yield f"[Stream error: {e}]"

    async def unload(self) -> None:
        self._backend_instance = None
        self._loaded = False

    def get_available_backends(self) -> list[dict[str, str]]:
        backends = []
        try:
            import llama_cpp  # noqa: F401
            backends.append({"name": "llama_cpp", "description": "llama.cpp Python bindings", "available": True})
        except ImportError:
            backends.append({"name": "llama_cpp", "description": "llama.cpp Python bindings", "available": False})

        backends.append({"name": "ollama", "description": "Ollama local inference server", "available": True})
        return backends


local_inference_engine = LocalInferenceEngine()
