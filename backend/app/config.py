import os
import sys
from pathlib import Path
from typing import Optional

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings


def _default_data_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return str(Path(base) / "PolySpace" / "data")
    if sys.platform == "darwin":
        return str(Path.home() / "Library" / "Application Support" / "PolySpace" / "data")
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return str(Path(xdg) / "PolySpace" / "data")
    return str(Path.home() / ".local" / "share" / "PolySpace" / "data")


class Settings(BaseSettings):
    APP_NAME: str = "PolySpace"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATA_DIR: str = _default_data_dir()

    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_RECYCLE: int = 3600

    LLM_BASE_MODEL: str = ""
    LLM_STRONG_MODEL: Optional[str] = None
    LLM_PERFORMANCE_MODEL: Optional[str] = None
    LLM_COST_EFFECTIVE_MODEL: Optional[str] = None
    LLM_MULTIMODAL_MODEL: Optional[str] = None
    LLM_SCREEN_MODEL: Optional[str] = None
    LLM_REQUEST_TIMEOUT: float = 60.0
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0

    GITHUB_TOKEN: Optional[SecretStr] = None
    POLICIES_PATH: str = "./policies/POLICIES.yaml"
    AGENT_EXECUTION_MODE: str = "auto"

    WS_MAX_CONNECTIONS: int = 100
    WS_HEARTBEAT_INTERVAL: float = 30.0
    WS_HEARTBEAT_TIMEOUT: float = 60.0
    WS_MAX_MESSAGE_SIZE: int = 1048576

    CORS_ORIGINS: list[str] = []

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def set_database_url(cls, v: str, info) -> str:
        if v:
            return v
        data_dir = info.data.get("DATA_DIR", _default_data_dir())
        db_path = Path(data_dir) / "polyspace.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path}"

    @field_validator("LLM_BASE_MODEL")
    @classmethod
    def validate_base_model(cls, v: str) -> str:
        if not v and not _is_test_mode():
            import warnings
            warnings.warn(
                "POLYSPACE_LLM_BASE_MODEL is not set. LLM features will not work.",
                stacklevel=2,
            )
        return v

    @property
    def effective_data_dir(self) -> Path:
        return Path(self.DATA_DIR)

    @property
    def memory_dir(self) -> Path:
        return self.effective_data_dir / "memory"

    @property
    def dreams_dir(self) -> Path:
        return self.effective_data_dir / "dreams"

    @property
    def evolution_dir(self) -> Path:
        return self.effective_data_dir / "evolution"

    @property
    def cron_store_path(self) -> Path:
        return self.effective_data_dir / "cron_jobs.json"

    @property
    def github_token_plain(self) -> Optional[str]:
        if self.GITHUB_TOKEN:
            return self.GITHUB_TOKEN.get_secret_value()
        return None

    model_config = {"env_prefix": "POLYSPACE_", "extra": "ignore"}


_test_mode = False


def _is_test_mode() -> bool:
    return _test_mode


def set_test_mode(mode: bool = True) -> None:
    global _test_mode
    _test_mode = mode


def _load_persisted_env() -> None:
    import json as _json

    data_dir = Path(os.environ.get("POLYSPACE_DATA_DIR", "") or _default_data_dir())

    env_store_path = data_dir / "env_overrides.json"
    if env_store_path.exists():
        try:
            with open(env_store_path, "r", encoding="utf-8") as f:
                overrides = _json.load(f)
            for key, value in overrides.items():
                env_key = f"POLYSPACE_{key}"
                if value is None:
                    os.environ.pop(env_key, None)
                elif isinstance(value, list):
                    os.environ[env_key] = _json.dumps(value)
                elif isinstance(value, bool):
                    os.environ[env_key] = str(value).lower()
                else:
                    os.environ[env_key] = str(value)
        except Exception:
            pass

    model_config_path = data_dir / "llm_config.json"
    if model_config_path.exists():
        try:
            with open(model_config_path, "r", encoding="utf-8") as f:
                config_data = _json.load(f)
            model_env_map = {
                "base_model": "POLYSPACE_LLM_BASE_MODEL",
                "strong_model": "POLYSPACE_LLM_STRONG_MODEL",
                "performance_model": "POLYSPACE_LLM_PERFORMANCE_MODEL",
                "cost_effective_model": "POLYSPACE_LLM_COST_EFFECTIVE_MODEL",
                "multimodal_model": "POLYSPACE_LLM_MULTIMODAL_MODEL",
                "screen_model": "POLYSPACE_LLM_SCREEN_MODEL",
            }
            for config_key, env_key in model_env_map.items():
                value = config_data.get(config_key, "")
                if value and env_key not in os.environ:
                    os.environ[env_key] = str(value)
        except Exception:
            pass


_load_persisted_env()

settings = Settings()
