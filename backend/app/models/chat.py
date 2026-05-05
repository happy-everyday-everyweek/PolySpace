from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatMessageModel(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    tool_calls: list[dict] = []
    tool_results: list[dict] = []
    created_at: datetime = datetime.now()


class ChatSessionModel(BaseModel):
    id: str
    title: Optional[str] = None
    mode: str = "agent"
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
