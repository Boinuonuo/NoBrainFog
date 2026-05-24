# 🧠 NoBrainFog

中文 | [English](README.en.md)

NoBrainFog 是一个 AI 驱动的个人任务入口系统。它把你在 Discord 或企业微信里发来的碎片化想法整理成统一的 Markdown `todo.md`。

核心思想：聊天平台只是入口，真正的数据层是同一个 `todo.md`。

```text
Discord / WeChat Work
        ↓
NoBrainFog adapter process
        ↓
/root/nbf-vault/todo.md
        ↓
rclone / Google Drive sync
```

## 推荐目录结构

```text
/root/NoBrainFog/                  # 唯一代码目录，git pull 只在这里
/root/nobrainfog-config/
  discord.env                      # Discord 私有配置，不进 Git
  wechat.env                       # 企业微信私有配置，不进 Git
/root/nbf-vault/
  todo.md                          # 唯一真实任务文件，可被 rclone 同步
```

原则：

```text
代码只有一份
配置可以有多份
数据只能有一份
```

## 安装

```bash
cd /root

git clone https://github.com/Boinuonuo/NoBrainFog.git
cd /root/NoBrainFog

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果已经 clone 过：

```bash
cd /root/NoBrainFog
git pull
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置 env

NoBrainFog 不再默认读取根目录 `.env`。每个 adapter 必须显式指定 env 文件。

```bash
python main.py --env-file /root/nobrainfog-config/discord.env
python main.py --env-file /root/nobrainfog-config/wechat.env
```

创建配置目录并复制模板：

```bash
mkdir -p /root/nobrainfog-config
mkdir -p /root/nbf-vault

cp /root/NoBrainFog/discord.env.example /root/nobrainfog-config/discord.env
cp /root/NoBrainFog/wechat.env.example /root/nobrainfog-config/wechat.env
```

两份真实 env 都建议指向同一个任务文件：

```env
MD_PATH=/root/nbf-vault/todo.md
```

不要提交真实 env 文件。它们包含 Discord token、企业微信 Secret、AI API Key 等敏感信息。

## Discord 配置

### 1. 创建 Discord Application

打开 <https://discord.com/developers/applications>。

1. 点击 **New Application**。
2. 命名，例如 `NoBrainFog`。
3. 左侧进入 **Bot**。
4. 创建 bot，并复制 **Token**。
5. 在 Bot 页面打开 **MESSAGE CONTENT INTENT**。

### 2. 获取你的 Discord User ID

1. Discord 用户设置里打开 **Developer Mode**。
2. 右键你的头像或用户名。
3. 点击 **Copy User ID**。
4. 写入 `TARGET_USER_ID`。

### 3. 邀请 Bot

Developer Portal：

```text
OAuth2 → URL Generator
```

Scopes 选择：

```text
bot
```

Bot Permissions 至少选择：

```text
Send Messages
Read Message History
Attach Files
```

NoBrainFog 当前主要处理你和 bot 的 DM。邀请进服务器的意义是方便建立 DM 关系。

### 4. Discord env 示例

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

启动：

```bash
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/discord.env
```

成功时会看到：

```text
✨ NoBrainFog Bot is now online as ...
```

## 企业微信配置

企业微信 adapter 提供 `/wechat` webhook，让企业微信把消息转发给 NoBrainFog。

推荐公网链路：

```text
企业微信后台
  ↓
https://wechat.your-domain.com/wechat
  ↓
Cloudflare Tunnel / Nginx
  ↓
http://127.0.0.1:8080/wechat
  ↓
NoBrainFog WeChat Work adapter
```

### 1. 创建企业微信自建应用

企业微信管理后台：<https://work.weixin.qq.com/>

```text
应用管理 → 自建应用 → 创建应用
```

### 2. 获取 credentials

需要准备：

```text
WECHAT_CORP_ID
WECHAT_CORP_SECRET
WECHAT_AGENT_ID
WECHAT_TOKEN
WECHAT_ENCODING_AES_KEY
```

位置：

- **Corp ID**：我的企业 → 企业信息。
- **Agent ID**：自建应用详情页 → 凭证与基础信息。
- **Corp Secret**：自建应用详情页 → 凭证与基础信息。
- **Token**：自建应用详情页 → 接收消息 → API 接收消息服务器配置。
- **EncodingAESKey**：同一个接收消息页面随机生成。

`WECHAT_TOKEN` 和 `WECHAT_ENCODING_AES_KEY` 必须同时写在企业微信页面和 `wechat.env` 里，并保持完全一致。

### 3. WeChat env 示例

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

`AUTHORIZED_USERS` 可以留空，表示允许所有能访问该应用的用户使用。之后如果要限制用户，可以填企业微信 user id，多个用户用英文逗号分隔。

### 4. 启动 WeChat adapter

```bash
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/wechat.env
```

成功时会看到：

```text
🚀 企业微信机器人启动在 0.0.0.0:8080
```

本机测试：

```bash
curl -i http://127.0.0.1:8080/wechat
```

看到 `403 Verification failed` 通常是正常的，说明 `/wechat` route 活着，只是你没有带企业微信签名参数。

### 5. Cloudflare Tunnel 推荐配置

如果 cloudflared 和 NoBrainFog 在同一台 Debian 上，Cloudflare Tunnel 的 Public Hostname 可以这样填：

```text
Subdomain: wechat
Domain: your-domain.com
Path: 留空
Service Type: HTTP
Service URL: localhost:8080
```

企业微信后台最终填写：

```text
URL: https://wechat.your-domain.com/wechat
Token: 和 WECHAT_TOKEN 一样
EncodingAESKey: 和 WECHAT_ENCODING_AES_KEY 一样
```

### 6. 企业微信可信 IP

