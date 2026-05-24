# adapters/email_imap.py
import imaplib
import time
from email.utils import parseaddr

from core.email_parser import parse_email_bytes
from core.ingest import IngestService


class EmailIMAPAdapter:
    """
    Polls an IMAP inbox and turns unread emails into NoBrainFog tasks.

    This adapter intentionally keeps the first version simple:
    - search unread emails
    - parse subject/from/body
    - send clean text into IngestService
    - mark successful messages as seen
    - optionally move successful messages to a processed folder
    """

    def __init__(self, config):
        self.config = config
        self.ingest = IngestService(config)

        self.host = config.get("EMAIL_IMAP_HOST")
        self.port = int(config.get("EMAIL_IMAP_PORT") or 993)
        self.username = config.get("EMAIL_USERNAME")
        self.password = config.get("EMAIL_PASSWORD")
        self.mailbox = config.get("EMAIL_MAILBOX") or "INBOX"
        self.poll_seconds = int(config.get("EMAIL_POLL_SECONDS") or 60)
        self.processed_folder = (config.get("EMAIL_PROCESSED_FOLDER") or "").strip()
        self.max_messages_per_poll = int(config.get("EMAIL_MAX_MESSAGES_PER_POLL") or 10)

    def run(self):
        print("📬 NoBrainFog Email IMAP adapter started")
        print(f"Mailbox: {self.username} / {self.mailbox}")
        print(f"Poll interval: {self.poll_seconds}s")

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
        display_sender = sender_email or sender_name or parsed.sender or "unknown sender"
        display_subject = parsed.subject or "(no subject)"

        print(f"📨 Capturing email: {display_subject} <{display_sender}>")
        row = self.ingest.capture_task(parsed.ingest_text, source="email")
        print(f"✨ Saved email task: {row}")

        mail.store(message_id, "+FLAGS", "\\Seen")
        if self.processed_folder:
            self.move_to_processed(mail, message_id)

        return True

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
