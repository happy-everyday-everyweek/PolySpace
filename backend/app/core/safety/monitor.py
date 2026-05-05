from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class ResourceBudget:
    max_tokens_per_request: int = 100000
    max_requests_per_minute: int = 60
    max_tool_calls_per_minute: int = 30
    max_concurrent_tools: int = 5


@dataclass
class ToolCallRecord:
    tool_name: str
    timestamp: datetime = field(default_factory=datetime.now)


class RuntimeMonitor:
    MAX_HISTORY = 1000

    def __init__(self, budget: Optional[ResourceBudget] = None):
        self._budget = budget or ResourceBudget()
        self._tool_call_history: deque[ToolCallRecord] = deque(maxlen=self.MAX_HISTORY)
        self._jitter_threshold = 5
        self._jitter_window = timedelta(seconds=30)
        self._stats_cache: Optional[dict] = None
        self._stats_cache_time: Optional[datetime] = None

    def record_tool_call(self, tool_name: str) -> None:
        self._tool_call_history.append(ToolCallRecord(tool_name=tool_name))
        self._stats_cache = None

    def detect_jitter(self) -> bool:
        now = datetime.now()
        window_start = now - self._jitter_window
        recent_calls = [
            r for r in self._tool_call_history if r.timestamp >= window_start
        ]
        if len(recent_calls) < self._jitter_threshold:
            return False
        unique_tools = len(set(r.tool_name for r in recent_calls))
        return unique_tools >= self._jitter_threshold

    def check_rate_limit(self) -> bool:
        now = datetime.now()
        window_start = now - timedelta(minutes=1)
        recent_calls = [
            r for r in self._tool_call_history if r.timestamp >= window_start
        ]
        return len(recent_calls) < self._budget.max_tool_calls_per_minute

    def verify_determinism(self, expected: str, actual: str) -> bool:
        return expected.strip() == actual.strip()

    def get_stats(self) -> dict:
        now = datetime.now()
        if self._stats_cache and self._stats_cache_time:
            if (now - self._stats_cache_time).total_seconds() < 5:
                return self._stats_cache

        recent_minute = [r for r in self._tool_call_history if r.timestamp >= now - timedelta(minutes=1)]
        self._stats_cache = {
            "total_calls": len(self._tool_call_history),
            "calls_last_minute": len(recent_minute),
            "jitter_detected": self.detect_jitter(),
            "rate_limit_ok": self.check_rate_limit(),
        }
        self._stats_cache_time = now
        return self._stats_cache


runtime_monitor = RuntimeMonitor()
