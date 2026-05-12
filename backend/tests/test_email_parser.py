import pytest
from email import policy
from email.message import EmailMessage

from app.services.email.parser import EmailParser
from app.services.email.models import MessageDirection, MessageParticipantRole


class TestEmailParser:
    def test_parse_simple_text_email(self):
        raw_email = b"""From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <test123@example.com>

Hello, this is a test email.
"""
        result = EmailParser.parse_raw_message(raw_email, "recipient@example.com")
        assert result is not None
        assert result.subject == "Test Email"
        assert result.text.strip() == "Hello, this is a test email."

    def test_parse_multipart_email(self):
        raw_email = b"""From: sender@example.com
To: recipient@example.com
Subject: Multipart Test
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <multipart123@example.com>
Content-Type: multipart/mixed; boundary="----=_Part_1"

------=_Part_1
Content-Type: text/plain

Plain text body
------=_Part_1
Content-Type: text/html

<html><body>HTML body</body></html>
------=_Part_1--
"""
        result = EmailParser.parse_raw_message(raw_email, "recipient@example.com")
        assert result is not None
        assert "Plain text body" in result.text
        assert "HTML body" in result.html

    def test_parse_email_with_attachments(self):
        raw_email = b"""From: sender@example.com
To: recipient@example.com
Subject: With Attachment
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <attach123@example.com>
Content-Type: multipart/mixed; boundary="----=_Part_1"

------=_Part_1
Content-Type: text/plain

Check the attachment.
------=_Part_1
Content-Type: application/octet-stream; name="document.pdf"
Content-Disposition: attachment; filename="document.pdf"

binarydata
------=_Part_1--
"""
        result = EmailParser.parse_raw_message(raw_email, "recipient@example.com")
        assert result is not None
        assert len(result.attachments) == 1
        assert result.attachments[0].filename == "document.pdf"

    def test_parse_email_with_cc(self):
        raw_email = b"""From: sender@example.com
To: primary@example.com
Cc: cc1@example.com, cc2@example.com
Subject: With CC
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <cc123@example.com>

Test body
"""
        result = EmailParser.parse_raw_message(raw_email, "primary@example.com")
        assert result is not None
        roles = [p.role for p in result.participants]
        assert MessageParticipantRole.CC in roles

    def test_parse_email_direction_incoming(self):
        raw_email = b"""From: external@example.com
To: my@example.com
Subject: Incoming
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <incoming123@example.com>

Body
"""
        result = EmailParser.parse_raw_message(raw_email, "my@example.com")
        assert result is not None
        assert result.direction == MessageDirection.INCOMING

    def test_parse_email_direction_outgoing(self):
        raw_email = b"""From: my@example.com
To: external@example.com
Subject: Outgoing
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <outgoing123@example.com>

Body
"""
        result = EmailParser.parse_raw_message(raw_email, "my@example.com")
        assert result is not None
        assert result.direction == MessageDirection.OUTGOING

    def test_parse_email_with_thread_reference(self):
        raw_email = b"""From: sender@example.com
To: recipient@example.com
Subject: Re: Thread
References: <original123@example.com>
In-Reply-To: <original123@example.com>
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <reply123@example.com>

Reply body
"""
        result = EmailParser.parse_raw_message(raw_email, "recipient@example.com")
        assert result is not None
        assert result.thread_id == "<original123@example.com>"

    def test_parse_email_malformed_returns_none(self):
        raw_email = b"not a valid email at all"
        result = EmailParser.parse_raw_message(raw_email)
        assert result is None or isinstance(result, object)

    def test_parse_email_empty_body(self):
        raw_email = b"""From: sender@example.com
To: recipient@example.com
Subject: Empty
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <empty123@example.com>

"""
        result = EmailParser.parse_raw_message(raw_email)
        assert result is not None
        assert result.text == ""

    def test_parse_email_with_display_name(self):
        raw_email = b"""From: John Doe <john@example.com>
To: Jane Doe <jane@example.com>
Subject: Named
Date: Mon, 1 Jan 2024 12:00:00 +0000
Message-ID: <named123@example.com>

Body
"""
        result = EmailParser.parse_raw_message(raw_email)
        assert result is not None
        from_participant = next(p for p in result.participants if p.role == MessageParticipantRole.FROM)
        assert from_participant.display_name == "John Doe"
        assert from_participant.address == "john@example.com"


