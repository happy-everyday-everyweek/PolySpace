from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SkillCategory(str, Enum):
    PRODUCTIVITY = "productivity"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    DEVELOPMENT = "development"
    COMMUNICATION = "communication"
    DATA = "data"
    EDUCATION = "education"


class SkillStatus(str, Enum):
    PUBLISHED = "published"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class MarketplaceSkill(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    description: str
    category: SkillCategory
    version: str = "1.0.0"
    author: str = ""
    author_id: str = ""
    icon: str = "package"
    tags: list[str] = Field(default_factory=list)
    entry_point: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    status: SkillStatus = SkillStatus.PUBLISHED
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    reviews: list[dict] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class SkillPublishRequest(BaseModel):
    name: str
    description: str
    category: SkillCategory
    version: str = "1.0.0"
    author: str = ""
    icon: str = "package"
    tags: list[str] = Field(default_factory=list)
    entry_point: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)


class SkillReviewRequest(BaseModel):
    rating: int
    comment: str


_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "skill_marketplace")


_BUILTIN_SKILLS: list[dict] = [
    {
        "name": "seo-optimizer",
        "description": "SEO 内容优化技能，支持关键词分析、内容评分、元标签生成",
        "category": "analysis",
        "version": "1.0.0",
        "author": "PolySpace",
        "icon": "search",
        "tags": ["seo", "marketing", "content"],
    },
    {
        "name": "code-reviewer",
        "description": "AI 代码审查技能，自动检测代码问题、安全漏洞、性能瓶颈",
        "category": "development",
        "version": "1.0.0",
        "author": "PolySpace",
        "icon": "code",
        "tags": ["code", "review", "security"],
    },
    {
        "name": "data-analyzer",
        "description": "数据分析技能，自动生成统计摘要、趋势分析、异常检测",
        "category": "data",
        "version": "1.0.0",
        "author": "PolySpace",
        "icon": "bar-chart",
        "tags": ["data", "analysis", "statistics"],
    },
    {
        "name": "meeting-summarizer",
        "description": "会议纪要生成技能，从会议记录中提取要点、行动项、决策",
        "category": "productivity",
        "version": "1.0.0",
        "author": "PolySpace",
        "icon": "users",
        "tags": ["meeting", "summary", "notes"],
    },
    {
        "name": "email-drafter",
        "description": "邮件草拟技能，根据上下文生成专业邮件回复",
        "category": "communication",
        "version": "1.0.0",
        "author": "PolySpace",
        "icon": "mail",
        "tags": ["email", "draft", "communication"],
    },
    {
        "name": "learning-tutor",
        "description": "个性化学习辅导技能，苏格拉底式提问、知识图谱构建",
        "category": "education",
        "version": "1.0.0",
        "author": "PolySpace",
        "icon": "graduation-cap",
        "tags": ["learning", "tutor", "education"],
    },
    {
        "name": "workflow-automator",
        "description": "工作流自动化技能，将重复操作编排为自动化流程",
        "category": "automation",
        "version": "1.0.0",
        "author": "PolySpace",
        "icon": "workflow",
        "tags": ["automation", "workflow", "efficiency"],
    },
    {
        "name": "creative-writer",
        "description": "创意写作技能，支持故事、诗歌、文案等多种创作风格",
        "category": "creative",
        "version": "1.0.0",
        "author": "PolySpace",
        "icon": "pen-tool",
        "tags": ["writing", "creative", "story"],
    },
]


