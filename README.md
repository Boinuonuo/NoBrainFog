# 🧠 NoBrainFog (无脑·雾)

> “用了它，头脑清楚，告别脑雾。”

**NoBrainFog** 是一套基于 AI 驱动的个人任务架构系统。它能将你零散、感性、甚至带有情绪的碎片化输入，转化为结构化的 Markdown 任务矩阵。

它的核心不是某一个聊天平台，而是一个共享的 `todo.md` 数据层。Discord、企业微信、未来的 CLI / Email adapter 都只是不同入口。

## ✨ 特性

- **Vibe-to-Grid**：允许胡言乱语，AI 负责逻辑收束。
- **Time Intelligence**：自动识别“后天”、“下周三”并计算精准日期。
- **Privacy First**：核心逻辑与展示层分离，任务数据保存在本地 `todo.md`。
- **Multi-Adapter**：同一份代码可以启动多个 adapter 进程，例如 Discord + 企业微信。
- **Shared Data Layer**：多个 adapter 可以指向同一个 `MD_PATH`，配合 rclone / Google Drive 做同步。

## 🧱 推荐架构

推荐把代码、配置、数据分开：

```text
/root/NoBrainFog/                  # 唯一代码目录，git pull 只在这里
/root/nobrainfog-config/
  discord.env                      # Discord 私有配置，不进 Git
  wechat.env                       # 企业微信私有配置，不进 Git
/root/nbf-vault/
  todo.md                          # 唯一真实任务文件，可被 rclone 同步
```

核心原则：

```text
代码只有一份
配置可以有多份
数据只能有一份
```

典型数据流：

```text
Discord / WeChat Work
        ↓
NoBrainFog adapter process
        ↓
/root/nbf-vault/todo.md
        ↓
rclone sync / Google Drive
        ↓
外部编辑也能回流到 bot
```

## 📦 安装

```bash
cd /root

git clone https://github.com/Boinuonuo/NoBrainFog.git
cd /root/NoBrainFog

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果你已经 clone 过：

```bash
cd /root/NoBrainFog
git pull
source .venv/bin/activate
pip install -r requirements.txt
```

## 🔐 配置 env 文件

NoBrainFog 不再默认读取根目录 `.env`。

现在必须显式指定 adapter env 文件：

```bash
python main.py --env-file /root/nobrainfog-config/discord.env
python main.py --env-file /root/nobrainfog-config/wechat.env
```

创建配置目录：

```bash
mkdir -p /root/nobrainfog-config
mkdir -p /root/nbf-vault
```

复制模板：

```bash
cp /root/NoBrainFog/discord.env.example /root/nobrainfog-config/discord.env
cp /root/NoBrainFog/wechat.env.example /root/nobrainfog-config/wechat.env
```

编辑真实配置：

```bash
nano /root/nobrainfog-config/discord.env
nano /root/nobrainfog-config/wechat.env
```

两份 env 都建议指向同一个任务文件：

```env
MD_PATH=/root/nbf-vault/todo.md
```

不要把真实 env 文件提交到 GitHub。它们包含 Discord token、企业微信 Secret、AI API Key 等敏感信息。

## 🤖 Discord 配置教程

### 1. 创建 Discord Application

1. 打开 Discord Developer Portal：<https://discord.com/developers/applications>
2. 点击 **New Application**。
3. 命名，例如 `NoBrainFog`。
4. 进入这个 application 的详情页。

### 2. 创建 Bot

1. 左侧进入 **Bot**。
2. 点击 **Add Bot** 或创建 bot user。
3. 在 Bot 页面复制 **Token**。
4. 把 token 写入：

```env
DISCORD_TOKEN=your_discord_bot_token_here
```

Bot token 等同密码，不要截图、不要发给别人、不要提交到 GitHub。

### 3. 开启 Message Content Intent

NoBrainFog 的 Discord adapter 会读取你的 DM 文本内容，所以需要在 Developer Portal 的 Bot 页面开启：

```text
Privileged Gateway Intents
  MESSAGE CONTENT INTENT = ON