NoBrainFog 会优先使用企业微信 `message/send` 接口主动回复你。这个出站接口需要企业微信后台允许你的服务器公网出口 IP。

如果日志里出现：

```text
errcode: 60020
not allow to access from your ip
from ip: x.x.x.x
```

去企业微信后台把这个 `from ip` 加入可信 IP / IP 白名单。

大概路径：

```text
应用管理 → 自建应用 → NoBrainFog → 开发者接口 / 企业可信 IP / 可信 IP
```

保存后重启 WeChat adapter：

```bash
~/bots.sh restart nbf-wcbot
```

如果你的家庭公网 IP 变化，可能会再次出现 `60020`。看日志里的新 `from ip`，重新加入可信 IP 即可。

### 7. 企业微信消息去重

企业微信在 AI 响应慢、网络慢或回调返回不稳定时可能重试同一条消息。NoBrainFog 使用企业微信 `MsgId` 做轻量去重，避免同一条消息被重复写入 `todo.md`。

默认去重 marker 保存在：

```text
/root/nbf-vault/.wechat_msg_dedupe/
```

也可以在 `wechat.env` 中自定义：

```env
WECHAT_DEDUPE_DIR=/root/nbf-vault/.wechat_msg_dedupe
```

这不是 `todo.md` 文件锁。它只负责拦截企业微信 webhook 重试导致的重复写入。

## 常用命令

Discord 和企业微信都支持这些核心命令：

```text
/report 或 /r 或 /rep       查看任务列表
/export 或 /e 或 /exp       导出 todo.md 文本
/undo                       撤回最后一条任务
/done 2                     标记 #2 完成
/done 关键词                按关键词完成任务
/edit 2 新内容              修改任务描述
/pri 2 P1                   修改优先级
/priority 2 P1              修改优先级
/due 2 2026-05-30           修改截止日期
/deadline 2 2026-05-30      修改截止日期
/due 2 none                 清空截止日期
/memo 2 备注                修改备注
/memo 2 none                清空备注
/prior                      生成优先级建议
/cbt 2                      对某个任务做 CBT 拆解
/cbt all                    分析全部任务
/yesucan                    生成鼓励/推进消息
/help 或 /h 或 /admhelp      查看帮助
```

Discord 额外支持：

```text
/import                     上传 todo.md 替换当前任务文件
```

企业微信暂不支持语音转写。图片入口已接入基础 pipeline，但建议先以文字任务为主。

## 同时运行 Discord + 企业微信

推荐用两个 tmux session，例如你的自动化脚本可以启动：

```text
nbf-dcbot  → Discord adapter
nbf-wcbot  → WeChat Work adapter
```

手动启动示例：

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

查看：

```bash
tmux ls
```

重新进入：

```bash
tmux attach -t nbf-dcbot
tmux attach -t nbf-wcbot
```

## rclone / Google Drive 同步建议

如果你已经配置了 rclone remote，例如：

```text
gdrive
```

推荐同步唯一真实任务文件所在目录：

```text
/root/nbf-vault/
```

目标结构可以类似：

```text
gdrive:NoBrainFog/
  todo.md
```

原则：

```text
Discord adapter 写 /root/nbf-vault/todo.md
WeChat adapter 写 /root/nbf-vault/todo.md
rclone 负责把 /root/nbf-vault/todo.md 同步到 Google Drive
外部编辑后再由 rclone 拉回本地
```

## 故障排除

### 启动时报 env 缺失

确认你使用的是显式启动方式：

```bash
python main.py --env-file /root/nobrainfog-config/discord.env
python main.py --env-file /root/nobrainfog-config/wechat.env
```

### Discord bot 上线但不回复

检查：

1. `TARGET_USER_ID` 是否是你的 Discord 用户 ID。
2. 是否给 bot 发的是 DM。
3. Developer Portal 是否开启了 **MESSAGE CONTENT INTENT**。
4. `DISCORD_TOKEN` 是否来自正确 bot。
5. Python 控制台是否有异常。

### 企业微信 URL 验证失败

检查：

1. WeChat adapter 是否正在运行。
2. `https://wechat.your-domain.com/wechat` 是否能访问到你的服务器。
3. Token / EncodingAESKey 是否和 `wechat.env` 完全一致。
4. Flask 日志是否有 signature mismatch、AES decrypt failed、Corp ID mismatch。
5. 是否有企业微信域名备案主体或关联主体要求。

### 企业微信能写入但不回复

检查日志里是否有：

```text
errcode: 60020
not allow to access from your ip
```

如果有，把日志里的 `from ip` 加入企业微信可信 IP。

### AI 处理失败

检查：

1. `AI_DRIVER` 是否是 `openai` 或 `gemini`。
2. `API_KEY` 或 `GEMINI_API_KEY` 是否正确。
3. `API_BASE` 是否适配你的模型服务。
4. 服务器是否能访问对应 API。

## 安全建议

- 不要提交真实 env 文件。
- 不要把 Discord token、企业微信 Secret、AI API Key 发到聊天里。
- 企业微信生产环境使用 HTTPS。
- 定期轮换 Discord token 和企业微信 Secret。
- `AUTHORIZED_USERS` 后续可以收紧，避免企业内所有人都能操作你的任务库。

## 文件说明

```text
main.py                  # 显式读取 --env-file 并启动指定 adapter
adapters/discord_bot.py  # Discord DM adapter
adapters/wechat_work.py  # 企业微信 webhook adapter
core/help_text.py        # Discord / WeChat 帮助文案
core/idempotency.py      # 企业微信 webhook 重试去重
core/ingest.py           # 统一输入入口
core/handler.py          # todo.md 文件读写逻辑
discord.env.example      # Discord 配置模板
wechat.env.example       # 企业微信配置模板
```
