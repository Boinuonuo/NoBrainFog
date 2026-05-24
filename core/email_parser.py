# core/email_parser.py
"""
Email parsing helpers for the NoBrainFog Email adapter.

This module does not connect to IMAP and does not write todo.md.
It only turns a raw email message into clean text that can be sent into
IngestService.capture_task(..., source="email").
"""
from dataclasses import dataclass
from email import policy
from email.message import Message
from email.parser import BytesParser, Parser
from html.parser import HTMLParser
from typing import Iterable, Optional


MAX_BODY_CHARS = 6000

QUOTE_PREFIXES = (
    ">",
    "On ",
    "From:",
    "Sent:",
    "To:",
    "Subject:",
    "发件人:",
    "发送时间:",
    "收件人:",
    "主题:",
)

FORWARD_MARKERS = (
    "-----Original Message-----",
    "---------- Forwarded message ---------",
    "Begin forwarded message:",
    "转发的邮件",
    "原始邮件",
)

SIGNATURE_MARKERS = (
    "--",
    "-- ",
    "Sent from my iPhone",
    "Sent from my iPad",
    "Sent from Outlook",
    "Get Outlook for",
    "发自我的 iPhone",
)


@dataclass
class ParsedEmail:
    subject: str
    sender: str
    message_id: str
    body: str
    ingest_text: str


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"br", "p", "div", "li", "tr", "table", "blockquote"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"p", "div", "li", "tr", "blockquote"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if data:
            self.parts.append(data)

    def text(self):
        return "".join(self.parts)


def parse_email_bytes(raw_message: bytes) -> ParsedEmail:
    """Parse raw RFC822 email bytes."""
    message = BytesParser(policy=policy.default).parsebytes(raw_message)
    return parse_email_message(message)


def parse_email_string(raw_message: str) -> ParsedEmail:
    """Parse a raw RFC822 email string."""
    message = Parser(policy=policy.default).parsestr(raw_message)
    return parse_email_message(message)


def parse_email_message(message: Message) -> ParsedEmail:
    """Parse an email.message.Message into a ParsedEmail."""
    subject = _header_value(message.get("Subject"))
    sender = _header_value(message.get("From"))
    message_id = _header_value(message.get("Message-ID"))

    body = extract_best_body(message)
    clean_body = clean_email_body(body)
    ingest_text = build_ingest_text(subject=subject, sender=sender, body=clean_body)

    return ParsedEmail(
        subject=subject,
        sender=sender,
        message_id=message_id,
        body=clean_body,
        ingest_text=ingest_text,
    )


def extract_best_body(message: Message) -> str:
    """
    Prefer text/plain. Fall back to text/html converted to plain text.
    Ignore attachments.
    """
    plain_parts = []
    html_parts = []

    for part in _walk_body_parts(message):
        content_type = part.get_content_type()
        text = _safe_get_content(part)
        if not text:
            continue

        if content_type == "text/plain":
            plain_parts.append(text)
        elif content_type == "text/html":
            html_parts.append(html_to_text(text))

    if plain_parts:
        return "\n".join(plain_parts)

    if html_parts:
        return "\n".join(html_parts)

    return ""


def clean_email_body(body: str) -> str:
    """Remove common reply/forward clutter and normalize whitespace."""
    body = normalize_newlines(body)
    lines = body.split("\n")

    cleaned = []
    for line in lines:
        stripped = line.strip()

        if _is_forward_marker(stripped):
            break

        if _is_signature_marker(stripped):
            break

        if _is_quote_line(stripped):
            break

        cleaned.append(stripped)

    text = squash_blank_lines(cleaned).strip()
    if len(text) > MAX_BODY_CHARS:
        text = text[:MAX_BODY_CHARS].rstrip() + "\n\n... email body truncated by NoBrainFog ..."

    return text


def build_ingest_text(subject: str, sender: str, body: str) -> str:
    """Build the text payload that should be sent to the AI task cleaner."""
    parts = ["Please turn this email into a NoBrainFog task."]

    if subject:
        parts.append(f"Subject: {subject}")

    if sender:
        parts.append(f"From: {sender}")

    if body:
        parts.append("Body:")
        parts.append(body)

    return "\n".join(parts).strip()


def html_to_text(html: str) -> str:
    extractor = _HTMLTextExtractor()
    extractor.feed(html or "")
    return extractor.text()


def normalize_newlines(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def squash_blank_lines(lines: Iterable[str]) -> str:
    output = []
    blank_seen = False

    for line in lines:
        if not line:
            if not blank_seen:
                output.append("")
            blank_seen = True
            continue

        output.append(line)
        blank_seen = False

    return "\n".join(output)


def _walk_body_parts(message: Message):
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
                continue
            if _is_attachment(part):
                continue
            yield part
    else:
        yield message


def _is_attachment(part: Message) -> bool:
    disposition = (part.get_content_disposition() or "").lower()
    return disposition == "attachment"


def _safe_get_content(part: Message) -> str:
    try:
        content = part.get_content()
    except Exception:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")

    if isinstance(content, bytes):
        charset = part.get_content_charset() or "utf-8"
        return content.decode(charset, errors="replace")

    return str(content or "")


def _header_value(value: Optional[str]) -> str:
    return str(value or "").strip()


def _is_quote_line(line: str) -> bool:
    if not line:
        return False

    return any(line.startswith(prefix) for prefix in QUOTE_PREFIXES)


def _is_forward_marker(line: str) -> bool:
    return any(marker in line for marker in FORWARD_MARKERS)


def _is_signature_marker(line: str) -> bool:
    return any(line == marker or line.startswith(marker) for marker in SIGNATURE_MARKERS)
