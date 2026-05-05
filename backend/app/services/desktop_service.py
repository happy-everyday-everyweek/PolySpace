from __future__ import annotations

from typing import Any

from app.core.tools.desktop_tool import DesktopTool


class DesktopService:
    def __init__(self) -> None:
        self._tool = DesktopTool()

    async def screenshot(self) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="screenshot")
        finally:
            await self._tool.hibernate()

    async def click(self, x: int, y: int, button: str = "left", double: bool = False) -> dict[str, Any]:
        await self._tool.activate()
        try:
            action = "double_click" if double else "click"
            return await self._tool.call(action=action, x=x, y=y, button=button)
        finally:
            await self._tool.hibernate()

    async def right_click(self, x: int, y: int) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="right_click", x=x, y=y)
        finally:
            await self._tool.hibernate()

    async def long_press(self, x: int, y: int, duration: float = 0.5) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="long_press", x=x, y=y, duration=duration)
        finally:
            await self._tool.hibernate()

    async def type_text(self, text: str) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="input_text", text=text)
        finally:
            await self._tool.hibernate()

    async def press_key(self, key: str) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="key_tap", key=key)
        finally:
            await self._tool.hibernate()

    async def key_combo(self, keys: list[str]) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="key_combo", keys=keys)
        finally:
            await self._tool.hibernate()

    async def scroll(self, amount: int = -3) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="scroll", amount=amount)
        finally:
            await self._tool.hibernate()

    async def scroll_up(self, amount: int = 5, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="scroll_up", amount=amount, x=x, y=y)
        finally:
            await self._tool.hibernate()

    async def scroll_down(self, amount: int = 5, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="scroll_down", amount=amount, x=x, y=y)
        finally:
            await self._tool.hibernate()

    async def move_mouse(self, x: int, y: int) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="move_mouse", x=x, y=y)
        finally:
            await self._tool.hibernate()

    async def hover(self, x: int, y: int, duration: float = 0.3) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="hover", x=x, y=y, duration=duration)
        finally:
            await self._tool.hibernate()

    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.3) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="drag", start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y, duration=duration)
        finally:
            await self._tool.hibernate()

    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.3) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="swipe", start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y, duration=duration)
        finally:
            await self._tool.hibernate()

    async def get_mouse_pos(self) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="get_mouse_pos")
        finally:
            await self._tool.hibernate()

    async def get_screen_size(self) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="get_screen_size")
        finally:
            await self._tool.hibernate()

    async def wait(self, wait_ms: int = 500) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="wait", wait_ms=wait_ms)
        finally:
            await self._tool.hibernate()

    async def analyze(self, instruction: str, host: str = "localhost", port: int = 8000) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="analyze", instruction=instruction, host=host, port=port)
        finally:
            await self._tool.hibernate()

    async def automate(self, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        await self._tool.activate()
        results = []
        try:
            for step in steps:
                result = await self._tool.call(**step)
                results.append(result)
            return results
        finally:
            await self._tool.hibernate()


desktop_service = DesktopService()
