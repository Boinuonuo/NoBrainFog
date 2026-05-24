# adapters/wechat_work.py
import base64
import hashlib
import struct
import time
import xml.etree.ElementTree as ET

import requests
from Crypto.Cipher import AES
from flask import Flask, jsonify, request

from core.ingest import IngestService


class WeChatWorkCryptoError(Exception):
    """Raised when WeChat Work callback crypto verification/decryption fails."""


class WeChatWorkBot:
    MESSAGE_LIMIT = 1800

    def __init__(self, config):
        self.app = Flask(__name__)
        self.config = config
        self.ingest = IngestService(config)
        self.processor = self.ingest.processor
        self.handler = self.ingest.handler

        self.corp_id = config.get("WECHAT_CORP_ID")
        self.corp_secret = config.get("WECHAT_CORP_SECRET")
        self.agent_id = config.get("WECHAT_AGENT_ID")
        self.token = config.get("WECHAT_TOKEN")
        self.encoding_aes_key = config.get("WECHAT_ENCODING_AES_KEY")
        self.aes_key = self._build_aes_key(self.encoding_aes_key)

        self.access_token = None
        self.token_expires = 0
        self.authorized_users = set(config.get("AUTHORIZED_USERS", []))

        self._setup_routes()

    def _build_aes_key(self, encoding_aes_key):
        if not encoding_aes_key:
            return None

        try:
            aes_key = base64.b64decode(f"{encoding_aes_key}=")
        except Exception as e:
            raise WeChatWorkCryptoError(f"Invalid WECHAT_ENCODING_AES_KEY: {e}")

        if len(aes_key) != 32:
            raise WeChatWorkCryptoError(
                "Invalid AES key length. Check WECHAT_ENCODING_AES_KEY."
            )

        return aes_key

    def _get_access_token(self):
        """获取企业微信 access_token，用于主动发消息。"""
        if self.access_token and time.time() <= self.token_expires - 300:
            return self.access_token

        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret,
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("errcode") != 0:
            print(f"❌ 获取 access_token 失败: {data}")
            raise Exception(f"企业微信认证失败: {data.get('errmsg', '未知错误')}")

        self.access_token = data["access_token"]
        self.token_expires = time.time() + data["expires_in"]
        print("✅ 成功获取 access_token")
        return self.access_token

    def _calculate_signature(self, timestamp, nonce, encrypted_payload):
        if not all([self.token, timestamp, nonce, encrypted_payload]):
            return None

        items = [self.token, timestamp, nonce, encrypted_payload]
        items.sort()
        return hashlib.sha1("".join(items).encode("utf-8")).hexdigest()

    def _verify_signature(self, signature, timestamp, nonce, encrypted_payload):
        expected = self._calculate_signature(timestamp, nonce, encrypted_payload)
        return bool(expected and signature and expected == signature)

    def _decrypt_payload(self, encrypted_payload):
        if not self.aes_key or len(self.aes_key) != 32:
            raise WeChatWorkCryptoError(
                "Invalid AES key length. Check WECHAT_ENCODING_AES_KEY."
            )

        try:
            encrypted_data = base64.b64decode(encrypted_payload)
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
            decrypted = cipher.decrypt(encrypted_data)
        except Exception as e:
            raise WeChatWorkCryptoError(f"AES decrypt failed: {e}")

        if not decrypted:
            raise WeChatWorkCryptoError("AES decrypt returned empty data.")

        pad = decrypted[-1]
        if pad < 1 or pad > 32:
            raise WeChatWorkCryptoError("Invalid PKCS#7 padding.")

        content = decrypted[:-pad]
        if len(content) < 20:
            raise WeChatWorkCryptoError("Decrypted payload is too short.")

        xml_length = struct.unpack("!I", content[16:20])[0]
        xml_start = 20
        xml_end = xml_start + xml_length

        plaintext = content[xml_start:xml_end].decode("utf-8")
        from_corp_id = content[xml_end:].decode("utf-8")

        if self.corp_id and from_corp_id != self.corp_id:
            raise WeChatWorkCryptoError("Corp ID mismatch in decrypted callback payload.")

        return plaintext

    def _encrypt_payload(self, plaintext_xml):
        if not self.aes_key or len(self.aes_key) != 32:
            raise WeChatWorkCryptoError(
                "Invalid AES key length. Check WECHAT_ENCODING_AES_KEY."
            )

        # WeChat Work encrypted payload format:
        # 16 random bytes + 4 bytes xml length + xml + corp_id + PKCS#7 padding
        random_bytes = b"NoBrainFogRndStr"
        xml_bytes = plaintext_xml.encode("utf-8")
        corp_bytes = (self.corp_id or "").encode("utf-8")
        msg = random_bytes + struct.pack("!I", len(xml_bytes)) + xml_bytes + corp_bytes

        pad = 32 - (len(msg) % 32)
        if pad == 0:
            pad = 32
        msg += bytes([pad]) * pad

        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
        encrypted = cipher.encrypt(msg)
        return base64.b64encode(encrypted).decode("utf-8")

    def _extract_encrypt_from_xml(self, xml_data):
        try:
            root = ET.fromstring(xml_data)
        except Exception as e:
            raise WeChatWorkCryptoError(f"Invalid callback XML: {e}")

        encrypted_node = root.find("Encrypt")
        if encrypted_node is None or not encrypted_node.text:
            raise WeChatWorkCryptoError("Missing Encrypt field in callback XML.")

        return encrypted_node.text

    def _make_encrypted_response_xml(self, plaintext_xml, timestamp=None, nonce=None):
        timestamp = timestamp or str(int(time.time()))
        nonce = nonce or str(int(time.time() * 1000))
        encrypted = self._encrypt_payload(plaintext_xml)
        signature = self._calculate_signature(timestamp, nonce, encrypted)

        return f"""
<xml>
<Encrypt><![CDATA[{encrypted}]]></Encrypt>
<MsgSignature><![CDATA[{signature}]]></MsgSignature>
<TimeStamp>{timestamp}</TimeStamp>
<Nonce><![CDATA[{nonce}]]></Nonce>
</xml>
""".strip()

    def _setup_routes(self):
        @self.app.route("/wechat", methods=["GET"])
        def verify_url():
            """企业微信 URL 验证。"""
            signature = request.args.get("msg_signature", "")
            timestamp = request.args.get("timestamp", "")
            nonce = request.args.get("nonce", "")
            echostr = request.args.get("echostr", "")

            try:
                if not self._verify_signature(signature, timestamp, nonce, echostr):
                    print("❌ 企业微信服务器验证失败: signature mismatch")
                    return "Verification failed", 403

                plain_echostr = self._decrypt_payload(echostr)
                print("✅ 企业微信服务器验证成功")
                return plain_echostr
            except Exception as e:
                print(f"❌ 企业微信服务器验证异常: {e}")
                return "Verification failed", 403

        @self.app.route("/wechat", methods=["POST"])
        def handle_message():
            """企业微信消息回调。"""
            try:
                signature = request.args.get("msg_signature", "")
                timestamp = request.args.get("timestamp", "")
                nonce = request.args.get("nonce", "")
                data = request.data

                if not data:
                    return jsonify({"status": "error", "message": "No data received"}), 400

                encrypted_payload = self._extract_encrypt_from_xml(data)

                if not self._verify_signature(signature, timestamp, nonce, encrypted_payload):
                    print("❌ 企业微信消息签名验证失败")
                    return jsonify({"status": "error", "message": "Invalid signature"}), 403

                decrypted_xml = self._decrypt_payload(encrypted_payload)
                root = ET.fromstring(decrypted_xml)

                to_user = root.findtext("ToUserName", "")
                from_user = root.findtext("FromUserName", "")
                msg_type = root.findtext("MsgType", "")

                if self.authorized_users and from_user not in self.authorized_users:
                    print(f"❌ 未授权用户: {from_user}")
                    reply = "❌ 您没有权限使用此机器人"
                else:
                    reply = self._dispatch_message(root, msg_type, from_user)

                # 推荐路径：主动发消息，企业微信客户端更稳定可见。
                if self._send_active_reply(from_user, reply):
                    return "success"

                # Fallback：如果主动发送失败，则尝试加密被动回复。
                passive_xml = self._make_plain_response_xml(
                    to_user=from_user,
                    from_user=to_user or self.corp_id,
                    content=reply,
                )
                return self._make_encrypted_response_xml(passive_xml, timestamp, nonce)

            except Exception as e:
                print(f"❌ 处理消息异常: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

    def _dispatch_message(self, root, msg_type, user_id):
        if msg_type == "text":
            content = root.findtext("Content", "")
            return self._process_text_message(user_id, content)

        if msg_type == "image":
            media_id = root.findtext("MediaId", "")
            return self._process_image_message(user_id, media_id)

        if msg_type == "voice":
            return "❌ 企业微信语音暂未接入转写。请先发送文字。"

        return f"❌ 暂不支持此类型消息：{msg_type or 'unknown'}"

    def _process_text_message(self, user_id, content):
        content = (content or "").strip()

        if not content:
            return "❌ 请输入有效内容"

        if content.startswith("/"):
            return self._handle_command(user_id, content)

        return self._handle_task(user_id, content)

    def _handle_command(self, user_id, command):
        raw_command = (command or "").strip()
        cmd = raw_command.lower()

        if cmd in ["/report", "/rep", "/r"]:
            return self._safe_call("获取任务", lambda: self.handler.format_report())

        if cmd == "/undo":
            return self._safe_call("撤回", lambda: self.handler.undo_last()[1])

        if cmd in ["/export", "/exp", "/e"]:
            return self._safe_call(
                "导出",
                lambda: f"📄 任务导出\n\n{self.handler.get_todo_text()}",
            )

        if cmd in ["/help", "/h", "/admhelp"]:
            return self._wechat_help_text()

        if cmd.startswith("/done"):
            selector = raw_command[len("/done"):].strip()
            if not selector:
                return "Usage: /done 2 或 /done 关键词"
            return self.handler.mark_done(selector)[1]

        if cmd.startswith("/edit"):
            payload = raw_command[len("/edit"):].strip()
            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                return "Usage: /edit 2 新任务内容"
            return self.handler.edit_task(parts[0], parts[1])[1]

        if cmd.startswith("/priority") or cmd.startswith("/pri"):
            if cmd.startswith("/priority"):
                payload = raw_command[len("/priority"):].strip()
            else:
                payload = raw_command[len("/pri"):].strip()

            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                return "Usage: /priority 2 P1 或 /pri 2 P1"
            return self.handler.update_priority(parts[0], parts[1])[1]

        if cmd.startswith("/deadline") or cmd.startswith("/due"):
            if cmd.startswith("/deadline"):
                payload = raw_command[len("/deadline"):].strip()
            else:
                payload = raw_command[len("/due"):].strip()

            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                return "Usage: /deadline 2 2026-05-30 或 /due 2 none"
            return self.handler.update_deadline(parts[0], parts[1])[1]

        if cmd.startswith("/memo"):
            payload = raw_command[len("/memo"):].strip()
            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                return "Usage: /memo 2 备注内容 或 /memo 2 none"
            return self.handler.update_memo(parts[0], parts[1])[1]

        if cmd in ["/prior", "/priority_report"]:
            return self._safe_call(
                "优先级分析",
                lambda: self.processor.analyze_todo(
                    self.handler.get_todo_text(),
                    mode="prior",
                ),
            )

        if cmd.startswith("/cbt"):
            return self._handle_cbt(raw_command)

        if cmd in ["/yesucan", "/motivate", "/motivation"]:
            return self._safe_call(
                "鼓励消息",
                lambda: self.processor.analyze_todo(
                    self.handler.get_todo_text(),
                    mode="yesucan",
                ),
            )

        if cmd == "/import":
            return "❌ 企业微信暂不支持 /import。请继续用 Discord 上传 todo.md。"

        return f"❌ 未知命令: {command}\n输入 /help 查看帮助"

    def _handle_cbt(self, raw_command):
        payload = raw_command[len("/cbt"):].strip()

        if not payload:
            return "Usage: /cbt 2 或 /cbt all"

        try:
            todo_text = self.handler.get_todo_text()

            if payload.lower() == "all":
                return self.processor.analyze_todo(todo_text, mode="cbt_all")

            task, error = self.handler._find_task(payload)
            if not task:
                return error

            target_task = (
                f"#{task['number']} "
                f"[{task['priority']}][{task['category']}] "
                f"{task['task']}\n"
                f"Deadline: {task['deadline'] or 'No deadline'}\n"
                f"Memo: {task['memo'] or 'No memo'}"
            )

            return self.processor.analyze_todo(
                todo_text,
                mode="cbt",
                target_task=target_task,
            )
        except Exception as e:
            return f"❌ CBT 分析失败: {str(e)}"

    def _handle_task(self, user_id, content):
        try:
            row = self.ingest.capture_task(
                text=content,
                source="wechat_work",
            )

            if not row:
                return "✅ 任务已处理。\n\n💡 使用 /report 查看所有任务。"

            return self._limit_message(
                f"✅ 任务已成功添加！\n\n{row}\n\n💡 使用 /report 查看所有任务。"
            )
        except Exception as e:
            print(f"❌ 处理任务异常: {e}")
            return f"❌ 处理任务时出错: {str(e)}"

    def _process_image_message(self, user_id, media_id):
        """企业微信图片入口：下载媒体后复用现有 image_data pipeline。"""
        try:
            media = self._download_media(media_id)

            if not media:
                return "❌ 图片下载失败"

            image_data = {
                "mime_type": media.get("mime_type") or "image/jpeg",
                "data": media["content"],
            }

            row = self.ingest.capture_task(
                text="请从这张图片里整理出一个任务。",
                image_data=image_data,
                source="wechat_work",
            )

            if not row:
                return "✅ 图片已处理。\n\n💡 使用 /report 查看所有任务。"

            return self._limit_message(
                f"✅ 图片任务已成功添加！\n\n{row}\n\n💡 使用 /report 查看所有任务。"
            )
        except Exception as e:
            print(f"❌ 处理图片异常: {e}")
            return f"❌ 处理图片异常: {str(e)}"

    def _download_media(self, media_id):
        try:
            access_token = self._get_access_token()
            url = "https://qyapi.weixin.qq.com/cgi-bin/media/get"
            params = {
                "access_token": access_token,
                "media_id": media_id,
            }

            response = requests.get(url, params=params, timeout=30)
            content_type = response.headers.get("Content-Type", "")

            if response.status_code != 200:
                print(f"❌ 下载媒体失败: {response.status_code} {response.text[:300]}")
                return None

            if "application/json" in content_type:
                try:
                    data = response.json()
                except Exception:
                    data = {"raw": response.text[:300]}
                print(f"❌ 下载媒体返回错误: {data}")
                return None

            return {
                "content": response.content,
                "mime_type": content_type.split(";")[0] or "application/octet-stream",
            }
        except Exception as e:
            print(f"❌ 下载媒体异常: {e}")
            return None

    def _safe_call(self, label, fn):
        try:
            return self._limit_message(fn())
        except Exception as e:
            return f"❌ {label}失败: {str(e)}"

    def _wechat_help_text(self):
        return """
🧠 NoBrainFog 企业微信机器人帮助

基础：
/report 或 /r：查看任务列表
/export 或 /e：导出 todo.md 文本
/undo：撤回最后一条任务
/help 或 /h：显示帮助

新增任务：
直接发送文字，我会整理成 Markdown todo。

管理：
/done 2：标记 #2 完成
/done 关键词：按关键词完成任务
/edit 2 新内容：修改任务描述
/pri 2 P1：修改优先级
/due 2 2026-05-30：修改截止日期
/due 2 none：清空截止日期
/memo 2 备注：修改备注
/memo 2 none：清空备注

分析：
/prior：生成优先级建议
/cbt 2：拆解单个任务
/cbt all：分析全部任务
/yesucan：生成鼓励/推进消息

暂不支持：
/import：请继续用 Discord 上传 todo.md
语音转写：暂未接入
""".strip()

    def _limit_message(self, content, suffix="\n\n...内容太长，已截断。"):
        content = content or ""

        if len(content) <= self.MESSAGE_LIMIT:
            return content

        keep = max(0, self.MESSAGE_LIMIT - len(suffix))
        return content[:keep].rstrip() + suffix

    def _send_active_reply(self, user_id, content):
        if not user_id:
            print("❌ 主动回复失败: missing user_id")
            return False

        return self.send_message(user_id, self._limit_message(content))

    def send_message(self, user_id, content):
        """主动发送企业微信应用消息。"""
        try:
            access_token = self._get_access_token()
            url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"

            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": int(self.agent_id),
                "text": {"content": content},
                "safe": 0,
            }

            response = requests.post(
                url,
                params={"access_token": access_token},
                json=data,
                timeout=10,
            )
            result = response.json()

            if result.get("errcode") == 0:
                print(f"✅ 消息发送成功: {user_id}")
                return True

            print(f"❌ 消息发送失败: {result}")
            return False
        except Exception as e:
            print(f"❌ 发送消息异常: {e}")
            return False

    def _safe_cdata(self, value):
        return str(value or "").replace("]]>", "]]]]><![CDATA[>")

    def _make_plain_response_xml(self, to_user, from_user, content):
        timestamp = str(int(time.time()))
        safe_to_user = self._safe_cdata(to_user)
        safe_from_user = self._safe_cdata(from_user)
        safe_content = self._safe_cdata(self._limit_message(content))

        return f"""
<xml>
<ToUserName><![CDATA[{safe_to_user}]]></ToUserName>
<FromUserName><![CDATA[{safe_from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{safe_content}]]></Content>
</xml>
""".strip()

    def run(self, host="0.0.0.0", port=8080, debug=False):
        print(f"🚀 企业微信机器人启动在 {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
