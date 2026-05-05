
from pydantic import BaseModel


class ToolModel(BaseModel):
    name: str
    description: str
    state: str = "inactive"
    parameters: dict = {}
