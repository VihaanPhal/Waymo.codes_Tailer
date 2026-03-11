import os
import time
import json
import logging
import requests
from datetime import datetime, timedelta
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
POLL_INTERVAL = 1  # seconds
CODE_HISTORY_FILE = "seen_codes.json"
CODE_EXPIRY_HOURS = 24  # Remember codes for 24 hours
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_BOT_TOKEN_2 = os.environ.get("TELEGRAM_BOT_TOKEN_2")
TELEGRAM_CHAT_ID_2 = os.environ.get("TELEGRAM_CHAT_ID_2")
TELEGRAM_BOT_TOKEN_3 = os.environ.get("TELEGRAM_BOT_TOKEN_3")
TELEGRAM_CHAT_ID_3 = os.environ.get("TELEGRAM_CHAT_ID_3")
TELEGRAM_BOT_TOKEN_4 = os.environ.get("TELEGRAM_BOT_TOKEN_4")
TELEGRAM_CHAT_ID_4 = os.environ.get("TELEGRAM_CHAT_ID_4")
TELEGRAM_BOT_TOKEN_5 = os.environ.get("TELEGRAM_BOT_TOKEN_5")
TELEGRAM_CHAT_ID_5 = os.environ.get("TELEGRAM_CHAT_ID_5")
TELEGRAM_BOT_TOKEN_6 = os.environ.get("TELEGRAM_BOT_TOKEN_6")
TELEGRAM_CHAT_ID_6 = os.environ.get("TELEGRAM_CHAT_ID_6")

# Track the last seen code (for display purposes)
last_seen_code = None

# Track all seen codes with timestamps to avoid duplicate notifications
seen_codes = {}

# Track bot start time for uptime calculation
start_time = None

# Track update offsets for each bot to avoid processing duplicate messages
update_offsets = {"primary": 0, "secondary": 0, "tertiary": 0, "quaternary": 0, "quinary": 0, "senary": 0}


def load_seen_codes():
    """Load seen codes from JSON file"""
    global seen_codes
    try:
        if os.path.exists(CODE_HISTORY_FILE):
            with open(CODE_HISTORY_FILE, 'r') as f:
                seen_codes = json.load(f)
            logger.info(f"Loaded {len(seen_codes)} codes from history")
    except Exception as e:
        logger.error(f"Error loading seen codes: {e}")
        seen_codes = {}


