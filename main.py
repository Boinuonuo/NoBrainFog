import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from adapters import create_adapter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Start one NoBrainFog adapter with an explicit env file."
    )
    parser.add_argument(
        "--env-file",
        required=True,
        help="Path to the adapter-specific env file, for example /root/nobrainfog-config/discord.env",
    )
    return parser.parse_args()


def load_env_file(env_file):
    env_path = Path(env_file).expanduser().resolve()

    if not env_path.exists():
        print(f"❌ Env file not found: {env_path}")
        return False

    if not env_path.is_file():
        print(f"❌ Env path is not a file: {env_path}")
        return False

    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded env file: {env_path}")
    return True


def read_csv_env(name):
    raw_value = os.getenv(name, "")
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def check_env():
    """
    Safety Guard: Audit environment variables before startup.
    """
    adapter_type = os.getenv("ADAPTER_TYPE", "").strip().lower()

    required_vars = ["ADAPTER_TYPE", "AI_DRIVER", "MD_PATH"]

    # 根据适配器类型检查必需变量
    if adapter_type == "discord":
        required_vars.extend(["DISCORD_TOKEN", "TARGET_USER_ID"])
    elif adapter_type == "wechat_work":
        required_vars.extend([
            "WECHAT_CORP_ID",
            "WECHAT_CORP_SECRET",
            "WECHAT_AGENT_ID",
            "WECHAT_TOKEN",
            "WECHAT_ENCODING_AES_KEY",
        ])
    elif adapter_type == "email_imap":
        required_vars.extend([
            "EMAIL_IMAP_HOST",
            "EMAIL_USERNAME",
            "EMAIL_PASSWORD",
        ])
    else:
        print(
            f"❌ Invalid ADAPTER_TYPE: {adapter_type}. "
            "Use 'discord', 'wechat_work', or 'email_imap'."
        )
        return False

    # AI 驱动配置检查
    driver = (os.getenv("AI_DRIVER") or "").strip().lower()
    if driver == "gemini":
        required_vars.append("GEMINI_API_KEY")
    elif driver == "openai":
        required_vars.append("API_KEY")
    else:
        print(f"❌ Invalid AI_DRIVER: {driver}. Use 'gemini' or 'openai'.")
        return False

    missing = [v for v in required_vars if not os.getenv(v)]

    if missing:
        print(f"❌ Brain Fog Alert! Missing critical variables: {', '.join(missing)}")
        print("Please complete the selected adapter env file before launching.")
        return False
    return True


def build_config():
    return {
        "AI_DRIVER": os.getenv("AI_DRIVER"),
        "API_KEY": os.getenv("API_KEY"),
        "API_BASE": os.getenv("API_BASE"),
        "MODEL_NAME": os.getenv("MODEL_NAME"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL"),
        "TARGET_USER_ID": os.getenv("TARGET_USER_ID"),
        "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
        "MD_PATH": os.getenv("MD_PATH"),
        "CATEGORIES": os.getenv("CATEGORIES", "Work,Life"),

        # 企业微信配置
        "WECHAT_CORP_ID": os.getenv("WECHAT_CORP_ID"),
        "WECHAT_CORP_SECRET": os.getenv("WECHAT_CORP_SECRET"),
        "WECHAT_AGENT_ID": os.getenv("WECHAT_AGENT_ID"),
        "WECHAT_TOKEN": os.getenv("WECHAT_TOKEN"),
        "WECHAT_ENCODING_AES_KEY": os.getenv("WECHAT_ENCODING_AES_KEY"),
        "WECHAT_DEDUPE_DIR": os.getenv("WECHAT_DEDUPE_DIR"),
        "AUTHORIZED_USERS": read_csv_env("AUTHORIZED_USERS"),

        # Email IMAP 配置
        "EMAIL_IMAP_HOST": os.getenv("EMAIL_IMAP_HOST"),
        "EMAIL_IMAP_PORT": os.getenv("EMAIL_IMAP_PORT", "993"),
        "EMAIL_USERNAME": os.getenv("EMAIL_USERNAME"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "EMAIL_MAILBOX": os.getenv("EMAIL_MAILBOX", "INBOX"),
        "EMAIL_POLL_SECONDS": os.getenv("EMAIL_POLL_SECONDS", "60"),
        "EMAIL_PROCESSED_FOLDER": os.getenv("EMAIL_PROCESSED_FOLDER", ""),
        "EMAIL_MAX_MESSAGES_PER_POLL": os.getenv("EMAIL_MAX_MESSAGES_PER_POLL", "10"),
        "EMAIL_DEDUPE_DIR": os.getenv("EMAIL_DEDUPE_DIR"),
        "EMAIL_SMTP_ENABLED": os.getenv("EMAIL_SMTP_ENABLED", "true"),
        "EMAIL_SMTP_HOST": os.getenv("EMAIL_SMTP_HOST"),
        "EMAIL_SMTP_PORT": os.getenv("EMAIL_SMTP_PORT", "587"),
        "EMAIL_SMTP_USERNAME": os.getenv("EMAIL_SMTP_USERNAME"),
        "EMAIL_SMTP_PASSWORD": os.getenv("EMAIL_SMTP_PASSWORD"),
        "EMAIL_REPLY_FROM": os.getenv("EMAIL_REPLY_FROM"),
        "EMAIL_ALLOWED_SENDERS": os.getenv("EMAIL_ALLOWED_SENDERS", ""),
        "EMAIL_ALLOWED_DOMAINS": os.getenv("EMAIL_ALLOWED_DOMAINS", ""),
        "NOTIFY_DISCORD_ENABLED": os.getenv("NOTIFY_DISCORD_ENABLED", "false"),
    }


def main():
    args = parse_args()

    if not load_env_file(args.env_file):
        sys.exit(1)

    if not check_env():
        sys.exit(1)

    adapter_type = os.getenv("ADAPTER_TYPE", "").strip().lower()
    config = build_config()

    print(f"🚀 Initializing NoBrainFog Bot with adapter: {adapter_type}")
    bot = create_adapter(adapter_type, config)

    if adapter_type == "discord":
        bot.run(os.getenv("DISCORD_TOKEN"))
    elif adapter_type == "wechat_work":
        bot.run(host="0.0.0.0", port=8080)
    elif adapter_type == "email_imap":
        bot.run()


if __name__ == "__main__":
    main()
