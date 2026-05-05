from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class LifecyclePhase(str, Enum):
    PRE_CHECK = "pre_check"
    ACTIVATE = "activate"
    EXECUTE = "execute"
    POST_PROCESS = "post_process"
    DEACTIVATE = "deactivate"


@dataclass
class LifecycleEvent:
    capability_name: str
    phase: LifecyclePhase
    success: bool = True
    error: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LifecycleHook:
    def __init__(self) -> None:
        self._hooks: dict[LifecyclePhase, list[Callable[[LifecycleEvent], Any]]] = {
            phase: [] for phase in LifecyclePhase
        }

    def register(self, phase: LifecyclePhase, callback: Callable[[LifecycleEvent], Any]) -> None:
        self._hooks[phase].append(callback)

    def unregister(self, phase: LifecyclePhase, callback: Callable[[LifecycleEvent], Any]) -> None:
        try:
            self._hooks[phase].remove(callback)
        except ValueError:
            pass

    async def fire(self, event: LifecycleEvent) -> None:
        for callback in self._hooks[event.phase]:
            try:
                result = callback(event)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error(f"Lifecycle hook error at {event.phase.value} for {event.capability_name}: {e}")


lifecycle_hook = LifecycleHook()
