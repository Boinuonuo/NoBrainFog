# 🧠 NoBrainFog

[中文](README.md) | English

NoBrainFog is an AI-powered personal task intake system. It turns fragmented thoughts from Discord or WeChat Work into a unified Markdown `todo.md` task file.

The core idea: chat platforms are only input adapters. The real data layer is one shared `todo.md`.

```text
Discord / WeChat Work
        ↓
NoBrainFog adapter process
        ↓
/root/nbf-vault/todo.md
        ↓
rclone / Google Drive sync
```

## Recommended directory layout

```text
/root/NoBrainFog/                  # the only code directory; run git pull here
/root/nobrainfog-config/
  discord.env                      # private Discord config, not committed
  wechat.env                       # private WeChat Work config, not committed
/root/nbf-vault/
  todo.md                          # the single real task file, can be synced by rclone
```

Principles:

```text
One codebase
Multiple config files
One data file
```

## Installation

```bash
cd /root

git clone https://github.com/Boinuonuo/NoBrainFog.git
cd /root/NoBrainFog

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If the repository already exists:

```bash
cd /root/NoBrainFog
git pull
source .venv/bin/activate
pip install -r requirements.txt
```

## Env configuration

NoBrainFog no longer reads a root `.env` file by default. Each adapter must be started with an explicit env file.

```bash
python main.py --env-file /root/nobrainfog-config/discord.env
python main.py --env-file /root/nobrainfog-config/wechat.env
```

Create config/data directories and copy templates:

```bash
mkdir -p /root/nobrainfog-config
mkdir -p /root/nbf-vault

cp /root/NoBrainFog/discord.env.example /root/nobrainfog-config/discord.env
cp /root/NoBrainFog/wechat.env.example /root/nobrainfog-config/wechat.env
```

Both real env files should point to the same task file:

```env
MD_PATH=/root/nbf-vault/todo.md
```

Never commit real env files. They contain secrets such as Discord tokens, WeChat Work secrets, and AI API keys.

## Discord setup

### 1. Create a Discord Application

Open <https://discord.com/developers/applications>.

1. Click **New Application**.
2. Name it, for example `NoBrainFog`.
3. Go to **Bot** in the sidebar.
4. Create a bot and copy its **Token**.
5. Enable **MESSAGE CONTENT INTENT** on the Bot page.

### 2. Get your Discord User ID

1. Enable **Developer Mode** in Discord user settings.
2. Right-click your avatar or username.
3. Click **Copy User ID**.
4. Put it in `TARGET_USER_ID`.

### 3. Invite the bot

In the Developer Portal:

```text
OAuth2 → URL Generator
```

Select this scope:

```text
bot
```

Recommended bot permissions:

```text
Send Messages
Read Message History
Attach Files
```

NoBrainFog currently focuses on DM messages between you and the bot. Inviting it to a server mainly helps establish a shared-server relationship so DMs are easier to open.

### 4. Discord env example

```env
ADAPTER_TYPE=discord

AI_DRIVER=openai
API_KEY=your_openai_or_grok_key_here
API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o

DISCORD_TOKEN=your_discord_bot_token_here
TARGET_USER_ID=123456789012345678

MD_PATH=/root/nbf-vault/todo.md
CATEGORIES=Personal,Work,Shop,Art,Finance,Admin
```

Start the Discord adapter:

```bash
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/discord.env
```

Successful startup looks like:

```text
✨ NoBrainFog Bot is now online as ...
```

## WeChat Work setup

The WeChat Work adapter exposes a `/wechat` webhook endpoint so WeChat Work can forward messages to NoBrainFog.

Recommended public path:

```text
WeChat Work console
  ↓
https://wechat.your-domain.com/wechat
  ↓
Cloudflare Tunnel / Nginx
  ↓
http://127.0.0.1:8080/wechat
  ↓
