import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.config import settings

logger = logging.getLogger(__name__)

try:
    from croniter import croniter
    _HAS_CRONITER = True
except ImportError:
    _HAS_CRONITER = False


class CronScheduleKind(Enum):
    AT = "at"
    EVERY = "every"
    CRON = "cron"


@dataclass
class CronSchedule:
    kind: CronScheduleKind = CronScheduleKind.EVERY
    at: str = ""
    every_ms: int = 60000
    anchor_ms: float | None = None
    cron_expr: str = ""
    tz: str = "UTC"
    stagger_ms: int = 0


@dataclass
class CronPayload:
    kind: str = "systemEvent"
    text: str = ""
    message: str = ""
    model: str | None = None
    timeout_seconds: float = 300.0
    tools_allow: list[str] = field(default_factory=list)


@dataclass
class CronDelivery:
    mode: str = "none"
    channel: str = ""
    to: str = ""


@dataclass
class CronJobState:
    next_run_at_ms: float | None = None
    running_at_ms: float | None = None
    last_run_at_ms: float | None = None
    last_run_status: str = ""
    last_error: str = ""
    consecutive_errors: int = 0
    last_duration_ms: float = 0.0


@dataclass
class CronJob:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    enabled: bool = True
    schedule: CronSchedule = field(default_factory=CronSchedule)
    payload: CronPayload = field(default_factory=CronPayload)
    delivery: CronDelivery = field(default_factory=CronDelivery)
    state: CronJobState = field(default_factory=CronJobState)
    created_at_ms: float = field(default_factory=time.time)
    updated_at_ms: float = field(default_factory=time.time)
    _callback: Callable[[CronPayload], Awaitable[Any]] | None = field(default=None, repr=False)

    def compute_next_run(self, now_ms: float | None = None) -> float | None:
        if not self.enabled:
            return None
        now = now_ms or time.time() * 1000

        if self.schedule.kind == CronScheduleKind.AT:
            if self.state.last_run_at_ms is not None:
                return None
            try:
                from datetime import datetime
                target = datetime.fromisoformat(self.schedule.at).timestamp() * 1000
                return target if target > now else None
            except (ValueError, OSError):
                return None

        elif self.schedule.kind == CronScheduleKind.EVERY:
            anchor = self.schedule.anchor_ms or self.created_at_ms
            elapsed = now - anchor
            if elapsed < 0:
                return anchor
            interval = self.schedule.every_ms
            periods = int(elapsed / interval) + 1
            return anchor + periods * interval

        elif self.schedule.kind == CronScheduleKind.CRON:
            return self._compute_cron_next(now)

        return None

    def _compute_cron_next(self, now_ms: float) -> float | None:
        if _HAS_CRONITER:
            return self._compute_cron_next_croniter(now_ms)
        return self._compute_cron_next_fallback(now_ms)

    def _compute_cron_next_croniter(self, now_ms: float) -> float | None:
        try:
            from datetime import datetime, timezone
            now_dt = datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc)
            cron = croniter(self.schedule.cron_expr, now_dt)
            next_dt = cron.get_next(datetime)
            return next_dt.timestamp() * 1000
        except (ValueError, KeyError) as e:
            logger.warning("croniter parse error for '%s': %s", self.schedule.cron_expr, e)
            return None

    def _compute_cron_next_fallback(self, now_ms: float) -> float | None:
        try:
            parts = self.schedule.cron_expr.strip().split()
            if len(parts) != 5:
                return None
            minute, hour, day_month, month, day_week = parts
            from datetime import datetime, timedelta
            now_dt = datetime.utcnow()
            for offset_min in range(1, 60 * 24 * 7):
                candidate = now_dt + timedelta(minutes=offset_min)
                if self._cron_part_matches(minute, candidate.minute, 0, 59) and \
                   self._cron_part_matches(hour, candidate.hour, 0, 23) and \
                   self._cron_part_matches(day_month, candidate.day, 1, 31) and \
                   self._cron_part_matches(month, candidate.month, 1, 12) and \
                   self._cron_part_matches(day_week, candidate.isoweekday() % 7, 0, 6):
                    return candidate.timestamp() * 1000
            return None
        except Exception:
            return None

    @staticmethod
    def _cron_part_matches(expr: str, value: int, low: int, high: int) -> bool:
        if expr == "*":
            return True
        for part in expr.split(","):
            if "-" in part:
                rng = part.split("-")
                if len(rng) == 2 and int(rng[0]) <= value <= int(rng[1]):
                    return True
            elif "/" in part:
                base, step = part.split("/")
                b = int(base) if base != "*" else low
                if (value - b) % int(step) == 0 and value >= b:
                    return True
            elif part.isdigit() and int(part) == value:
                return True
        return False


