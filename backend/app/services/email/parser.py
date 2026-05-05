import email
import re
from email.policy import default as default_policy
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional

from .models import (
    EmailAttachment,
    EmailMessage,
    MessageDirection,
    MessageParticipant,
    MessageParticipantRole,
)


class EmailParser:
    @staticmethod
    def parse_raw_message(
        raw_email: bytes,
        account_address: str = "",
        folder: str = "INBOX",
        uid: int = 0,
        account_id: int = 0,
    ) -> Optional[EmailMessage]:
        try:
            msg = email.message_from_bytes(raw_email, policy=default_policy)
            return EmailParser._build_message(msg, account_address, folder, uid, account_id)
        except Exception:
            return None

    @staticmethod
    def _build_message(
        msg,
        account_address: str,
        folder: str,
        uid: int,
        account_id: int,
    ) -> EmailMessage:
        from_addr = msg.get("From", "")
        _, from_email = parseaddr(from_addr)
        from_name, _ = parseaddr(from_addr)

        participants = []

        participants.append(MessageParticipant(
            role=MessageParticipantRole.FROM,
            address=from_email or from_addr,
            display_name=from_name if from_name != from_email else "",
        ))

        for header_name, role in [
            ("To", MessageParticipantRole.TO),
            ("Cc", MessageParticipantRole.CC),
            ("Bcc", MessageParticipantRole.BCC),
        ]:
            header_val = msg.get(header_name, "")
            if header_val:
                for addr_str in header_val.split(","):
                    name, addr = parseaddr(addr_str.strip())
                    if addr:
                        participants.append(MessageParticipant(
                            role=role,
                            address=addr,
                            display_name=name if name != addr else "",
                        ))

        text = ""
        html = ""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    att = EmailParser._extract_attachment(part)
                    if att:
                        attachments.append(att)
                elif content_type == "text/plain" and not text:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        text = payload.decode(charset, errors="replace")
                elif content_type == "text/html" and not html:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        html = payload.decode(charset, errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")

        date_str = msg.get("Date", "")
        received_at = None
        if date_str:
            try:
                received_at = parsedate_to_datetime(date_str)
            except Exception:
                pass

        message_id = msg.get("Message-ID", "")
        thread_id = EmailParser._extract_thread_id(msg)

        sender_addr = from_email or from_addr
        direction = (
            MessageDirection.OUTGOING
            if sender_addr.lower() == account_address.lower()
            else MessageDirection.INCOMING
        )

        return EmailMessage(
            message_id=message_id,
            thread_id=thread_id,
            subject=msg.get("Subject", ""),
            text=EmailParser._strip_reply_quotations(text),
            html=html,
            direction=direction,
            participants=participants,
            attachments=attachments,
            received_at=received_at,
            folder=folder,
            account_id=account_id,
            db_id=uid,
        )

    @staticmethod
    def _extract_attachment(part) -> Optional[EmailAttachment]:
        try:
            filename = part.get_filename() or "unnamed-attachment"
            data = part.get_payload(decode=True)
            content_type = part.get_content_type()
            return EmailAttachment(
                filename=filename,
                content_type=content_type,
                size=len(data) if data else 0,
                data=data,
            )
        except Exception:
            return None

    @staticmethod
    def _extract_thread_id(msg) -> str:
        references = msg.get("References", "")
        if references:
            refs = references.strip().split()
            if refs:
                return refs[0].strip()

        in_reply_to = msg.get("In-Reply-To", "")
        if in_reply_to:
            return in_reply_to.strip()

        message_id = msg.get("Message-ID", "")
        if message_id:
            return message_id.strip()

        return ""

    @staticmethod
    def _strip_reply_quotations(text: str) -> str:
        if not text:
            return text
        quotation_patterns = [
            r"^On .+ wrote:.*",
            r"^---+ ?Original Message ?---+.*",
            r"^从.+:.*",
            r"^-+ ?原始邮件 ?-+.*",
            r"^>.*",
        ]
        lines = text.split("\n")
        result = []
        for line in lines:
            if any(re.match(pat, line.strip()) for pat in quotation_patterns):
                break
            result.append(line)
        return "\n".join(result).strip()

    @staticmethod
    def extract_links(text: str) -> list[str]:
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

    @staticmethod
    def extract_email_addresses(text: str) -> list[str]:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return list(set(re.findall(email_pattern, text)))

    @staticmethod
    def extract_phone_numbers(text: str) -> list[str]:
        phone_pattern = r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        return re.findall(phone_pattern, text)

    @staticmethod
    def compute_message_direction(sender_address: str, account_address: str) -> MessageDirection:
        if not sender_address or not account_address:
            return MessageDirection.INCOMING
        return (
            MessageDirection.OUTGOING
            if sender_address.lower() == account_address.lower()
            else MessageDirection.INCOMING
        )