NoBrainFog WeChat Work adapter
```

### 1. Create a WeChat Work custom app

WeChat Work admin console: <https://work.weixin.qq.com/>

```text
App Management → Custom Apps → Create App
```

### 2. Get credentials

You need:

```text
WECHAT_CORP_ID
WECHAT_CORP_SECRET
WECHAT_AGENT_ID
WECHAT_TOKEN
WECHAT_ENCODING_AES_KEY
```

Where to find them:

- **Corp ID**: My Company → Company Info.
- **Agent ID**: custom app details → credentials/basic info.
- **Corp Secret**: custom app details → credentials/basic info.
- **Token**: custom app details → Receive Messages → API receive message server config.
- **EncodingAESKey**: generated on the same Receive Messages page.

`WECHAT_TOKEN` and `WECHAT_ENCODING_AES_KEY` must match exactly between the WeChat Work console and `wechat.env`.

### 3. WeChat env example

```env
ADAPTER_TYPE=wechat_work

AI_DRIVER=openai
API_KEY=your_openai_or_grok_key_here
API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o

WECHAT_CORP_ID=your_corp_id_here
WECHAT_CORP_SECRET=your_corp_secret_here
WECHAT_AGENT_ID=1000001
WECHAT_TOKEN=your_callback_token_here
WECHAT_ENCODING_AES_KEY=your_encoding_aes_key_here

AUTHORIZED_USERS=

# Optional. Leave empty to default to a hidden folder next to MD_PATH.
# WECHAT_DEDUPE_DIR=/root/nbf-vault/.wechat_msg_dedupe

MD_PATH=/root/nbf-vault/todo.md
CATEGORIES=Personal,Work,Shop,Art,Finance,Admin
```

`AUTHORIZED_USERS` can be left empty, which allows all users who can access the WeChat Work app. To restrict access later, provide WeChat Work user IDs separated by commas.

### 4. Start the WeChat adapter

```bash
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/wechat.env
```

Successful startup looks like:

```text
🚀 企业微信机器人启动在 0.0.0.0:8080
```

Local test:

```bash
curl -i http://127.0.0.1:8080/wechat
```

Seeing `403 Verification failed` is usually fine. It means the `/wechat` route is alive, but your manual request did not include WeChat Work signature parameters.

### 5. Recommended Cloudflare Tunnel configuration

If `cloudflared` and NoBrainFog run on the same Debian machine, configure the Tunnel Public Hostname like this:

```text
Subdomain: wechat
Domain: your-domain.com
Path: leave empty
Service Type: HTTP
Service URL: localhost:8080
```

In the WeChat Work console, use:

```text
URL: https://wechat.your-domain.com/wechat
Token: same as WECHAT_TOKEN
EncodingAESKey: same as WECHAT_ENCODING_AES_KEY
```

### 6. WeChat Work trusted IP

NoBrainFog prefers using the WeChat Work `message/send` API to actively reply to you. This outbound API requires your server's public egress IP to be allowed in the WeChat Work console.

If logs show:

```text
errcode: 60020
not allow to access from your ip
from ip: x.x.x.x
```

Add that `from ip` to the WeChat Work trusted IP / IP allowlist.

Approximate path:

```text
App Management → Custom App → NoBrainFog → Developer Interface / Trusted IP
```

Then restart the WeChat adapter:

```bash
~/bots.sh restart nbf-wcbot
```

If your home ISP changes your public IP, `60020` may happen again. Check the new `from ip` in logs and add it to the trusted IP list.

### 7. WeChat message dedupe

When AI responses are slow or the callback response is unstable, WeChat Work may retry the same message. NoBrainFog uses WeChat Work `MsgId` for lightweight dedupe so one message is not written to `todo.md` multiple times.

Default dedupe marker directory:

```text
/root/nbf-vault/.wechat_msg_dedupe/
```

You can customize it in `wechat.env`:

```env
WECHAT_DEDUPE_DIR=/root/nbf-vault/.wechat_msg_dedupe
```

This is not a `todo.md` file lock. It only prevents duplicate writes caused by WeChat webhook retries.

## Common commands

Discord and WeChat Work both support these core commands:

```text
/report or /r or /rep       Show task list
/export or /e or /exp       Export todo.md text
/undo                       Undo the last task
/done 2                     Mark #2 as done
/done keyword               Mark a task by keyword
/edit 2 new text            Edit task description
/pri 2 P1                   Update priority
/priority 2 P1              Update priority
/due 2 2026-05-30           Update deadline
/deadline 2 2026-05-30      Update deadline
/due 2 none                 Clear deadline
/memo 2 note                Update memo
/memo 2 none                Clear memo
/prior                      Generate priority analysis
/cbt 2                      CBT breakdown for one task
/cbt all                    Analyze all tasks
/yesucan                    Generate a motivational push message
/help or /h or /admhelp     Show help
```

Discord additionally supports:

```text
/import                     Upload todo.md to replace the current task file
```

WeChat Work does not support voice transcription yet. Image input has a basic pipeline, but text tasks are still the recommended primary workflow.

## Run Discord + WeChat Work together

Recommended tmux sessions:

```text
nbf-dcbot  → Discord adapter
nbf-wcbot  → WeChat Work adapter
```

Manual examples:

```bash
tmux new -s nbf-dcbot
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/discord.env
```

```bash
tmux new -s nbf-wcbot
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/wechat.env
```

List sessions:

```bash
tmux ls
```

Attach:

```bash
tmux attach -t nbf-dcbot
tmux attach -t nbf-wcbot
```

## rclone / Google Drive sync recommendation

If you already have an rclone remote such as:

```text
gdrive
```

Sync the single real task directory:

```text
/root/nbf-vault/
```

Target structure can look like:

```text
gdrive:NoBrainFog/
  todo.md
