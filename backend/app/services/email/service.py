import asyncio
import imaplib
import json
import logging
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import aiosqlite

from .models import (
    EmailFolder,
    MessageChannelSyncStatus,
    MessageDirection,
    MessageParticipant,
    MessageParticipantRole,
    SendMessageInput,
)
from .parser import EmailParser

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, db_path: str = "data/emails.db"):
        self.db_path = db_path
        self._init_db_lock = asyncio.Lock()
        self._encryption_key = self._get_or_create_key()
        self._parser = EmailParser()

    @staticmethod
    def _get_or_create_key() -> bytes:
        key_path = Path("data/.email_key")
        try:
            from cryptography.fernet import Fernet
            if key_path.exists():
                return key_path.read_bytes()
            key = Fernet.generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_bytes(key)
            return key
        except ImportError:
            import base64
            import hashlib
            if key_path.exists():
                return key_path.read_bytes()
            key = base64.urlsafe_b64encode(hashlib.sha256(b"polyspace_email_key").digest())
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_bytes(key)
            return key

    def _encrypt_password(self, password: str) -> str:
        try:
            from cryptography.fernet import Fernet
            return Fernet(self._encryption_key).encrypt(password.encode()).decode()
        except ImportError:
            import base64
            return base64.b64encode(password.encode()).decode()

    def _decrypt_password(self, encrypted: str) -> str:
        try:
            from cryptography.fernet import Fernet
            return Fernet(self._encryption_key).decrypt(encrypted.encode()).decode()
        except ImportError:
            import base64
            return base64.b64decode(encrypted.encode()).decode()

    async def _init_db(self):
        async with self._init_db_lock:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS email_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email_address TEXT NOT NULL UNIQUE,
                        provider TEXT DEFAULT 'imap_smtp',
                        imap_host TEXT NOT NULL,
                        imap_port INTEGER DEFAULT 993,
                        smtp_host TEXT NOT NULL,
                        smtp_port INTEGER DEFAULT 587,
                        username TEXT NOT NULL,
                        password_encrypted TEXT NOT NULL,
                        use_ssl INTEGER DEFAULT 1,
                        handle_aliases TEXT DEFAULT '',
                        sync_status TEXT DEFAULT 'not_synced',
                        sync_cursor TEXT DEFAULT '',
                        last_synced_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS emails (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER NOT NULL,
                        message_id TEXT,
                        thread_id TEXT DEFAULT '',
                        subject TEXT,
                        text TEXT,
                        html TEXT,
                        direction TEXT DEFAULT 'incoming',
                        participants TEXT DEFAULT '[]',
                        attachments TEXT DEFAULT '[]',
                        folder TEXT DEFAULT 'INBOX',
                        is_read INTEGER DEFAULT 0,
                        is_starred INTEGER DEFAULT 0,
                        is_deleted INTEGER DEFAULT 0,
                        category TEXT DEFAULT '',
                        priority TEXT DEFAULT '',
                        date_received TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (account_id) REFERENCES email_accounts(id)
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS email_drafts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER NOT NULL,
                        subject TEXT,
                        to_addresses TEXT DEFAULT '',
                        cc TEXT DEFAULT '',
                        bcc TEXT DEFAULT '',
                        body_text TEXT,
                        body_html TEXT DEFAULT '',
                        thread_id TEXT DEFAULT '',
                        in_reply_to TEXT DEFAULT '',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (account_id) REFERENCES email_accounts(id)
                    )
                """)
                try:
                    await db.execute(
                        "CREATE INDEX IF NOT EXISTS "
                        "idx_emails_account_folder ON emails(account_id, folder, is_deleted)"
                    )
                    await db.execute(
                        "CREATE INDEX IF NOT EXISTS idx_emails_thread ON emails(thread_id)"
                    )
                    await db.execute(
                        "CREATE INDEX IF NOT EXISTS idx_emails_message_id ON emails(message_id)"
                    )
                    await db.execute(
                        "CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date_received)"
                    )
                except Exception:
                    pass
                await db.commit()

    async def add_account(self, name: str, email_address: str, imap_host: str,
                          smtp_host: str, username: str, password: str,
                          imap_port: int = 993, smtp_port: int = 587,
                          use_ssl: bool = True,
                          provider: str = "imap_smtp") -> int:
        await self._init_db()
        password_encrypted = self._encrypt_password(password)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO email_accounts
                   (name, email_address, provider, imap_host, imap_port, smtp_host, smtp_port,
                    username, password_encrypted, use_ssl)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, email_address, provider, imap_host, imap_port, smtp_host, smtp_port,
                 username, password_encrypted, 1 if use_ssl else 0)
            )
            await db.commit()
            return cursor.lastrowid

    async def list_accounts(self) -> list[dict]:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, name, email_address, provider, "
                "imap_host, imap_port, smtp_host, smtp_port, "
                "use_ssl, handle_aliases, sync_status, sync_cursor, "
                "last_synced_at, created_at FROM email_accounts"
            ) as cursor:
                return [dict(row) async for row in cursor]

    async def get_account(self, account_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM email_accounts WHERE id = ?", (account_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_account(self, account_id: int, **kwargs) -> bool:
        allowed_fields = {"name", "imap_host", "imap_port", "smtp_host", "smtp_port",
                          "use_ssl", "handle_aliases"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [account_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE email_accounts SET {set_clause} WHERE id = ?", values)
            await db.commit()
            return True

    async def delete_account(self, account_id: int):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM emails WHERE account_id = ?", (account_id,))
            await db.execute("DELETE FROM email_drafts WHERE account_id = ?", (account_id,))
            await db.execute("DELETE FROM email_accounts WHERE id = ?", (account_id,))
            await db.commit()

    async def fetch_emails(self, account_id: int, folder: str = "INBOX",
                           limit: int = 50, offset: int = 0,
                           search: str = "") -> list[dict]:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if search:
                query = """SELECT id, message_id, thread_id, subject, text, html, direction,
                                  participants, attachments, folder, is_read, is_starred,
                                  category, priority, date_received
                           FROM emails
                           WHERE account_id = ? AND folder = ? AND is_deleted = 0
                             AND (subject LIKE ? OR text LIKE ?)
                           ORDER BY date_received DESC
                           LIMIT ? OFFSET ?"""
                params = (account_id, folder, f"%{search}%", f"%{search}%", limit, offset)
            else:
                query = """SELECT id, message_id, thread_id, subject, text, html, direction,
                                  participants, attachments, folder, is_read, is_starred,
                                  category, priority, date_received
                           FROM emails
                           WHERE account_id = ? AND folder = ? AND is_deleted = 0
                           ORDER BY date_received DESC
                           LIMIT ? OFFSET ?"""
                params = (account_id, folder, limit, offset)
            async with db.execute(query, params) as cursor:
                results = []
                async for row in cursor:
                    d = dict(row)
                    try:
                        import json
                        d["participants"] = json.loads(d.get("participants", "[]"))
                        d["attachments"] = json.loads(d.get("attachments", "[]"))
                    except Exception:
                        d["participants"] = []
                        d["attachments"] = []
                    results.append(d)
                return results

    async def get_email(self, email_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM emails WHERE id = ?", (email_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                d = dict(row)
                try:
                    import json
                    d["participants"] = json.loads(d.get("participants", "[]"))
                    d["attachments"] = json.loads(d.get("attachments", "[]"))
                except Exception:
                    d["participants"] = []
                    d["attachments"] = []
                return d

    async def get_thread_emails(self, thread_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM emails WHERE thread_id = ? AND is_deleted = 0
                   ORDER BY date_received ASC""",
                (thread_id,)
            ) as cursor:
                results = []
                async for row in cursor:
                    d = dict(row)
                    try:
                        import json
                        d["participants"] = json.loads(d.get("participants", "[]"))
                        d["attachments"] = json.loads(d.get("attachments", "[]"))
                    except Exception:
                        d["participants"] = []
                        d["attachments"] = []
                    results.append(d)
                return results

    async def sync_emails(self, account_id: int, folder: str = "INBOX",
                          limit: int = 50) -> int:
        await self._init_db()
        account = await self.get_account(account_id)
        if not account:
            return 0

        password = self._decrypt_password(account["password_encrypted"])

        try:
            if account["use_ssl"]:
                imap = imaplib.IMAP4_SSL(account["imap_host"], account["imap_port"])
            else:
                imap = imaplib.IMAP4(account["imap_host"], account["imap_port"])

            imap.login(account["username"], password)
            imap.select(folder)

            _, message_ids = imap.search(None, "ALL")
            synced = 0

            import json

            for mid in message_ids[0].split()[-limit:]:
                _, msg_data = imap.fetch(mid, "(RFC822)")
                raw_email = msg_data[0][1]

                parsed = self._parser.parse_raw_message(
                    raw_email,
                    account_address=account["email_address"],
                    folder=folder,
                    uid=int(mid),
                    account_id=account_id,
                )
                if not parsed:
                    continue

                participants_json = json.dumps([p.to_dict() for p in parsed.participants])
                attachments_json = json.dumps([a.to_dict() for a in parsed.attachments])

                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute(
                        """INSERT OR IGNORE INTO emails
                           (account_id, message_id, thread_id, subject, text, html, direction,
                            participants, attachments, folder, date_received)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (account_id, parsed.message_id, parsed.thread_id,
                         parsed.subject, parsed.text, parsed.html,
                         parsed.direction.value, participants_json, attachments_json,
                         folder, parsed.received_at.isoformat() if parsed.received_at else "")
                    )
                    await db.commit()
                synced += 1

            imap.logout()

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE email_accounts SET sync_status = ?, last_synced_at = ? WHERE id = ?",
                    (MessageChannelSyncStatus.ACTIVE.value, datetime.utcnow().isoformat(), account_id)
                )
                await db.commit()

            return synced

        except Exception as e:
            logger.error(f"Email sync failed for account {account_id}: {e}")
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE email_accounts SET sync_status = ? WHERE id = ?",
                    (MessageChannelSyncStatus.FAILED.value, account_id)
                )
                await db.commit()
            return 0

    async def list_folders(self, account_id: int) -> list[dict]:
        account = await self.get_account(account_id)
        if not account:
            return []

        password = self._decrypt_password(account["password_encrypted"])
        folders = []

        try:
            if account["use_ssl"]:
                imap = imaplib.IMAP4_SSL(account["imap_host"], account["imap_port"])
            else:
                imap = imaplib.IMAP4(account["imap_host"], account["imap_port"])

            imap.login(account["username"], password)
            _, folder_list = imap.list()

            for f in folder_list:
                if not f:
                    continue
                try:
                    parts = f.decode("utf-8", errors="replace").split('"/"')
                    if len(parts) >= 2:
                        name = parts[-1].strip().strip('"')
                    else:
                        name = f.decode("utf-8", errors="replace").strip()
                    is_sent = name.lower() in ("sent", "sent items", "sent mail", "已发送")
                    is_drafts = name.lower() in ("drafts", "draft", "草稿箱")
                    is_trash = name.lower() in ("trash", "deleted items", "已删除", "垃圾箱")
                    is_spam = name.lower() in ("spam", "junk", "垃圾邮件")
                    folders.append(EmailFolder(
                        name=name, path=name,
                        is_sent_folder=is_sent, is_drafts_folder=is_drafts,
                        is_trash_folder=is_trash, is_spam_folder=is_spam,
                    ).to_dict())
                except Exception:
                    continue

            imap.logout()
        except Exception as e:
            logger.error(f"List folders failed for account {account_id}: {e}")

        return folders

    async def send_email(self, account_id: int, send_input: SendMessageInput) -> bool:
        await self._init_db()
        account = await self.get_account(account_id)
        if not account:
            return False

        password = self._decrypt_password(account["password_encrypted"])

        try:
            msg = MIMEMultipart("alternative" if send_input.html else "mixed")
            msg["From"] = account["email_address"]
            msg["To"] = ", ".join(send_input.to_list)
            msg["Subject"] = send_input.subject

            if send_input.cc_list:
                msg["Cc"] = ", ".join(send_input.cc_list)
            if send_input.bcc_list:
                msg["Bcc"] = ", ".join(send_input.bcc_list)
            if send_input.in_reply_to:
                msg["In-Reply-To"] = send_input.in_reply_to
                msg["References"] = send_input.in_reply_to

            if send_input.body:
                msg.attach(MIMEText(send_input.body, "plain"))
            if send_input.html:
                msg.attach(MIMEText(send_input.html, "html"))

            for att in send_input.attachments:
                if att.data:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(att.data)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={att.filename}",
                    )
                    msg.attach(part)

            with smtplib.SMTP(account["smtp_host"], account["smtp_port"]) as server:
                server.starttls()
                server.login(account["username"], password)
                recipients = send_input.to_list + send_input.cc_list + send_input.bcc_list
                server.sendmail(account["email_address"], recipients, msg.as_string())

            participants = [
                MessageParticipant(
                    role=MessageParticipantRole.FROM,
                    address=account["email_address"],
                ).to_dict(),
            ]
            for addr in send_input.to_list:
                participants.append({"role": "to", "address": addr})
            for addr in send_input.cc_list:
                participants.append({"role": "cc", "address": addr})

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT INTO emails
                       (account_id, message_id, thread_id, subject, text, html, direction,
                        participants, attachments, folder, date_received)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'SENT', ?)""",
                    (account_id, "", send_input.thread_id, send_input.subject,
                     send_input.body, send_input.html, MessageDirection.OUTGOING.value,
                     json.dumps(participants), "[]",
                     datetime.utcnow().isoformat())
                )
                await db.commit()

            return True

        except Exception as e:
            logger.error(f"Send email failed for account {account_id}: {e}")
            return False

    async def save_draft(self, account_id: int, subject: str, to: str,
                         body: str, cc: str = "", bcc: str = "",
                         body_html: str = "", thread_id: str = "",
                         in_reply_to: str = "") -> int:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO email_drafts
                   (account_id, subject, to_addresses, cc, bcc,
                    body_text, body_html, thread_id, in_reply_to)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (account_id, subject, to, cc, bcc,
                 body, body_html, thread_id, in_reply_to)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_draft(self, draft_id: int, **kwargs) -> bool:
        allowed = {"subject", "to_addresses", "cc", "bcc", "body_text", "body_html", "thread_id", "in_reply_to"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [draft_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE email_drafts SET {set_clause} WHERE id = ?", values)
            await db.commit()
            return True

    async def list_drafts(self, account_id: int) -> list[dict]:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM email_drafts WHERE account_id = ? ORDER BY updated_at DESC",
                (account_id,)
            ) as cursor:
                return [dict(row) async for row in cursor]

    async def delete_draft(self, draft_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM email_drafts WHERE id = ?", (draft_id,))
            await db.commit()

    async def mark_read(self, email_id: int, is_read: bool = True):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE emails SET is_read = ? WHERE id = ?",
                (1 if is_read else 0, email_id)
            )
            await db.commit()

    async def mark_starred(self, email_id: int, is_starred: bool = True):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE emails SET is_starred = ? WHERE id = ?",
                (1 if is_starred else 0, email_id)
            )
            await db.commit()

    async def delete_email(self, email_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE emails SET is_deleted = 1 WHERE id = ?", (email_id,))
            await db.commit()

    async def move_email(self, email_id: int, folder: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE emails SET folder = ? WHERE id = ?", (folder, email_id)
            )
            await db.commit()

    async def batch_mark_read(self, email_ids: list[int], is_read: bool = True):
        if not email_ids:
            return
        async with aiosqlite.connect(self.db_path) as db:
            placeholders = ",".join("?" * len(email_ids))
            await db.execute(
                f"UPDATE emails SET is_read = ? WHERE id IN ({placeholders})",
                [1 if is_read else 0] + email_ids
            )
            await db.commit()

    async def batch_delete(self, email_ids: list[int]):
        if not email_ids:
            return
        async with aiosqlite.connect(self.db_path) as db:
            placeholders = ",".join("?" * len(email_ids))
            await db.execute(
                f"UPDATE emails SET is_deleted = 1 WHERE id IN ({placeholders})",
                email_ids
            )
            await db.commit()

    async def get_email_stats(self, account_id: int) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            stats = {}
            async with db.execute(
                "SELECT COUNT(*) as total FROM emails WHERE account_id = ? AND is_deleted = 0",
                (account_id,)
            ) as cursor:
                row = await cursor.fetchone()
                stats["total"] = row["total"] if row else 0
            async with db.execute(
                "SELECT COUNT(*) as unread FROM emails WHERE account_id = ? AND is_deleted = 0 AND is_read = 0",
                (account_id,)
            ) as cursor:
                row = await cursor.fetchone()
                stats["unread"] = row["unread"] if row else 0
            async with db.execute(
                "SELECT COUNT(*) as starred FROM emails WHERE account_id = ? AND is_deleted = 0 AND is_starred = 1",
                (account_id,)
            ) as cursor:
                row = await cursor.fetchone()
                stats["starred"] = row["starred"] if row else 0
            async with db.execute(
                "SELECT folder, COUNT(*) as count FROM emails WHERE account_id = ? AND is_deleted = 0 GROUP BY folder",
                (account_id,)
            ) as cursor:
                stats["by_folder"] = {row["folder"]: row["count"] async for row in cursor}
            return stats

    async def update_email_category_priority(self, email_id: int, category: str = "", priority: str = ""):
        async with aiosqlite.connect(self.db_path) as db:
            if category:
                await db.execute("UPDATE emails SET category = ? WHERE id = ?", (category, email_id))
            if priority:
                await db.execute("UPDATE emails SET priority = ? WHERE id = ?", (priority, email_id))
            await db.commit()


_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
