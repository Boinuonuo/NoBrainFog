# 🧠 NoBrainFog

English | [中文](README.zh.md)

NoBrainFog is an AI-powered personal task intake system. It turns fragmented thoughts from Discord, WeChat Work, CLI, or Email into one shared Markdown `todo.md` task file.

Chat platforms and inboxes are only adapters. The real data layer is local, portable, and sync-friendly.

```text
Discord / WeChat Work / CLI / Email
        ↓
NoBrainFog adapter or toolkit
        ↓
/root/nbf-vault/todo.md
        ↓
Markdown / Excel / rclone sync
```

## Highlights

- Capture messy thoughts and turn them into structured Markdown tasks.
- Run Discord, WeChat Work, Email, and CLI workflows from one codebase.
- Use separate private config files for each adapter.
- Store all tasks in one shared `todo.md`.
- Export tasks as Markdown or formatted Excel `.xlsx` files.
- Use Email as a remote inbox gateway for task capture, reports, and exports.
- Use the CLI toolkit for local add/report/edit/export/lint workflows.
- Sync the task file with rclone / Google Drive.
- Manage tasks with commands such as `/report`, `/done`, `/edit`, `/pri`, `/due`, `/memo`, `/prior`, `/cbt`, and `/yesucan`.

## Recommended layout

```text
/root/NoBrainFog/                  # code only
/root/nobrainfog-config/           # private adapter config files
/root/nbf-vault/todo.md            # the single real task file
```

Principles:

```text
One codebase
Multiple config files
One data file
```

## Quick start

```bash
cd /root

git clone https://github.com/Boinuonuo/NoBrainFog.git
cd /root/NoBrainFog

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Each adapter is started with an explicit env file:

```bash
python main.py --env-file /root/nobrainfog-config/discord.env
python main.py --env-file /root/nobrainfog-config/wechat.env
python main.py --env-file /root/nobrainfog-config/email.env
```

Use the example files as templates:

```text
discord.env.example
wechat.env.example
email.env.example
cli.env.example
```

All real config files should point to the same `MD_PATH`.

## Documentation

- [English full guide](README.en.md)
- [中文完整教程](README.zh.md)

## Discord adapter

The Discord adapter works through direct messages. It supports rich help embeds, reactions, image input, task export, Excel export, and task file import.

Discord-only capabilities:

```text
/import    Upload a todo.md file to replace the current task file
/excel     Export the current task file as a formatted .xlsx workbook
/xlsx      Alias for /excel
```

Discord is the recommended control console for day-to-day task management.

## Email IMAP adapter

The Email adapter turns a dedicated mailbox into a remote NoBrainFog gateway.

Typical flow:

```text
Forward email to the tool inbox
        ↓
Email IMAP adapter polls unread messages
        ↓
Allowed sender check
        ↓
