import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

ENV_STORE_FILE = "env_overrides.json"

_SECRET_KEYS = {
    "LLM_BASE_MODEL_API_KEY",
    "LLM_STRONG_MODEL_API_KEY",
    "LLM_PERFORMANCE_MODEL_API_KEY",
    "LLM_COST_EFFECTIVE_MODEL_API_KEY",
    "LLM_MULTIMODAL_MODEL_API_KEY",
    "LLM_SCREEN_MODEL_API_KEY",
}

_MASKED_VALUE = "***"

_READONLY_KEYS = {"APP_VERSION"}

_BOOLEAN_KEYS = {"DEBUG", "LOCAL_INFERENCE_ENABLED", "OFFLINE_MAP_ENABLED", "OFFLINE_WIKI_ENABLED"}

_INTEGER_KEYS = {
    "DATABASE_POOL_SIZE",
    "DATABASE_MAX_OVERFLOW",
    "DATABASE_POOL_RECYCLE",
    "LLM_MAX_RETRIES",
    "WS_MAX_CONNECTIONS",
    "WS_MAX_MESSAGE_SIZE",
}

_FLOAT_KEYS = {
    "LLM_REQUEST_TIMEOUT",
    "LLM_RETRY_DELAY",
    "WS_HEARTBEAT_INTERVAL",
    "WS_HEARTBEAT_TIMEOUT",
}

_LIST_KEYS = {"CORS_ORIGINS"}

_ENV_VAR_DEFINITIONS = [
    {
        "key": "DATA_DIR", "label": "数据目录",
        "group": "general", "type": "path",
        "description": "应用数据存储目录",
    },
    {
        "key": "DEBUG", "label": "调试模式",
        "group": "general", "type": "bool",
        "description": "启用调试日志和开发模式",
    },
    {
        "key": "DATABASE_URL", "label": "数据库连接",
        "group": "database", "type": "string",
        "description": "数据库连接字符串，留空使用默认SQLite",
    },
    {
        "key": "DATABASE_POOL_SIZE", "label": "连接池大小",
        "group": "database", "type": "int",
        "description": "数据库连接池大小",
    },
    {
        "key": "DATABASE_MAX_OVERFLOW", "label": "最大溢出连接",
        "group": "database", "type": "int",
        "description": "连接池最大溢出连接数",
    },
    {
        "key": "DATABASE_POOL_RECYCLE", "label": "连接回收时间",
        "group": "database", "type": "int",
        "description": "连接池回收时间(秒)",
    },
    {
        "key": "LLM_REQUEST_TIMEOUT", "label": "请求超时",
        "group": "llm", "type": "float",
        "description": "LLM请求超时时间(秒)",
    },
    {
        "key": "LLM_MAX_RETRIES", "label": "最大重试次数",
        "group": "llm", "type": "int",
        "description": "LLM请求最大重试次数",
    },
    {
        "key": "LLM_RETRY_DELAY", "label": "重试延迟",
        "group": "llm", "type": "float",
        "description": "LLM请求重试延迟(秒)",
    },
    {
        "key": "POLICIES_PATH", "label": "策略文件路径",
        "group": "integration", "type": "path",
        "description": "安全策略YAML文件路径",
    },
    {
        "key": "WS_MAX_CONNECTIONS", "label": "最大WS连接",
        "group": "network", "type": "int",
        "description": "WebSocket最大连接数",
    },
    {
        "key": "WS_HEARTBEAT_INTERVAL", "label": "心跳间隔",
        "group": "network", "type": "float",
        "description": "WebSocket心跳间隔(秒)",
    },
    {
        "key": "WS_HEARTBEAT_TIMEOUT", "label": "心跳超时",
        "group": "network", "type": "float",
        "description": "WebSocket心跳超时(秒)",
    },
    {
        "key": "WS_MAX_MESSAGE_SIZE", "label": "最大消息大小",
        "group": "network", "type": "int",
        "description": "WebSocket最大消息大小(字节)",
    },
    {
        "key": "CORS_ORIGINS", "label": "CORS允许源",
        "group": "network", "type": "list",
        "description": "允许的跨域源列表",
    },
]


