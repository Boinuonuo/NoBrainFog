# 🧠 NoBrainFog

English | [中文](README.zh.md)

NoBrainFog is an AI-powered personal task intake system. It turns fragmented thoughts from Discord or WeChat Work into one shared Markdown `todo.md` task file.

Chat platforms are only adapters. The real data layer is local, portable, and sync-friendly.

```text
Discord / WeChat Work
        ↓
NoBrainFog adapter process
        ↓
/root/nbf-vault/todo.md
        ↓
rclone / Google Drive sync
```

## Highlights

- Capture messy thoughts and turn them into structured Markdown tasks.
- Run multiple adapters from one codebase.
- Use separate private config files for Discord and WeChat Work.
- Store all tasks in one shared `todo.md`.
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
```

Use the example files as templates:

```text
discord.env.example
wechat.env.example
```

Both real config files should point to the same `MD_PATH`.

## Documentation

- [English full guide](README.en.md)
- [中文完整教程](README.zh.md)

## Discord adapter

The Discord adapter works through direct messages. It supports rich help embeds, reactions, image input, task export, and task file import.

Discord-only capability:

```text
/import    Upload a todo.md file to replace the current task file
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

## Common commands

```text
/report or /r or /rep       Show task list
/export or /e or /exp       Export todo.md text
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

## Files

```text
main.py                  # loads --env-file and starts the selected adapter
adapters/discord_bot.py  # Discord DM adapter
adapters/wechat_work.py  # WeChat Work webhook adapter
core/help_text.py        # adapter-specific help text
core/idempotency.py      # WeChat webhook retry dedupe
core/ingest.py           # unified input ingestion
core/handler.py          # todo.md read/write logic
```
