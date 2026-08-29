import os
import asyncio
from dotenv import load_dotenv
import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Load environment variables
load_dotenv()

# Config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = "276728739"

# Userbot credentials (my.telegram.org)
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH')
TARGET_BOT_USERNAME = os.getenv('TARGET_BOT_USERNAME')

SESSION_STRING = os.getenv('TELEGRAM_SESSION')

# Init Telethon Userbot client
user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def send_telegram_message(message: str) -> None:
    """Sends a formatted message to your Telegram chat(s).

    CHAT_IDS environment variable may contain a comma-separated list of chat IDs.
    If CHAT_IDS is not set, falls back to the single CHAT_ID constant.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Prefer CHAT_IDS env (comma-separated) but fallback to legacy CHAT_ID constant
    chat_ids_env = os.getenv('CHAT_IDS')
    if chat_ids_env:
        chat_ids = [cid.strip() for cid in chat_ids_env.split(',') if cid.strip()]
    else:
        chat_ids = [CHAT_ID]

    for cid in chat_ids:
        payload = {
            "chat_id": cid,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Error sending Telegram notification to {cid}: {e}")


@user_client.on(events.NewMessage(from_users=TARGET_BOT_USERNAME, pattern=r'PORTUGAL'))
async def handle_target_bot_message(event):
    """Event handler for incoming messages from the target bot."""
    incoming_text = event.message.text
    print(f"[*] Intercepted new message from {TARGET_BOT_USERNAME}")

    full_message = f"{incoming_text}"
    
    # Run synchronous request function in a non-blocking thread executor
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, send_telegram_message, full_message)


async def main():
    print(f"Starting Telegram Monitor for target bot: @{TARGET_BOT_USERNAME}...")
    await user_client.start()
    print("[+] Userbot connected and listening for incoming messages.")
    await user_client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
