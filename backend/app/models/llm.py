from typing import Optional

from pydantic import BaseModel


class LLMModelConfigModel(BaseModel):
    name: str
    tier: str
    provider: str
    model_id: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    capabilities: list[str] = []
    scene_description: Optional[str] = None
