from __future__ import annotations

from enum import Enum

import aiosqlite


class AuditCategory(str, Enum):
    API_REQUEST = "api_request"
    DEVICE_CONNECT = "device_connect"
    DEVICE_DISCONNECT = "device_disconnect"
    DEVICE_EXECUTE = "device_execute"
    DEVICE_BROADCAST = "device_broadcast"
    DEVICE_CAPABILITY = "device_capability"
    SYNC_PUSH = "sync_push"
    SYNC_PULL = "sync_pull"
    SYNC_CONFLICT = "sync_conflict"
    TOOL_CALL = "tool_call"
    TOOL_REGISTER = "tool_register"
    TOOL_UNREGISTER = "tool_unregister"
    AGENT_RUN = "agent_run"
    AGENT_TOOL_CALL = "agent_tool_call"
    POLICY_EVALUATE = "policy_evaluate"
    POLICY_BLOCK = "policy_block"
    POLICY_CONFIRM = "policy_confirm"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    MEMORY_DELETE = "memory_delete"
    MEMORY_CONSOLIDATE = "memory_consolidate"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    SHELL_EXECUTE = "shell_execute"
    SYSTEM_CONFIG = "system_config"
    AUTH_ACTION = "auth_action"
    WEBSOCKET = "websocket"


class AuditLevel(str, Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


AUDIT_DB_PATH = "polyspace_audit.db"

_CREATE_AUDIT_LOGS = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    timestamp TEXT NOT NULL,
    category TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'info',
    action TEXT NOT NULL,
    actor_type TEXT NOT NULL DEFAULT 'system',
    actor_id TEXT NOT NULL DEFAULT '',
    actor_ip TEXT NOT NULL DEFAULT '',
    source_device_id TEXT,
    source_platform TEXT,
    target_device_id TEXT,
    target_platform TEXT,
    resource_type TEXT NOT NULL DEFAULT '',
    resource_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'success',
    duration_ms REAL,
    request_summary TEXT NOT NULL DEFAULT '',
    response_summary TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '',
    checksum TEXT
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_audit_trace_id ON audit_logs(trace_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_audit_category ON audit_logs(category);",
    "CREATE INDEX IF NOT EXISTS idx_audit_level ON audit_logs(level);",
    "CREATE INDEX IF NOT EXISTS idx_audit_category_timestamp ON audit_logs(category, timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_type, actor_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_source_device ON audit_logs(source_device_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_target_device ON audit_logs(target_device_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_trace_ts ON audit_logs(trace_id, timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_audit_level_ts ON audit_logs(level, timestamp);",
]

_CREATE_INTEGRITY = """
CREATE TABLE IF NOT EXISTS audit_integrity (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    check_type TEXT NOT NULL,
    total_records INTEGER NOT NULL DEFAULT 0,
    verified_records INTEGER NOT NULL DEFAULT 0,
    failed_records INTEGER NOT NULL DEFAULT 0,
    detail TEXT NOT NULL DEFAULT ''
);
"""

_CREATE_TOKEN_USAGE = """
CREATE TABLE IF NOT EXISTS token_usage_records (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL DEFAULT '',
    session_id TEXT NOT NULL DEFAULT '',
    model_name TEXT NOT NULL DEFAULT '',
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL
);
"""

_TOKEN_USAGE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage_records(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_token_usage_session ON token_usage_records(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_token_usage_model ON token_usage_records(model_name);",
]


async def init_audit_db() -> None:
    async with aiosqlite.connect(AUDIT_DB_PATH) as db:
        await db.execute(_CREATE_AUDIT_LOGS)
        await db.execute(_CREATE_INTEGRITY)
        await db.execute(_CREATE_TOKEN_USAGE)
        for idx_sql in _CREATE_INDEXES:
            await db.execute(idx_sql)
        for idx_sql in _TOKEN_USAGE_INDEXES:
            await db.execute(idx_sql)
        await db.commit()
