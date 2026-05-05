import json
import logging
from pathlib import Path
from typing import Optional

from app.config import settings
from app.core.llm.models import ModelConfig, ModelDispatcherConfig, ModelTier

logger = logging.getLogger(__name__)

CONFIG_FILE = "llm_config.json"


class ModelConfigStore:
    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = Path(data_dir or settings.DATA_DIR)
        self._config_path = self._data_dir / CONFIG_FILE
        self._config_data: dict = {}
        self._load()

    def _load(self) -> None:
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config_data = json.load(f)
                logger.info("Loaded LLM config from %s", self._config_path)
            except Exception as e:
                logger.error("Failed to load LLM config: %s", e)
                self._config_data = {}
        else:
            self._config_data = {}

    def _save(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            logger.info("Saved LLM config to %s", self._config_path)
        except Exception as e:
            logger.error("Failed to save LLM config: %s", e)

    def get_flat_config(self) -> dict:
        return dict(self._config_data)

    def update_flat_config(self, updates: dict) -> None:
        for key, value in updates.items():
            if value is not None:
                self._config_data[key] = value
            elif key in self._config_data:
                del self._config_data[key]
        self._save()

    def get_dispatcher_config(self) -> ModelDispatcherConfig:
        base_model = self._build_model_config("base")
        if base_model is None:
            base_model_name = settings.LLM_BASE_MODEL or "default"
            base_model = ModelConfig(
                name=base_model_name,
                tier=ModelTier.BASE,
                provider="litellm",
                model_id=base_model_name,
            )

        strong_model = self._build_model_config("strong")
        performance_model = self._build_model_config("performance")
        cost_effective_model = self._build_model_config("cost_effective")

        vertical_models = []
        for tier_key, model_tier in [
            ("multimodal", ModelTier.VERTICAL_MULTIMODAL),
            ("screen", ModelTier.VERTICAL_SCREEN),
        ]:
            vm = self._build_model_config(tier_key, model_tier)
            if vm:
                vertical_models.append(vm)

        return ModelDispatcherConfig(
            base_model=base_model,
            strong_model=strong_model,
            performance_model=performance_model,
            cost_effective_model=cost_effective_model,
            vertical_models=vertical_models,
        )

    def _build_model_config(
        self, tier_prefix: str, tier: Optional[ModelTier] = None
    ) -> Optional[ModelConfig]:
        model_id = self._config_data.get(f"{tier_prefix}_model", "")
        if not model_id:
            env_fallback = {
                "base": settings.LLM_BASE_MODEL,
                "strong": settings.LLM_STRONG_MODEL,
                "performance": settings.LLM_PERFORMANCE_MODEL,
                "cost_effective": settings.LLM_COST_EFFECTIVE_MODEL,
                "multimodal": settings.LLM_MULTIMODAL_MODEL,
                "screen": settings.LLM_SCREEN_MODEL,
            }
            model_id = env_fallback.get(tier_prefix, "")

        if not model_id:
            return None

        if tier is None:
            tier_map = {
                "base": ModelTier.BASE,
                "strong": ModelTier.STRONG,
                "performance": ModelTier.PERFORMANCE,
                "cost_effective": ModelTier.COST_EFFECTIVE,
            }
            tier = tier_map.get(tier_prefix, ModelTier.BASE)

        provider = self._config_data.get(f"{tier_prefix}_provider", "")
        api_key = self._config_data.get(f"{tier_prefix}_api_key", "")
        api_base = self._config_data.get(f"{tier_prefix}_api_base", "")

        if not provider:
            provider = self._detect_provider(model_id, api_base)

        return ModelConfig(
            name=model_id,
            tier=tier,
            provider=provider,
            model_id=model_id,
            api_key=api_key or None,
            api_base=api_base or None,
        )

    def _detect_provider(self, model_id: str, api_base: str = "") -> str:
        if api_base and "ollama" in api_base.lower():
            return "ollama"
        if api_base and "anthropic" in api_base.lower():
            return "anthropic"
        if model_id.startswith("claude"):
            return "anthropic"
        if model_id.startswith("gpt") or model_id.startswith("o1") or model_id.startswith("o3"):
            return "openai"
        if model_id.startswith("glm") or model_id.startswith("chatglm"):
            return "zhipu"
        if model_id.startswith("qwen"):
            return "qwen"
        if model_id.startswith("deepseek"):
            return "deepseek"
        return "openai"


_model_config_store: Optional[ModelConfigStore] = None


def get_model_config_store() -> ModelConfigStore:
    global _model_config_store
    if _model_config_store is None:
        _model_config_store = ModelConfigStore()
    return _model_config_store
