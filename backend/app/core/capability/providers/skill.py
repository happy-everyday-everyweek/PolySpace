from __future__ import annotations

from typing import Any, Optional

from app.core.capability.base import (
    CapabilityCallContext,
    CapabilityCategory,
    CapabilityMeta,
    CapabilityPlatform,
    CapabilityProvider,
    CapabilityResult,
    CapabilitySource,
)

_CATEGORY_MAP: dict[str, CapabilityCategory] = {
    "general": CapabilityCategory.PRODUCTIVITY,
    "coding": CapabilityCategory.DEVELOPMENT,
    "writing": CapabilityCategory.CONTENT,
    "data": CapabilityCategory.ANALYTICS,
    "research": CapabilityCategory.KNOWLEDGE,
}


class SkillProvider(CapabilityProvider):
    def __init__(self) -> None:
        self._skills: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "skill"

    @property
    def source_type(self) -> CapabilitySource:
        return CapabilitySource.SKILL

    def _get_loader(self):
        from app.core.skills.loader import skill_loader
        return skill_loader

    async def discover(self) -> list[CapabilityMeta]:
        loader = self._get_loader()
        skills = loader.discover()
        self._skills = {s.name: s for s in skills}
        result: list[CapabilityMeta] = []
        for skill_def in skills:
            category_str = getattr(skill_def, "category", "general")
            meta = CapabilityMeta(
                name=f"skill_{skill_def.name}",
                display_name=skill_def.name,
                description=skill_def.description,
                source_type=CapabilitySource.SKILL,
                category=_CATEGORY_MAP.get(category_str, CapabilityCategory.PRODUCTIVITY),
                platforms=[CapabilityPlatform.BACKEND],
                parameters=getattr(skill_def, "parameters", {}),
                version=getattr(skill_def, "version", "1.0.0"),
                provider_name=self.name,
            )
            result.append(meta)
        return result

    async def activate(self, capability_name: str) -> None:
        pass

    async def execute(
        self,
        capability_name: str,
        params: dict[str, Any],
        context: CapabilityCallContext,
    ) -> CapabilityResult:
        skill_name = capability_name.removeprefix("skill_")
        loader = self._get_loader()
        try:
            data = await loader.execute_skill(skill_name, **params)
            return CapabilityResult(success=True, data=data)
        except Exception as e:
            return CapabilityResult(success=False, error=str(e))

    async def deactivate(self, capability_name: str) -> None:
        pass

    async def health_check(self, capability_name: str) -> bool:
        skill_name = capability_name.removeprefix("skill_")
        loader = self._get_loader()
        return loader.get_skill(skill_name) is not None

    def get_capability(self, name: str) -> Optional[CapabilityMeta]:
        skill_name = name.removeprefix("skill_")
        skill_def = self._skills.get(skill_name)
        if not skill_def:
            return None
        category_str = getattr(skill_def, "category", "general")
        return CapabilityMeta(
            name=name,
            display_name=skill_def.name,
            description=skill_def.description,
            source_type=CapabilitySource.SKILL,
            category=_CATEGORY_MAP.get(category_str, CapabilityCategory.PRODUCTIVITY),
            platforms=[CapabilityPlatform.BACKEND],
            parameters=getattr(skill_def, "parameters", {}),
            provider_name=self.name,
        )
