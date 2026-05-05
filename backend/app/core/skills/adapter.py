from __future__ import annotations

from typing import Any

from app.core.skills.loader import SkillDef, SkillLoader, skill_loader
from app.core.tool.base import BaseTool, ToolState


class SkillToolAdapter(BaseTool):
    def __init__(self, skill_def: SkillDef, loader: SkillLoader | None = None) -> None:
        super().__init__(
            name=f"skill_{skill_def.name}",
            description=skill_def.description,
        )
        self._skill_def = skill_def
        self._loader = loader or skill_loader
        self._state = ToolState.INACTIVE

    @property
    def skill_def(self) -> SkillDef:
        return self._skill_def

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs: Any) -> Any:
        return await self._loader.execute_skill(self._skill_def.name, **kwargs)

    async def _on_hibernate(self) -> None:
        pass

    def get_definition(self) -> dict[str, Any]:
        properties = {}
        required = []
        for param_name, param_info in self._skill_def.parameters.items():
            properties[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", ""),
            }
            if param_info.get("required", False):
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
