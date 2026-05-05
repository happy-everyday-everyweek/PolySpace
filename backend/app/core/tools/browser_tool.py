from __future__ import annotations

from typing import Any

from app.core.tool.base import BaseTool


class BrowserTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="browser",
            description="Browser automation tool for web navigation and interaction",
        )
        self._browser = None
        self._page = None

    async def _on_activate(self) -> None:
        try:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
            self._page = await self._browser.new_page()
        except ImportError:
            self._browser = None
            self._page = None

    async def _on_call(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "")

        if self._page is None:
            return {"error": "Browser not available. Install playwright: pip install playwright && playwright install"}

        try:
            if action == "navigate":
                url = kwargs.get("url", "")
                await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                title = await self._page.title()
                return {"title": title, "url": self._page.url}

            elif action == "screenshot":
                screenshot_bytes = await self._page.screenshot(full_page=kwargs.get("full_page", False))
                import base64
                return {"screenshot_base64": base64.b64encode(screenshot_bytes).decode()}

            elif action == "get_text":
                selector = kwargs.get("selector", "body")
                element = await self._page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    return {"text": text}
                return {"error": f"Element not found: {selector}"}

            elif action == "click":
                selector = kwargs.get("selector", "")
                await self._page.click(selector, timeout=10000)
                return {"success": True}

            elif action == "fill":
                selector = kwargs.get("selector", "")
                value = kwargs.get("value", "")
                await self._page.fill(selector, value, timeout=10000)
                return {"success": True}

            elif action == "evaluate":
                script = kwargs.get("script", "")
                result = await self._page.evaluate(script)
                return {"result": result}

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None

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
                            "enum": ["navigate", "screenshot", "get_text", "click", "fill", "evaluate"],
                            "description": "Browser action to perform",
                        },
                        "url": {"type": "string", "description": "URL to navigate to"},
                        "selector": {"type": "string", "description": "CSS selector for element"},
                        "value": {"type": "string", "description": "Value to fill in"},
                        "script": {"type": "string", "description": "JavaScript to evaluate"},
                        "full_page": {"type": "boolean", "description": "Take full page screenshot"},
                    },
                    "required": ["action"],
                },
            },
        }