class SkillMarketplaceService:
    def __init__(self):
        self._skills: dict[str, MarketplaceSkill] = {}
        self._installed: set[str] = set()
        self._load_all()
        self._init_builtins()

    def _load_all(self):
        try:
            if os.path.exists(_DATA_DIR):
                for fname in os.listdir(_DATA_DIR):
                    if fname.endswith(".json"):
                        with open(os.path.join(_DATA_DIR, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            skill = MarketplaceSkill(**data)
                            self._skills[skill.id] = skill
        except Exception:
            pass
        installed_path = os.path.join(_DATA_DIR, "installed.json")
        try:
            if os.path.exists(installed_path):
                with open(installed_path, "r", encoding="utf-8") as f:
                    self._installed = set(json.load(f))
        except Exception:
            pass

    def _init_builtins(self):
        for skill_data in _BUILTIN_SKILLS:
            name = skill_data["name"]
            existing = None
            for s in self._skills.values():
                if s.name == name:
                    existing = s
                    break
            if not existing:
                skill = MarketplaceSkill(**skill_data, author_id="system")
                self._skills[skill.id] = skill
                self._save(skill)

    def _save(self, skill: MarketplaceSkill):
        os.makedirs(_DATA_DIR, exist_ok=True)
        path = os.path.join(_DATA_DIR, f"{skill.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(skill.model_dump(), f, ensure_ascii=False, indent=2)

    def _save_installed(self):
        os.makedirs(_DATA_DIR, exist_ok=True)
        path = os.path.join(_DATA_DIR, "installed.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(self._installed), f)

    async def publish(self, req: SkillPublishRequest, author_id: str = "") -> MarketplaceSkill:
        skill = MarketplaceSkill(
            name=req.name,
            description=req.description,
            category=req.category,
            version=req.version,
            author=req.author,
            author_id=author_id,
            icon=req.icon,
            tags=req.tags,
            entry_point=req.entry_point,
            parameters=req.parameters,
            dependencies=req.dependencies,
        )
        self._skills[skill.id] = skill
        self._save(skill)
        return skill

    async def list_skills(
        self,
        category: Optional[SkillCategory] = None,
        search: Optional[str] = None,
        sort_by: str = "downloads",
        limit: int = 50,
        offset: int = 0,
    ) -> list[MarketplaceSkill]:
        results = list(self._skills.values())
        if category:
            results = [s for s in results if s.category == category]
        if search:
            search_lower = search.lower()
            results = [s for s in results if search_lower in s.name.lower() or search_lower in s.description.lower() or any(search_lower in t.lower() for t in s.tags)]
        if sort_by == "downloads":
            results.sort(key=lambda s: s.downloads, reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda s: s.rating, reverse=True)
        elif sort_by == "newest":
            results.sort(key=lambda s: s.created_at, reverse=True)
        return results[offset : offset + limit]

    async def get_skill(self, skill_id: str) -> Optional[MarketplaceSkill]:
        return self._skills.get(skill_id)

    async def install(self, skill_id: str) -> bool:
        skill = self._skills.get(skill_id)
        if not skill:
            return False
        self._installed.add(skill_id)
        skill.downloads += 1
        self._save(skill)
        self._save_installed()
        return True

    async def uninstall(self, skill_id: str) -> bool:
        if skill_id in self._installed:
            self._installed.discard(skill_id)
            self._save_installed()
            return True
        return False

    async def list_installed(self) -> list[MarketplaceSkill]:
        return [self._skills[sid] for sid in self._installed if sid in self._skills]

    async def review(self, skill_id: str, user_id: str, req: SkillReviewRequest) -> Optional[MarketplaceSkill]:
        skill = self._skills.get(skill_id)
        if not skill:
            return None
        review = {"user_id": user_id, "rating": max(1, min(5, req.rating)), "comment": req.comment, "created_at": datetime.now().isoformat()}
        skill.reviews.append(review)
        total_rating = sum(r["rating"] for r in skill.reviews)
        skill.rating_count = len(skill.reviews)
        skill.rating = round(total_rating / skill.rating_count, 1)
        self._save(skill)
        return skill

    async def delete_skill(self, skill_id: str) -> bool:
        if skill_id in self._skills:
            del self._skills[skill_id]
            self._installed.discard(skill_id)
            path = os.path.join(_DATA_DIR, f"{skill_id}.json")
            if os.path.exists(path):
                os.remove(path)
            self._save_installed()
            return True
        return False


skill_marketplace_service = SkillMarketplaceService()
