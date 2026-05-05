from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class EmailProvider(Enum):
    IMAP_SMTP = "imap_smtp"
    GMAIL = "gmail"
    MICROSOFT = "microsoft"


class MessageDirection(Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class MessageParticipantRole(Enum):
    FROM = "from"
    TO = "to"
    CC = "cc"
    BCC = "bcc"


class MessageChannelSyncStatus(Enum):
    NOT_SYNCED = "not_synced"
    ONGOING = "ongoing"
    ACTIVE = "active"
    FAILED = "failed"


class EmailCategory(Enum):
    WORK = "work"
    PERSONAL = "personal"
    PROMOTIONAL = "promotional"
    SOCIAL = "social"
    FINANCIAL = "financial"
    TRAVEL = "travel"
    SHOPPING = "shopping"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class EmailPriority(Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class EmailAttachment:
    filename: str
    content_type: str = "application/octet-stream"
    size: int = 0
    data: Optional[bytes] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
        }


@dataclass
class MessageParticipant:
    role: MessageParticipantRole
    address: str
    display_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "address": self.address,
            "display_name": self.display_name,
        }


@dataclass
class EmailMessage:
    message_id: str = ""
    thread_id: str = ""
    subject: str = ""
    text: str = ""
    html: str = ""
    direction: MessageDirection = MessageDirection.INCOMING
    participants: list[MessageParticipant] = field(default_factory=list)
    attachments: list[EmailAttachment] = field(default_factory=list)
    received_at: Optional[datetime] = None
    is_read: bool = False
    is_starred: bool = False
    is_deleted: bool = False
    folder: str = "INBOX"
    account_id: int = 0
    db_id: int = 0
    category: str = ""
    priority: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.db_id,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "text": self.text,
            "html": self.html,
            "direction": self.direction.value,
            "participants": [p.to_dict() for p in self.participants],
            "attachments": [a.to_dict() for a in self.attachments],
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "is_read": self.is_read,
            "is_starred": self.is_starred,
            "is_deleted": self.is_deleted,
            "folder": self.folder,
            "account_id": self.account_id,
            "category": self.category,
            "priority": self.priority,
        }

    @property
    def sender(self) -> str:
        for p in self.participants:
            if p.role == MessageParticipantRole.FROM:
                return p.display_name or p.address
        return ""

    @property
    def sender_address(self) -> str:
        for p in self.participants:
            if p.role == MessageParticipantRole.FROM:
                return p.address
        return ""

    @property
    def to_addresses(self) -> list[str]:
        return [p.address for p in self.participants if p.role == MessageParticipantRole.TO]

    @property
    def cc_addresses(self) -> list[str]:
        return [p.address for p in self.participants if p.role == MessageParticipantRole.CC]

    @property
    def body_preview(self) -> str:
        text = self.text or self.html
        if not text:
            return ""
        return text[:200] + "..." if len(text) > 200 else text


@dataclass
class EmailAccount:
    id: int = 0
    name: str = ""
    email_address: str = ""
    provider: EmailProvider = EmailProvider.IMAP_SMTP
    imap_host: str = ""
    imap_port: int = 993
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    password_encrypted: str = ""
    use_ssl: bool = True
    handle_aliases: str = ""
    sync_status: MessageChannelSyncStatus = MessageChannelSyncStatus.NOT_SYNCED
    sync_cursor: str = ""
    last_synced_at: Optional[str] = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email_address": self.email_address,
            "provider": self.provider.value,
            "imap_host": self.imap_host,
            "imap_port": self.imap_port,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "username": self.username,
            "use_ssl": self.use_ssl,
            "handle_aliases": self.handle_aliases,
            "sync_status": self.sync_status.value,
            "sync_cursor": self.sync_cursor,
            "last_synced_at": self.last_synced_at,
            "created_at": self.created_at,
        }


@dataclass
class EmailDraft:
    id: int = 0
    account_id: int = 0
    subject: str = ""
    to: str = ""
    cc: str = ""
    bcc: str = ""
    body_text: str = ""
    body_html: str = ""
    thread_id: str = ""
    in_reply_to: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "subject": self.subject,
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "thread_id": self.thread_id,
            "in_reply_to": self.in_reply_to,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class EmailFolder:
    name: str = ""
    path: str = ""
    delimiter: str = "/"
    is_sent_folder: bool = False
    is_drafts_folder: bool = False
    is_trash_folder: bool = False
    is_spam_folder: bool = False
    parent_folder: str = ""
    total_messages: int = 0
    unread_messages: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "delimiter": self.delimiter,
            "is_sent_folder": self.is_sent_folder,
            "is_drafts_folder": self.is_drafts_folder,
            "is_trash_folder": self.is_trash_folder,
            "is_spam_folder": self.is_spam_folder,
            "parent_folder": self.parent_folder,
            "total_messages": self.total_messages,
            "unread_messages": self.unread_messages,
        }


@dataclass
class SendMessageInput:
    to: str | list[str]
    subject: str
    body: str = ""
    html: str = ""
    cc: str | list[str] | None = None
    bcc: str | list[str] | None = None
    in_reply_to: str = ""
    thread_id: str = ""
    attachments: list[EmailAttachment] = field(default_factory=list)

    @property
    def to_list(self) -> list[str]:
        return [self.to] if isinstance(self.to, str) else self.to

    @property
    def cc_list(self) -> list[str]:
        if self.cc is None:
            return []
        return [self.cc] if isinstance(self.cc, str) else self.cc

    @property
    def bcc_list(self) -> list[str]:
        if self.bcc is None:
            return []
        return [self.bcc] if isinstance(self.bcc, str) else self.bcc
