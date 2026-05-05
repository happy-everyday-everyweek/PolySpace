from __future__ import annotations

from typing import Any

from app.core.tool.base import BaseTool


class SearchTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="search",
            description="Search the web using DuckDuckGo",
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs: Any) -> Any:
        query = kwargs.get("query", "")
        max_results = int(kwargs.get("max_results", 5))

        if not query:
            return {"error": "No search query provided"}

        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                formatted = []
                for r in results:
                    formatted.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
                return {"results": formatted, "query": query}

        except ImportError:
            return {"error": "Search not available. Install: pip install duckduckgo-search"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass

    def get_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results (default: 5)"},
                    },
                    "required": ["query"],
                },
            },
        }
