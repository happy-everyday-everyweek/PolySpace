import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite


class KanbanService:
    def __init__(self, db_path: str = "data/kanban.db"):
        self.db_path = db_path
        self._init_db_lock = asyncio.Lock()

    async def _init_db(self):
        async with self._init_db_lock:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS boards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS columns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        board_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        position INTEGER DEFAULT 0,
                        color TEXT DEFAULT '#7c6ff7',
                        wip_limit INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS cards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        column_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        assignee TEXT,
                        priority TEXT DEFAULT 'medium',
                        tags TEXT,
                        position INTEGER DEFAULT 0,
                        due_date TEXT,
                        archived INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
                    )
                """)
                await db.commit()

    async def create_board(self, name: str, description: str = "") -> int:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            cursor = await db.execute(
                "INSERT INTO boards (name, description) VALUES (?, ?)",
                (name, description)
            )
            board_id = cursor.lastrowid
            default_columns = [
                ("To Do", 0, "#9AA0A6", 0),
                ("In Progress", 1, "#FBBC04", 5),
                ("Done", 2, "#34A853", 0),
            ]
            for col_name, pos, color, wip in default_columns:
                await db.execute(
                    "INSERT INTO columns (board_id, name, position, color, wip_limit) VALUES (?, ?, ?, ?, ?)",
                    (board_id, col_name, pos, color, wip)
                )
            await db.commit()
            return board_id

    async def list_boards(self):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, name, description, created_at, updated_at FROM boards ORDER BY updated_at DESC"
            ) as cursor:
                return [dict(row) async for row in cursor]

    async def get_board(self, board_id: int) -> Optional[dict]:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, name, description FROM boards WHERE id = ?", (board_id,)
            ) as cursor:
                board = await cursor.fetchone()
                if not board:
                    return None
                board_dict = dict(board)
                async with db.execute(
                    """SELECT id, name, position, color, wip_limit FROM columns
                       WHERE board_id = ? ORDER BY position""",
                    (board_id,)
                ) as col_cursor:
                    columns = []
                    async for col in col_cursor:
                        col_dict = dict(col)
                        async with db.execute(
                            """SELECT id, title, description, assignee, priority, tags,
                                      position, due_date, archived, created_at, updated_at
                               FROM cards WHERE column_id = ? AND archived = 0 ORDER BY position""",
                            (col_dict["id"],)
                        ) as card_cursor:
                            col_dict["cards"] = [dict(card) async for card in card_cursor]
                        columns.append(col_dict)
                    board_dict["columns"] = columns
                return board_dict

    async def update_board(self, board_id: int, **kwargs):
        await self._init_db()
        allowed_fields = {"name", "description"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [board_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE boards SET {set_clause} WHERE id = ?", values)
            await db.commit()

    async def delete_board(self, board_id: int):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM boards WHERE id = ?", (board_id,))
            await db.commit()

    async def add_column(self, board_id: int, name: str, color: str = "#7c6ff7", wip_limit: int = 0) -> int:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM columns WHERE board_id = ?",
                (board_id,)
            ) as cursor:
                row = await cursor.fetchone()
                position = row[0] if row else 0
            cursor = await db.execute(
                "INSERT INTO columns (board_id, name, position, color, wip_limit) VALUES (?, ?, ?, ?, ?)",
                (board_id, name, position, color, wip_limit)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_column(self, column_id: int, **kwargs):
        await self._init_db()
        allowed_fields = {"name", "color", "position", "wip_limit"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [column_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE columns SET {set_clause} WHERE id = ?", values)
            await db.commit()

    async def delete_column(self, column_id: int):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM columns WHERE id = ?", (column_id,))
            await db.commit()

    async def reorder_columns(self, board_id: int, column_ids: list[int]):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            for position, col_id in enumerate(column_ids):
                await db.execute(
                    "UPDATE columns SET position = ? WHERE id = ? AND board_id = ?",
                    (position, col_id, board_id)
                )
            await db.commit()

    async def add_card(self, column_id: int, title: str, description: str = "",
                       assignee: str = "", priority: str = "medium",
                       tags: str = "", due_date: str = "") -> int:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM cards WHERE column_id = ?",
                (column_id,)
            ) as cursor:
                row = await cursor.fetchone()
                position = row[0] if row else 0
            cursor = await db.execute(
                """INSERT INTO cards (column_id, title, description, assignee, priority, tags, position, due_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (column_id, title, description, assignee, priority, tags, position, due_date)
            )
            await db.commit()
            return cursor.lastrowid

    async def move_card(self, card_id: int, target_column_id: int, target_position: int = 0):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT column_id, position FROM cards WHERE id = ?", (card_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return
                src_column_id, src_position = row[0], row[1]

            if src_column_id == target_column_id:
                if target_position > src_position:
                    await db.execute(
                        (
                            "UPDATE cards SET position = position - 1"
                            " WHERE column_id = ? AND position > ? AND position <= ?"
                        ),
                        (src_column_id, src_position, target_position)
                    )
                elif target_position < src_position:
                    await db.execute(
                        (
                            "UPDATE cards SET position = position + 1"
                            " WHERE column_id = ? AND position >= ? AND position < ?"
                        ),
                        (src_column_id, target_position, src_position)
                    )
            else:
                await db.execute(
                    "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
                    (src_column_id, src_position)
                )
                await db.execute(
                    "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
                    (target_column_id, target_position)
                )

            await db.execute(
                "UPDATE cards SET column_id = ?, position = ?, updated_at = ? WHERE id = ?",
                (target_column_id, target_position, datetime.utcnow().isoformat(), card_id)
            )
            await db.commit()

    async def update_card(self, card_id: int, **kwargs):
        await self._init_db()
        allowed_fields = {"title", "description", "assignee", "priority", "tags", "due_date"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [card_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE cards SET {set_clause} WHERE id = ?", values)
            await db.commit()

    async def delete_card(self, card_id: int):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cards WHERE id = ?", (card_id,))
            await db.commit()

    async def archive_card(self, card_id: int):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE cards SET archived = 1, updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), card_id)
            )
            await db.commit()

    async def unarchive_card(self, card_id: int):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT column_id FROM cards WHERE id = ?", (card_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return
            async with db.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM cards WHERE column_id = ? AND archived = 0",
                (row[0],)
            ) as cursor:
                pos_row = await cursor.fetchone()
                position = pos_row[0] if pos_row else 0
            await db.execute(
                "UPDATE cards SET archived = 0, position = ?, updated_at = ? WHERE id = ?",
                (position, datetime.utcnow().isoformat(), card_id)
            )
            await db.commit()

    async def get_archived_cards(self, board_id: int):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT c.* FROM cards c
                   JOIN columns col ON c.column_id = col.id
                   WHERE col.board_id = ? AND c.archived = 1
                   ORDER BY c.updated_at DESC""",
                (board_id,)
            ) as cursor:
                return [dict(row) async for row in cursor]

    async def search_cards(self, board_id: int, query: str):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            search_pattern = f"%{query}%"
            async with db.execute(
                """SELECT c.*, col.name as column_name FROM cards c
                   JOIN columns col ON c.column_id = col.id
                   WHERE col.board_id = ? AND c.archived = 0
                   AND (c.title LIKE ? OR c.description LIKE ? OR c.assignee LIKE ? OR c.tags LIKE ?)
                   ORDER BY c.position""",
                (board_id, search_pattern, search_pattern, search_pattern, search_pattern)
            ) as cursor:
                return [dict(row) async for row in cursor]

    async def get_board_stats(self, board_id: int) -> dict:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            stats = {"total_cards": 0, "by_priority": {}, "by_column": {}, "overdue": 0, "archived": 0}
            async with db.execute(
                """SELECT c.name, COUNT(cd.id) as count
                   FROM columns c LEFT JOIN cards cd ON c.id = cd.column_id AND cd.archived = 0
                   WHERE c.board_id = ?
                   GROUP BY c.id""",
                (board_id,)
            ) as cursor:
                async for row in cursor:
                    stats["by_column"][row["name"]] = row["count"]
                    stats["total_cards"] += row["count"]
            async with db.execute(
                (
                    "SELECT priority, COUNT(*) as count FROM cards"
                    " WHERE column_id IN (SELECT id FROM columns WHERE board_id = ?)"
                    " AND archived = 0 GROUP BY priority"
                ),
                (board_id,)
            ) as cursor:
                async for row in cursor:
                    stats["by_priority"][row["priority"]] = row["count"]
            async with db.execute(
                """SELECT COUNT(*) as count FROM cards
                   WHERE column_id IN (SELECT id FROM columns WHERE board_id = ?)
                   AND due_date < ? AND due_date != '' AND archived = 0""",
                (board_id, datetime.utcnow().strftime("%Y-%m-%d"))
            ) as cursor:
                row = await cursor.fetchone()
                stats["overdue"] = row[0] if row else 0
            async with db.execute(
                """SELECT COUNT(*) as count FROM cards
                   WHERE column_id IN (SELECT id FROM columns WHERE board_id = ?) AND archived = 1""",
                (board_id,)
            ) as cursor:
                row = await cursor.fetchone()
                stats["archived"] = row[0] if row else 0
            return stats
