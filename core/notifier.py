# core/notifier.py
"""
Notification helpers for NoBrainFog background adapters.

The Email IMAP adapter can run without the Discord adapter process.
This module uses Discord's REST API directly to send a DM notification.
"""
import requests


DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordDMNotifier:
    def __init__(self, token, target_user_id, enabled=True, timeout_seconds=10):
        self.token = token
        self.target_user_id = str(target_user_id or "").strip()
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self._dm_channel_id = None

    @classmethod
    def from_config(cls, config):
        enabled = str(config.get("NOTIFY_DISCORD_ENABLED", "false")).strip().lower()
        return cls(
            token=config.get("DISCORD_TOKEN"),
            target_user_id=config.get("TARGET_USER_ID"),
            enabled=enabled in {"1", "true", "yes", "on"},
        )

    def send(self, content):
        if not self.enabled:
            return False

        if not self.token or not self.target_user_id:
            print("⚠️ Discord notification skipped: missing DISCORD_TOKEN or TARGET_USER_ID")
            return False

        channel_id = self.get_dm_channel_id()
        response = requests.post(
            f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
            headers=self.headers,
            json={"content": self.truncate_content(content)},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return True

    def get_dm_channel_id(self):
        if self._dm_channel_id:
            return self._dm_channel_id

        response = requests.post(
            f"{DISCORD_API_BASE}/users/@me/channels",
            headers=self.headers,
            json={"recipient_id": self.target_user_id},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        self._dm_channel_id = payload["id"]
        return self._dm_channel_id

    @property
    def headers(self):
        return {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }

    def truncate_content(self, content):
        text = str(content or "").strip()
        if len(text) <= 1900:
            return text
        return text[:1900].rstrip() + "\n\n... notification truncated ..."


def format_email_success_notification(subject, sender, row):
    return (
        "📬 Email captured by NoBrainFog\n\n"
        f"From: {sender or 'unknown sender'}\n"
        f"Subject: {subject or '(no subject)'}\n\n"
        "Saved to `todo.md`.\n"
        f"```text\n{row}\n```"
    )


def format_email_failure_notification(subject, sender, error):
    return (
        "⚠️ Email capture failed\n\n"
        f"From: {sender or 'unknown sender'}\n"
        f"Subject: {subject or '(no subject)'}\n\n"
        f"Reason: {error}"
    )
