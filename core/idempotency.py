import os
import time
from pathlib import Path


class MessageDeduper:
    """Small file-based idempotency layer for webhook retries.

    The goal is not to lock todo.md. It only prevents the same external message
    from being processed twice when a webhook provider retries because AI work was
    slow or the network response was delayed.
    """

    def __init__(self, store_dir, ttl_seconds=7 * 24 * 60 * 60):
        self.store_dir = Path(store_dir).expanduser().resolve()
        self.ttl_seconds = ttl_seconds
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _safe_key(self, key):
        return "".join(ch if ch.isalnum() or ch in ["-", "_"] else "_" for ch in str(key))

    def _path_for(self, key):
        return self.store_dir / f"{self._safe_key(key)}.seen"

    def cleanup(self):
        now = time.time()
        for marker in self.store_dir.glob("*.seen"):
            try:
                if now - marker.stat().st_mtime > self.ttl_seconds:
                    marker.unlink()
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"⚠️ Failed to clean dedupe marker {marker}: {e}")

    def claim(self, key):
        """Return True if this message should be processed.

        Uses O_EXCL so duplicate webhook retries cannot create the same marker
        twice, even if two requests arrive close together.
        """
        if not key:
            return True

        self.cleanup()
        marker_path = self._path_for(key)

        try:
            fd = os.open(str(marker_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(str(int(time.time())))
            return True
        except FileExistsError:
            return False

    def release(self, key):
        """Remove a marker so a failed message can be retried later."""
        if not key:
            return

        try:
            self._path_for(key).unlink()
        except FileNotFoundError:
            pass
