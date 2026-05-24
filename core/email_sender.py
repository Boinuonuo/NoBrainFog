# core/email_sender.py
"""
SMTP email sender for NoBrainFog Email adapter replies.

Supports plain text replies and small attachments such as todo.md or .xlsx.
"""
import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path


class EmailSender:
    def __init__(self, config):
        self.host = config.get("EMAIL_SMTP_HOST") or "smtp.gmail.com"
        self.port = int(config.get("EMAIL_SMTP_PORT") or 587)
        self.username = config.get("EMAIL_SMTP_USERNAME") or config.get("EMAIL_USERNAME")
        self.password = self.normalize_password(
            config.get("EMAIL_SMTP_PASSWORD") or config.get("EMAIL_PASSWORD")
        )
        self.reply_from = config.get("EMAIL_REPLY_FROM") or self.username
        self.enabled = str(config.get("EMAIL_SMTP_ENABLED", "true")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def send_text(self, *, to, subject, body):
        return self.send(to=to, subject=subject, body=body, attachments=[])

    def send_with_attachment(self, *, to, subject, body, attachment_path, filename=None):
        return self.send(
            to=to,
            subject=subject,
            body=body,
            attachments=[(Path(attachment_path), filename)],
        )

    def send(self, *, to, subject, body, attachments=None):
        if not self.enabled:
            print("⚠️ SMTP reply skipped: EMAIL_SMTP_ENABLED is false")
            return False

        if not self.username or not self.password:
            raise ValueError("Missing SMTP username/password for Email reply.")

        message = EmailMessage()
        message["From"] = self.reply_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body or "")

        for attachment_path, filename in attachments or []:
            self.attach_file(message, attachment_path, filename=filename)

        with smtplib.SMTP(self.host, self.port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(self.username, self.password)
            smtp.send_message(message)

        return True

    def attach_file(self, message, attachment_path, filename=None):
        path = Path(attachment_path).expanduser().resolve()
        content_type, _ = mimetypes.guess_type(str(path))
        if not content_type:
            content_type = "application/octet-stream"

        maintype, subtype = content_type.split("/", 1)
        message.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=filename or path.name,
        )

    def normalize_password(self, password):
        return "".join(str(password or "").split())
