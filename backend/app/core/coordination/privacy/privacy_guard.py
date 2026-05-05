import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DataSensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    TOP_SECRET = "top_secret"


@dataclass
class ConsentRecord:
    service_name: str
    data_types: list[str]
    channels: list[str]
    granted_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    revoked: bool = False

    def to_dict(self) -> dict:
        return {
            "service_name": self.service_name,
            "data_types": self.data_types,
            "channels": self.channels,
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
        }


SENSITIVE_PATTERNS = [
    "password", "passwd", "pwd",
    "credit_card", "card_number", "cvv", "cvc",
    "ssn", "social_security",
    "pin_code", "otp",
    "bank_account", "iban",
]


class PrivacyGuard:
    def __init__(self):
        self._data_sensitivity: dict[str, DataSensitivity] = {}
        self._audit_log: list[dict] = []
        self._max_audit = 200
        self._user_preferences: dict = {
            "allow_screen_analysis": True,
            "allow_notification_analysis": True,
            "allow_location_tracking": False,
            "allow_clipboard_analysis": True,
            "data_retention_days": 30,
        }
        self._sensitivity_rules = {
            "screen": DataSensitivity.CONFIDENTIAL,
            "notification": DataSensitivity.INTERNAL,
            "location": DataSensitivity.TOP_SECRET,
            "clipboard": DataSensitivity.CONFIDENTIAL,
            "email": DataSensitivity.CONFIDENTIAL,
            "chat": DataSensitivity.INTERNAL,
            "calendar": DataSensitivity.INTERNAL,
            "device_state": DataSensitivity.PUBLIC,
        }

    def classify_data(self, data_type: str, content: str = "") -> DataSensitivity:
        base = self._sensitivity_rules.get(data_type, DataSensitivity.INTERNAL)
        if content:
            content_lower = content.lower()
            for pattern in SENSITIVE_PATTERNS:
                if pattern in content_lower:
                    return DataSensitivity.TOP_SECRET
        return base

    def sanitize(self, content: str) -> str:
        sanitized = content
        for pattern in SENSITIVE_PATTERNS:
            if pattern in sanitized.lower():
                sanitized = "[REDACTED]"
                break
        return sanitized

    def check_access(self, service_name: str, data_type: str) -> bool:
        pref_key = f"allow_{data_type}_analysis"
        if pref_key in self._user_preferences:
            return self._user_preferences[pref_key]
        sensitivity = self._sensitivity_rules.get(data_type, DataSensitivity.INTERNAL)
        return sensitivity in (DataSensitivity.PUBLIC, DataSensitivity.INTERNAL)

    def log_access(self, service_name: str, data_type: str, action: str, granted: bool) -> None:
        self._audit_log.append({
            "service": service_name,
            "data_type": data_type,
            "action": action,
            "granted": granted,
            "timestamp": time.time(),
        })
        if len(self._audit_log) > self._max_audit:
            self._audit_log = self._audit_log[-self._max_audit:]

    def set_preference(self, key: str, value) -> None:
        self._user_preferences[key] = value

    def get_preferences(self) -> dict:
        return dict(self._user_preferences)

    def get_audit_log(self, limit: int = 50) -> list[dict]:
        return self._audit_log[-limit:]


class ConsentManager:
    def __init__(self):
        self._consents: dict[str, ConsentRecord] = {}

    def grant_consent(self, service_name: str, data_types: list[str], channels: list[str], expires_in: float = 0) -> ConsentRecord:
        record = ConsentRecord(
            service_name=service_name,
            data_types=data_types,
            channels=channels,
            expires_at=time.time() + expires_in if expires_in > 0 else 0,
        )
        self._consents[service_name] = record
        return record

    def revoke_consent(self, service_name: str) -> bool:
        record = self._consents.get(service_name)
        if record:
            record.revoked = True
            return True
        return False

    def revoke_all(self) -> int:
        count = 0
        for record in self._consents.values():
            if not record.revoked:
                record.revoked = True
                count += 1
        return count

    def check_consent(self, service_name: str, data_type: str = "", channel: str = "") -> bool:
        record = self._consents.get(service_name)
        if not record or record.revoked:
            return False
        if record.expires_at > 0 and time.time() > record.expires_at:
            record.revoked = True
            return False
        if data_type and data_type not in record.data_types:
            return False
        if channel and channel not in record.channels:
            return False
        return True

    def list_consents(self) -> list[dict]:
        return [r.to_dict() for r in self._consents.values()]


class LocalFirstStrategy:
    def __init__(self):
        self._local_processing_ratio: float = 0.6
        self._cloud_threshold = DataSensitivity.CONFIDENTIAL
        self._cache: dict[str, dict] = {}
        self._max_cache = 100

    def should_process_locally(self, data_type: str, content: str = "") -> bool:
        sensitivity = DataSensitivity.INTERNAL
        if data_type in ("location", "clipboard"):
            sensitivity = DataSensitivity.CONFIDENTIAL
        if content:
            for pattern in SENSITIVE_PATTERNS:
                if pattern in content.lower():
                    return True
        return sensitivity.value >= self._cloud_threshold.value

    def get_local_ratio(self) -> float:
        return self._local_processing_ratio

    def cache_result(self, key: str, result: dict) -> None:
        self._cache[key] = {"result": result, "timestamp": time.time()}
        if len(self._cache) > self._max_cache:
            oldest = min(self._cache, key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest]

    def get_cached(self, key: str) -> Optional[dict]:
        entry = self._cache.get(key)
        if entry and (time.time() - entry["timestamp"]) < 300:
            return entry["result"]
        return None


_guard: Optional[PrivacyGuard] = None
_consent: Optional[ConsentManager] = None
_local: Optional[LocalFirstStrategy] = None


def get_privacy_guard() -> PrivacyGuard:
    global _guard
    if _guard is None:
        _guard = PrivacyGuard()
    return _guard


def get_consent_manager() -> ConsentManager:
    global _consent
    if _consent is None:
        _consent = ConsentManager()
    return _consent


def get_local_first() -> LocalFirstStrategy:
    global _local
    if _local is None:
        _local = LocalFirstStrategy()
    return _local
