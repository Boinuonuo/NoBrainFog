# 📱 企业微信集成设置指南

## 🚀 快速开始

### 1. 创建企业微信应用

1. 登录[企业微信管理后台](https://work.weixin.qq.com/)
2. 进入「应用管理」→「自建应用」→「创建应用」
3. 填写应用信息：
   - 应用名称：NoBrainFog
   - 应用介绍：AI 驱动的任务管理工具
   - 应用图标：上传合适的图标

### 2. 获取应用配置

在企业微信应用详情页面获取以下信息：

- **企业 ID (Corp ID)**：在「我的企业」→「企业信息」中找到
- **应用 Secret**：在应用详情页的「凭证与基础信息」中
- **应用 ID (Agent ID)**：在应用详情页的「凭证与基础信息」中
- **Token**：在「接收消息」页面设置
- **EncodingAESKey**：在「接收消息」页面随机生成

### 3. 配置消息接收

1. 在应用详情页点击「接收消息」
2. 设置服务器 URL：`http://你的服务器IP:8080/wechat`
3. 设置 Token 和 EncodingAESKey
4. 启用「接收消息」和「发送消息」权限

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
# 切换到企业微信适配器
ADAPTER_TYPE=wechat_work

# 企业微信配置
WECHAT_CORP_ID=你的企业ID
WECHAT_CORP_SECRET=你的应用Secret
WECHAT_AGENT_ID=你的应用ID
WECHAT_TOKEN=你设置的Token
WECHAT_ENCODING_AES_KEY=生成的EncodingAESKey

# AI 配置（保持原有）
AI_DRIVER=openai
API_KEY=你的OpenAI密钥
MODEL_NAME=gpt-4o

# 其他配置
MD_PATH=./todo.md
CATEGORIES=Personal,Work,Shop,Art,Finance,Admin
```

### 5. 安装依赖

```bash
pip install -r requirements.txt
```

### 6. 启动服务

```bash
python main.py
```

服务将启动在 `http://0.0.0.0:8080`

## 🔧 网络配置

### 内网穿透（如果没有公网IP）

如果服务器在内网，可以使用以下工具：

#### 方案一：ngrok
```bash
# 安装 ngrok
pip install pyngrok

# 启动内网穿透
ngrok http 8080
```

#### 方案二：frp
```bash
# 在 frp 服务端配置
[common]
bind_port = 7000

[http]
type = http
local_port = 8080
custom_domains = your-domain.com
```

#### 方案三：Termux-API（如果使用 Termux）
```bash
# 使用 Termux 的网络功能
pkg install termux-api
```

## 📱 使用方法

### 基础命令
- `/report` 或 `/r` - 查看任务列表
- `/export` 或 `/e` - 导出任务内容  
- `/help` 或 `/h` - 显示帮助

### 添加任务
直接发送文字、图片或语音：
- "明天下午3点开会讨论项目进度"
- 发送截图自动识别任务
- 发送语音自动转换为文字任务

## 🛠️ 故障排除

### 1. 验证失败
- 检查 Token 是否正确
- 确认服务器 URL 可访问
- 查看 Flask 日志

### 2. 消息发送失败
- 检查应用权限是否开启
- 确认 access_token 是否有效
- 查看企业微信限制

### 3. AI 处理失败
- 检查 API 密钥是否正确
- 确认网络连接正常
- 查看 AI 服务状态

## 📋 权限配置

在企业微信中为应用开启以下权限：
- 发送消息到企业微信
- 接收消息
- 读取通讯录（如需要用户验证）

## 🔒 安全建议

1. 定期更换应用 Secret
2. 设置授权用户列表
3. 使用 HTTPS（生产环境）
4. 监控异常访问

## 📞 支持

如遇问题可：
1. 查看 Flask 日志
2. 检查企业微信应用状态
3. 验证网络连接
4. 查看企业微信文档

---

🎉 现在你的 NoBrainFog 可以在企业微信中使用了！