```

如果这个没有打开，bot 可能上线了，但看不到你发的文字内容。

### 4. 获取你的 Discord User ID

NoBrainFog 默认只处理指定用户的私信，避免别人误用你的 bot。

获取方法：

1. Discord 用户设置里打开 **Developer Mode**。
2. 右键你的头像或用户名。
3. 点击 **Copy User ID**。
4. 写入：

```env
TARGET_USER_ID=123456789012345678
```

### 5. 邀请 Bot 到服务器

1. Developer Portal 左侧进入 **OAuth2**。
2. 进入 **URL Generator**。
3. Scopes 选择：

```text
bot
```

如果你之后使用 slash command，再加：

```text
applications.commands
```

4. Bot Permissions 建议至少选择：

```text
Send Messages
Read Message History
Attach Files
```

5. 复制生成的邀请 URL，在浏览器打开。
6. 选择你的服务器并授权。

NoBrainFog 当前主要处理你和 bot 的 DM。邀请进服务器的意义是让你和 bot 之间建立共同服务器关系，方便打开私信。

### 6. 配置 Discord env

编辑：

```bash
nano /root/nobrainfog-config/discord.env
```

最小配置示例：

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

启动 Discord adapter：

```bash
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/discord.env
```

看到类似输出即代表上线：

```text
✨ NoBrainFog Bot is now online as ...
```

### 7. Discord 使用方法

给 bot 发私信：

```text
明天下午三点提醒我整理企业微信 webhook 配置
```

常用命令：

```text
/report 或 /rep      查看任务列表
/export 或 /exp      导出 todo.md
/import              上传 todo.md 替换当前任务文件
/undo                撤回最后一条任务
/done 2              标记 #2 完成
/edit 2 新内容       修改任务描述
/pri 2 P1            修改优先级
/due 2 2026-05-30    修改截止日期
/memo 2 备注         修改备注
/admhelp             查看完整帮助
```

## 💬 企业微信配置教程

企业微信 adapter 的作用是提供一个公网可访问的 `/wechat` webhook，让企业微信把消息转发给 NoBrainFog。

整体链路：

```text
企业微信后台
  ↓
https://wechat.your-domain.com/wechat
  ↓
Nginx / Tunnel
  ↓
http://127.0.0.1:8080/wechat
  ↓
NoBrainFog WeChat Work adapter
  ↓
/root/nbf-vault/todo.md
```

### 1. 创建企业微信自建应用

1. 登录企业微信管理后台：<https://work.weixin.qq.com/>
2. 进入 **应用管理**。
3. 找到 **自建应用**。
4. 点击 **创建应用**。
5. 填写应用信息：
   - 应用名称：`NoBrainFog`
   - 应用介绍：AI 驱动的任务管理工具
   - 应用图标：任选

### 2. 获取企业微信 credentials

你需要准备这些值：

```text
WECHAT_CORP_ID
WECHAT_CORP_SECRET
WECHAT_AGENT_ID
WECHAT_TOKEN
WECHAT_ENCODING_AES_KEY
```

对应位置：

- **Corp ID**：企业微信后台 → 我的企业 → 企业信息。
- **Agent ID**：自建应用详情页 → 凭证与基础信息。
- **Corp Secret / 应用 Secret**：自建应用详情页 → 凭证与基础信息。
- **Token**：自建应用详情页 → 接收消息 → API 接收消息服务器配置。
- **EncodingAESKey**：同一个接收消息页面随机生成。

`Token` 是你自己设置的随机字符串。它必须同时写在企业微信页面和 `wechat.env` 里。

`EncodingAESKey` 建议使用企业微信页面的随机生成按钮。它也必须同时写在企业微信页面和 `wechat.env` 里。

### 3. 配置 WeChat env

编辑：

```bash
nano /root/nobrainfog-config/wechat.env
```

最小配置示例：

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

MD_PATH=/root/nbf-vault/todo.md
CATEGORIES=Personal,Work,Shop,Art,Finance,Admin
```

`AUTHORIZED_USERS` 可以留空，表示允许所有能访问该企业微信应用的用户使用。之后如果要限制用户，可以填企业微信 user id，多个用户用英文逗号分隔。

### 4. 启动 WeChat adapter

```bash
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/wechat.env
```

成功时会看到类似：

```text
🚀 企业微信机器人启动在 0.0.0.0:8080
```

本机测试：

```bash
curl -i http://127.0.0.1:8080/wechat
```

看到 `403 Verification failed` 不一定是坏事。它说明 `/wechat` route 已经活了，只是你没有带企业微信验证参数。

### 5. 准备公网 HTTPS 域名

企业微信后台要求 URL 以 `http://` 或 `https://` 开头。生产环境建议使用 HTTPS。

推荐使用专用子域名：

```text
wechat.your-domain.com
```

DNS 中添加 A 记录：

```text
wechat.your-domain.com -> 你的 Debian 服务器公网 IP
```

### 6. Nginx 反向代理

