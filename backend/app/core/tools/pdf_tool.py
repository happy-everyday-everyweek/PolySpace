from __future__ import annotations

from typing import Any

from app.core.tool.base import BaseTool


class PDFTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="pdf",
            description="Parse and extract content from PDF files",
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "")
        file_path = kwargs.get("file_path", "")

        if not action:
            return {"error": "No action specified"}

        try:
            if action == "extract_text":
                if not file_path:
                    return {"error": "No file path provided"}
                return await self._extract_text(file_path, kwargs)

            elif action == "extract_images":
                if not file_path:
                    return {"error": "No file path provided"}
                return await self._extract_images(file_path)

            elif action == "get_metadata":
                if not file_path:
                    return {"error": "No file path provided"}
                return await self._get_metadata(file_path)

            elif action == "list_pages":
                if not file_path:
                    return {"error": "No file path provided"}
                return await self._list_pages(file_path)

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    async def _extract_text(self, file_path: str, kwargs: dict) -> dict[str, Any]:
        try:
            import fitz
            doc = fitz.open(file_path)
            page_numbers = kwargs.get("pages")
            if page_numbers:
                pages = [doc[i] for i in page_numbers if 0 <= i < len(doc)]
            else:
                pages = doc

            text_parts = []
            for page in pages:
                text_parts.append(page.get_text())

            doc.close()
            return {"text": "\n\n".join(text_parts), "page_count": len(doc)}

        except ImportError:
            return {"error": "PDF tool not available. Install: pip install PyMuPDF"}
        except Exception as e:
            return {"error": str(e)}

    async def _extract_images(self, file_path: str) -> dict[str, Any]:
        try:
            import base64  # noqa: F401

            import fitz
            doc = fitz.open(file_path)
            images = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    if base_image:
                        images.append({
                            "page": page_num,
                            "index": img_index,
                            "format": base_image.get("ext", ""),
                            "size": len(base_image.get("image", b"")),
                        })
            doc.close()
            return {"images": images, "count": len(images)}

        except ImportError:
            return {"error": "PDF tool not available. Install: pip install PyMuPDF"}
        except Exception as e:
            return {"error": str(e)}

    async def _get_metadata(self, file_path: str) -> dict[str, Any]:
        try:
            import fitz
            doc = fitz.open(file_path)
            meta = doc.metadata
            doc.close()
            return {
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "subject": meta.get("subject", ""),
                "creator": meta.get("creator", ""),
                "producer": meta.get("producer", ""),
                "page_count": len(doc),
            }
        except ImportError:
            return {"error": "PDF tool not available. Install: pip install PyMuPDF"}
        except Exception as e:
            return {"error": str(e)}

    async def _list_pages(self, file_path: str) -> dict[str, Any]:
        try:
            import fitz
            doc = fitz.open(file_path)
            pages = []
            for i in range(len(doc)):
                page = doc[i]
                pages.append({
                    "page_number": i,
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "text_length": len(page.get_text()),
                })
            doc.close()
            return {"pages": pages, "total": len(pages)}
        except ImportError:
            return {"error": "PDF tool not available. Install: pip install PyMuPDF"}
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
                        "action": {
                            "type": "string",
                            "enum": ["extract_text", "extract_images", "get_metadata", "list_pages"],
                            "description": "PDF action to perform",
                        },
                        "file_path": {"type": "string", "description": "Path to the PDF file"},
                        "pages": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Specific page numbers to extract (0-indexed)",
                        },
                    },
                    "required": ["action", "file_path"],
                },
            },
        }