```

Principle:

```text
Discord adapter writes /root/nbf-vault/todo.md
WeChat adapter writes /root/nbf-vault/todo.md
rclone syncs /root/nbf-vault/todo.md to Google Drive
external edits can later flow back to local through rclone
```

## Troubleshooting

### Missing env variables on startup

Make sure you use explicit env-file startup:

```bash
python main.py --env-file /root/nobrainfog-config/discord.env
python main.py --env-file /root/nobrainfog-config/wechat.env
```

### Discord bot is online but does not reply

Check:

1. `TARGET_USER_ID` is your Discord user ID.
2. You are sending a DM to the bot.
3. **MESSAGE CONTENT INTENT** is enabled in the Discord Developer Portal.
4. `DISCORD_TOKEN` belongs to the correct bot.
5. The Python console has no exception.

### WeChat URL verification fails

Check:

1. The WeChat adapter is running.
2. `https://wechat.your-domain.com/wechat` reaches your server.
3. Token / EncodingAESKey exactly match `wechat.env`.
4. Flask logs for signature mismatch, AES decrypt failed, or Corp ID mismatch.
5. Whether WeChat Work requires your domain registration subject to match or be related to the enterprise subject.

### WeChat writes tasks but does not reply

Check logs for:

```text
errcode: 60020
not allow to access from your ip
```

If present, add the logged `from ip` to WeChat Work trusted IP.

### AI processing fails

Check:

1. `AI_DRIVER` is `openai` or `gemini`.
2. `API_KEY` or `GEMINI_API_KEY` is correct.
3. `API_BASE` matches your model provider.
4. The server can reach the API provider.

## Security notes

- Do not commit real env files.
- Do not share Discord tokens, WeChat Work secrets, or AI API keys in chats.
- Use HTTPS for WeChat Work production callbacks.
- Rotate Discord tokens and WeChat Work secrets periodically.
- Consider tightening `AUTHORIZED_USERS` later so not every enterprise user can operate your task file.

## Files

```text
main.py                  # explicitly loads --env-file and starts the selected adapter
adapters/discord_bot.py  # Discord DM adapter
adapters/wechat_work.py  # WeChat Work webhook adapter
core/help_text.py        # Discord / WeChat help text
core/idempotency.py      # WeChat webhook retry dedupe
core/ingest.py           # unified input ingestion entry
core/handler.py          # todo.md read/write logic
discord.env.example      # Discord config template
wechat.env.example       # WeChat Work config template
```
