import os
import time
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = "276728739"
CHECK_INTERVAL_SECONDS = 5  # Poll every 5 minutes

API_URL = "https://my.sciencemuseum.org.uk/api/products/productionseasons"

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-GB,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://my.sciencemuseum.org.uk",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

PAYLOAD = {
    "productionSeasonIdFilter": [],
    "keywordIds": ["794"],
    "startDate": "2026-07-01T00:00",
    "endDate": "2026-10-01T23:59",
    "keywords": [],
}

# In-memory store for performance availability state: { performance_id: bool_is_available }
seen_states = {}


def send_telegram_message(message: str) -> None:
    """Sends a formatted message to your Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    payload2 = {
        "chat_id": "193811197",
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        res2 = requests.post(url, json=payload2, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")


def check_available_sessions() -> None:
    """Fetches sessions and alerts ONLY on new availability state transitions."""
    global seen_states

    try:
        response = requests.post(API_URL, headers=HEADERS, json=PAYLOAD, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch cinema data: {e}")
        return

    newly_available_alerts = []

    for production in data.get("productions", []):
        title = production.get("productionTitle", "Film Session")
        for perf in production.get("performances", []):
            perf_id = perf.get("id")
            if not perf_id:
                continue

            is_on_sale = perf.get("isOnSale", False)
            status_msg = perf.get("performanceStatusMessage", "")

            # Current availability flag
            is_currently_available = is_on_sale or (status_msg.lower() != "sold out")
            previously_available = seen_states.get(perf_id, False)

            # State transition check: Alert only if it wasn't available before, but is now
            if is_currently_available and not previously_available:
                display_date = perf.get("displayDate", "Unknown Date")
                display_time = perf.get("displayTime", "Unknown Time")
                booking_url = perf.get("actionUrl", "")

                newly_available_alerts.append(
                    f"🎬 *{title}*\n"
                    f"📅 *Date:* {display_date}\n"
                    f"⏰ *Time:* {display_time}\n"
                    f"🔗 [Book Now]({booking_url})"
                )

            # Update the stored state for this performance
            seen_states[perf_id] = is_currently_available

    # Send alerts if there are new openings
    if newly_available_alerts:
        alert_body = "\n\n---\n\n".join(newly_available_alerts)
        full_message = f"🎟️ **Tickets Available!!!**\n\n{alert_body}"
        print(f"Found {len(newly_available_alerts)} newly available session(s). Sending alert...")
        send_telegram_message(full_message)
    else:
        print("Checked: No new availability transitions found.")


if __name__ == "__main__":
    print("Starting Science Museum Ticket Monitor with state tracking...")
    while True:
        check_available_sessions()
        time.sleep(CHECK_INTERVAL_SECONDS)
