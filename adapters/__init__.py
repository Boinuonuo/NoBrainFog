from .discord_bot import NoBrainFogBot
from .email_imap import EmailIMAPAdapter
from .wechat_work import WeChatWorkBot


def create_adapter(adapter_type, config):
    if adapter_type == "discord":
        return NoBrainFogBot(config)
    elif adapter_type == "wechat_work":
        return WeChatWorkBot(config)
    elif adapter_type == "email_imap":
        return EmailIMAPAdapter(config)
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")
