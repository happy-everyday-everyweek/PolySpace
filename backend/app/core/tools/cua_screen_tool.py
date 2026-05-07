from __future__ import annotations

import base64
import io
import logging
from typing import Any

from app.core.tool.base import BaseTool

logger = logging.getLogger(__name__)


class CuaScreenTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="cua_screen",
            description=(
                "Enhanced screen operation tool powered by CUA - mouse, keyboard, "
                "screen capture, window management, UI element detection, OCR"
            ),
        )
        self._cua_auto_available = False
        self._cua_som_available = False
        self._pyautogui = None
        self._mss = None

    async def _on_activate(self) -> None:
        try:
            import cua_auto.keyboard  # noqa: F401
            import cua_auto.mouse  # noqa: F401
            import cua_auto.screen  # noqa: F401
            self._cua_auto_available = True
            logger.info("CUA auto module loaded successfully")
        except ImportError:
            self._cua_auto_available = False
            logger.debug("CUA auto not available, falling back to pyautogui")

        try:
            from som import OmniParser  # noqa: F401
            self._cua_som_available = True
            logger.info("CUA SOM (OmniParser) loaded successfully")
        except ImportError:
            self._cua_som_available = False
            logger.debug("CUA SOM not available")

        if not self._cua_auto_available:
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

        if action in ("screenshot", "screen_size", "cursor_position", "detect_ui", "ocr"):
            return await self._handle_screen_action(action, **kwargs)
        elif action in ("click", "double_click", "right_click", "move_to", "drag", "scroll"):
            return await self._handle_mouse_action(action, **kwargs)
        elif action in ("type_text", "press_key", "hotkey", "key_down", "key_up"):
            return await self._handle_keyboard_action(action, **kwargs)
        elif action in ("get_active_window", "list_windows", "activate_window",
                        "minimize_window", "maximize_window", "close_window",
                        "set_window_size", "set_window_position", "launch_app"):
            return await self._handle_window_action(action, **kwargs)
        else:
            return {"error": f"Unknown action: {action}. Supported: screenshot, click, type_text, detect_ui, etc."}

    async def _handle_screen_action(self, action: str, **kwargs: Any) -> Any:
        if self._cua_auto_available:
            import cua_auto.screen as screen

            if action == "screenshot":
                img = screen.screenshot()
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return {"screenshot_base64": base64.b64encode(buf.getvalue()).decode()}

            elif action == "screen_size":
                w, h = screen.screen_size()
                return {"width": w, "height": h}

            elif action == "cursor_position":
                x, y = screen.cursor_position()
                return {"x": x, "y": y}

            elif action == "detect_ui":
                if self._cua_som_available:
                    from som import OmniParser
                    img = screen.screenshot()
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    parser = OmniParser()
                    result = parser.parse(
                        screenshot_data=buf.getvalue(),
                        box_threshold=kwargs.get("box_threshold", 0.3),
                        iou_threshold=kwargs.get("iou_threshold", 0.1),
                        use_ocr=kwargs.get("use_ocr", True),
                    )
                    return {
                        "elements": [
                            {
                                "type": e.__class__.__name__,
                                "bbox": e.bbox if hasattr(e, "bbox") else None,
                                "content": e.content if hasattr(e, "content") else None,
                                "confidence": e.confidence if hasattr(e, "confidence") else None,
                            }
                            for e in result.elements
                        ],
                        "screen_info": result.screen_info,
                        "element_count": len(result.elements),
                    }
                return {"error": "UI detection requires cua-som package (pip install cua-som)"}

            elif action == "ocr":
                if self._cua_som_available:
                    from som import OmniParser
                    img = screen.screenshot()
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    parser = OmniParser()
                    result = parser.parse(screenshot_data=buf.getvalue(), use_ocr=True)
                    texts = [e.content for e in result.elements if hasattr(e, "content") and e.content]
                    return {"text": "\n".join(texts), "element_count": len(texts)}
                return {"error": "OCR requires cua-som package"}

        if self._pyautogui is not None:
            if action == "screenshot":
                img = self._pyautogui.screenshot()
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return {"screenshot_base64": base64.b64encode(buf.getvalue()).decode()}
            elif action == "screen_size":
                return {"width": self._pyautogui.size().width, "height": self._pyautogui.size().height}
            elif action == "cursor_position":
                pos = self._pyautogui.position()
                return {"x": pos.x, "y": pos.y}

        return {"error": "Screen operation not available. Install: pip install cua-auto or pyautogui"}

    async def _handle_mouse_action(self, action: str, **kwargs: Any) -> Any:
        if self._cua_auto_available:
            import cua_auto.mouse as mouse

            if action == "click":
                mouse.click(kwargs.get("x", 0), kwargs.get("y", 0))
            elif action == "double_click":
                mouse.double_click(kwargs.get("x", 0), kwargs.get("y", 0))
            elif action == "right_click":
                mouse.right_click(kwargs.get("x", 0), kwargs.get("y", 0))
            elif action == "move_to":
                mouse.move_to(kwargs.get("x", 0), kwargs.get("y", 0))
            elif action == "drag":
                mouse.drag(
                    kwargs.get("start_x", 0), kwargs.get("start_y", 0),
                    kwargs.get("end_x", 0), kwargs.get("end_y", 0),
                )
            elif action == "scroll":
                mouse.scroll(dx=kwargs.get("dx", 0), dy=kwargs.get("dy", 3))
            return {"success": True, "backend": "cua-auto"}

        if self._pyautogui is not None:
            if action == "click":
                self._pyautogui.click(x=kwargs.get("x"), y=kwargs.get("y"), button=kwargs.get("button", "left"))
            elif action == "double_click":
                self._pyautogui.doubleClick(x=kwargs.get("x"), y=kwargs.get("y"))
            elif action == "right_click":
                self._pyautogui.rightClick(x=kwargs.get("x"), y=kwargs.get("y"))
            elif action == "move_to":
                self._pyautogui.moveTo(x=kwargs.get("x"), y=kwargs.get("y"))
            elif action == "drag":
                self._pyautogui.drag(
                    kwargs.get("end_x", 0) - kwargs.get("start_x", 0),
                    kwargs.get("end_y", 0) - kwargs.get("start_y", 0),
                    kwargs.get("start_x", 0), kwargs.get("start_y", 0),
                )
            elif action == "scroll":
                self._pyautogui.scroll(kwargs.get("dy", 3))
            return {"success": True, "backend": "pyautogui"}

        return {"error": "Mouse operation not available"}

    async def _handle_keyboard_action(self, action: str, **kwargs: Any) -> Any:
        if self._cua_auto_available:
            import cua_auto.keyboard as keyboard

            if action == "type_text":
                keyboard.type_text(kwargs.get("text", ""))
            elif action == "press_key":
                keyboard.press_key(kwargs.get("key", "enter"))
            elif action == "hotkey":
                keyboard.hotkey(kwargs.get("keys", []))
            elif action == "key_down":
                keyboard.key_down(kwargs.get("key", ""))
            elif action == "key_up":
                keyboard.key_up(kwargs.get("key", ""))
            return {"success": True, "backend": "cua-auto"}

        if self._pyautogui is not None:
            if action == "type_text":
                self._pyautogui.typewrite(kwargs.get("text", ""))
            elif action == "press_key":
                self._pyautogui.press(kwargs.get("key", "enter"))
            elif action == "hotkey":
                self._pyautogui.hotkey(*kwargs.get("keys", []))
            return {"success": True, "backend": "pyautogui"}

        return {"error": "Keyboard operation not available"}

    async def _handle_window_action(self, action: str, **kwargs: Any) -> Any:
        if self._cua_auto_available:
            import cua_auto.window as window

            if action == "get_active_window":
                title = window.get_active_window_title()
                handle = window.get_active_window_handle()
                return {"title": title, "handle": handle}
            elif action == "list_windows":
                title_filter = kwargs.get("title", "")
                if title_filter:
                    handles = window.get_windows_with_title(title_filter)
                    return {"handles": handles, "count": len(handles)}
                return {"error": "Provide 'title' parameter to filter windows"}
            elif action == "activate_window":
                window.activate_window(kwargs.get("handle", ""))
                return {"success": True}
            elif action == "minimize_window":
                window.minimize_window(kwargs.get("handle", ""))
                return {"success": True}
            elif action == "maximize_window":
                window.maximize_window(kwargs.get("handle", ""))
                return {"success": True}
            elif action == "close_window":
                window.close_window(kwargs.get("handle", ""))
                return {"success": True}
            elif action == "set_window_size":
                window.set_window_size(kwargs.get("handle", ""), kwargs.get("width", 800), kwargs.get("height", 600))
                return {"success": True}
            elif action == "set_window_position":
                window.set_window_position(kwargs.get("handle", ""), kwargs.get("x", 0), kwargs.get("y", 0))
                return {"success": True}
            elif action == "launch_app":
                window.launch(kwargs.get("app", ""))
                return {"success": True}

        return {"error": "Window management requires cua-auto package (pip install cua-auto)"}

    async def _on_hibernate(self) -> None:
        self._cua_auto_available = False
        self._cua_som_available = False
        self._pyautogui = None
        self._mss = None
