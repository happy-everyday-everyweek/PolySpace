from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    DOCUMENT = "document"
    CODE = "code"
    CHART = "chart"
    TABLE = "table"
    SVG = "svg"
    HTML = "html"
    IMAGE = "image"


class ArtifactStatus(str, Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: ArtifactType
    title: str
    content: str
    language: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: ArtifactStatus = ArtifactStatus.COMPLETED
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None
    file_path: Optional[str] = None


class ArtifactCreateRequest(BaseModel):
    type: ArtifactType
    title: str
    content: str
    language: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None


class ArtifactUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "artifacts")


class ArtifactService:
    def __init__(self):
        self._artifacts: dict[str, Artifact] = {}
        self._load_all()

    def _load_all(self):
        try:
            if os.path.exists(_DATA_DIR):
                for fname in os.listdir(_DATA_DIR):
                    if fname.endswith(".json"):
                        with open(os.path.join(_DATA_DIR, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            artifact = Artifact(**data)
                            self._artifacts[artifact.id] = artifact
        except Exception:
            pass

    def _save(self, artifact: Artifact):
        os.makedirs(_DATA_DIR, exist_ok=True)
        path = os.path.join(_DATA_DIR, f"{artifact.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(artifact.model_dump(), f, ensure_ascii=False, indent=2)

    async def create(self, req: ArtifactCreateRequest) -> Artifact:
        artifact = Artifact(
            type=req.type,
            title=req.title,
            content=req.content,
            language=req.language,
            metadata=req.metadata,
            session_id=req.session_id,
        )
        self._artifacts[artifact.id] = artifact
        self._save(artifact)
        return artifact

    async def get(self, artifact_id: str) -> Optional[Artifact]:
        return self._artifacts.get(artifact_id)

    async def list_artifacts(
        self,
        type: Optional[ArtifactType] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Artifact]:
        results = list(self._artifacts.values())
        if type:
            results = [a for a in results if a.type == type]
        if session_id:
            results = [a for a in results if a.session_id == session_id]
        results.sort(key=lambda a: a.created_at, reverse=True)
        return results[offset : offset + limit]

    async def update(self, artifact_id: str, req: ArtifactUpdateRequest) -> Optional[Artifact]:
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            return None
        if req.title is not None:
            artifact.title = req.title
        if req.content is not None:
            artifact.content = req.content
        if req.metadata is not None:
            artifact.metadata.update(req.metadata)
        self._save(artifact)
        return artifact

    async def delete(self, artifact_id: str) -> bool:
        if artifact_id in self._artifacts:
            del self._artifacts[artifact_id]
            path = os.path.join(_DATA_DIR, f"{artifact_id}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        return False

    async def render(self, artifact_id: str) -> Optional[dict]:
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            return None
        rendered = {
            "id": artifact.id,
            "type": artifact.type.value,
            "title": artifact.title,
            "content": artifact.content,
            "language": artifact.language,
            "metadata": artifact.metadata,
            "created_at": artifact.created_at,
        }
        if artifact.type == ArtifactType.CODE:
            rendered["runnable"] = artifact.language in ("python", "javascript", "html")
        elif artifact.type == ArtifactType.HTML:
            rendered["sandbox_srcdoc"] = artifact.content
        elif artifact.type == ArtifactType.SVG:
            rendered["inline_svg"] = artifact.content
        return rendered


artifact_service = ArtifactService()
