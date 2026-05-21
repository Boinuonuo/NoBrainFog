from .discord_bot import NoBrainFogBot
from .wechat_work import WeChatWorkBot

def create_adapter(adapter_type, config):
    if adapter_type == 'discord':
        return NoBrainFogBot(config)
    elif adapter_type == 'wechat_work':
        return WeChatWorkBot(config)
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")