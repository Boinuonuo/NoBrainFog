# core/email_commands.py
"""
Email command parsing for the NoBrainFog Email adapter.

Commands are intentionally small and explicit. The first non-empty line of the
email body wins. If the body is empty, the subject is checked as a fallback.
"""
from dataclasses import dataclass


SUPPORTED_EMAIL_COMMANDS = {
    "/export",
    "/excel",
    "/xlsx",
    "/report",
    "/help",
    "/ping",
}


@dataclass
class EmailCommand:
    name: str
    raw: str


EMAIL_HELP_TEXT = """
NoBrainFog Email Commands

Send one of these commands from an allowed sender:

/export
  Reply with todo.md as an attachment.

/excel or /xlsx
  Reply with a formatted Excel workbook as an attachment.

/report
  Reply with the current task report as email text.

/help
  Reply with this help text.

/ping
  Reply with a small health-check message.

Any non-command email from an allowed sender is treated as a task capture.
""".strip()


def parse_email_command(subject, body):
    candidate = first_non_empty_line(body) or first_non_empty_line(subject)
    if not candidate:
        return None

    command = candidate.strip().split()[0].lower()
    if command in SUPPORTED_EMAIL_COMMANDS:
        return EmailCommand(name=command, raw=candidate.strip())

    return None


def first_non_empty_line(text):
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
