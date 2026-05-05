import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class PolySpaceError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500, detail: Any = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail


class ToolError(PolySpaceError):
    def __init__(self, message: str, tool_name: str = "", detail: Any = None):
        super().__init__(message, code="TOOL_ERROR", status_code=500, detail=detail)
        self.tool_name = tool_name


class LLMError(PolySpaceError):
    def __init__(self, message: str, provider: str = "", model: str = "", detail: Any = None):
        super().__init__(message, code="LLM_ERROR", status_code=502, detail=detail)
        self.provider = provider
        self.model = model


class LLMRateLimitError(LLMError):
    def __init__(self, message: str = "Rate limit exceeded", provider: str = "", model: str = ""):
        super().__init__(message, provider=provider, model=model)
        self.code = "LLM_RATE_LIMIT"
        self.status_code = 429


class LLMTimeoutError(LLMError):
    def __init__(self, message: str = "LLM request timed out", provider: str = "", model: str = ""):
        super().__init__(message, provider=provider, model=model)
        self.code = "LLM_TIMEOUT"
        self.status_code = 504


class MemoryError(PolySpaceError):
    def __init__(self, message: str, detail: Any = None):
        super().__init__(message, code="MEMORY_ERROR", status_code=500, detail=detail)


class SafetyViolationError(PolySpaceError):
    def __init__(self, message: str, policy: str = "", detail: Any = None):
        super().__init__(message, code="SAFETY_VIOLATION", status_code=403, detail=detail)
        self.policy = policy


class ServiceUnavailableError(PolySpaceError):
    def __init__(self, message: str = "Service is not initialized", service: str = ""):
        super().__init__(message, code="SERVICE_UNAVAILABLE", status_code=503)
        self.service = service


class ValidationError(PolySpaceError):
    def __init__(self, message: str, detail: Any = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, detail=detail)


class NotFoundError(PolySpaceError):
    def __init__(self, message: str = "Resource not found", resource: str = ""):
        super().__init__(message, code="NOT_FOUND", status_code=404)
        self.resource = resource


def _format_error_response(exc: PolySpaceError) -> dict:
    response: dict[str, Any] = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }
    if exc.detail is not None:
        response["error"]["detail"] = exc.detail
    return response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PolySpaceError)
    async def polyspace_error_handler(request: Request, exc: PolySpaceError) -> JSONResponse:
        log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
        logger.log(
            log_level,
            "PolySpaceError [%s] %s - path=%s",
            exc.code,
            exc.message,
            request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_format_error_response(exc),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception - path=%s: %s",
            request.url.path,
            str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            },
        )
