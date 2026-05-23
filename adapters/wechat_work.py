# adapters/wechat_work.py
import time
import json
import hashlib
import requests
from flask import Flask, request, jsonify
from core.ingest import IngestService

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
        
        # 认证相关
        self.access_token = None
        self.token_expires = 0
        
        # 授权用户列表
        self.authorized_users = set(config.get("AUTHORIZED_USERS", []))
        
        self._setup_routes()
    
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
    
    def _verify_signature(self, signature, timestamp, nonce):
        """验证消息签名"""
        if not all([signature, timestamp, nonce, self.token]):
            return False
        
        # 构造签名
        tmp_arr = [self.token, timestamp, nonce]
        tmp_arr.sort()
        tmp_str = ''.join(tmp_arr)
        tmp_str = hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()
        
        return tmp_str == signature
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/wechat', methods=['GET'])
        def verify_url():
            """验证服务器地址"""
            signature = request.args.get('msg_signature', '')
            timestamp = request.args.get('timestamp', '')
            nonce = request.args.get('nonce', '')
            echostr = request.args.get('echostr', '')
            
            if self._verify_signature(signature, timestamp, nonce):
                print("✅ 企业微信服务器验证成功")
                return echostr
            else:
                print("❌ 企业微信服务器验证失败")
                return 'Verification failed', 403
        
        @self.app.route('/wechat', methods=['POST'])
        def handle_message():
            """处理消息"""
            try:
                # 验证签名
                signature = request.args.get('msg_signature', '')
                timestamp = request.args.get('timestamp', '')
                nonce = request.args.get('nonce', '')
                
                if not self._verify_signature(signature, timestamp, nonce):
                    return jsonify({'status': 'error', 'message': 'Invalid signature'})
                
                # 解析消息
                data = request.data
                if not data:
                    return jsonify({'status': 'error', 'message': 'No data received'})
                
                # 这里简化处理，实际需要解密消息
                import xml.etree.ElementTree as ET
                root = ET.fromstring(data)
                
                msg_type = root.find('MsgType').text
                user_id = root.find('FromUserName').text
                create_time = root.find('CreateTime').text
                
                # 检查用户权限
                if self.authorized_users and user_id not in self.authorized_users:
                    print(f"❌ 未授权用户: {user_id}")
                    return self._make_response_xml(user_id, "❌ 您没有权限使用此机器人")
                
                # 处理不同类型的消息
                if msg_type == 'text':
                    content = root.find('Content').text
                    response = self._process_text_message(user_id, content)
                elif msg_type == 'image':
                    media_id = root.find('MediaId').text
                    response = self._process_image_message(user_id, media_id)
                elif msg_type == 'voice':
                    media_id = root.find('MediaId').text
                    response = self._process_voice_message(user_id, media_id)
                else:
                    response = "❌ 暂不支持此类型消息"
                
                return self._make_response_xml(user_id, response)
                
            except Exception as e:
                print(f"❌ 处理消息异常: {e}")
                return jsonify({'status': 'error', 'message': str(e)})
    
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
        
        elif cmd in ['/export', '/exp', '/e']:
            try:
                content = self.ingest.handler.export_content()
                if len(content) > 2000:
                    return "📄 任务内容过长，请通过文件获取"
                return f"📄 **任务导出**\n\n```markdown\n{content}\n```"
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
            result = self.ingest.process_input(content)
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
            # 下载图片
            image_data = self._download_media(media_id)
            if image_data:
                # 处理图片内容
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
            # 下载语音
            voice_data = self._download_media(media_id)
            if voice_data:
                # 处理语音内容
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
    
    def _make_response_xml(self, user_id, content):
        """构造响应消息 XML"""
        timestamp = str(int(time.time()))
        nonce = str(int(time.time() * 1000))
        
        # 简化版本，实际需要加密
        xml = f"""
<xml>
<ToUserName><![CDATA[{user_id}]]></ToUserName>
<FromUserName><![CDATA[{self.agent_id}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>
""".strip()
        
        return xml
    
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