class EnvStore:
    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = Path(data_dir or settings.DATA_DIR)
        self._store_path = self._data_dir / ENV_STORE_FILE
        self._overrides: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self._store_path.exists():
            try:
                with open(self._store_path, "r", encoding="utf-8") as f:
                    self._overrides = json.load(f)
                logger.info("Loaded env overrides from %s", self._store_path)
            except Exception as e:
                logger.error("Failed to load env overrides: %s", e)
                self._overrides = {}

    def _save(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._store_path, "w", encoding="utf-8") as f:
                json.dump(self._overrides, f, indent=2, ensure_ascii=False)
            logger.info("Saved env overrides to %s", self._store_path)
        except Exception as e:
            logger.error("Failed to save env overrides: %s", e)

    def get_all(self) -> dict[str, Any]:
        result = {}
        for defn in _ENV_VAR_DEFINITIONS:
            key = defn["key"]
            value = self._get_effective_value(key)
            if defn["type"] == "secret" and value:
                result[key] = _MASKED_VALUE
            else:
                result[key] = value
        return result

    def get_definitions(self) -> list[dict]:
        return list(_ENV_VAR_DEFINITIONS)

    def get_by_group(self) -> dict[str, list[dict]]:
        groups: dict[str, list[dict]] = {}
        for defn in _ENV_VAR_DEFINITIONS:
            group = defn["group"]
            if group not in groups:
                groups[group] = []
            key = defn["key"]
            value = self._get_effective_value(key)
            entry = dict(defn)
            if defn["type"] == "secret" and value:
                entry["value"] = _MASKED_VALUE
                entry["has_value"] = bool(value)
            else:
                entry["value"] = value
                entry["has_value"] = value is not None and value != ""
            groups[group].append(entry)
        return groups

    def update(self, updates: dict[str, Any]) -> dict[str, str]:
        changed: dict[str, str] = {}
        for key, value in updates.items():
            if key in _READONLY_KEYS:
                continue
            defn = self._find_definition(key)
            if not defn:
                continue
            if defn["type"] == "secret" and value == _MASKED_VALUE:
                continue
            if value is None or value == "":
                if key in self._overrides:
                    del self._overrides[key]
                    changed[key] = "removed"
            else:
                converted = self._convert_value(key, value)
                self._overrides[key] = converted
                changed[key] = "updated"
        if changed:
            self._save()
            self._apply_to_runtime()
        return changed

    def _get_effective_value(self, key: str) -> Any:
        if key in self._overrides:
            return self._overrides[key]
        env_key = f"POLYSPACE_{key}"
        env_val = os.environ.get(env_key)
        if env_val is not None:
            return self._convert_value(key, env_val)
        return getattr(settings, key, None)

    def _convert_value(self, key: str, value: Any) -> Any:
        if key in _BOOLEAN_KEYS:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if key in _INTEGER_KEYS:
            return int(value)
        if key in _FLOAT_KEYS:
            return float(value)
        if key in _LIST_KEYS:
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return [s.strip() for s in value.split(",") if s.strip()]
            return value
        return value

    def _apply_to_runtime(self) -> None:
        for key, value in self._overrides.items():
            env_key = f"POLYSPACE_{key}"
            if value is None:
                os.environ.pop(env_key, None)
            else:
                if isinstance(value, list):
                    os.environ[env_key] = json.dumps(value)
                elif isinstance(value, bool):
                    os.environ[env_key] = str(value).lower()
                else:
                    os.environ[env_key] = str(value)

    def _find_definition(self, key: str) -> Optional[dict]:
        for defn in _ENV_VAR_DEFINITIONS:
            if defn["key"] == key:
                return defn
        return None


_env_store: Optional[EnvStore] = None


def get_env_store() -> EnvStore:
    global _env_store
    if _env_store is None:
        _env_store = EnvStore()
        _env_store._apply_to_runtime()
    return _env_store