安装 Nginx 和 Certbot：

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx -y
```

创建 Nginx 配置：

```bash
sudo nano /etc/nginx/sites-available/nobrainfog-wechat
```

示例配置：

```nginx
server {
    server_name wechat.your-domain.com;

    location /wechat {
        proxy_pass http://127.0.0.1:8080/wechat;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/nobrainfog-wechat /etc/nginx/sites-enabled/nobrainfog-wechat
sudo nginx -t
sudo systemctl reload nginx
```

申请 HTTPS 证书：

```bash
sudo certbot --nginx -d wechat.your-domain.com
```

最终企业微信后台 URL 填：

```text
https://wechat.your-domain.com/wechat
```

### 7. 企业微信后台接收消息配置

进入自建应用详情页：

```text
应用管理 → 自建应用 → NoBrainFog → 接收消息 → API 接收消息
```

填写：

```text
URL: https://wechat.your-domain.com/wechat
Token: 和 WECHAT_TOKEN 一模一样
EncodingAESKey: 和 WECHAT_ENCODING_AES_KEY 一模一样
```

然后保存。

如果保存失败，优先检查：

1. WeChat adapter 是否正在运行。
2. 域名 DNS 是否指向正确服务器。
3. Nginx 是否能把 `/wechat` 转发到 `127.0.0.1:8080`。
4. 企业微信页面的 Token 是否和 `wechat.env` 一致。
5. 企业微信页面的 EncodingAESKey 是否和 `wechat.env` 一致。
6. Flask / Python 控制台是否有签名或解密相关错误。

### 8. 企业微信使用方法

应用配置成功后，在企业微信里给 NoBrainFog 应用发消息：

```text
明天下午三点开会讨论项目进度
```

常用命令：

```text
/report 或 /r      查看任务列表
/export 或 /e      导出任务内容
/help 或 /h        显示帮助
/undo              撤回最后一条任务
```

## 🧵 同时运行 Discord + 企业微信

推荐用两个 tmux session：

### Discord session

```bash
tmux new -s nbf-discord
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/discord.env
```

按 `Ctrl+B`，再按 `D`，可以把 session 放到后台。

### WeChat session

```bash
tmux new -s nbf-wechat
cd /root/NoBrainFog
source .venv/bin/activate
python main.py --env-file /root/nobrainfog-config/wechat.env
```

查看 session：

```bash
tmux ls
```

重新进入：

```bash
tmux attach -t nbf-discord
tmux attach -t nbf-wechat
```

## 🔄 rclone / Google Drive 同步建议

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

注意：如果多个 adapter 或外部编辑同时写入同一个文件，未来最好给 `TodoHandler` 增加文件锁，避免极端情况下写入冲突。

## 🛠️ 故障排除

### 启动时报 env 缺失

确认你用的是新的显式启动方式：

```bash
python main.py --env-file /root/nobrainfog-config/discord.env
python main.py --env-file /root/nobrainfog-config/wechat.env
```

不要再依赖根目录 `.env`。

### Discord bot 上线但不回复

检查：

1. `TARGET_USER_ID` 是否是你的 Discord 用户 ID。
2. 是否给 bot 发的是 DM。
3. Developer Portal 里是否开启了 **MESSAGE CONTENT INTENT**。
4. `DISCORD_TOKEN` 是否来自正确的 bot。
5. Python 控制台是否有异常。

### 企业微信 URL 验证失败

检查：

1. `python main.py --env-file /root/nobrainfog-config/wechat.env` 是否正在运行。
2. Nginx 是否 reload 成功。
3. `https://wechat.your-domain.com/wechat` 是否能访问到你的服务器。
4. 企业微信页面的 Token / EncodingAESKey 是否和 `wechat.env` 完全一致。
5. 是否有域名备案主体或企业主体关联要求。

### AI 处理失败

检查：

1. `AI_DRIVER` 是否是 `openai` 或 `gemini`。
2. `API_KEY` 或 `GEMINI_API_KEY` 是否正确。
3. `API_BASE` 是否适配你的模型服务。
4. 服务器是否能访问对应 API。

## 🔒 安全建议

- 不要提交真实 env 文件。
- 不要把 Discord token、企业微信 Secret、AI API Key 发到聊天里。
- 企业微信生产环境使用 HTTPS。
- 定期轮换 Discord token 和企业微信 Secret。
- `AUTHORIZED_USERS` 后续可以收紧，避免企业内所有人都能操作你的任务库。

## 📄 文件说明

```text
main.py                  # 显式读取 --env-file 并启动指定 adapter
adapters/discord_bot.py  # Discord DM adapter
adapters/wechat_work.py  # 企业微信 webhook adapter
core/ingest.py           # 统一输入入口
core/handler.py          # todo.md 文件读写逻辑
discord.env.example      # Discord 配置模板
wechat.env.example       # 企业微信配置模板
```
