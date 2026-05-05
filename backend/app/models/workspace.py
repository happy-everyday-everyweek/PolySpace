from typing import Optional

from pydantic import BaseModel


class WorkspaceDocumentModel(BaseModel):
    id: str
    name: str
    type: str
    path: str
    content: Optional[str] = None
