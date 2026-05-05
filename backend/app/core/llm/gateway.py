import asyncio
import logging
import time
from typing import Any, AsyncIterator, Optional

from app.config import settings
from app.core.exceptions import LLMError, LLMRateLimitError, LLMTimeoutError

try:
    import litellm
except ImportError:
    litellm = None

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max: int = 1,
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max = half_open_max
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._state = "closed"
        self._half_open_count = 0

    @property
    def state(self) -> str:
        if self._state == "open":
            if time.monotonic() - self._last_failure_time > self._recovery_timeout:
                self._state = "half_open"
                self._half_open_count = 0
        return self._state

    def record_success(self) -> None:
        if self._state == "half_open":
            self._state = "closed"
        self._failure_count = 0

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._state == "half_open":
            self._state = "open"
        elif self._failure_count >= self._failure_threshold:
            self._state = "open"
            logger.warning(
                "Circuit breaker opened after %d failures",
                self._failure_count,
            )

    def allow_request(self) -> bool:
        state = self.state
        if state == "closed":
            return True
        if state == "half_open":
            if self._half_open_count < self._half_open_max:
                self._half_open_count += 1
                return True
            return False
        return False


class LLMGateway:
    def __init__(self):
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

    def _get_breaker(self, model: str) -> CircuitBreaker:
        if model not in self._circuit_breakers:
            self._circuit_breakers[model] = CircuitBreaker()
        return self._circuit_breakers[model]

    def _resolve_api_params(self, model: str, kwargs: dict) -> dict:
        params: dict[str, Any] = {}
        if "api_key" in kwargs:
            params["api_key"] = kwargs.pop("api_key")
        if "api_base" in kwargs:
            params["api_base"] = kwargs.pop("api_base")
        return params

    async def acompletion(
        self,
        model: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Any:
        if litellm is None:
            raise LLMError("litellm is not installed", provider="unknown", model=model)

        breaker = self._get_breaker(model)
        if not breaker.allow_request():
            raise LLMError(
                f"Circuit breaker is open for model {model}",
                provider="unknown",
                model=model,
            )

        last_exception = None
        api_params = self._resolve_api_params(model, kwargs)
        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
                params: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    "timeout": settings.LLM_REQUEST_TIMEOUT,
                }
                if tools:
                    params["tools"] = tools
                    params["tool_choice"] = "auto"
                params.update(api_params)
                params.update(kwargs)

                result = await litellm.acompletion(**params)
                breaker.record_success()
                return result

            except asyncio.TimeoutError:
                last_exception = LLMTimeoutError(model=model)
                logger.warning(
                    "LLM request timeout (attempt %d/%d) for model %s",
                    attempt + 1,
                    settings.LLM_MAX_RETRIES,
                    model,
                )
            except Exception as e:
                error_str = str(e).lower()
                if "rate" in error_str and "limit" in error_str:
                    last_exception = LLMRateLimitError(model=model)
                    breaker.record_failure()
                    raise last_exception

                last_exception = LLMError(str(e), model=model)
                breaker.record_failure()
                logger.warning(
                    "LLM request failed (attempt %d/%d) for model %s: %s",
                    attempt + 1,
                    settings.LLM_MAX_RETRIES,
                    model,
                    str(e),
                )

            if attempt < settings.LLM_MAX_RETRIES - 1:
                delay = settings.LLM_RETRY_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)

        breaker.record_failure()
        raise last_exception or LLMError("Max retries exceeded", model=model)

    async def acompletion_stream(
        self,
        model: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[Any]:
        if litellm is None:
            raise LLMError("litellm is not installed", provider="unknown", model=model)

        breaker = self._get_breaker(model)
        if not breaker.allow_request():
            raise LLMError(
                f"Circuit breaker is open for model {model}",
                provider="unknown",
                model=model,
            )

        try:
            api_params = self._resolve_api_params(model, kwargs)
            params: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "stream": True,
                "timeout": settings.LLM_REQUEST_TIMEOUT,
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            params.update(api_params)
            params.update(kwargs)

            response = await litellm.acompletion(**params)
            async for chunk in response:
                yield chunk
            breaker.record_success()

        except asyncio.TimeoutError:
            breaker.record_failure()
            raise LLMTimeoutError(model=model)
        except Exception as e:
            breaker.record_failure()
            raise LLMError(str(e), model=model)

    async def aembedding(
        self,
        model: str,
        input: list[str],
        **kwargs,
    ) -> Any:
        if litellm is None:
            raise LLMError("litellm is not installed", provider="unknown", model=model)

        breaker = self._get_breaker(model)
        if not breaker.allow_request():
            raise LLMError(
                f"Circuit breaker is open for model {model}",
                provider="unknown",
                model=model,
            )

        last_exception = None
        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
                result = await litellm.aembedding(
                    model=model,
                    input=input,
                    timeout=settings.LLM_REQUEST_TIMEOUT,
                    **kwargs,
                )
                breaker.record_success()
                return result
            except Exception as e:
                last_exception = LLMError(str(e), model=model)
                breaker.record_failure()
                if attempt < settings.LLM_MAX_RETRIES - 1:
                    delay = settings.LLM_RETRY_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)

        raise last_exception or LLMError("Max retries exceeded", model=model)

    def get_model_id(self, config) -> str:
        if config.provider and config.model_id:
            return f"{config.provider}/{config.model_id}"
        return config.model_id

    def get_breaker_stats(self) -> dict[str, str]:
        return {model: breaker.state for model, breaker in self._circuit_breakers.items()}


llm_gateway = LLMGateway()