Normal email → capture as task
Command email → reply by SMTP
```

Supported Email commands:

```text
/ping                    Reply with a health-check message
/help or /h              Reply with Email command help
/report or /r or /rep    Reply with the current task report
/export or /e or /exp    Reply with todo.md as an attachment
/excel or /xlsx          Reply with a formatted Excel workbook as an attachment
```

Recommended Gmail settings:

```env
ADAPTER_TYPE=email_imap
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_USERNAME=your-tool-inbox@gmail.com
EMAIL_PASSWORD=your_google_app_password
EMAIL_MAILBOX=INBOX
EMAIL_POLL_SECONDS=60
EMAIL_MAX_MESSAGES_PER_POLL=5
EMAIL_PROCESSED_FOLDER=NoBrainFog/Processed
```

Use a Google App Password, not your normal Gmail password. App Password spaces are normalized automatically.

Sender restrictions are important because Email commands can export your task file:

```env
EMAIL_ALLOWED_SENDERS=your-main-email@example.com
EMAIL_ALLOWED_DOMAINS=
EMAIL_COMMANDS_REQUIRE_EXACT_SENDER=true
```

SMTP replies default to Gmail SMTP and reuse the IMAP username/password when SMTP-specific values are empty:

```env
EMAIL_SMTP_ENABLED=true
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=
EMAIL_SMTP_PASSWORD=
EMAIL_REPLY_FROM=
```

## WeChat Work adapter

The WeChat Work adapter exposes a `/wechat` webhook endpoint and supports active replies through the WeChat Work API.

Recommended public callback URL:

```text
https://wechat.your-domain.com/wechat
```

If NoBrainFog and `cloudflared` run on the same machine, the Cloudflare Tunnel origin can point to:

```text
localhost:8080
```

WeChat Work may retry callbacks when AI responses are slow. NoBrainFog uses WeChat `MsgId` to prevent duplicate writes.

WeChat Work is maintained as a secondary adapter. Discord and Email are usually better daily workflows.

## CLI toolkit

The CLI toolkit is a local interface for server-side workflows. It is not a long-running adapter.

Create a config file first:

```bash
cp cli.env.example /root/nobrainfog-config/cli.env
```

Install the short command:

```bash
bash scripts/install_nbf_cli.sh
```

Common usage:

```bash
nbf help
nbf report
nbf add "Check the insurance bill"
nbf done 2
nbf pri 2 P1
nbf due 2 2026-05-30
nbf memo 2 "waiting for reply"
nbf excel --output /tmp/nobrainfog-todo.xlsx
nbf lint
```

Only `add` requires AI credentials. Most other commands only need `MD_PATH`.

## Common commands

```text
/report or /r or /rep       Show task list
/export or /e or /exp       Export todo.md text
/excel or /xlsx             Export formatted Excel file
/undo                       Undo the last task
/done 2                     Mark #2 as done
/edit 2 new text            Edit task description
/pri 2 P1                   Update priority
/due 2 2026-05-30           Update deadline
/memo 2 note                Update memo
/prior                      Generate priority analysis
/cbt 2                      CBT breakdown for one task
/cbt all                    Analyze all tasks
/yesucan                    Generate a motivational push message
/help or /h or /admhelp     Show help
```

Not every adapter supports every command. Discord is the richest control surface; Email focuses on capture, report, and export.

## Local tools

Export `todo.md` to Excel from the command line:

```bash
python tools/export_todo_excel.py \
  --input /root/nbf-vault/todo.md \
  --output /tmp/nobrainfog-todo.xlsx
```

Run the optional C task-table linter:

```bash
gcc tools/c/nbf-todo-lint.c -o /tmp/nbf-todo-lint
/tmp/nbf-todo-lint /root/nbf-vault/todo.md
```

## Checks

GitHub Actions runs a lightweight CI workflow on push and pull request:

```text
Python compile check
C todo lint compile check
Excel exporter smoke test
C lint smoke test
CLI toolkit smoke test
Email parser smoke test
Email command alias smoke test
```

## Files

```text
main.py                         # loads --env-file and starts the selected adapter
adapters/discord_bot.py         # Discord DM adapter
adapters/wechat_work.py         # WeChat Work webhook adapter
adapters/email_imap.py          # Email IMAP polling adapter
core/help_text.py               # Discord / WeChat help text
core/email_commands.py          # Email command aliases
core/email_parser.py            # Email body cleanup
core/email_sender.py            # SMTP replies and attachments
core/email_dedupe.py            # Email dedupe marker store
core/idempotency.py             # WeChat webhook retry dedupe
core/ingest.py                  # unified input ingestion
core/handler.py                 # todo.md read/write logic
core/excel_exporter.py          # Excel workbook export logic
tools/nbf_cli.py                # local NoBrainFog CLI toolkit
tools/export_todo_excel.py      # local todo.md → .xlsx CLI
tools/c/nbf-todo-lint.c         # optional C todo.md table linter
web/landing/                    # small static project page
.github/workflows/check.yml     # CI checks
```