def save_seen_codes():
    """Save seen codes to JSON file"""
    try:
        with open(CODE_HISTORY_FILE, 'w') as f:
            json.dump(seen_codes, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving seen codes: {e}")


def cleanup_old_codes():
    """Remove codes older than CODE_EXPIRY_HOURS"""
    global seen_codes
    cutoff = datetime.now() - timedelta(hours=CODE_EXPIRY_HOURS)
    cutoff_str = cutoff.isoformat()

    old_count = len(seen_codes)
    seen_codes = {code: ts for code, ts in seen_codes.items() if ts > cutoff_str}
    removed = old_count - len(seen_codes)

    if removed > 0:
        logger.info(f"Cleaned up {removed} expired codes")
        save_seen_codes()


def is_code_seen(code):
    """Check if a code has been seen within the expiry window"""
    if code not in seen_codes:
        return False

    # Check if the code is still within the expiry window
    code_time = datetime.fromisoformat(seen_codes[code])
    expiry_time = code_time + timedelta(hours=CODE_EXPIRY_HOURS)
    return datetime.now() < expiry_time


def mark_code_seen(code):
    """Mark a code as seen with current timestamp"""
    seen_codes[code] = datetime.now().isoformat()
    save_seen_codes()
    logger.info(f"Code {code} added to history ({len(seen_codes)} codes tracked)")


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
    """Send a message via Telegram bot to all configured destinations"""
    # Build list of configured destinations
    destinations = []
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        destinations.append(("Primary", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID))
    if TELEGRAM_BOT_TOKEN_2 and TELEGRAM_CHAT_ID_2:
        destinations.append(("Secondary", TELEGRAM_BOT_TOKEN_2, TELEGRAM_CHAT_ID_2))
    if TELEGRAM_BOT_TOKEN_3 and TELEGRAM_CHAT_ID_3:
        destinations.append(("Tertiary", TELEGRAM_BOT_TOKEN_3, TELEGRAM_CHAT_ID_3))
    if TELEGRAM_BOT_TOKEN_4 and TELEGRAM_CHAT_ID_4:
        destinations.append(("Quaternary", TELEGRAM_BOT_TOKEN_4, TELEGRAM_CHAT_ID_4))
    if TELEGRAM_BOT_TOKEN_5 and TELEGRAM_CHAT_ID_5:
        destinations.append(("Quinary", TELEGRAM_BOT_TOKEN_5, TELEGRAM_CHAT_ID_5))
    if TELEGRAM_BOT_TOKEN_6 and TELEGRAM_CHAT_ID_6:
        destinations.append(("Senary", TELEGRAM_BOT_TOKEN_6, TELEGRAM_CHAT_ID_6))

    if not destinations:
        logger.error("No Telegram credentials configured")
        return False

    success_count = 0
    for name, bot_token, chat_id in destinations:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Telegram message sent successfully to {name}")
            success_count += 1
        except requests.RequestException as e:
            # Try to extract detailed error from Telegram API response
            error_detail = str(e)
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_json = e.response.json()
                    if 'description' in error_json:
                        error_detail = error_json['description']
            except:
                pass
            logger.error(f"Error sending Telegram message to {name}: {error_detail}")

    return success_count > 0


def get_telegram_updates(bot_name, bot_token, offset):
    """Fetch new updates (incoming messages) for a bot"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        params = {
            "offset": offset,
            "limit": 100,
            "timeout": 0,  # Non-blocking
            "allowed_updates": ["message"]
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("ok"):
            return data.get("result", [])
        return []
    except requests.RequestException as e:
        logger.error(f"Error fetching updates for {bot_name}: {e}")
        return []


def format_uptime(seconds):
    """Format uptime in a human-readable way"""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def handle_ping_command(bot_token, chat_id, message_id):
    """Send a pong response with bot status"""
    global start_time, last_seen_code

    uptime = format_uptime(time.time() - start_time) if start_time else "Unknown"
    code_display = last_seen_code if last_seen_code else "N/A"

    status_message = (
        f"<b>Pong!</b>\n\n"
        f"<b>Status:</b> Active\n"
        f"<b>Monitoring:</b> waymo.codes\n"
        f"<b>Last code seen:</b> <code>{code_display}</code>\n"
        f"<b>Uptime:</b> {uptime}\n"
        f"<b>Poll interval:</b> {POLL_INTERVAL}s"
    )

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": status_message,
            "parse_mode": "HTML",
            "reply_parameters": {"message_id": message_id}
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Ping response sent to chat {chat_id}")
    except requests.RequestException as e:
        logger.error(f"Error sending ping response: {e}")


def poll_for_commands():
    """Poll all configured bots for incoming commands"""
    global update_offsets

    # Build list of bots to poll
    bots = []
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        bots.append(("primary", TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID))
    if TELEGRAM_BOT_TOKEN_2 and TELEGRAM_CHAT_ID_2:
        bots.append(("secondary", TELEGRAM_BOT_TOKEN_2, TELEGRAM_CHAT_ID_2))
    if TELEGRAM_BOT_TOKEN_3 and TELEGRAM_CHAT_ID_3:
        bots.append(("tertiary", TELEGRAM_BOT_TOKEN_3, TELEGRAM_CHAT_ID_3))
    if TELEGRAM_BOT_TOKEN_4 and TELEGRAM_CHAT_ID_4:
        bots.append(("quaternary", TELEGRAM_BOT_TOKEN_4, TELEGRAM_CHAT_ID_4))
    if TELEGRAM_BOT_TOKEN_5 and TELEGRAM_CHAT_ID_5:
        bots.append(("quinary", TELEGRAM_BOT_TOKEN_5, TELEGRAM_CHAT_ID_5))
    if TELEGRAM_BOT_TOKEN_6 and TELEGRAM_CHAT_ID_6:
        bots.append(("senary", TELEGRAM_BOT_TOKEN_6, TELEGRAM_CHAT_ID_6))

    for bot_name, bot_token, authorized_chat_id in bots:
        updates = get_telegram_updates(bot_name, bot_token, update_offsets[bot_name])

        for update in updates:
            update_id = update.get("update_id", 0)
            # Update offset to acknowledge this message
            update_offsets[bot_name] = max(update_offsets[bot_name], update_id + 1)

            message = update.get("message", {})
            if not message:
                continue

            # Ignore messages from bots
            from_user = message.get("from", {})
            if from_user.get("is_bot", False):
                continue

            # Get message details
            text = message.get("text", "").strip().lower()
            chat_id = message.get("chat", {}).get("id")
            message_id = message.get("message_id")

            # Only respond to authorized chat
            if str(chat_id) != str(authorized_chat_id):
                logger.debug(f"Ignoring message from unauthorized chat: {chat_id}")
                continue

            # Handle ping command
            if text == "ping":
                logger.info(f"Received ping command from {bot_name}")
                handle_ping_command(bot_token, chat_id, message_id)


def check_for_new_code():
    """Check for a new code and send notification if found"""
    global last_seen_code

    result = fetch_current_code()

    if result is None:
        return

    current_code = result["code"]

    # Update last_seen_code for display purposes
    last_seen_code = current_code

    # Check if we've already seen this code recently
    if is_code_seen(current_code):
        logger.info(f"Duplicate code detected: {current_code} - message NOT sent (seen in last {CODE_EXPIRY_HOURS}h)")
        return

    # Truly new code - not seen in the last 24 hours
    logger.info(f"New code detected: {current_code} (not seen in last {CODE_EXPIRY_HOURS} hours)")

    message = (
        f"<b>New Waymo Code!</b>\n\n"
        f"<code>{current_code}</code>\n\n"
    )

    if send_telegram_message(message):
        mark_code_seen(current_code)
    # If message fails, we'll retry next poll


def main():
    """Main loop to monitor for new codes"""
    global start_time
    start_time = time.time()
    last_cleanup = time.time()

    logger.info("Starting Waymo Code Monitor")

    # Load previously seen codes from file
    load_seen_codes()

    # Validate configuration (primary destination is required)
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return

    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID environment variable not set")
        return

    # Log configured destinations
    dest_count = 1
    if TELEGRAM_BOT_TOKEN_2 and TELEGRAM_CHAT_ID_2:
        dest_count += 1
    if TELEGRAM_BOT_TOKEN_3 and TELEGRAM_CHAT_ID_3:
        dest_count += 1
    if TELEGRAM_BOT_TOKEN_4 and TELEGRAM_CHAT_ID_4:
        dest_count += 1
    if TELEGRAM_BOT_TOKEN_5 and TELEGRAM_CHAT_ID_5:
        dest_count += 1
    if TELEGRAM_BOT_TOKEN_6 and TELEGRAM_CHAT_ID_6:
        dest_count += 1
    logger.info(f"Configured {dest_count} Telegram destination(s)")

    logger.info(f"Polling every {POLL_INTERVAL} seconds")
    logger.info(f"Code history expiry: {CODE_EXPIRY_HOURS} hours")

    # Send startup notification
    send_telegram_message("Waymo Code Monitor started! Watching for new codes...")

    while True:
        try:
            check_for_new_code()
            poll_for_commands()

            # Cleanup old codes every hour
            if time.time() - last_cleanup > 3600:
                cleanup_old_codes()
                last_cleanup = time.time()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
