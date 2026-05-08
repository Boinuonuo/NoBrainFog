import os
import sys
from dotenv import load_dotenv
from adapters.discord_bot import NoBrainFogBot

def check_env():
    """
    Safety Guard: Audit environment variables before startup.
    """
    required_vars = ["DISCORD_TOKEN", "TARGET_USER_ID", "AI_DRIVER"]
    
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
    config = {
        "AI_DRIVER": os.getenv("AI_DRIVER"),
        "API_KEY": os.getenv("API_KEY"),
        "API_BASE": os.getenv("API_BASE"),
        "MODEL_NAME": os.getenv("MODEL_NAME"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL"),
        "TARGET_USER_ID": os.getenv("TARGET_USER_ID"),
        "MD_PATH": os.getenv("MD_PATH", "./todo.md"),
        "CATEGORIES": os.getenv("CATEGORIES", "Work,Life")
    }

    print("🚀 Initializing NoBrainFog Bot...")
    bot = NoBrainFogBot(config)
    bot.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    main()
