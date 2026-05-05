from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import aiosqlite

MIGRATION_VERSION = 2


class TodoService:
    def __init__(self, db_path: str = "data/todo.db"):
        self.db_path = db_path
        self._init_db_lock = asyncio.Lock()

    async def _init_db(self):
        async with self._init_db_lock:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA journal_mode=WAL")
                await db.execute("PRAGMA foreign_keys=ON")
                await self._run_migrations(db)
                await db.commit()

    async def _run_migrations(self, db: aiosqlite.Connection):
        await db.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        async with db.execute("SELECT MAX(version) FROM _migrations") as cursor:
            row = await cursor.fetchone()
            current_version = row[0] if row and row[0] else 0

        if current_version < 1:
            await self._migrate_v1(db)
        if current_version < 2:
            await self._migrate_v2(db)

    async def _migrate_v1(self, db: aiosqlite.Connection):
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                color TEXT DEFAULT '',
                icon TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'none',
                importance TEXT DEFAULT 'normal',
                urgency TEXT DEFAULT 'normal',
                due_date TEXT,
                due_time TEXT,
                start_date TEXT,
                start_time TEXT,
                recurrence TEXT DEFAULT '',
                list_id INTEGER,
                tags TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                kanban_card_id INTEGER,
                kanban_board_id INTEGER,
                calendar_event_id TEXT,
                source TEXT DEFAULT 'manual',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (list_id) REFERENCES task_lists(id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_tasks_list_id ON tasks(list_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS ix_tasks_due_date ON tasks(due_date)")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_subtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                remind_at TEXT NOT NULL,
                repeat_type TEXT DEFAULT 'none',
                repeat_interval INTEGER DEFAULT 1,
                repeat_days TEXT DEFAULT '',
                repeat_end_date TEXT,
                is_triggered INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                frequency TEXT DEFAULT 'daily',
                target_days TEXT DEFAULT '',
                color TEXT DEFAULT '',
                icon TEXT DEFAULT '',
                reminder_time TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habit_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                checkin_date TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(habit_id, checkin_date),
                FOREIGN KEY (habit_id) REFERENCES task_habits(id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                habit_id INTEGER,
                focus_duration INTEGER DEFAULT 25,
                break_duration INTEGER DEFAULT 5,
                long_break_duration INTEGER DEFAULT 15,
                sessions_before_long_break INTEGER DEFAULT 4,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
                FOREIGN KEY (habit_id) REFERENCES task_habits(id) ON DELETE SET NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                focus_duration INTEGER DEFAULT 25,
                break_duration INTEGER DEFAULT 5,
                long_break_duration INTEGER DEFAULT 15,
                sessions_before_long_break INTEGER DEFAULT 4,
                auto_start_break INTEGER DEFAULT 1,
                auto_start_focus INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute(
            "INSERT INTO _migrations (version) VALUES (?)", (1,)
        )

    async def _migrate_v2(self, db: aiosqlite.Connection):
        try:
            async with db.execute("SELECT 1 FROM todos LIMIT 1") as cursor:
                await cursor.fetchone()
            has_old_table = True
        except Exception:
            has_old_table = False

        if has_old_table:
            await db.execute("""
                INSERT OR IGNORE INTO tasks
                    (title, description, status, priority, due_date,
                     tags, kanban_card_id, kanban_board_id,
                     created_at, updated_at, completed_at, source)
                SELECT title, description, status,
                    CASE priority WHEN 'normal' THEN 'none' ELSE priority END,
                    due_date, tags, kanban_card_id, kanban_board_id,
                    created_at, updated_at, completed_at, 'migrated'
                FROM todos
            """)
            await db.execute("DROP TABLE IF EXISTS todos")

        await db.execute(
            "INSERT INTO _migrations (version) VALUES (?)", (2,)
        )

    def _row_to_dict(self, row: aiosqlite.Row) -> dict:
        d = dict(row)
        tags_str = d.get("tags", "")
        d["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        if "recurrence" in d and isinstance(d["recurrence"], str) and d["recurrence"]:
            try:
                d["recurrence"] = json.loads(d["recurrence"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d

    async def _get_db(self) -> aiosqlite.Connection:
        await self._init_db()
        db = await aiosqlite.connect(self.db_path)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON")
        return db

    # ── Task Lists ──────────────────────────────────────────────

    async def create_list(
        self, name: str, parent_id: int | None = None,
        color: str = "", icon: str = "", sort_order: int = 0,
    ) -> dict:
        db = await self._get_db()
        try:
            now = datetime.utcnow().isoformat()
            cursor = await db.execute(
                """INSERT INTO task_lists (name, parent_id, color, icon, sort_order, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, parent_id, color, icon, sort_order, now, now),
            )
            list_id = cursor.lastrowid
            await db.commit()
            return await self.get_list(list_id)
        finally:
            await db.close()

    async def get_list(self, list_id: int) -> Optional[dict]:
        db = await self._get_db()
        try:
            async with db.execute("SELECT * FROM task_lists WHERE id = ?", (list_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db.close()

    async def update_list(self, list_id: int, **updates: Any) -> Optional[dict]:
        db = await self._get_db()
        try:
            allowed = {"name", "parent_id", "color", "icon", "sort_order"}
            filtered = {k: v for k, v in updates.items() if k in allowed}
            if not filtered:
                return await self.get_list(list_id)
            filtered["updated_at"] = datetime.utcnow().isoformat()
            set_clause = ", ".join(f"{k} = ?" for k in filtered)
            values = list(filtered.values()) + [list_id]
            await db.execute(f"UPDATE task_lists SET {set_clause} WHERE id = ?", values)
            await db.commit()
            return await self.get_list(list_id)
        finally:
            await db.close()

    async def delete_list(self, list_id: int) -> bool:
        db = await self._get_db()
        try:
            cursor = await db.execute("DELETE FROM task_lists WHERE id = ?", (list_id,))
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    async def list_lists(self, parent_id: int | None = None) -> list[dict]:
        db = await self._get_db()
        try:
            if parent_id is not None:
                async with db.execute(
                    "SELECT * FROM task_lists WHERE parent_id = ? ORDER BY sort_order, created_at",
                    (parent_id,),
                ) as cursor:
                    return [dict(row) async for row in cursor]
            else:
                async with db.execute(
                    "SELECT * FROM task_lists ORDER BY sort_order, created_at",
                ) as cursor:
                    return [dict(row) async for row in cursor]
        finally:
            await db.close()

    # ── Tasks ────────────────────────────────────────────────────

    async def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "none",
        importance: str = "normal",
        urgency: str = "normal",
        due_date: str | None = None,
        due_time: str | None = None,
        start_date: str | None = None,
        start_time: str | None = None,
        recurrence: dict | None = None,
        list_id: int | None = None,
        tags: list[str] | None = None,
        notes: str = "",
        source: str = "manual",
        kanban_card_id: int | None = None,
        kanban_board_id: int | None = None,
        calendar_event_id: str | None = None,
        reminders: list[dict] | None = None,
        subtasks: list[str] | None = None,
    ) -> dict:
        db = await self._get_db()
        try:
            now = datetime.utcnow().isoformat()
            tags_str = ",".join(tags) if tags else ""
            recurrence_str = json.dumps(recurrence, ensure_ascii=False) if recurrence else ""
            cursor = await db.execute(
                """INSERT INTO tasks
                   (title, description, status, priority, importance, urgency,
                    due_date, due_time, start_date, start_time, recurrence,
                    list_id, tags, notes, source, kanban_card_id, kanban_board_id,
                    calendar_event_id, created_at, updated_at)
                   VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, description, priority, importance, urgency,
                 due_date, due_time, start_date, start_time, recurrence_str,
                 list_id, tags_str, notes, source, kanban_card_id, kanban_board_id,
                 calendar_event_id, now, now),
            )
            task_id = cursor.lastrowid

            if reminders:
                for r in reminders:
                    await db.execute(
                        """INSERT INTO task_reminders
                           (task_id, remind_at, repeat_type, repeat_interval, repeat_days, repeat_end_date)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (task_id, r.get("remind_at", ""), r.get("repeat_type", "none"),
                         r.get("repeat_interval", 1), r.get("repeat_days", ""),
                         r.get("repeat_end_date")),
                    )

            if subtasks:
                for idx, st_title in enumerate(subtasks):
                    await db.execute(
                        "INSERT INTO task_subtasks (task_id, title, sort_order) VALUES (?, ?, ?)",
                        (task_id, st_title, idx),
                    )

            await db.commit()
            return await self.get_task(task_id)
        finally:
            await db.close()

    async def get_task(self, task_id: int) -> Optional[dict]:
        db = await self._get_db()
        try:
            async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
            task = self._row_to_dict(row)
            task["subtasks"] = await self._get_subtasks(db, task_id)
            task["reminders"] = await self._get_reminders(db, task_id)
            task["attachments"] = await self._get_attachments(db, task_id)
            return task
        finally:
            await db.close()

    async def update_task(self, task_id: int, **updates: Any) -> Optional[dict]:
        db = await self._get_db()
        try:
            allowed = {
                "title", "description", "status", "priority", "importance", "urgency",
                "due_date", "due_time", "start_date", "start_time", "recurrence",
                "list_id", "tags", "notes", "sort_order",
                "kanban_card_id", "kanban_board_id", "calendar_event_id",
            }
            filtered = {k: v for k, v in updates.items() if k in allowed}
            if not filtered:
                return await self.get_task(task_id)
            if "tags" in filtered and isinstance(filtered["tags"], list):
                filtered["tags"] = ",".join(filtered["tags"])
            if "recurrence" in filtered and isinstance(filtered["recurrence"], dict):
                filtered["recurrence"] = json.dumps(filtered["recurrence"], ensure_ascii=False)
            filtered["updated_at"] = datetime.utcnow().isoformat()
            set_clause = ", ".join(f"{k} = ?" for k in filtered)
            values = list(filtered.values()) + [task_id]
            await db.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            await db.commit()
            return await self.get_task(task_id)
        finally:
            await db.close()

    async def complete_task(self, task_id: int) -> Optional[dict]:
        db = await self._get_db()
        try:
            now = datetime.utcnow().isoformat()
            await db.execute(
                "UPDATE tasks SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?",
                (now, now, task_id),
            )
            await db.commit()
            return await self.get_task(task_id)
        finally:
            await db.close()

    async def reopen_task(self, task_id: int) -> Optional[dict]:
        db = await self._get_db()
        try:
            now = datetime.utcnow().isoformat()
            await db.execute(
                "UPDATE tasks SET status = 'pending', completed_at = NULL, updated_at = ? WHERE id = ?",
                (now, task_id),
            )
            await db.commit()
            return await self.get_task(task_id)
        finally:
            await db.close()

    async def delete_task(self, task_id: int) -> bool:
        db = await self._get_db()
        try:
            cursor = await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    async def list_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        list_id: int | None = None,
        tag: str | None = None,
        due_before: str | None = None,
        due_after: str | None = None,
        importance: str | None = None,
        urgency: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "DESC",
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict]:
        db = await self._get_db()
        try:
            conditions = []
            params: list[Any] = []
            if status:
                conditions.append("status = ?")
                params.append(status)
            if priority:
                conditions.append("priority = ?")
                params.append(priority)
            if list_id is not None:
                conditions.append("list_id = ?")
                params.append(list_id)
            if tag:
                conditions.append("(tags LIKE ? OR tags LIKE ? OR tags LIKE ?)")
                params.extend([f"{tag},%", f"%,{tag}", f"%,{tag},%"])
            if due_before:
                conditions.append("due_date <= ?")
                params.append(due_before)
            if due_after:
                conditions.append("due_date >= ?")
                params.append(due_after)
            if importance:
                conditions.append("importance = ?")
                params.append(importance)
            if urgency:
                conditions.append("urgency = ?")
                params.append(urgency)

            where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
            valid_sorts = {"created_at", "due_date", "priority", "title", "sort_order", "updated_at"}
            if sort_by not in valid_sorts:
                sort_by = "created_at"
            direction = "ASC" if sort_order.upper() == "ASC" else "DESC"

            async with db.execute(
                f"SELECT * FROM tasks{where_clause} ORDER BY {sort_by} {direction} LIMIT ? OFFSET ?",
                params + [limit, offset],
            ) as cursor:
                rows = [self._row_to_dict(row) async for row in cursor]

            for task in rows:
                task["subtasks"] = await self._get_subtasks(db, task["id"])
                task["reminders"] = await self._get_reminders(db, task["id"])

            return rows
        finally:
            await db.close()

    async def get_overdue(self) -> list[dict]:
        now = datetime.utcnow().strftime("%Y-%m-%d")
        return await self.list_tasks(status="pending", due_before=now, sort_by="due_date", sort_order="ASC")

    async def get_tasks_by_date(self, date: str) -> list[dict]:
        return await self.list_tasks(due_after=date, due_before=date, sort_by="due_time", sort_order="ASC")

    async def get_tasks_by_date_range(self, start: str, end: str) -> list[dict]:
        return await self.list_tasks(due_after=start, due_before=end, sort_by="due_date", sort_order="ASC")

    async def get_quadrant_tasks(self) -> dict:
        db = await self._get_db()
        try:
            quadrants = {"q1": [], "q2": [], "q3": [], "q4": []}
            async with db.execute(
                "SELECT * FROM tasks WHERE status != 'completed' AND status != 'cancelled'"
            ) as cursor:
                async for row in cursor:
                    task = self._row_to_dict(row)
                    imp = task.get("importance", "normal")
                    urg = task.get("urgency", "normal")
                    is_important = imp in ("important", "high")
                    is_urgent = urg in ("urgent", "high")
                    if is_important and is_urgent:
                        quadrants["q1"].append(task)
                    elif is_important and not is_urgent:
                        quadrants["q2"].append(task)
                    elif not is_important and is_urgent:
                        quadrants["q3"].append(task)
                    else:
                        quadrants["q4"].append(task)
            return quadrants
        finally:
            await db.close()

    async def get_task_stats(self) -> dict:
        db = await self._get_db()
        try:
            stats: dict[str, Any] = {
                "total": 0, "pending": 0, "in_progress": 0,
                "completed": 0, "cancelled": 0, "overdue": 0,
                "by_priority": {}, "by_list": {},
            }
            async with db.execute("SELECT COUNT(*) FROM tasks") as cursor:
                row = await cursor.fetchone()
                stats["total"] = row[0] if row else 0
            async with db.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status") as cursor:
                async for row in cursor:
                    if row[0] in stats:
                        stats[row[0]] = row[1]
            now = datetime.utcnow().strftime("%Y-%m-%d")
            async with db.execute(
                "SELECT COUNT(*) FROM tasks "
                "WHERE status = 'pending' AND due_date IS NOT NULL "
                "AND due_date != '' AND due_date < ?",
                (now,),
            ) as cursor:
                row = await cursor.fetchone()
                stats["overdue"] = row[0] if row else 0
            async with db.execute("SELECT priority, COUNT(*) FROM tasks GROUP BY priority") as cursor:
                async for row in cursor:
                    stats["by_priority"][row[0]] = row[1]
            async with db.execute(
                "SELECT list_id, COUNT(*) FROM tasks "
                "WHERE list_id IS NOT NULL GROUP BY list_id"
            ) as cursor:
                async for row in cursor:
                    stats["by_list"][str(row[0])] = row[1]
            return stats
        finally:
            await db.close()

    async def get_linked_todos(self, kanban_card_id: int) -> list[dict]:
        db = await self._get_db()
        try:
            async with db.execute(
                "SELECT * FROM tasks WHERE kanban_card_id = ?", (kanban_card_id,)
            ) as cursor:
                return [self._row_to_dict(row) async for row in cursor]
        finally:
            await db.close()

    # ── Subtasks ─────────────────────────────────────────────────

    async def _get_subtasks(self, db: aiosqlite.Connection, task_id: int) -> list[dict]:
        async with db.execute(
            "SELECT * FROM task_subtasks WHERE task_id = ? ORDER BY sort_order", (task_id,)
        ) as cursor:
            return [dict(row) async for row in cursor]

    async def add_subtask(self, task_id: int, title: str, sort_order: int = 0) -> Optional[dict]:
        db = await self._get_db()
        try:
            cursor = await db.execute(
                "INSERT INTO task_subtasks (task_id, title, sort_order) VALUES (?, ?, ?)",
                (task_id, title, sort_order),
            )
            subtask_id = cursor.lastrowid
            await db.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), task_id),
            )
            await db.commit()
            async with db.execute("SELECT * FROM task_subtasks WHERE id = ?", (subtask_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db.close()

    async def update_subtask(self, subtask_id: int, **updates: Any) -> Optional[dict]:
        db = await self._get_db()
        try:
            allowed = {"title", "completed", "sort_order"}
            filtered = {k: v for k, v in updates.items() if k in allowed}
            if not filtered:
                return None
            set_clause = ", ".join(f"{k} = ?" for k in filtered)
            values = list(filtered.values()) + [subtask_id]
            await db.execute(f"UPDATE task_subtasks SET {set_clause} WHERE id = ?", values)
            await db.commit()
            async with db.execute("SELECT * FROM task_subtasks WHERE id = ?", (subtask_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db.close()

    async def delete_subtask(self, subtask_id: int) -> bool:
        db = await self._get_db()
        try:
            cursor = await db.execute("DELETE FROM task_subtasks WHERE id = ?", (subtask_id,))
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    # ── Reminders ────────────────────────────────────────────────

    async def _get_reminders(self, db: aiosqlite.Connection, task_id: int) -> list[dict]:
        async with db.execute(
            "SELECT * FROM task_reminders WHERE task_id = ? ORDER BY remind_at", (task_id,)
        ) as cursor:
            return [dict(row) async for row in cursor]

    async def add_reminder(
        self, task_id: int, remind_at: str,
        repeat_type: str = "none", repeat_interval: int = 1,
        repeat_days: str = "", repeat_end_date: str | None = None,
    ) -> Optional[dict]:
        db = await self._get_db()
        try:
            cursor = await db.execute(
                """INSERT INTO task_reminders
                   (task_id, remind_at, repeat_type, repeat_interval, repeat_days, repeat_end_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (task_id, remind_at, repeat_type, repeat_interval, repeat_days, repeat_end_date),
            )
            reminder_id = cursor.lastrowid
            await db.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), task_id),
            )
            await db.commit()
            async with db.execute("SELECT * FROM task_reminders WHERE id = ?", (reminder_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db.close()

    async def delete_reminder(self, reminder_id: int) -> bool:
        db = await self._get_db()
        try:
            cursor = await db.execute("DELETE FROM task_reminders WHERE id = ?", (reminder_id,))
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    async def get_pending_reminders(self) -> list[dict]:
        db = await self._get_db()
        try:
            now = datetime.utcnow().isoformat()
            async with db.execute(
                "SELECT r.*, t.title as task_title "
                "FROM task_reminders r JOIN tasks t ON r.task_id = t.id "
                "WHERE r.is_triggered = 0 AND r.remind_at <= ?",
                (now,),
            ) as cursor:
                return [dict(row) async for row in cursor]
        finally:
            await db.close()

    async def mark_reminder_triggered(self, reminder_id: int) -> bool:
        db = await self._get_db()
        try:
            cursor = await db.execute(
                "UPDATE task_reminders SET is_triggered = 1 WHERE id = ?", (reminder_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    # ── Attachments ──────────────────────────────────────────────

    async def _get_attachments(self, db: aiosqlite.Connection, task_id: int) -> list[dict]:
        async with db.execute(
            "SELECT * FROM task_attachments WHERE task_id = ? ORDER BY created_at", (task_id,)
        ) as cursor:
            return [dict(row) async for row in cursor]

    async def add_attachment(
        self, task_id: int, file_name: str, file_path: str,
        file_type: str = "", file_size: int = 0,
    ) -> Optional[dict]:
        db = await self._get_db()
        try:
            cursor = await db.execute(
                """INSERT INTO task_attachments (task_id, file_name, file_path, file_type, file_size)
                   VALUES (?, ?, ?, ?, ?)""",
                (task_id, file_name, file_path, file_type, file_size),
            )
            att_id = cursor.lastrowid
            await db.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), task_id),
            )
            await db.commit()
            async with db.execute("SELECT * FROM task_attachments WHERE id = ?", (att_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db.close()

    async def delete_attachment(self, attachment_id: int) -> bool:
        db = await self._get_db()
        try:
            cursor = await db.execute("DELETE FROM task_attachments WHERE id = ?", (attachment_id,))
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    # ── Habits ───────────────────────────────────────────────────

    async def create_habit(
        self, title: str, description: str = "",
        frequency: str = "daily", target_days: str = "",
        color: str = "", icon: str = "",
        reminder_time: str = "", sort_order: int = 0,
    ) -> dict:
        db = await self._get_db()
        try:
            now = datetime.utcnow().isoformat()
            cursor = await db.execute(
                """INSERT INTO task_habits
                   (title, description, frequency, target_days,
                    color, icon, reminder_time, sort_order,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, description, frequency, target_days,
                 color, icon, reminder_time, sort_order, now, now),
            )
            habit_id = cursor.lastrowid
            await db.commit()
            return await self.get_habit(habit_id)
        finally:
            await db.close()

    async def get_habit(self, habit_id: int) -> Optional[dict]:
        db = await self._get_db()
        try:
            async with db.execute("SELECT * FROM task_habits WHERE id = ?", (habit_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                habit = dict(row)
                habit["checkins"] = await self._get_habit_checkins(db, habit_id)
                habit["streak"] = await self._calculate_streak(db, habit_id)
                return habit
        finally:
            await db.close()

    async def update_habit(self, habit_id: int, **updates: Any) -> Optional[dict]:
        db = await self._get_db()
        try:
            allowed = {
                "title", "description", "frequency", "target_days",
                "color", "icon", "reminder_time", "sort_order",
            }
            filtered = {k: v for k, v in updates.items() if k in allowed}
            if not filtered:
                return await self.get_habit(habit_id)
            filtered["updated_at"] = datetime.utcnow().isoformat()
            set_clause = ", ".join(f"{k} = ?" for k in filtered)
            values = list(filtered.values()) + [habit_id]
            await db.execute(f"UPDATE task_habits SET {set_clause} WHERE id = ?", values)
            await db.commit()
            return await self.get_habit(habit_id)
        finally:
            await db.close()

    async def delete_habit(self, habit_id: int) -> bool:
        db = await self._get_db()
        try:
            cursor = await db.execute("DELETE FROM task_habits WHERE id = ?", (habit_id,))
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    async def list_habits(self) -> list[dict]:
        db = await self._get_db()
        try:
            async with db.execute("SELECT * FROM task_habits ORDER BY sort_order, created_at") as cursor:
                habits = [dict(row) async for row in cursor]
            for habit in habits:
                habit["checkins"] = await self._get_habit_checkins(db, habit["id"])
                habit["streak"] = await self._calculate_streak(db, habit["id"])
            return habits
        finally:
            await db.close()

    async def checkin_habit(self, habit_id: int, date: str | None = None, note: str = "") -> Optional[dict]:
        db = await self._get_db()
        try:
            checkin_date = date or datetime.utcnow().strftime("%Y-%m-%d")
            now = datetime.utcnow().isoformat()
            try:
                cursor = await db.execute(
                    "INSERT INTO habit_checkins (habit_id, checkin_date, note, created_at) VALUES (?, ?, ?, ?)",
                    (habit_id, checkin_date, note, now),
                )
                checkin_id = cursor.lastrowid
            except aiosqlite.IntegrityError:
                await db.execute(
                    "UPDATE habit_checkins SET note = ? WHERE habit_id = ? AND checkin_date = ?",
                    (note, habit_id, checkin_date),
                )
                checkin_id = -1
            await db.execute(
                "UPDATE task_habits SET updated_at = ? WHERE id = ?",
                (now, habit_id),
            )
            await db.commit()
            if checkin_id > 0:
                async with db.execute("SELECT * FROM habit_checkins WHERE id = ?", (checkin_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
            return {"habit_id": habit_id, "checkin_date": checkin_date, "note": note}
        finally:
            await db.close()

    async def uncheckin_habit(self, habit_id: int, date: str) -> bool:
        db = await self._get_db()
        try:
            cursor = await db.execute(
                "DELETE FROM habit_checkins WHERE habit_id = ? AND checkin_date = ?",
                (habit_id, date),
            )
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    async def _get_habit_checkins(self, db: aiosqlite.Connection, habit_id: int) -> list[dict]:
        async with db.execute(
            "SELECT * FROM habit_checkins WHERE habit_id = ? ORDER BY checkin_date DESC",
            (habit_id,),
        ) as cursor:
            return [dict(row) async for row in cursor]

    async def _calculate_streak(self, db: aiosqlite.Connection, habit_id: int) -> int:
        async with db.execute(
            "SELECT checkin_date FROM habit_checkins WHERE habit_id = ? ORDER BY checkin_date DESC",
            (habit_id,),
        ) as cursor:
            dates = [row[0] async for row in cursor]
        if not dates:
            return 0
        streak = 0
        today = datetime.utcnow().date()
        for d in dates:
            try:
                checkin_date = datetime.strptime(d, "%Y-%m-%d").date()
                expected = today - timedelta(days=streak)
                if checkin_date == expected:
                    streak += 1
                elif checkin_date > expected:
                    continue
                else:
                    break
            except ValueError:
                break
        return streak

    # ── Pomodoro ─────────────────────────────────────────────────

    async def get_pomodoro_settings(self) -> dict:
        db = await self._get_db()
        try:
            async with db.execute("SELECT * FROM pomodoro_settings ORDER BY id DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            return {
                "focus_duration": 25, "break_duration": 5,
                "long_break_duration": 15, "sessions_before_long_break": 4,
                "auto_start_break": 1, "auto_start_focus": 0,
            }
        finally:
            await db.close()

    async def update_pomodoro_settings(self, **updates: Any) -> dict:
        db = await self._get_db()
        try:
            allowed = {
                "focus_duration", "break_duration", "long_break_duration",
                "sessions_before_long_break", "auto_start_break", "auto_start_focus",
            }
            filtered = {k: v for k, v in updates.items() if k in allowed}
            if not filtered:
                return await self.get_pomodoro_settings()
            filtered["updated_at"] = datetime.utcnow().isoformat()

            async with db.execute("SELECT id FROM pomodoro_settings ORDER BY id DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
            if row:
                set_clause = ", ".join(f"{k} = ?" for k in filtered)
                values = list(filtered.values()) + [row[0]]
                await db.execute(f"UPDATE pomodoro_settings SET {set_clause} WHERE id = ?", values)
            else:
                cols = ", ".join(filtered.keys())
                placeholders = ", ".join("?" for _ in filtered)
                await db.execute(
                    f"INSERT INTO pomodoro_settings ({cols}) VALUES ({placeholders})",
                    list(filtered.values()),
                )
            await db.commit()
            return await self.get_pomodoro_settings()
        finally:
            await db.close()

    async def create_pomodoro_session(
        self, task_id: int | None = None, habit_id: int | None = None,
        focus_duration: int | None = None, break_duration: int | None = None,
        long_break_duration: int | None = None,
        sessions_before_long_break: int | None = None,
    ) -> dict:
        db = await self._get_db()
        try:
            settings = await self.get_pomodoro_settings()
            now = datetime.utcnow().isoformat()
            cursor = await db.execute(
                """INSERT INTO pomodoro_sessions
                   (task_id, habit_id, focus_duration, break_duration, long_break_duration,
                    sessions_before_long_break, status, started_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'focusing', ?, ?)""",
                (task_id, habit_id,
                 focus_duration or settings["focus_duration"],
                 break_duration or settings["break_duration"],
                 long_break_duration or settings["long_break_duration"],
                 sessions_before_long_break or settings["sessions_before_long_break"],
                 now, now),
            )
            session_id = cursor.lastrowid
            await db.commit()
            return await self.get_pomodoro_session(session_id)
        finally:
            await db.close()

    async def get_pomodoro_session(self, session_id: int) -> Optional[dict]:
        db = await self._get_db()
        try:
            async with db.execute("SELECT * FROM pomodoro_sessions WHERE id = ?", (session_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            await db.close()

    async def complete_pomodoro_session(self, session_id: int) -> Optional[dict]:
        db = await self._get_db()
        try:
            now = datetime.utcnow().isoformat()
            await db.execute(
                "UPDATE pomodoro_sessions SET status = 'completed', completed_at = ? WHERE id = ?",
                (now, session_id),
            )
            await db.commit()
            return await self.get_pomodoro_session(session_id)
        finally:
            await db.close()

    async def cancel_pomodoro_session(self, session_id: int) -> Optional[dict]:
        db = await self._get_db()
        try:
            now = datetime.utcnow().isoformat()
            await db.execute(
                "UPDATE pomodoro_sessions SET status = 'cancelled', completed_at = ? WHERE id = ?",
                (now, session_id),
            )
            await db.commit()
            return await self.get_pomodoro_session(session_id)
        finally:
            await db.close()

    async def list_pomodoro_sessions(
        self, task_id: int | None = None, limit: int = 50,
    ) -> list[dict]:
        db = await self._get_db()
        try:
            if task_id:
                async with db.execute(
                    "SELECT * FROM pomodoro_sessions WHERE task_id = ? ORDER BY created_at DESC LIMIT ?",
                    (task_id, limit),
                ) as cursor:
                    return [dict(row) async for row in cursor]
            async with db.execute(
                "SELECT * FROM pomodoro_sessions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ) as cursor:
                return [dict(row) async for row in cursor]
        finally:
            await db.close()

    # ── Smart Recognition ────────────────────────────────────────

    def parse_smart_text(self, text: str) -> dict:
        result: dict[str, Any] = {
            "title": text,
            "due_date": None,
            "due_time": None,
            "priority": "none",
            "importance": "normal",
            "urgency": "normal",
            "tags": [],
            "reminders": [],
        }

        now = datetime.now()

        priority_patterns = [
            (r"(?:紧急|urgent|!!!|重要|important|!\s*!)\s*", "urgent"),
            (r"(?:高优先|high\s*priority|!!)\s*", "high"),
            (r"(?:中优先|medium\s*priority|!)\s*", "medium"),
            (r"(?:低优先|low\s*priority)\s*", "low"),
        ]
        for pattern, pri in priority_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result["priority"] = pri
                if pri in ("urgent", "high"):
                    result["importance"] = "important"
                    result["urgency"] = "urgent"
                text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

        relative_days = {
            "今天": 0, "今日": 0, "today": 0,
            "明天": 1, "明日": 1, "tomorrow": 1,
            "后天": 2, "後天": 2, "day after tomorrow": 2,
        }
        for keyword, delta in relative_days.items():
            if keyword in text.lower():
                target = now + timedelta(days=delta)
                result["due_date"] = target.strftime("%Y-%m-%d")
                text = text.replace(keyword, "").strip()
                break

        weekday_map = {
            "周一": 0, "星期一": 0, "monday": 0,
            "周二": 1, "星期二": 1, "tuesday": 1,
            "周三": 2, "星期三": 2, "wednesday": 2,
            "周四": 3, "星期四": 3, "thursday": 3,
            "周五": 4, "星期五": 4, "friday": 4,
            "周六": 5, "星期六": 5, "saturday": 5,
            "周日": 6, "星期日": 6, "sunday": 6,
        }
        if not result["due_date"]:
            for keyword, target_weekday in weekday_map.items():
                if keyword in text.lower():
                    days_ahead = target_weekday - now.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target = now + timedelta(days=days_ahead)
                    result["due_date"] = target.strftime("%Y-%m-%d")
                    text = text.replace(keyword, "").strip()
                    break

        if not result["due_date"]:
            date_match = re.search(
                r"(?:on\s+)?(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text
            )
            if date_match:
                y = date_match.group(1)
                m = int(date_match.group(2))
                d = int(date_match.group(3))
                result["due_date"] = f"{y}-{m:02d}-{d:02d}"
                text = text[:date_match.start()] + text[date_match.end():]
                text = text.strip()
            else:
                date_match = re.search(
                    r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?", text
                )
                if date_match:
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    year = int(date_match.group(3)) if date_match.group(3) else now.year
                    if year < 100:
                        year += 2000
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        result["due_date"] = f"{year}-{month:02d}-{day:02d}"
                        text = text[:date_match.start()] + text[date_match.end():]
                        text = text.strip()

        time_match = re.search(
            r"(?:at\s+)?(\d{1,2}):(\d{2})(?:\s*(am|pm|AM|PM))?", text
        )
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            ampm = time_match.group(3)
            if ampm:
                if ampm.lower() == "pm" and hour < 12:
                    hour += 12
                elif ampm.lower() == "am" and hour == 12:
                    hour = 0
            result["due_time"] = f"{hour:02d}:{minute:02d}"
            text = text[:time_match.start()] + text[time_match.end():]
            text = text.strip()
        else:
            cn_time_match = re.search(r"(\d{1,2})点(?:(\d{1,2})分?)?(?:半)?", text)
            if cn_time_match:
                hour = int(cn_time_match.group(1))
                minute = int(cn_time_match.group(2)) if cn_time_match.group(2) else 0
                if "半" in cn_time_match.group(0):
                    minute = 30
                result["due_time"] = f"{hour:02d}:{minute:02d}"
                text = text[:cn_time_match.start()] + text[cn_time_match.end():]
                text = text.strip()

        tag_matches = re.findall(r"[#＃](\S+)", text)
        if tag_matches:
            result["tags"] = tag_matches
            text = re.sub(r"[#＃]\S+\s*", "", text).strip()

        if result["due_date"] and result["due_time"]:
            remind_at = f"{result['due_date']}T{result['due_time']}:00"
            result["reminders"] = [{"remind_at": remind_at, "repeat_type": "none"}]

        result["title"] = text.strip() or "Untitled"
        return result

    async def create_task_smart(self, text: str, source: str = "smart") -> dict:
        parsed = self.parse_smart_text(text)
        return await self.create_task(
            title=parsed["title"],
            priority=parsed["priority"],
            importance=parsed["importance"],
            urgency=parsed["urgency"],
            due_date=parsed["due_date"],
            due_time=parsed["due_time"],
            tags=parsed["tags"],
            source=source,
            reminders=parsed["reminders"],
        )


todo_service = TodoService()
