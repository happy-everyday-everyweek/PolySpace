import asyncio
import time
from typing import Callable, Optional

from app.core.connector.device_manager import DeviceManager
from app.core.safety.confirmation import ConfirmationManager
from app.core.safety.monitor import RuntimeMonitor
from app.core.safety.policies import PolicyEngine
from app.core.tool.registry import ToolRegistry


class ExecutionService:
    def __init__(
        self,
        tool_registry: ToolRegistry,
        policy_engine: PolicyEngine,
        confirmation_manager: ConfirmationManager,
        runtime_monitor: RuntimeMonitor,
        device_manager: Optional[DeviceManager] = None,
        default_timeout: float = 60.0,
        max_retries: int = 2,
    ):
        self._tools = tool_registry
        self._policies = policy_engine
        self._confirmation = confirmation_manager
        self._monitor = runtime_monitor
        self._device_manager = device_manager
        self._default_timeout = default_timeout
        self._max_retries = max_retries
        self._step_callback: Optional[Callable[[dict], None]] = None

    def set_step_callback(self, callback: Callable[[dict], None]) -> None:
        self._step_callback = callback

    async def execute_tool(self, tool_name: str, params: dict,
                           timeout: Optional[float] = None,
                           device_id: Optional[str] = None) -> dict:
        action_str = f"{tool_name}({params})"
        policy_action, policy_msg = self._policies.evaluate(action_str)

        if policy_action.value == "block":
            return {"status": "blocked", "message": policy_msg}

        if policy_action.value == "confirm":
            request = await self._confirmation.request_confirmation(action_str, policy_msg or "")
            return {
                "status": "pending_confirmation",
                "request_id": request.id,
                "message": policy_msg,
            }

        if self._monitor.detect_jitter():
            return {"status": "jitter_detected", "message": "Tool jitter detected. Please wait."}

        if not self._monitor.check_rate_limit():
            return {"status": "rate_limited", "message": "Rate limit exceeded."}

        self._monitor.record_tool_call(tool_name)

        effective_timeout = timeout or self._default_timeout
        last_error = None

        for attempt in range(self._max_retries + 1):
            try:
                start_time = time.time()

                if device_id and self._device_manager:
                    action = params.get("action", "execute")
                    remote_params = {k: v for k, v in params.items() if k != "action"}
                    result = await asyncio.wait_for(
                        self._device_manager.execute_on_device(
                            device_id=device_id,
                            tool_name=tool_name,
                            action=action,
                            params=remote_params,
                        ),
                        timeout=effective_timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        self._tools.call_tool(tool_name, **params),
                        timeout=effective_timeout
                    )

                duration_ms = (time.time() - start_time) * 1000

                step_info = {
                    "tool": tool_name,
                    "params": params,
                    "status": "ok",
                    "duration_ms": duration_ms,
                    "attempt": attempt + 1,
                    "device_id": device_id,
                }
                self._notify_step(step_info)

                return {"status": "ok", "result": result, "duration_ms": duration_ms}

            except asyncio.TimeoutError:
                last_error = f"Tool execution timed out after {effective_timeout}s"
                step_info = {
                    "tool": tool_name,
                    "params": params,
                    "status": "timeout",
                    "attempt": attempt + 1,
                    "device_id": device_id,
                }
                self._notify_step(step_info)

            except Exception as e:
                last_error = str(e)
                step_info = {
                    "tool": tool_name,
                    "params": params,
                    "status": "error",
                    "error": last_error,
                    "attempt": attempt + 1,
                    "device_id": device_id,
                }
                self._notify_step(step_info)

                if attempt < self._max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))

        return {"status": "error", "message": last_error or "Unknown error after retries"}

    async def execute_chain(self, steps: list[dict]) -> list[dict]:
        results = []
        for step in steps:
            tool_name = step.get("tool")
            params = step.get("params", {})
            device_id = step.get("device_id")
            if not tool_name:
                results.append({"status": "error", "message": "Missing tool name"})
                continue
            result = await self.execute_tool(tool_name, params, device_id=device_id)
            results.append(result)
            if result.get("status") not in ("ok",):
                break
        return results

    async def execute_on_device(self, device_id: str, tool_name: str,
                                 action: str, params: dict,
                                 timeout: Optional[float] = None) -> dict:
        if not self._device_manager:
            return {"status": "error", "message": "Device manager not available"}

        effective_timeout = timeout or self._default_timeout

        try:
            result = await asyncio.wait_for(
                self._device_manager.execute_on_device(
                    device_id=device_id,
                    tool_name=tool_name,
                    action=action,
                    params=params,
                ),
                timeout=effective_timeout
            )
            return {"status": "ok", "result": result}
        except asyncio.TimeoutError:
            return {"status": "error", "message": f"Device execution timed out after {effective_timeout}s"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _notify_step(self, step_info: dict) -> None:
        if self._step_callback:
            self._step_callback(step_info)
