from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import aiosqlite
from app.api.v1.auth import get_current_user
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy import func, select

from app.core.audit.models import AUDIT_DB_PATH
from app.core.audit.service import audit_service
from app.db.database import async_session
from app.models.tables import ChatMessage, ChatSession, WorkspaceDocument

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_chat_stats(start: datetime | None, end: datetime | None) -> dict:
    async with async_session() as session:
        conditions = []
        if start:
            conditions.append(ChatMessage.created_at >= start)
        if end:
            conditions.append(ChatMessage.created_at <= end)

        user_msg_count = await session.scalar(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.role == "user", *conditions
            )
        )
        assistant_msg_count = await session.scalar(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.role == "assistant", *conditions
            )
        )
        user_chars = await session.scalar(
            select(func.coalesce(func.sum(func.length(ChatMessage.content)), 0)).where(
                ChatMessage.role == "user", *conditions
            )
        )
        session_count = await session.scalar(
            select(func.count(ChatSession.id))
        )

        return {
            "session_count": session_count or 0,
            "user_message_count": user_msg_count or 0,
            "assistant_message_count": assistant_msg_count or 0,
            "user_characters_typed": user_chars or 0,
        }


async def _get_document_stats(start: datetime | None, end: datetime | None) -> dict:
    async with async_session() as session:
        conditions = []
        if start:
            conditions.append(WorkspaceDocument.updated_at >= start)
        if end:
            conditions.append(WorkspaceDocument.updated_at <= end)

        doc_count = await session.scalar(
            select(func.count(WorkspaceDocument.id)).where(*conditions)
        )
        total_chars = await session.scalar(
            select(
                func.coalesce(
                    func.sum(func.length(WorkspaceDocument.content)), 0
                )
            ).where(*conditions)
        )

        return {
            "documents_edited": doc_count or 0,
            "document_total_chars": total_chars or 0,
            "document_estimated_words": (total_chars or 0) // 2 if total_chars else 0,
        }


async def _get_audit_activity_stats(start: datetime | None, end: datetime | None) -> dict:
    conditions = []
    params: list = []
    if start:
        conditions.append("timestamp >= ?")
        params.append(start.isoformat())
    if end:
        conditions.append("timestamp <= ?")
        params.append(end.isoformat())
    where = " AND ".join(conditions) if conditions else "1=1"

    async with aiosqlite.connect(AUDIT_DB_PATH) as db:
        cursor = await db.execute(
            f"SELECT COUNT(*) FROM audit_logs WHERE {where} AND category IN ('agent_run', 'agent_tool_call')",
            params,
        )
        ai_tasks = (await cursor.fetchone())[0]

        cursor = await db.execute(
            f"SELECT COUNT(*) FROM audit_logs WHERE {where} AND category IN ('tool_call', 'agent_tool_call')",
            params,
        )
        tool_calls = (await cursor.fetchone())[0]

        cursor = await db.execute(
            f"SELECT COALESCE(SUM(duration_ms), 0) FROM audit_logs "
            f"WHERE {where} AND category IN ('agent_run', 'agent_tool_call', 'tool_call')",
            params,
        )
        ai_duration_ms = (await cursor.fetchone())[0]

        cursor = await db.execute(
            f"SELECT COUNT(*) FROM audit_logs WHERE {where} AND category = 'file_write'",
            params,
        )
        file_edits = (await cursor.fetchone())[0]

        return {
            "ai_tasks_completed": ai_tasks,
            "tool_calls_made": tool_calls,
            "ai_duration_seconds": round(ai_duration_ms / 1000, 1),
            "ai_estimated_time_saved_minutes": round(ai_duration_ms / 1000 / 60 * 3, 0),
            "file_edits": file_edits,
        }


@router.get("/stats")
async def get_overview_stats(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    period: Optional[str] = Query(None, description="Time period: 7d, 30d, 90d, all"),
):
    now = datetime.utcnow()
    start = None
    end = None

    if period == "7d":
        start = now - timedelta(days=7)
    elif period == "30d":
        start = now - timedelta(days=30)
    elif period == "90d":
        start = now - timedelta(days=90)

    chat_stats = await _get_chat_stats(start, end)
    doc_stats = await _get_document_stats(start, end)
    activity_stats = await _get_audit_activity_stats(start, end)
    token_stats = await audit_service.get_token_stats(start, end)

    return {
        "period": period or "all",
        "chat": chat_stats,
        "documents": doc_stats,
        "ai_activity": activity_stats,
        "tokens": token_stats,
    }
