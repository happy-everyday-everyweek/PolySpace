from __future__ import annotations

import asyncio
import base64
import io
import json
from typing import Any

from app.core.tool.base import BaseTool


class DesktopTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="screen_operation",
            description="Screen operation tool - multimodal AI analysis and click/swipe/input/key operations for desktop",
        )
        self._pyautogui = None
        self._mss = None

    async def _on_activate(self) -> None:
        try:
            import pyautogui
            self._pyautogui = pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.1
        except ImportError:
            self._pyautogui = None

        try:
            import mss
            self._mss = mss
        except ImportError:
            self._mss = None

    async def _on_call(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "")

        if self._pyautogui is None:
            return {"error": "Screen operation not available. Install: pip install pyautogui mss"}

        try:
            if action == "screenshot":
                return self._take_screenshot()

            elif action == "click":
                x = kwargs.get("x")
                y = kwargs.get("y")
                button = kwargs.get("button", "left")
                clicks = kwargs.get("clicks", 1)
                if x is not None and y is not None:
                    self._pyautogui.click(x=int(x), y=int(y), button=button, clicks=clicks)
                return {"success": True}

            elif action == "double_click":
                x = kwargs.get("x")
                y = kwargs.get("y")
                if x is not None and y is not None:
                    self._pyautogui.doubleClick(x=int(x), y=int(y))
                return {"success": True}

            elif action == "right_click":
                x = kwargs.get("x")
                y = kwargs.get("y")
                if x is not None and y is not None:
                    self._pyautogui.rightClick(x=int(x), y=int(y))
                return {"success": True}

            elif action == "long_press":
                x = kwargs.get("x")
                y = kwargs.get("y")
                duration = kwargs.get("duration", 0.5)
                if x is not None and y is not None:
                    self._pyautogui.moveTo(int(x), int(y))
                    self._pyautogui.mouseDown(button="left")
                    await asyncio.sleep(float(duration))
                    self._pyautogui.mouseUp(button="left")
                return {"success": True}

            elif action == "input_text":
                text = kwargs.get("text", "")
                interval = kwargs.get("interval", 0.02)
                self._pyautogui.typewrite(text, interval=interval)
                return {"success": True}

            elif action == "key_tap":
                key = kwargs.get("key", "")
                self._pyautogui.press(key)
                return {"success": True}

            elif action == "key_combo":
                key = kwargs.get("key", "")
                keys = kwargs.get("keys", [])
                if keys:
                    self._pyautogui.hotkey(*keys)
                elif key:
                    key_parts = key.split("+")
                    if len(key_parts) > 1:
                        self._pyautogui.hotkey(*key_parts)
                    else:
                        self._pyautogui.press(key)
                return {"success": True}

            elif action == "scroll":
                amount = kwargs.get("amount", -3)
                x = kwargs.get("x")
                y = kwargs.get("y")
                self._pyautogui.scroll(amount, x=x, y=y)
                return {"success": True}

            elif action == "scroll_up":
                amount = kwargs.get("amount", 5)
                x = kwargs.get("x")
                y = kwargs.get("y")
                self._pyautogui.scroll(amount, x=x, y=y)
                return {"success": True}

            elif action == "scroll_down":
                amount = kwargs.get("amount", 5)
                x = kwargs.get("x")
                y = kwargs.get("y")
                self._pyautogui.scroll(-amount, x=x, y=y)
                return {"success": True}

            elif action == "move_mouse":
                x = kwargs.get("x")
                y = kwargs.get("y")
                duration = kwargs.get("duration", 0.25)
                if x is not None and y is not None:
                    self._pyautogui.moveTo(int(x), int(y), duration=duration)
                return {"success": True}

            elif action == "hover":
                x = kwargs.get("x")
                y = kwargs.get("y")
                duration = kwargs.get("duration", 0.3)
                if x is not None and y is not None:
                    self._pyautogui.moveTo(int(x), int(y))
                    await asyncio.sleep(float(duration))
                return {"success": True}

            elif action == "drag":
                start_x = kwargs.get("start_x")
                start_y = kwargs.get("start_y")
                end_x = kwargs.get("end_x")
                end_y = kwargs.get("end_y")
                duration = kwargs.get("duration", 0.3)
                if all(v is not None for v in [start_x, start_y, end_x, end_y]):
                    self._pyautogui.moveTo(int(start_x), int(start_y))
                    self._pyautogui.mouseDown(button="left")
                    self._pyautogui.moveTo(int(end_x), int(end_y), duration=float(duration))
                    self._pyautogui.mouseUp(button="left")
                return {"success": True}

            elif action == "swipe":
                start_x = kwargs.get("start_x")
                start_y = kwargs.get("start_y")
                end_x = kwargs.get("end_x")
                end_y = kwargs.get("end_y")
                duration = kwargs.get("duration", 0.3)
                if all(v is not None for v in [start_x, start_y, end_x, end_y]):
                    self._pyautogui.moveTo(int(start_x), int(start_y))
                    self._pyautogui.mouseDown(button="left")
                    self._pyautogui.moveTo(int(end_x), int(end_y), duration=float(duration))
                    self._pyautogui.mouseUp(button="left")
                return {"success": True}

            elif action == "get_mouse_pos":
                pos = self._pyautogui.position()
                return {"x": pos.x, "y": pos.y}

            elif action == "get_screen_size":
                size = self._pyautogui.size()
                return {"width": size.width, "height": size.height}

            elif action == "wait":
                wait_ms = kwargs.get("wait_ms", 500)
                await asyncio.sleep(float(wait_ms) / 1000.0)
                return {"success": True}

            elif action == "analyze":
                return await self._analyze_with_screenshot(**kwargs)

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _take_screenshot(self) -> dict[str, Any]:
        if self._mss is not None:
            with self._mss.mss() as sct:
                monitor = sct.monitors[0]
                shot = sct.grab(monitor)
                from PIL import Image
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return {"screenshot_base64": base64.b64encode(buf.getvalue()).decode()}
        else:
            screenshot = self._pyautogui.screenshot()
            buf = io.BytesIO()
            screenshot.save(buf, format="PNG")
            return {"screenshot_base64": base64.b64encode(buf.getvalue()).decode()}

    async def _analyze_with_screenshot(self, **kwargs: Any) -> dict[str, Any]:
        instruction = kwargs.get("instruction", "")
        if not instruction:
            return {"error": "Missing instruction for analyze"}

        screenshot_result = self._take_screenshot()
        screenshot_base64 = screenshot_result.get("screenshot_base64")
        if not screenshot_base64:
            return {"error": "Failed to take screenshot"}

        size = self._pyautogui.size()

        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 8000)

        try:
            import urllib.request
            payload = json.dumps({
                "instruction": instruction,
                "screenshot": screenshot_base64,
                "screenshot_format": "png",
                "has_multimodal_input": True,
                "platform": "desktop",
                "screen_width": size.width,
                "screen_height": size.height,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"http://{host}:{port}/api/v1/models/autoglm",
                data=payload,
                headers={"Content-Type": "application/json"},
            )

            loop = asyncio.get_event_loop()
            response_data = await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(req, timeout=120).read(),
            )
            result = json.loads(response_data)
            actions = result.get("actions", [])

            executed_results = []
            for act in actions:
                act_type = act.get("type", "")
                act_params = act.get("params", {})
                try:
                    exec_result = await self._on_call(action=act_type, **act_params)
                    executed_results.append({
                        "type": act_type,
                        "success": not exec_result.get("error"),
                        "result": exec_result,
                    })
                    await asyncio.sleep(0.3)
                except Exception as e:
                    executed_results.append({
                        "type": act_type,
                        "success": False,
                        "error": str(e),
                    })
                    break

            return {
                "success": True,
                "action_count": len(actions),
                "executed": executed_results,
            }

        except Exception as e:
            return {"error": f"Analyze failed: {str(e)}"}

    async def _on_hibernate(self) -> None:
        self._pyautogui = None
        self._mss = None

    def get_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "screenshot", "click", "double_click", "right_click",
                                "long_press", "input_text", "key_tap", "key_combo",
                                "scroll", "scroll_up", "scroll_down",
                                "move_mouse", "hover", "drag", "swipe",
                                "get_mouse_pos", "get_screen_size", "wait", "analyze",
                            ],
                            "description": "Screen operation action to perform",
                        },
                        "x": {"type": "integer", "description": "X coordinate"},
                        "y": {"type": "integer", "description": "Y coordinate"},
                        "start_x": {"type": "integer", "description": "Drag/Swipe start X"},
                        "start_y": {"type": "integer", "description": "Drag/Swipe start Y"},
                        "end_x": {"type": "integer", "description": "Drag/Swipe end X"},
                        "end_y": {"type": "integer", "description": "Drag/Swipe end Y"},
                        "duration": {"type": "integer", "description": "Duration in ms"},
                        "text": {"type": "string", "description": "Text to input"},
                        "key": {"type": "string", "description": "Key or key combination (e.g. 'ctrl+c')"},
                        "keys": {"type": "array", "items": {"type": "string"}, "description": "Key combination array"},
                        "amount": {"type": "integer", "description": "Scroll amount"},
                        "button": {"type": "string", "enum": ["left", "right", "middle"], "description": "Mouse button"},
                        "instruction": {"type": "string", "description": "Natural language instruction for AI analysis"},
                        "wait_ms": {"type": "integer", "description": "Wait duration in milliseconds"},
                    },
                    "required": ["action"],
                },
            },
        }
