from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional

import aiosqlite

from app.core.audit.models import (
    AUDIT_DB_PATH,
    AuditCategory,
    AuditLevel,
)

logger = logging.getLogger(__name__)

_trace_id_var: ContextVar[str] = ContextVar("audit_trace_id", default="")
_span_id_var: ContextVar[str] = ContextVar("audit_span_id", default="")
_parent_span_id_var: ContextVar[str] = ContextVar("audit_parent_span_id", default="")


def get_trace_id() -> str:
    return _trace_id_var.get()


def get_span_id() -> str:
    return _span_id_var.get()


def new_trace_id() -> str:
    tid = str(uuid.uuid4())
    _trace_id_var.set(tid)
    _span_id_var.set(str(uuid.uuid4()))
    _parent_span_id_var.set("")
    return tid


def new_span(parent: bool = True) -> str:
    old_span = _span_id_var.get()
    new_sid = str(uuid.uuid4())
    if parent:
        _parent_span_id_var.set(old_span)
    _span_id_var.set(new_sid)
    return new_sid


def _compute_checksum(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_INSERT_SQL = """
INSERT INTO audit_logs (
    id, trace_id, span_id, parent_span_id, timestamp,
    category, level, action, actor_type, actor_id, actor_ip,
    source_device_id, source_platform, target_device_id, target_platform,
    resource_type, resource_id, status, duration_ms,
    request_summary, response_summary, detail, checksum
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_INSERT_TOKEN_SQL = """
INSERT INTO token_usage_records (
    id, thread_id, session_id, model_name, input_tokens, output_tokens, timestamp
) VALUES (?, ?, ?, ?, ?, ?, ?)
"""


class AuditService:
    def __init__(self, max_buffer_size: int = 200, flush_interval: float = 2.0, max_total_buffer: int = 10000):
        self._buffer: list[tuple] = []
        self._token_buffer: list[tuple] = []
        self._max_buffer = max_buffer_size
        self._flush_interval = flush_interval
        self._max_total_buffer = max_total_buffer
        self._flush_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._token_lock = asyncio.Lock()
        self._checksum_queue: list[tuple[int, dict]] = []

    async def start(self) -> None:
        if self._flush_task and not self._flush_task.done():
            return
        self._flush_task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self.flush()

    async def _flush_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Audit flush error: %s", e)

    async def flush(self) -> None:
        await self._flush_audit()
        await self._flush_tokens()

    async def _flush_audit(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            batch = self._buffer[:]
            checksum_batch = self._checksum_queue[:]
            self._buffer.clear()
            self._checksum_queue.clear()

        rows_with_checksum = []
        for idx, checksum_data in checksum_batch:
            if idx < len(batch):
                checksum = _compute_checksum(checksum_data)
                rows_with_checksum.append(batch[idx] + (checksum,))

        try:
            async with aiosqlite.connect(AUDIT_DB_PATH) as db:
                await db.executemany(_INSERT_SQL, rows_with_checksum)
                await db.commit()
        except Exception as e:
            logger.error("Audit write error: %s", e)
            async with self._lock:
                if len(self._buffer) + len(batch) <= self._max_total_buffer:
                    self._buffer.extend(batch)
                    self._checksum_queue.extend(checksum_batch)
                else:
                    logger.error("Audit buffer overflow, dropping %d records", len(batch))

    async def _flush_tokens(self) -> None:
        async with self._token_lock:
            if not self._token_buffer:
                return
            batch = self._token_buffer[:]
            self._token_buffer.clear()

        try:
            async with aiosqlite.connect(AUDIT_DB_PATH) as db:
                await db.executemany(_INSERT_TOKEN_SQL, batch)
                await db.commit()
        except Exception as e:
            logger.error("Token usage write error: %s", e)
            async with self._token_lock:
                if len(self._token_buffer) + len(batch) <= self._max_total_buffer:
                    self._token_buffer.extend(batch)
                else:
                    logger.error("Token buffer overflow, dropping %d records", len(batch))

    async def record(
        self,
        category: str | AuditCategory,
        action: str,
        *,
        level: str | AuditLevel = AuditLevel.INFO,
        actor_type: str = "system",
        actor_id: str = "",
        actor_ip: str = "",
        source_device_id: str | None = None,
        source_platform: str | None = None,
        target_device_id: str | None = None,
        target_platform: str | None = None,
        resource_type: str = "",
        resource_id: str = "",
        status: str = "success",
        duration_ms: float | None = None,
        request_summary: str = "",
        response_summary: str = "",
        detail: str = "",
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> str:
        cat = category.value if isinstance(category, AuditCategory) else category
        lvl = level.value if isinstance(level, AuditLevel) else level

        tid = trace_id or _trace_id_var.get() or str(uuid.uuid4())
        sid = span_id or _span_id_var.get() or str(uuid.uuid4())
        psid = parent_span_id or _parent_span_id_var.get() or ""

        record_id = str(uuid.uuid4())
        ts = datetime.utcnow().isoformat()

        row = (
            record_id,
            tid,
            sid,
            psid or None,
            ts,
            cat,
            lvl,
            action,
            actor_type,
            actor_id,
            actor_ip,
            source_device_id,
            source_platform,
            target_device_id,
            target_platform,
            resource_type,
            resource_id,
            status,
            duration_ms,
            request_summary[:2000] if request_summary else "",
            response_summary[:2000] if response_summary else "",
            detail[:5000] if detail else "",
        )

        checksum_data = {
            "id": record_id, "trace_id": tid, "span_id": sid,
            "parent_span_id": psid or None, "timestamp": ts,
            "category": cat, "level": lvl, "action": action,
            "actor_type": actor_type, "actor_id": actor_id,
            "actor_ip": actor_ip, "source_device_id": source_device_id,
            "source_platform": source_platform, "target_device_id": target_device_id,
            "target_platform": target_platform, "resource_type": resource_type,
            "resource_id": resource_id, "status": status,
            "duration_ms": duration_ms, "request_summary": request_summary[:2000] if request_summary else "",
            "response_summary": response_summary[:2000] if response_summary else "",
            "detail": detail[:5000] if detail else "",
        }

        async with self._lock:
            buffer_idx = len(self._buffer)
            self._buffer.append(row)
            self._checksum_queue.append((buffer_idx, checksum_data))
            if len(self._buffer) >= self._max_buffer:
                await self.flush()

        return record_id

    async def query(
        self,
        *,
        category: str | None = None,
        level: str | None = None,
        actor_type: str | None = None,
        actor_id: str | None = None,
        source_device_id: str | None = None,
        target_device_id: str | None = None,
        trace_id: str | None = None,
        status: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        conditions = []
        params: list[Any] = []

        if category:
            conditions.append("category = ?")
            params.append(category)
        if level:
            conditions.append("level = ?")
            params.append(level)
        if actor_type:
            conditions.append("actor_type = ?")
            params.append(actor_type)
        if actor_id:
            conditions.append("actor_id = ?")
            params.append(actor_id)
        if source_device_id:
            conditions.append("source_device_id = ?")
            params.append(source_device_id)
        if target_device_id:
            conditions.append("target_device_id = ?")
            params.append(target_device_id)
        if trace_id:
            conditions.append("trace_id = ?")
            params.append(trace_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM audit_logs WHERE {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with aiosqlite.connect(AUDIT_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()

            return [
                {
                    "id": r["id"],
                    "trace_id": r["trace_id"],
                    "span_id": r["span_id"],
                    "parent_span_id": r["parent_span_id"],
                    "timestamp": r["timestamp"],
                    "category": r["category"],
                    "level": r["level"],
                    "action": r["action"],
                    "actor_type": r["actor_type"],
                    "actor_id": r["actor_id"],
                    "actor_ip": r["actor_ip"],
                    "source_device_id": r["source_device_id"],
                    "source_platform": r["source_platform"],
                    "target_device_id": r["target_device_id"],
                    "target_platform": r["target_platform"],
                    "resource_type": r["resource_type"],
                    "resource_id": r["resource_id"],
                    "status": r["status"],
                    "duration_ms": r["duration_ms"],
                    "request_summary": r["request_summary"],
                    "response_summary": r["response_summary"],
                    "detail": r["detail"],
                    "checksum": r["checksum"],
                }
                for r in rows
            ]

    async def get_trace_chain(self, trace_id: str) -> list[dict[str, Any]]:
        async with aiosqlite.connect(AUDIT_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM audit_logs WHERE trace_id = ? ORDER BY timestamp",
                [trace_id],
            )
            rows = await cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "span_id": r["span_id"],
                    "parent_span_id": r["parent_span_id"],
                    "timestamp": r["timestamp"],
                    "category": r["category"],
                    "action": r["action"],
                    "status": r["status"],
                    "duration_ms": r["duration_ms"],
                    "source_device_id": r["source_device_id"],
                    "target_device_id": r["target_device_id"],
                    "detail": r["detail"],
                }
                for r in rows
            ]

    async def verify_integrity(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        conditions = []
        params: list[Any] = []
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        where = " AND ".join(conditions) if conditions else "1=1"

        async with aiosqlite.connect(AUDIT_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                f"SELECT * FROM audit_logs WHERE {where} ORDER BY timestamp",
                params,
            )
            rows = await cursor.fetchall()

            total = len(rows)
            verified = 0
            failed = 0
            failed_ids: list[str] = []

            for r in rows:
                row_dict = dict(r)
                if not row_dict.get("checksum"):
                    failed += 1
                    failed_ids.append(row_dict["id"])
                    continue

                check_data = {k: v for k, v in row_dict.items() if k != "checksum"}
                expected = _compute_checksum(check_data)
                if expected == row_dict["checksum"]:
                    verified += 1
                else:
                    failed += 1
                    failed_ids.append(row_dict["id"])

            integrity_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO audit_integrity "
                "(id, timestamp, check_type, total_records, "
                "verified_records, failed_records, detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    integrity_id,
                    datetime.utcnow().isoformat(),
                    "full_verify",
                    total,
                    verified,
                    failed,
                    json.dumps(failed_ids[:100]) if failed_ids else "",
                ],
            )
            await db.commit()

            return {
                "total": total,
                "verified": verified,
                "failed": failed,
                "failed_ids": failed_ids[:50],
                "integrity_rate": verified / total if total > 0 else 1.0,
            }

    async def get_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        conditions = []
        params: list[Any] = []
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        where = " AND ".join(conditions) if conditions else "1=1"

        async with aiosqlite.connect(AUDIT_DB_PATH) as db:
            cursor = await db.execute(
                f"SELECT COUNT(*) as cnt FROM audit_logs WHERE {where}", params
            )
            row = await cursor.fetchone()
            total = row[0] if row else 0

            cursor = await db.execute(
                f"SELECT category, COUNT(*) as cnt FROM audit_logs WHERE {where} GROUP BY category",
                params,
            )
            by_category = dict(await cursor.fetchall())

            cursor = await db.execute(
                f"SELECT level, COUNT(*) as cnt FROM audit_logs WHERE {where} GROUP BY level",
                params,
            )
            by_level = dict(await cursor.fetchall())

            cursor = await db.execute(
                f"SELECT status, COUNT(*) as cnt FROM audit_logs WHERE {where} GROUP BY status",
                params,
            )
            by_status = dict(await cursor.fetchall())

            cursor = await db.execute(
                f"SELECT source_device_id, COUNT(*) as cnt "
                f"FROM audit_logs WHERE {where} "
                f"AND source_device_id IS NOT NULL "
                f"GROUP BY source_device_id LIMIT 20",
                params,
            )
            by_device = dict(await cursor.fetchall())

            return {
                "total": total,
                "by_category": by_category,
                "by_level": by_level,
                "by_status": by_status,
                "by_device": by_device,
            }

    async def record_token_usage(
        self,
        *,
        thread_id: str = "",
        session_id: str = "",
        model_name: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        record_id = str(uuid.uuid4())
        ts = datetime.utcnow().isoformat()
        row = (record_id, thread_id, session_id, model_name, input_tokens, output_tokens, ts)
        async with self._token_lock:
            self._token_buffer.append(row)
            if len(self._token_buffer) >= self._max_buffer:
                await self._flush_tokens()

    async def get_token_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        conditions = []
        params: list[Any] = []
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        where = " AND ".join(conditions) if conditions else "1=1"

        async with aiosqlite.connect(AUDIT_DB_PATH) as db:
            cursor = await db.execute(
                f"SELECT COUNT(*) as cnt, "
                f"COALESCE(SUM(input_tokens), 0) as total_input, "
                f"COALESCE(SUM(output_tokens), 0) as total_output "
                f"FROM token_usage_records WHERE {where}",
                params,
            )
            row = await cursor.fetchone()
            total_records = row[0] if row else 0
            total_input = row[1] if row else 0
            total_output = row[2] if row else 0

            cursor = await db.execute(
                f"SELECT model_name, COUNT(*) as cnt, "
                f"COALESCE(SUM(input_tokens), 0) as input_sum, "
                f"COALESCE(SUM(output_tokens), 0) as output_sum "
                f"FROM token_usage_records WHERE {where} "
                f"GROUP BY model_name",
                params,
            )
            by_model = []
            for r in await cursor.fetchall():
                by_model.append({
                    "model_name": r[0],
                    "count": r[1],
                    "input_tokens": r[2],
                    "output_tokens": r[3],
                })

            return {
                "total_records": total_records,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_input + total_output,
                "by_model": by_model,
            }


audit_service = AuditService()


class AuditSpan:
    def __init__(
        self,
        category: str | AuditCategory,
        action: str,
        **kwargs: Any,
    ):
        self._category = category
        self._action = action
        self._kwargs = kwargs
        self._start_time: float = 0.0
        self._old_trace: str = ""
        self._old_span: str = ""
        self._old_parent: str = ""

    async def __aenter__(self):
        self._old_trace = _trace_id_var.get()
        self._old_span = _span_id_var.get()
        self._old_parent = _parent_span_id_var.get()

        if not self._old_trace:
            new_trace_id()
        new_span(parent=True)

        self._start_time = time.monotonic()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.monotonic() - self._start_time) * 1000
        status = "error" if exc_type else "success"
        level = AuditLevel.ERROR if exc_type else AuditLevel.INFO
        detail = str(exc_val) if exc_val else self._kwargs.get("detail", "")

        await audit_service.record(
            category=self._category,
            action=self._action,
            level=level,
            status=status,
            duration_ms=round(duration_ms, 2),
            detail=detail,
            **{k: v for k, v in self._kwargs.items() if k != "detail"},
        )

        _trace_id_var.set(self._old_trace)
        _span_id_var.set(self._old_span)
        _parent_span_id_var.set(self._old_parent)

        return False
