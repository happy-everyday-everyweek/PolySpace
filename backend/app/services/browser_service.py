from __future__ import annotations

from typing import Any

from app.core.tools.browser_tool import BrowserTool


class BrowserService:
    def __init__(self) -> None:
        self._tool = BrowserTool()

    async def navigate(self, url: str) -> dict[str, Any]:
        await self._tool.activate()
        try:
            result = await self._tool.call(action="navigate", url=url)
            return result
        finally:
            await self._tool.hibernate()

    async def screenshot(self, url: str | None = None, full_page: bool = False) -> dict[str, Any]:
        await self._tool.activate()
        try:
            if url:
                await self._tool.call(action="navigate", url=url)
            return await self._tool.call(action="screenshot", full_page=full_page)
        finally:
            await self._tool.hibernate()

    async def get_text(self, url: str, selector: str = "body") -> dict[str, Any]:
        await self._tool.activate()
        try:
            await self._tool.call(action="navigate", url=url)
            return await self._tool.call(action="get_text", selector=selector)
        finally:
            await self._tool.hibernate()

    async def interact(self, url: str, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        await self._tool.activate()
        results = []
        try:
            await self._tool.call(action="navigate", url=url)
            for action_def in actions:
                action_type = action_def.get("type", "")
                if action_type == "click":
                    result = await self._tool.call(action="click", selector=action_def.get("selector", ""))
                elif action_type == "fill":
                    result = await self._tool.call(action="fill", selector=action_def.get("selector", ""), value=action_def.get("value", ""))
                elif action_type == "screenshot":
                    result = await self._tool.call(action="screenshot")
                else:
                    result = {"error": f"Unknown action: {action_type}"}
                results.append(result)
            return results
        finally:
            await self._tool.hibernate()


browser_service = BrowserService()
