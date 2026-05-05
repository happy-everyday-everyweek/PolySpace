import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import APIRouter

logger = logging.getLogger(__name__)


@dataclass
class MetricCounter:
    name: str
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "labels": self.labels}


@dataclass
class MetricHistogram:
    name: str
    _values: list[float] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)

    def observe(self, value: float) -> None:
        self._values.append(value)

    @property
    def count(self) -> int:
        return len(self._values)

    @property
    def sum(self) -> float:
        return sum(self._values)

    @property
    def avg(self) -> float:
        return self.sum / self.count if self.count > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "sum": round(self.sum, 3),
            "avg": round(self.avg, 3),
            "labels": self.labels,
        }


class MetricsCollector:
    def __init__(self):
        self._counters: dict[str, MetricCounter] = {}
        self._histograms: dict[str, MetricHistogram] = {}
        self._start_time: float = time.monotonic()

    def counter(self, name: str, labels: Optional[dict[str, str]] = None) -> MetricCounter:
        key = f"{name}:{labels}"
        if key not in self._counters:
            self._counters[key] = MetricCounter(name=name, labels=labels or {})
        return self._counters[key]

    def histogram(self, name: str, labels: Optional[dict[str, str]] = None) -> MetricHistogram:
        key = f"{name}:{labels}"
        if key not in self._histograms:
            self._histograms[key] = MetricHistogram(name=name, labels=labels or {})
        return self._histograms[key]

    def time_since_start(self) -> float:
        return time.monotonic() - self._start_time

    def collect(self) -> dict[str, Any]:
        return {
            "uptime_seconds": round(self.time_since_start(), 1),
            "counters": [c.to_dict() for c in self._counters.values()],
            "histograms": [h.to_dict() for h in self._histograms.values()],
        }


metrics = MetricsCollector()

router = APIRouter()


@router.get("")
async def get_metrics():
    return metrics.collect()


class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.monotonic()
        await self.app(scope, receive, send)
        duration = time.monotonic() - start

        path = scope.get("path", "")
        method = scope.get("method", "")
        status = None
        for msg in scope.get("asgi", {}).get("http_response_started", []):
            if isinstance(msg, dict) and "status" in msg:
                status = msg["status"]

        metrics.counter("http_requests_total", {"method": method, "path": path}).inc()
        metrics.histogram("http_request_duration_seconds", {"method": method, "path": path}).observe(duration)

        if status and status >= 500:
            metrics.counter("http_errors_total", {"method": method, "path": path, "status": str(status)}).inc()
