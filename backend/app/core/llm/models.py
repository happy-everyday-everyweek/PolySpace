from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ModelTier(str, Enum):
    BASE = "base"
    STRONG = "strong"
    PERFORMANCE = "performance"
    COST_EFFECTIVE = "cost_effective"
    VERTICAL_MULTIMODAL = "vertical_multimodal"
    VERTICAL_SCREEN = "vertical_screen"
    VERTICAL_CUSTOM = "vertical_custom"


class ModelConfig(BaseModel):
    name: str
    tier: ModelTier
    provider: str
    model_id: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    capabilities: list[str] = []
    scene_description: Optional[str] = None


class ModelDispatcherConfig(BaseModel):
    base_model: ModelConfig
    strong_model: Optional[ModelConfig] = None
    performance_model: Optional[ModelConfig] = None
    cost_effective_model: Optional[ModelConfig] = None
    vertical_models: list[ModelConfig] = []

    @property
    def has_tier_models(self) -> bool:
        return any([
            self.strong_model,
            self.performance_model,
            self.cost_effective_model,
        ])

    def get_model_by_tier(self, tier: ModelTier) -> Optional[ModelConfig]:
        tier_map = {
            ModelTier.BASE: self.base_model,
            ModelTier.STRONG: self.strong_model,
            ModelTier.PERFORMANCE: self.performance_model,
            ModelTier.COST_EFFECTIVE: self.cost_effective_model,
        }
        if tier in tier_map:
            return tier_map[tier]
        for vm in self.vertical_models:
            if vm.tier == tier:
                return vm
        return None

    def get_vertical_model(self, name: str) -> Optional[ModelConfig]:
        for vm in self.vertical_models:
            if vm.name == name:
                return vm
        return None

    def get_multimodal_model(self) -> Optional[ModelConfig]:
        for vm in self.vertical_models:
            if vm.tier == ModelTier.VERTICAL_MULTIMODAL:
                return vm
        return None

    def get_screen_model(self) -> Optional[ModelConfig]:
        for vm in self.vertical_models:
            if vm.tier == ModelTier.VERTICAL_SCREEN:
                return vm
        return None
