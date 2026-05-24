# adapters/wechat_work.py
import base64
import hashlib
import json
import socket
import struct
import time
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import requests
from Crypto.Cipher import AES
from flask import Flask, request, jsonify

from core.ingest import IngestService


class WeChatWorkCryptoError(Exception):
    """Raised when WeChat Work callback crypto verification/decryption fails."""


class WeChatWorkBot:
    def __init__(self, config):
        self.app = Flask(__name__)
        self.config = config
        self.ingest = IngestService(config)
        
        # 企业微信配置
        self.corp_id = config.get("WECHAT_CORP_ID")
        self.corp_secret = config.get("WECHAT_CORP_SECRET")
        self.agent_id = config.get("WECHAT_AGENT_ID")
        self.token = config.get("WECHAT_TOKEN")
        self.encoding_aes_key = config.get("WECHAT_ENCODING_AES_KEY")
        self.aes_key = self._build_aes_key(self.encoding_aes_key)
        
        # 认证相关
        self.access_token = None
        self.token_expires = 0
        
        # 授权用户列表
        self.authorized_users = set(config.get("AUTHORIZED_USERS", []))
        
        self._setup_routes()

    def _build_aes_key(self, encoding_aes_key):
        """Build the 32-byte AES key required by WeChat Work callback encryption."""
        if not encoding_aes_key:
            return None

        try:
            return base64.b64decode(f"{encoding_aes_key}=")
        except Exception as e:
            raise WeChatWorkCryptoError(f"Invalid WECHAT_ENCODING_AES_KEY: {e}")

    def _get_access_token(self):
        """获取企业微信 access_token"""
        if time.time() > self.token_expires - 300:  # 提前5分钟刷新
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                'corpid': self.corp_id,
                'corpsecret': self.corp_secret
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if data['errcode'] == 0:
                    self.access_token = data['access_token']
                    self.token_expires = time.time() + data['expires_in']
                    print("✅ 成功获取 access_token")
                else:
                    print(f"❌ 获取 access_token 失败: {data}")
                    raise Exception(f"企业微信认证失败: {data.get('errmsg', '未知错误')}")
            except Exception as e:
                print(f"❌ 请求 access_token 异常: {e}")
                raise
        
        return self.access_token

    def _calculate_signature(self, timestamp, nonce, encrypted_payload):
        """Calculate WeChat Work callback SHA1 signature."""
        if not all([self.token, timestamp, nonce, encrypted_payload]):
            return None

        items = [self.token, timestamp, nonce, encrypted_payload]
        items.sort()
        return hashlib.sha1(''.join(items).encode('utf-8')).hexdigest()

    def _verify_signature(self, signature, timestamp, nonce, encrypted_payload):
        """Verify WeChat Work callback signature."""
        expected = self._calculate_signature(timestamp, nonce, encrypted_payload)
        return bool(expected and signature and expected == signature)

    def _decrypt_payload(self, encrypted_payload):
        """Decrypt WeChat Work encrypted payload and return plaintext XML/text."""
        if not self.aes_key or len(self.aes_key) != 32:
            raise WeChatWorkCryptoError("Invalid AES key length. Check WECHAT_ENCODING_AES_KEY.")

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

        xml_length = socket.ntohl(struct.unpack("I", content[16:20])[0])
        xml_start = 20
        xml_end = xml_start + xml_length
        plaintext = content[xml_start:xml_end].decode('utf-8')
        from_corp_id = content[xml_end:].decode('utf-8')

        if self.corp_id and from_corp_id != self.corp_id:
            raise WeChatWorkCryptoError("Corp ID mismatch in decrypted callback payload.")

        return plaintext

    def _encrypt_payload(self, plaintext_xml):
        """Encrypt response XML for WeChat Work passive replies."""
        if not self.aes_key or len(self.aes_key) != 32:
            raise WeChatWorkCryptoError("Invalid AES key length. Check WECHAT_ENCODING_AES_KEY.")

        random_bytes = b'NoBrainFogRndStr!'
        xml_bytes = plaintext_xml.encode('utf-8')
        corp_bytes = (self.corp_id or '').encode('utf-8')
        msg = random_bytes + struct.pack('!I', len(xml_bytes)) + xml_bytes + corp_bytes

        pad = 32 - (len(msg) % 32)
        if pad == 0:
            pad = 32
        msg += bytes([pad]) * pad

        cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_key[:16])
        encrypted = cipher.encrypt(msg)
        return base64.b64encode(encrypted).decode('utf-8')

    def _extract_encrypt_from_xml(self, xml_data):
        """Extract <Encrypt> value from a WeChat Work callback XML body."""
        try:
            root = ET.fromstring(xml_data)
        except Exception as e:
            raise WeChatWorkCryptoError(f"Invalid callback XML: {e}")

        encrypted_node = root.find('Encrypt')
        if encrypted_node is None or not encrypted_node.text:
            raise WeChatWorkCryptoError("Missing Encrypt field in callback XML.")

        return encrypted_node.text

    def _make_encrypted_response_xml(self, plaintext_xml, timestamp=None, nonce=None):
        """Build encrypted passive response XML required by WeChat Work."""
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
        """设置路由"""
        
        @self.app.route('/wechat', methods=['GET'])
        def verify_url():
            """验证企业微信服务器地址"""
            signature = request.args.get('msg_signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            echostr = request.args.get('echostr', '')
            
            try:
                if not self._verify_signature(signature, timestamp, nonce, echostr):
                    print("❌ 企业微信服务器验证失败: signature mismatch")
                    return 'Verification failed', 403

                plain_echostr = self._decrypt_payload(echostr)
                print("✅ 企业微信服务器验证成功")
                return plain_echostr
            except Exception as e:
                print(f"❌ 企业微信服务器验证异常: {e}")
                return 'Verification failed', 403
        
        @self.app.route('/wechat', methods=['POST'])
        def handle_message():
            """处理企业微信消息"""
            try:
                signature = request.args.get('msg_signature', '')
                timestamp = request.args.get('timestamp', '')
                nonce = request.args.get('nonce', '')
                
                data = request.data
                if not data:
                    return jsonify({'status': 'error', 'message': 'No data received'})

                encrypted_payload = self._extract_encrypt_from_xml(data)

                if not self._verify_signature(signature, timestamp, nonce, encrypted_payload):
                    print("❌ 企业微信消息签名验证失败")
                    return jsonify({'status': 'error', 'message': 'Invalid signature'}), 403

                decrypted_xml = self._decrypt_payload(encrypted_payload)
                root = ET.fromstring(decrypted_xml)
                
                msg_type = root.findtext('MsgType', '')
                user_id = root.findtext('FromUserName', '')
                
                # 检查用户权限
                if self.authorized_users and user_id not in self.authorized_users:
                    print(f"❌ 未授权用户: {user_id}")
                    plaintext_response = self._make_plain_response_xml(user_id, "❌ 您没有权限使用此机器人")
                    return self._make_encrypted_response_xml(plaintext_response, timestamp, nonce)
                
                # 处理不同类型的消息
                if msg_type == 'text':
                    content = root.findtext('Content', '')
                    response = self._process_text_message(user_id, content)
                elif msg_type == 'image':
                    media_id = root.findtext('MediaId', '')
                    response = self._process_image_message(user_id, media_id)
                elif msg_type == 'voice':
                    media_id = root.findtext('MediaId', '')
                    response = self._process_voice_message(user_id, media_id)
                else:
                    response = "❌ 暂不支持此类型消息"

                plaintext_response = self._make_plain_response_xml(user_id, response)
                return self._make_encrypted_response_xml(plaintext_response, timestamp, nonce)
                
            except Exception as e:
                print(f"❌ 处理消息异常: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    def _process_text_message(self, user_id, content):
        """处理文本消息"""
        content = content.strip()
        
        if not content:
            return "❌ 请输入有效内容"
        
        # 处理命令
        if content.startswith('/'):
            return self._handle_command(user_id, content)
        else:
            return self._handle_task(user_id, content)
    
    def _handle_command(self, user_id, command):
        """处理命令"""
        cmd = command.lower()
        
        if cmd in ['/report', '/rep', '/r']:
            try:
                return self.ingest.handler.format_report()
            except Exception as e:
                return f"❌ 获取任务失败: {str(e)}"
        
        elif cmd in ['/undo']:
            try:
                ok, reply = self.ingest.handler.undo_last()
                return reply
            except Exception as e:
                return f"❌ 撤回失败: {str(e)}"
        
        elif cmd in ['/export', '/exp', '/e']:
            try:
                content = self.ingest.handler.get_todo_text()
                if len(content) > 2000:
                    return content[:2000] + "\n\n...内容太长，已截断。"
                return f"📄 任务导出\n\n{content}"
            except Exception as e:
                return f"❌ 导出失败: {str(e)}"
        
        elif cmd in ['/help', '/h']:
            return """
🧠 **NoBrainFog 企业微信机器人帮助**

**基础命令**
`/report` 或 `/r` - 查看当前任务列表
`/export` 或 `/e` - 导出任务内容
`/help` 或 `/h` - 显示帮助信息

**添加任务**
直接发送文字、图片或语音给我，我会自动转换为任务格式

**支持格式**
- 文字描述："明天下午3点开会讨论项目进度"
- 图片：截图或照片内容会自动识别
- 语音：语音内容会转换为文字任务

**任务分类**
支持多个类别：工作、生活、购物、艺术、财务、管理等
"""
        
        else:
            return f"❌ 未知命令: {command}\n输入 `/help` 查看帮助"
    
    def _handle_task(self, user_id, content):
        """处理任务创建"""
        try:
            result = self.ingest.capture_task(
                text=content,
                source="wechat_work"
            )
            if result:
                return "✅ 任务已成功添加！\n\n💡 提示：使用 `/report` 查看所有任务"
            else:
                return "❌ 任务添加失败，请检查格式或重试"
        except Exception as e:
            print(f"❌ 处理任务异常: {e}")
            return f"❌ 处理任务时出错: {str(e)}"
    
    def _process_image_message(self, user_id, media_id):
        """处理图片消息"""
        try:
            image_data = self._download_media(media_id)
            if image_data:
                result = self.ingest.process_image_input(image_data)
                if result:
                    return "✅ 图片任务已成功添加！"
                else:
                    return "❌ 图片处理失败，请重试"
            else:
                return "❌ 图片下载失败"
        except Exception as e:
            return f"❌ 处理图片异常: {str(e)}"
    
    def _process_voice_message(self, user_id, media_id):
        """处理语音消息"""
        try:
            voice_data = self._download_media(media_id)
            if voice_data:
                result = self.ingest.process_voice_input(voice_data)
                if result:
                    return "✅ 语音任务已成功添加！"
                else:
                    return "❌ 语音识别失败，请重试"
            else:
                return "❌ 语音下载失败"
        except Exception as e:
            return f"❌ 处理语音异常: {str(e)}"
    
    def _download_media(self, media_id):
        """下载媒体文件"""
        try:
            access_token = self._get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token={access_token}&media_id={media_id}"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.content
            else:
                print(f"❌ 下载媒体失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 下载媒体异常: {e}")
            return None

    def _make_plain_response_xml(self, user_id, content):
        """构造未加密的企业微信被动响应 XML。"""
        timestamp = str(int(time.time()))
        safe_content = escape(content or "")
        safe_user_id = escape(user_id or "")
        safe_agent_id = escape(str(self.agent_id or ""))

        return f"""
<xml>
<ToUserName><![CDATA[{safe_user_id}]]></ToUserName>
<FromUserName><![CDATA[{safe_agent_id}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{safe_content}]]></Content>
</xml>
""".strip()
    
    def send_message(self, user_id, content):
        """主动发送消息"""
        try:
            access_token = self._get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {"content": content}
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result['errcode'] == 0:
                print(f"✅ 消息发送成功: {user_id}")
                return True
            else:
                print(f"❌ 消息发送失败: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 发送消息异常: {e}")
            return False
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """启动 Flask 服务"""
        print(f"🚀 企业微信机器人启动在 {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
