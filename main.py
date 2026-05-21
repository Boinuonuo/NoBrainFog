import os
import sys
from dotenv import load_dotenv
from adapters import create_adapter

def check_env():
    """
    Safety Guard: Audit environment variables before startup.
    """
    adapter_type = os.getenv("ADAPTER_TYPE", "discord").lower()
    
    required_vars = ["AI_DRIVER"]
    
    # 根据适配器类型检查必需变量
    if adapter_type == "discord":
        required_vars.extend(["DISCORD_TOKEN", "TARGET_USER_ID"])
    elif adapter_type == "wechat_work":
        required_vars.extend(["WECHAT_CORP_ID", "WECHAT_CORP_SECRET", "WECHAT_AGENT_ID"])
    else:
        print(f"❌ Invalid ADAPTER_TYPE: {adapter_type}. Use 'discord' or 'wechat_work'.")
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
        print(f"❌ Brain Fog Alert! Missing critical variables in .env: {', '.join(missing)}")
        print("Please complete the .env configuration before launching to save API credits.")
        return False
    return True

def main():
    load_dotenv()
    
    if not check_env():
        sys.exit(1)
    
    # Centralized configuration management
    adapter_type = os.getenv("ADAPTER_TYPE", "discord").lower()
    
    config = {
        "AI_DRIVER": os.getenv("AI_DRIVER"),
        "API_KEY": os.getenv("API_KEY"),
        "API_BASE": os.getenv("API_BASE"),
        "MODEL_NAME": os.getenv("MODEL_NAME"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL"),
        "TARGET_USER_ID": os.getenv("TARGET_USER_ID"),
        "MD_PATH": os.getenv("MD_PATH", "./todo.md"),
        "CATEGORIES": os.getenv("CATEGORIES", "Work,Life"),
        
        # 企业微信配置
        "WECHAT_CORP_ID": os.getenv("WECHAT_CORP_ID"),
        "WECHAT_CORP_SECRET": os.getenv("WECHAT_CORP_SECRET"),
        "WECHAT_AGENT_ID": os.getenv("WECHAT_AGENT_ID"),
        "WECHAT_TOKEN": os.getenv("WECHAT_TOKEN"),
        "WECHAT_ENCODING_AES_KEY": os.getenv("WECHAT_ENCODING_AES_KEY"),
        "AUTHORIZED_USERS": os.getenv("AUTHORIZED_USERS", "").split(',') if os.getenv("AUTHORIZED_USERS") else []
    }

    print("🚀 Initializing NoBrainFog Bot...")
    bot = create_adapter(adapter_type, config)
    
    if adapter_type == "discord":
        bot.run(os.getenv("DISCORD_TOKEN"))
    elif adapter_type == "wechat_work":
        bot.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    main()
