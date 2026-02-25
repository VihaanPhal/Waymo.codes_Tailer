import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
WAYMO_URL = "https://waymo.codes/"
POLL_INTERVAL = 1  # 2 minutes in seconds
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Track the last seen code to avoid duplicate notifications
last_seen_code = None


def fetch_current_code():
    """Fetch the current code from waymo.codes"""
    try:
        headers = {
            "User-Agent": "WaymoCodeMonitor/1.0 (Personal Use)"
        }
        response = requests.get(WAYMO_URL, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        code_element = soup.select_one('.code-value')

        if code_element:
            code = code_element.text.strip()
            code_id = code_element.get('data-codeid', 'unknown')
            return {"code": code, "code_id": code_id}

        logger.warning("Could not find code element on page")
        return None

    except requests.RequestException as e:
        logger.error(f"Error fetching waymo.codes: {e}")
        return None


def send_telegram_message(message):
    """Send a message via Telegram bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not configured")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Telegram message sent successfully")
        return True

    except requests.RequestException as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False


def check_for_new_code():
    """Check for a new code and send notification if found"""
    global last_seen_code

    result = fetch_current_code()

    if result is None:
        return

    current_code = result["code"]

    if last_seen_code is None:
        # First run - just store the code, don't notify
        last_seen_code = current_code
        logger.info(f"Initial code detected: {current_code}")
        return

    if current_code != last_seen_code:
        # New code detected!
        logger.info(f"New code detected: {current_code} (was: {last_seen_code})")

        message = (
            f"<b>New Waymo Code!</b>\n\n"
            f"<code>{current_code}</code>\n\n"
        )

        if send_telegram_message(message):
            last_seen_code = current_code
        # If message fails, we'll retry next poll
    else:
        logger.debug(f"No change - current code: {current_code}")


def main():
    """Main loop to monitor for new codes"""
    logger.info("Starting Waymo Code Monitor")

    # Validate configuration
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return

    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID environment variable not set")
        return

    logger.info(f"Polling every {POLL_INTERVAL} seconds")

    # Send startup notification
    send_telegram_message("Waymo Code Monitor started! Watching for new codes...")

    while True:
        try:
            check_for_new_code()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
