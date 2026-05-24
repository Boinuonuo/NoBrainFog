# adapters/email_imap.py
import imaplib
import tempfile
import time
from email.utils import parseaddr
from pathlib import Path

from core.email_commands import EMAIL_HELP_TEXT, parse_email_command
from core.email_dedupe import EmailDedupeStore
from core.email_parser import parse_email_bytes
from core.email_sender import EmailSender
from core.excel_exporter import export_tasks_to_excel
from core.handler import TodoHandler
from core.ingest import IngestService
from core.notifier import (
    DiscordDMNotifier,
    format_email_failure_notification,
    format_email_success_notification,
)


class EmailIMAPAdapter:
    """
    Polls an IMAP inbox and turns unread emails into NoBrainFog tasks.

    Flow:
    - search unread emails
    - parse subject/from/body
    - skip non-whitelisted senders when a whitelist is configured
    - handle email commands such as /ping, /help, /report, /export, /excel, /xlsx
    - skip messages already recorded in the local dedupe store
    - send clean text into IngestService for normal task capture
    - notify Discord when configured
    - mark successful messages as seen
    - optionally move successful messages to a processed folder
    """

    def __init__(self, config):
        self.config = config
        self.ingest = IngestService(config)
        self.handler = TodoHandler(config.get("MD_PATH"))
        self.email_sender = EmailSender(config)
        self.notifier = DiscordDMNotifier.from_config(config)

        self.host = config.get("EMAIL_IMAP_HOST")
        self.port = int(config.get("EMAIL_IMAP_PORT") or 993)
        self.username = config.get("EMAIL_USERNAME")
        self.password = self.normalize_password(config.get("EMAIL_PASSWORD"))
        self.mailbox = config.get("EMAIL_MAILBOX") or "INBOX"
        self.poll_seconds = int(config.get("EMAIL_POLL_SECONDS") or 60)
        self.processed_folder = (config.get("EMAIL_PROCESSED_FOLDER") or "").strip()
        self.max_messages_per_poll = int(config.get("EMAIL_MAX_MESSAGES_PER_POLL") or 10)
        self.allowed_senders = self.parse_csv_config(config.get("EMAIL_ALLOWED_SENDERS"))
        self.allowed_domains = self.parse_domain_config(config.get("EMAIL_ALLOWED_DOMAINS"))
        self.dedupe = EmailDedupeStore(self.resolve_dedupe_dir(config))

    def run(self):
        print("📬 NoBrainFog Email IMAP adapter started")
        print(f"Mailbox: {self.username} / {self.mailbox}")
        print(f"Poll interval: {self.poll_seconds}s")
        print(f"Discord notification: {'enabled' if self.notifier.enabled else 'disabled'}")
        print(f"SMTP replies: {'enabled' if self.email_sender.enabled else 'disabled'}")
        if self.has_sender_whitelist():
            print("Sender whitelist: enabled")
        else:
            print("Sender whitelist: disabled; all senders are allowed")

        while True:
            try:
                processed_count = self.poll_once()
                if processed_count:
                    print(f"✅ Processed {processed_count} email(s)")
            except KeyboardInterrupt:
                print("👋 Email IMAP adapter stopped")
                raise
            except Exception as exc:
                print(f"⚠️ Email IMAP poll failed: {exc}")

            time.sleep(self.poll_seconds)

    def poll_once(self):
        processed_count = 0

        with self.connect() as mail:
            self.select_mailbox(mail)
            message_ids = self.search_unseen(mail)

            if not message_ids:
                return 0

            for message_id in message_ids[: self.max_messages_per_poll]:
                try:
                    if self.process_message(mail, message_id):
                        processed_count += 1
                except Exception as exc:
                    printable_id = message_id.decode(errors="replace") if isinstance(message_id, bytes) else str(message_id)
                    print(f"⚠️ Failed to process email id {printable_id}: {exc}")

        return processed_count

    def connect(self):
        mail = imaplib.IMAP4_SSL(self.host, self.port)
        mail.login(self.username, self.password)
        return mail

    def select_mailbox(self, mail):
        status, data = mail.select(self.mailbox)
        if status != "OK":
            raise RuntimeError(f"Failed to select mailbox {self.mailbox}: {data}")

    def search_unseen(self, mail):
        status, data = mail.search(None, "UNSEEN")
        if status != "OK":
            raise RuntimeError(f"Failed to search unread emails: {data}")

        if not data or not data[0]:
            return []

        return data[0].split()

    def process_message(self, mail, message_id):
        status, data = mail.fetch(message_id, "(RFC822)")
        if status != "OK" or not data:
            raise RuntimeError(f"Failed to fetch email: {data}")

        raw_message = self.extract_raw_message(data)
        parsed = parse_email_bytes(raw_message)

        sender_name, sender_email = parseaddr(parsed.sender)
        normalized_sender = (sender_email or parsed.sender or "").strip().lower()
        display_sender = sender_email or sender_name or parsed.sender or "unknown sender"
        display_subject = parsed.subject or "(no subject)"

        if not self.is_sender_allowed(normalized_sender):
            print(f"🚫 Ignoring non-whitelisted email: {display_subject} <{display_sender}>")
            mail.store(message_id, "+FLAGS", "\\Seen")
            return False

        command = parse_email_command(parsed.subject, parsed.body)
        if command:
            print(f"📩 Handling email command {command.name}: {display_subject} <{display_sender}>")
            self.handle_email_command(command, reply_to=normalized_sender or display_sender)
            mail.store(message_id, "+FLAGS", "\\Seen")
            if self.processed_folder:
                self.move_to_processed(mail, message_id)
            return True

        message_uid = self.fetch_uid(mail, message_id)
        dedupe_key = self.dedupe.make_key(
            message_id=parsed.message_id,
            uid=message_uid,
            subject=parsed.subject,
            sender=parsed.sender,
        )

        if self.dedupe.has_seen(dedupe_key):
            print(f"↪️ Skipping already processed email: {display_subject} <{display_sender}>")
            mail.store(message_id, "+FLAGS", "\\Seen")
            return False

        print(f"📨 Capturing email: {display_subject} <{display_sender}>")

        try:
            row = self.ingest.capture_task(parsed.ingest_text, source="email")
        except Exception as exc:
            self.notify_failure(display_subject, display_sender, exc)
            raise

        self.dedupe.mark_seen(
            dedupe_key,
            note=f"subject={display_subject}\nfrom={display_sender}\nmessage_id={parsed.message_id}\nuid={message_uid}\n",
        )
        print(f"✨ Saved email task: {row}")
        self.notify_success(display_subject, display_sender, row)

        mail.store(message_id, "+FLAGS", "\\Seen")
        if self.processed_folder:
            self.move_to_processed(mail, message_id)

        return True

    def handle_email_command(self, command, reply_to):
        if command.name == "/ping":
            self.email_sender.send_text(
                to=reply_to,
                subject="NoBrainFog Email: pong",
                body="pong ✅\n\nNoBrainFog Email adapter is running.",
            )
            return

        if command.name == "/help":
            self.email_sender.send_text(
                to=reply_to,
                subject="NoBrainFog Email Commands",
                body=EMAIL_HELP_TEXT,
            )
            return

        if command.name == "/report":
            self.email_sender.send_text(
                to=reply_to,
                subject="NoBrainFog Task Report",
                body=self.handler.format_report(),
            )
            return

        if command.name == "/export":
            md_path = Path(self.config.get("MD_PATH")).expanduser().resolve()
            self.email_sender.send_with_attachment(
                to=reply_to,
                subject="NoBrainFog export: todo.md",
                body="Attached is your current NoBrainFog todo.md export.",
                attachment_path=md_path,
                filename="todo.md",
            )
            return

        if command.name in {"/excel", "/xlsx"}:
            tasks = self.handler.get_tasks()
            with tempfile.TemporaryDirectory(prefix="nbf-email-export-") as temp_dir:
                output_path = Path(temp_dir) / "nobrainfog-todo.xlsx"
                export_tasks_to_excel(tasks, output_path)
                self.email_sender.send_with_attachment(
                    to=reply_to,
                    subject="NoBrainFog export: Excel workbook",
                    body="Attached is your current NoBrainFog Excel export.",
                    attachment_path=output_path,
                    filename="nobrainfog-todo.xlsx",
                )
            return

        raise ValueError(f"Unsupported email command: {command.name}")

    def fetch_uid(self, mail, message_id):
        status, data = mail.fetch(message_id, "(UID)")
        if status != "OK" or not data:
            return None

        for item in data:
            if not isinstance(item, tuple):
                continue
            header = item[0]
            if isinstance(header, bytes):
                header = header.decode(errors="replace")
            marker = "UID "
            if marker in header:
                return header.split(marker, 1)[1].split(")", 1)[0].strip()

        return None

    def extract_raw_message(self, fetch_data):
        for item in fetch_data:
            if isinstance(item, tuple) and len(item) >= 2:
                return item[1]
        raise RuntimeError("IMAP fetch response did not contain raw message bytes.")

    def move_to_processed(self, mail, message_id):
        self.ensure_processed_folder(mail)
        status, data = mail.copy(message_id, self.processed_folder)
        if status != "OK":
            raise RuntimeError(f"Failed to copy email to {self.processed_folder}: {data}")

        mail.store(message_id, "+FLAGS", "\\Deleted")
        mail.expunge()

    def ensure_processed_folder(self, mail):
        status, _ = mail.select(self.processed_folder)
        if status == "OK":
            self.select_mailbox(mail)
            return

        mail.create(self.processed_folder)
        self.select_mailbox(mail)

    def notify_success(self, subject, sender, row):
        try:
            self.notifier.send(format_email_success_notification(subject, sender, row))
        except Exception as exc:
            print(f"⚠️ Discord success notification failed: {exc}")

    def notify_failure(self, subject, sender, error):
        try:
            self.notifier.send(format_email_failure_notification(subject, sender, error))
        except Exception as exc:
            print(f"⚠️ Discord failure notification failed: {exc}")

    def resolve_dedupe_dir(self, config):
        configured = (config.get("EMAIL_DEDUPE_DIR") or "").strip()
        if configured:
            return configured

        md_path = Path(config.get("MD_PATH") or "./todo.md").expanduser().resolve()
        return md_path.parent / ".email_msg_dedupe"

    def has_sender_whitelist(self):
        return bool(self.allowed_senders or self.allowed_domains)

    def is_sender_allowed(self, sender_email):
        if not self.has_sender_whitelist():
            return True

        sender = (sender_email or "").strip().lower()
        if not sender:
            return False

        if sender in self.allowed_senders:
            return True

        if "@" in sender:
            domain = sender.rsplit("@", 1)[1]
            if domain in self.allowed_domains:
                return True

        return False

    def parse_csv_config(self, value):
        return {
            item.strip().lower()
            for item in str(value or "").split(",")
            if item.strip()
        }

    def parse_domain_config(self, value):
        return {
            item.strip().lower().lstrip("@")
            for item in str(value or "").split(",")
            if item.strip()
        }

    def normalize_password(self, password):
        """Google App Passwords are often displayed with spaces for readability."""
        return "".join(str(password or "").split())
