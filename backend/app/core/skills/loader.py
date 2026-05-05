from __future__ import annotations

import asyncio
import importlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillDef:
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    category: str = "general"
    entry_point: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    file_path: str = ""


class SkillLoader:
    def __init__(self, skills_dir: str | None = None) -> None:
        if skills_dir is None:
            skills_dir = os.path.join(os.getcwd(), "skills")
        self._skills_dir = skills_dir
        self._skills: dict[str, SkillDef] = {}
        self._loaded: dict[str, Any] = {}

    def discover(self) -> list[SkillDef]:
        skills_path = Path(self._skills_dir)
        if not skills_path.exists():
            return []

        discovered = []
        for yaml_file in skills_path.rglob("*.yaml"):
            skill = self._parse_skill_yaml(str(yaml_file))
            if skill:
                self._skills[skill.name] = skill
                discovered.append(skill)

        for yaml_file in skills_path.rglob("*.yml"):
            skill = self._parse_skill_yaml(str(yaml_file))
            if skill and skill.name not in self._skills:
                self._skills[skill.name] = skill
                discovered.append(skill)

        return discovered

    def _parse_skill_yaml(self, file_path: str) -> SkillDef | None:
        try:
            import yaml
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "name" not in data:
                return None

            return SkillDef(
                name=data["name"],
                description=data.get("description", ""),
                version=data.get("version", "1.0.0"),
                author=data.get("author", ""),
                category=data.get("category", "general"),
                entry_point=data.get("entry_point", ""),
                parameters=data.get("parameters", {}),
                file_path=file_path,
            )
        except Exception:
            return None

    def get_skill(self, name: str) -> SkillDef | None:
        return self._skills.get(name)

    def list_skills(self) -> list[SkillDef]:
        return list(self._skills.values())

    async def execute_skill(self, name: str, **kwargs: Any) -> Any:
        skill = self._skills.get(name)
        if not skill:
            raise KeyError(f"Skill '{name}' not found")

        if name in self._loaded:
            handler = self._loaded[name]
        else:
            handler = self._load_skill_module(skill)
            self._loaded[name] = handler

        if handler is None:
            raise RuntimeError(f"Failed to load skill module: {name}")

        if asyncio.iscoroutinefunction(handler):
            return await handler(**kwargs)
        return handler(**kwargs)

    def _load_skill_module(self, skill: SkillDef) -> Any | None:
        if not skill.entry_point:
            return None

        try:
            skill_dir = str(Path(skill.file_path).parent)
            module_path = Path(skill_dir) / skill.entry_point

            if module_path.exists():
                import sys
                if skill_dir not in sys.path:
                    sys.path.insert(0, skill_dir)

                module_name = skill.entry_point.replace(".py", "").replace("/", ".")
                spec = importlib.util.spec_from_file_location(module_name, str(module_path))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return getattr(module, "execute", getattr(module, "run", None))

            parts = skill.entry_point.split(":")
            if len(parts) == 2:
                module_name, func_name = parts
                module = importlib.import_module(module_name)
                return getattr(module, func_name, None)

        except Exception:
            pass

        return None

    def register_skill(self, skill: SkillDef) -> None:
        self._skills[skill.name] = skill

    def unregister_skill(self, name: str) -> bool:
        if name in self._skills:
            del self._skills[name]
            self._loaded.pop(name, None)
            return True
        return False


skill_loader = SkillLoader()