class CronStore:
    def __init__(self, store_path: str | Path | None = None):
        if store_path is None:
            store_path = settings.cron_store_path
        self._path = Path(store_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load_jobs(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def save_jobs(self, jobs: list[dict]) -> bool:
        try:
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self._path)
            return True
        except OSError as e:
            logger.error("Cron store save failed: %s", e)
            return False


class CronService:
    PERSIST_INTERVAL = 30.0
    MAX_RETRY_ATTEMPTS = 3
    RETRY_BASE_DELAY = 5.0

    def __init__(self, store_path: str | None = None):
        store = CronStore(store_path)
        self._store = store
        self._jobs: dict[str, CronJob] = {}
        self._running = False
        self._task: asyncio.Task | None = None
        self._global_callbacks: list[Callable[[CronJob, Any], Awaitable[None]]] = []
        self._last_persist: float = 0.0
        self._dirty: bool = False

    def on_job_complete(self, callback: Callable[[CronJob, Any], Awaitable[None]]):
        self._global_callbacks.append(callback)

    def add_job(self, job: CronJob) -> str:
        self._jobs[job.id] = job
        self._mark_dirty()
        return job.id

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._mark_dirty()
            return True
        return False

    def update_job(self, job_id: str, **kwargs) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        for k, v in kwargs.items():
            if k == "schedule" and isinstance(v, dict):
                for sk, sv in v.items():
                    if hasattr(job.schedule, sk):
                        setattr(job.schedule, sk, sv)
            elif k == "payload" and isinstance(v, dict):
                for pk, pv in v.items():
                    if hasattr(job.payload, pk):
                        setattr(job.payload, pk, pv)
            elif hasattr(job, k):
                setattr(job, k, v)
        job.updated_at_ms = time.time()
        job.state.next_run_at_ms = None
        self._mark_dirty()
        return True

    def get_job(self, job_id: str) -> dict | None:
        job = self._jobs.get(job_id)
        if not job:
            return None
        return self._job_to_dict(job)

    def list_jobs(self) -> list[dict]:
        return [self._job_to_dict(j) for j in self._jobs.values()]

    async def start(self):
        if self._running:
            return
        self._load()
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Cron service started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._persist()
        logger.info("Cron service stopped")

    async def _run_loop(self):
        while self._running:
            try:
                now_ms = time.time() * 1000
                next_wakeup = now_ms + 60000

                for job in list(self._jobs.values()):
                    if not job.enabled:
                        continue
                    next_run = job.state.next_run_at_ms or job.compute_next_run(now_ms)
                    if next_run is not None:
                        if next_run <= now_ms:
                            job.state.next_run_at_ms = None
                            await self._execute_job(job)
                            job.state.next_run_at_ms = job.compute_next_run(now_ms)
                        else:
                            next_wakeup = min(next_wakeup, next_run)

                sleep_ms = max(1000, next_wakeup - time.time() * 1000)
                sleep_s = min(sleep_ms / 1000, 60.0)

                self._maybe_persist()
                await asyncio.sleep(sleep_s)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("Cron loop error: %s", e)
                await asyncio.sleep(5)

    async def _execute_job(self, job: CronJob):
        if job.state.consecutive_errors >= self.MAX_RETRY_ATTEMPTS:
            delay = self.RETRY_BASE_DELAY * (2 ** min(job.state.consecutive_errors - self.MAX_RETRY_ATTEMPTS, 5))
            if job.state.last_run_at_ms and (time.time() * 1000 - job.state.last_run_at_ms) < delay * 1000:
                return

        start = time.time()
        job.state.running_at_ms = start * 1000
        logger.info("Executing cron job: %s (%s)", job.name, job.id)

        try:
            result = None
            if job._callback:
                result = await asyncio.wait_for(
                    job._callback(job.payload),
                    timeout=job.payload.timeout_seconds,
                )
            for cb in self._global_callbacks:
                try:
                    await cb(job, result)
                except Exception as e:
                    logger.error("Cron callback error: %s", e)

            job.state.last_run_status = "ok"
            job.state.consecutive_errors = 0
        except asyncio.TimeoutError:
            job.state.last_run_status = "error"
            job.state.last_error = "Timeout"
            job.state.consecutive_errors += 1
        except Exception as e:
            job.state.last_run_status = "error"
            job.state.last_error = str(e)
            job.state.consecutive_errors += 1

        job.state.last_run_at_ms = time.time() * 1000
        job.state.running_at_ms = None
        job.state.last_duration_ms = (time.time() - start) * 1000
        self._mark_dirty()

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _maybe_persist(self) -> None:
        now = time.time()
        if self._dirty and (now - self._last_persist) >= self.PERSIST_INTERVAL:
            self._persist()

    def _load(self):
        for raw in self._store.load_jobs():
            schedule = CronSchedule(
                kind=CronScheduleKind(raw.get("schedule", {}).get("kind", "every")),
                at=raw.get("schedule", {}).get("at", ""),
                every_ms=raw.get("schedule", {}).get("every_ms", 60000),
                cron_expr=raw.get("schedule", {}).get("cron_expr", ""),
            )
            payload = CronPayload(
                kind=raw.get("payload", {}).get("kind", "systemEvent"),
                text=raw.get("payload", {}).get("text", ""),
                message=raw.get("payload", {}).get("message", ""),
            )
            state_raw = raw.get("state", {})
            state = CronJobState(
                last_run_at_ms=state_raw.get("last_run_at_ms"),
                last_run_status=state_raw.get("last_run_status", ""),
                consecutive_errors=state_raw.get("consecutive_errors", 0),
            )
            job = CronJob(
                id=raw.get("id", str(uuid.uuid4())),
                name=raw.get("name", ""),
                enabled=raw.get("enabled", True),
                schedule=schedule,
                payload=payload,
                state=state,
                created_at_ms=raw.get("created_at_ms", time.time()),
            )
            self._jobs[job.id] = job

    def _persist(self):
        self._store.save_jobs([self._job_to_dict(j) for j in self._jobs.values()])
        self._dirty = False
        self._last_persist = time.time()

    def _job_to_dict(self, job: CronJob) -> dict:
        return {
            "id": job.id,
            "name": job.name,
            "enabled": job.enabled,
            "schedule": {
                "kind": job.schedule.kind.value,
                "at": job.schedule.at,
                "every_ms": job.schedule.every_ms,
                "cron_expr": job.schedule.cron_expr,
                "tz": job.schedule.tz,
            },
            "payload": {
                "kind": job.payload.kind,
                "text": job.payload.text,
                "message": job.payload.message,
                "model": job.payload.model,
                "timeout_seconds": job.payload.timeout_seconds,
            },
            "delivery": {
                "mode": job.delivery.mode,
                "channel": job.delivery.channel,
                "to": job.delivery.to,
            },
            "state": {
                "next_run_at_ms": job.state.next_run_at_ms,
                "last_run_at_ms": job.state.last_run_at_ms,
                "last_run_status": job.state.last_run_status,
                "last_error": job.state.last_error,
                "consecutive_errors": job.state.consecutive_errors,
                "last_duration_ms": job.state.last_duration_ms,
            },
            "created_at_ms": job.created_at_ms,
            "updated_at_ms": job.updated_at_ms,
        }


_cron_service: CronService | None = None


def get_cron_service() -> CronService:
    global _cron_service
    if _cron_service is None:
        _cron_service = CronService()
    return _cron_service
