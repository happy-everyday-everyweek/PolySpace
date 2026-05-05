from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional


class ToolState(str, Enum):
    INACTIVE = "inactive"
    ACTIVATING = "activating"
    ACTIVE = "active"
    CALLING = "calling"
    HIBERNATING = "hibernating"
    ERROR = "error"


_VALID_TRANSITIONS: dict[ToolState, set[ToolState]] = {
    ToolState.INACTIVE: {ToolState.ACTIVATING},
    ToolState.ACTIVATING: {ToolState.ACTIVE, ToolState.ERROR},
    ToolState.ACTIVE: {ToolState.CALLING, ToolState.HIBERNATING, ToolState.ERROR},
    ToolState.CALLING: {ToolState.ACTIVE, ToolState.ERROR, ToolState.HIBERNATING},
    ToolState.HIBERNATING: {ToolState.INACTIVE, ToolState.ERROR},
    ToolState.ERROR: {ToolState.ACTIVATING, ToolState.HIBERNATING},
}


class ToolStateMachine:
    def __init__(self, initial: ToolState = ToolState.INACTIVE):
        self._state = initial

    @property
    def state(self) -> ToolState:
        return self._state

    def transition(self, target: ToolState) -> None:
        if target not in _VALID_TRANSITIONS.get(self._state, set()):
            raise ValueError(f"Invalid transition: {self._state.value} -> {target.value}")
        self._state = target

    def can_transition(self, target: ToolState) -> bool:
        return target in _VALID_TRANSITIONS.get(self._state, set())


class BaseTool(ABC):
    def __init__(self, name: str, description: str, parameters: Optional[dict] = None):
        self.name = name
        self.description = description
        self.parameters = parameters or {"type": "object", "properties": {}}
        self._state_machine = ToolStateMachine()

    @property
    def state(self) -> ToolState:
        return self._state_machine.state

    async def activate(self) -> None:
        self._state_machine.transition(ToolState.ACTIVATING)
        try:
            await self._on_activate()
            self._state_machine.transition(ToolState.ACTIVE)
        except Exception:
            self._state_machine.transition(ToolState.ERROR)
            raise

    async def call(self, **kwargs) -> Any:
        if self.state not in (ToolState.ACTIVE, ToolState.CALLING):
            if self.state == ToolState.INACTIVE:
                await self.activate()
            else:
                raise RuntimeError(f"Tool '{self.name}' is in state {self.state.value}, cannot call")
        self._state_machine.transition(ToolState.CALLING)
        try:
            result = await self._on_call(**kwargs)
            self._state_machine.transition(ToolState.ACTIVE)
            return result
        except Exception:
            self._state_machine.transition(ToolState.ERROR)
            raise

    async def hibernate(self) -> None:
        if self.state == ToolState.INACTIVE:
            return
        if self.state in (ToolState.ACTIVE, ToolState.CALLING, ToolState.ERROR):
            if self._state_machine.can_transition(ToolState.HIBERNATING):
                self._state_machine.transition(ToolState.HIBERNATING)
            else:
                self._state_machine.transition(ToolState.ERROR)
                self._state_machine.transition(ToolState.HIBERNATING)
        try:
            await self._on_hibernate()
            self._state_machine.transition(ToolState.INACTIVE)
        except Exception:
            self._state_machine.transition(ToolState.ERROR)
            raise

    @abstractmethod
    async def _on_activate(self) -> None:
        ...

    @abstractmethod
    async def _on_call(self, **kwargs) -> Any:
        ...

    @abstractmethod
    async def _on_hibernate(self) -> None:
        ...

    def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
