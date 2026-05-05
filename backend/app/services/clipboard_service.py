from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ClipboardContentType(str, Enum):
    TEXT = "text"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    CODE = "code"
    IMAGE = "image"


class ClipboardItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    content: str
    content_type: ClipboardContentType = ClipboardContentType.TEXT
    language: Optional[str] = None
    source_device: Optional[str] = None
    analysis: Optional[dict] = None
    suggestions: list[dict] = Field(default_factory=list)
    is_sensitive: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ClipboardCreateRequest(BaseModel):
    content: str
    source_device: Optional[str] = None


_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clipboard")

_SENSITIVE_PATTERNS = [
    re.compile(r"\b\d{16,19}\b"),
    re.compile(r"\b\d{3,4}\s?\d{4}\s?\d{4}\s?\d{4}\b"),
    re.compile(r"(?i)password\s*[:=]\s*\S+"),
    re.compile(r"(?i)token\s*[:=]\s*\S+"),
    re.compile(r"(?i)secret\s*[:=]\s*\S+"),
    re.compile(r"\b\d{6}\b"),
]

_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_PATTERN = re.compile(r"(?:\+?86)?1[3-9]\d{9}")
_CODE_INDICATORS = ["def ", "function ", "class ", "import ", "const ", "let ", "var ", "#include", "func ", "package "]


class ClipboardService:
    def __init__(self):
        self._items: dict[str, ClipboardItem] = {}
        self._load_all()

    def _load_all(self):
        try:
            if os.path.exists(_DATA_DIR):
                for fname in os.listdir(_DATA_DIR):
                    if fname.endswith(".json"):
                        with open(os.path.join(_DATA_DIR, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            item = ClipboardItem(**data)
                            self._items[item.id] = item
        except Exception:
            pass

    def _save(self, item: ClipboardItem):
        os.makedirs(_DATA_DIR, exist_ok=True)
        path = os.path.join(_DATA_DIR, f"{item.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(item.model_dump(), f, ensure_ascii=False, indent=2)

    def _classify(self, content: str) -> tuple[ClipboardContentType, Optional[str]]:
        if _URL_PATTERN.search(content):
            return ClipboardContentType.URL, None
        if _EMAIL_PATTERN.search(content):
            return ClipboardContentType.EMAIL, None
        if _PHONE_PATTERN.search(content):
            return ClipboardContentType.PHONE, None
        for indicator in _CODE_INDICATORS:
            if indicator in content:
                lang = "python" if indicator in ("def ", "import ") else "javascript" if indicator in ("const ", "let ", "var ", "function ") else "other"
                return ClipboardContentType.CODE, lang
        return ClipboardContentType.TEXT, None

    def _check_sensitive(self, content: str) -> bool:
        for pattern in _SENSITIVE_PATTERNS:
            if pattern.search(content):
                return True
        return False

    def _generate_suggestions(self, content: str, content_type: ClipboardContentType) -> list[dict]:
        suggestions = []
        if content_type == ClipboardContentType.URL:
            suggestions.append({"action": "open_url", "label": "打开链接", "data": {"url": content.strip()}})
            suggestions.append({"action": "save_to_knowledge", "label": "保存到知识库", "data": {"url": content.strip()}})
        elif content_type == ClipboardContentType.EMAIL:
            suggestions.append({"action": "send_email", "label": "发送邮件", "data": {"to": content.strip()}})
            suggestions.append({"action": "add_contact", "label": "添加联系人", "data": {"email": content.strip()}})
        elif content_type == ClipboardContentType.PHONE:
            suggestions.append({"action": "call", "label": "拨打电话", "data": {"phone": content.strip()}})
            suggestions.append({"action": "send_sms", "label": "发送短信", "data": {"phone": content.strip()}})
        elif content_type == ClipboardContentType.CODE:
            suggestions.append({"action": "open_in_editor", "label": "在编辑器中打开", "data": {"code": content}})
            suggestions.append({"action": "explain_code", "label": "AI 解释代码", "data": {"code": content}})
            suggestions.append({"action": "format_code", "label": "格式化代码", "data": {"code": content}})
        else:
            suggestions.append({"action": "create_memo", "label": "创建备忘录", "data": {"content": content}})
            suggestions.append({"action": "create_todo", "label": "创建待办", "data": {"content": content}})
            suggestions.append({"action": "translate", "label": "AI 翻译", "data": {"text": content}})
            suggestions.append({"action": "summarize", "label": "AI 总结", "data": {"text": content}})
        return suggestions

    async def add(self, req: ClipboardCreateRequest) -> ClipboardItem:
        content = req.content.strip()
        if not content:
            raise ValueError("Content cannot be empty")
        content_type, language = self._classify(content)
        is_sensitive = self._check_sensitive(content)
        suggestions = [] if is_sensitive else self._generate_suggestions(content, content_type)
        analysis = {
            "length": len(content),
            "word_count": len(content.split()),
            "has_chinese": bool(re.search(r"[\u4e00-\u9fff]", content)),
            "has_english": bool(re.search(r"[a-zA-Z]", content)),
        }
        item = ClipboardItem(
            content=content,
            content_type=content_type,
            language=language,
            source_device=req.source_device,
            analysis=analysis,
            suggestions=suggestions,
            is_sensitive=is_sensitive,
        )
        self._items[item.id] = item
        self._save(item)
        return item

    async def get(self, item_id: str) -> Optional[ClipboardItem]:
        return self._items.get(item_id)

    async def list_items(
        self,
        content_type: Optional[ClipboardContentType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ClipboardItem]:
        results = list(self._items.values())
        if content_type:
            results = [i for i in results if i.content_type == content_type]
        results.sort(key=lambda i: i.created_at, reverse=True)
        return results[offset : offset + limit]

    async def delete(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            path = os.path.join(_DATA_DIR, f"{item_id}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        return False

    async def clear(self) -> int:
        count = len(self._items)
        self._items.clear()
        if os.path.exists(_DATA_DIR):
            for fname in os.listdir(_DATA_DIR):
                if fname.endswith(".json"):
                    os.remove(os.path.join(_DATA_DIR, fname))
        return count


clipboard_service = ClipboardService()
