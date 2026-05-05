from __future__ import annotations

from typing import Any

from app.core.tools.pdf_tool import PDFTool


class PDFService:
    def __init__(self) -> None:
        self._tool = PDFTool()

    async def extract_text(self, file_path: str, pages: list[int] | None = None) -> dict[str, Any]:
        await self._tool.activate()
        try:
            kwargs: dict[str, Any] = {"action": "extract_text", "file_path": file_path}
            if pages:
                kwargs["pages"] = pages
            return await self._tool.call(**kwargs)
        finally:
            await self._tool.hibernate()

    async def extract_images(self, file_path: str) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="extract_images", file_path=file_path)
        finally:
            await self._tool.hibernate()

    async def get_metadata(self, file_path: str) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="get_metadata", file_path=file_path)
        finally:
            await self._tool.hibernate()

    async def list_pages(self, file_path: str) -> dict[str, Any]:
        await self._tool.activate()
        try:
            return await self._tool.call(action="list_pages", file_path=file_path)
        finally:
            await self._tool.hibernate()

    async def summarize(self, file_path: str) -> dict[str, Any]:
        text_result = await self.extract_text(file_path)
        if "error" in text_result:
            return text_result
        return {
            "text": text_result.get("text", ""),
            "page_count": text_result.get("page_count", 0),
            "summary_available": True,
        }


pdf_service = PDFService()
