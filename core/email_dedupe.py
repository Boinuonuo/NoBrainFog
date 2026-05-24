# core/email_dedupe.py
"""
Lightweight email dedupe marker store.

The Email IMAP adapter can see the same message more than once when polling,
when IMAP flags are delayed, or when moving to a processed folder fails.
This module records stable message keys in a local marker directory so the
same email is not written to todo.md twice.
"""
import hashlib
from pathlib import Path


class EmailDedupeStore:
    def __init__(self, marker_dir):
        self.marker_dir = Path(marker_dir).expanduser().resolve()
        self.marker_dir.mkdir(parents=True, exist_ok=True)

    def make_key(self, *, message_id=None, uid=None, subject=None, sender=None):
        raw_key = message_id or uid or f"{sender or ''}|{subject or ''}"
        normalized = str(raw_key).strip() or "unknown-email"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def has_seen(self, key):
        return self._marker_path(key).exists()

    def mark_seen(self, key, note=""):
        path = self._marker_path(key)
        path.write_text(note or key, encoding="utf-8")

    def _marker_path(self, key):
        safe_key = "".join(ch for ch in key if ch.isalnum() or ch in {"-", "_"})
        return self.marker_dir / f"{safe_key}.seen"