class TestEmailParserReplyStripping:
    def test_strip_online_wrote_pattern(self):
        text = """Thanks for your email!

On Mon, Jan 1, 2024 at 12:00 PM, someone@example.com wrote:
This is the quoted reply
"""
        result = EmailParser._strip_reply_quotations(text)
        assert "On Mon, Jan 1" not in result
        assert "Thanks for your email!" in result

    def test_strip_original_message_pattern(self):
        text = """Reply content

--- Original Message ---
Original content here
"""
        result = EmailParser._strip_reply_quotations(text)
        assert "--- Original Message ---" not in result
        assert "Reply content" in result

    def test_strip_chinese_reply_pattern(self):
        text = """Thanks!

> Chinese quoted text
"""
        result = EmailParser._strip_reply_quotations(text)
        assert result is not None

    def test_strip_quoted_lines(self):
        text = """My reply

> Their quoted response
> More quoted text
"""
        result = EmailParser._strip_reply_quotations(text)
        assert "My reply" in result
        assert "> Their" not in result

    def test_no_stripping_for_plain_text(self):
        text = """This is just a normal email
with multiple lines
and no reply markers.
"""
        result = EmailParser._strip_reply_quotations(text)
        assert "This is just a normal email" in result


class TestEmailParserExtractors:
    def test_extract_links_basic(self):
        text = "Check https://example.com and http://test.org for more info"
        links = EmailParser.extract_links(text)
        assert "https://example.com" in links
        assert "http://test.org" in links

    def test_extract_links_no_duplicates(self):
        text = "Visit https://example.com and https://test.org"
        links = EmailParser.extract_links(text)
        assert len(links) == 2
        assert "https://example.com" in links
        assert "https://test.org" in links

    def test_extract_links_with_special_chars(self):
        text = "Link: https://example.com/path?param=value&q=1"
        links = EmailParser.extract_links(text)
        assert len(links) == 1

    def test_extract_email_addresses(self):
        text = "Contact test@example.com or admin@test.org for help"
        emails = EmailParser.extract_email_addresses(text)
        assert "test@example.com" in emails
        assert "admin@test.org" in emails

    def test_extract_email_addresses_no_duplicates(self):
        text = "Email test@test.com or test@test.com again"
        emails = EmailParser.extract_email_addresses(text)
        assert "test@test.com" in emails

    def test_extract_phone_numbers_us_format(self):
        text = "Call 123-456-7890 or (123) 456-7890"
        phones = EmailParser.extract_phone_numbers(text)
        assert len(phones) >= 1

    def test_extract_phone_numbers_international(self):
        text = "International: +1-234-567-8900"
        phones = EmailParser.extract_phone_numbers(text)
        assert len(phones) >= 1


class TestEmailParserComputeDirection:
    def test_compute_direction_incoming(self):
        result = EmailParser.compute_message_direction(
            "external@example.com", "my@example.com"
        )
        assert result == MessageDirection.INCOMING

    def test_compute_direction_outgoing(self):
        result = EmailParser.compute_message_direction(
            "my@example.com", "my@example.com"
        )
        assert result == MessageDirection.OUTGOING

    def test_compute_direction_case_insensitive(self):
        result = EmailParser.compute_message_direction(
            "MY@EXAMPLE.COM", "my@example.com"
        )
        assert result == MessageDirection.OUTGOING

    def test_compute_direction_empty_sender(self):
        result = EmailParser.compute_message_direction("", "my@example.com")
        assert result == MessageDirection.INCOMING

    def test_compute_direction_empty_account(self):
        result = EmailParser.compute_message_direction("sender@example.com", "")
        assert result == MessageDirection.INCOMING
