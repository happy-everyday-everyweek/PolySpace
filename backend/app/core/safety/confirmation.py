from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Optional


class ConfirmationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"


@dataclass
class ConfirmationRequest:
    id: str
    action: str
    message: str
    status: ConfirmationStatus = ConfirmationStatus.PENDING


class ConfirmationManager:
    def __init__(self):
        self._pending: dict[str, ConfirmationRequest] = {}
        self._callbacks: dict[str, Callable[[bool], Awaitable[None]]] = {}

    async def request_confirmation(self, action: str, message: str) -> ConfirmationRequest:
        import uuid

        request_id = str(uuid.uuid4())
        request = ConfirmationRequest(id=request_id, action=action, message=message)
        self._pending[request_id] = request
        return request

    async def approve(self, request_id: str) -> None:
        request = self._pending.get(request_id)
        if request:
            request.status = ConfirmationStatus.APPROVED
            callback = self._callbacks.pop(request_id, None)
            if callback:
                await callback(True)
            self._pending.pop(request_id, None)

    async def deny(self, request_id: str) -> None:
        request = self._pending.get(request_id)
        if request:
            request.status = ConfirmationStatus.DENIED
            callback = self._callbacks.pop(request_id, None)
            if callback:
                await callback(False)
            self._pending.pop(request_id, None)

    def get_pending(self) -> list[ConfirmationRequest]:
        return [
            r for r in self._pending.values() if r.status == ConfirmationStatus.PENDING
        ]

    def get_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        return self._pending.get(request_id)


confirmation_manager = ConfirmationManager()
