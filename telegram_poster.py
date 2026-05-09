import os
import requests
import logging
import time

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # e.g. @yourchannelname or -100xxxxxxxxxx
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


def send_message(text: str, channel_id: str = None) -> bool:
    """Send plain text message to Telegram channel."""
    chat = channel_id or CHANNEL_ID
    if not chat or not TOKEN:
        logger.error("TELEGRAM_TOKEN or TELEGRAM_CHANNEL_ID not set in .env")
        return False

    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if not data.get("ok"):
            logger.error(f"Telegram API error: {data.get('description')}")
            return False
        logger.info("Posted to Telegram successfully")
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_daily_header():
    """Post a daily header message before the job dump."""
    from datetime import datetime
    today = datetime.now().strftime("%d %b %Y")
    msg = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗓 <b>FRESH JOBS — {today}</b>\n"
        f"✅ Verified • Direct Apply Links\n"
        f"👇 Scroll down for today's openings\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    return send_message(msg)


def send_no_jobs_notice():
    """Post if nothing new was found in a run."""
    msg = "🔍 No new fresher jobs found in this sweep. Checking again in 3 hours!"
    return send_message(msg)


def send_error_alert(error_str: str):
    """Send error alert to channel (optional, useful for debugging)."""
    admin_id = os.getenv("TELEGRAM_ADMIN_ID")
    if admin_id:
        msg = f"⚠️ Bot error:\n<code>{error_str[:300]}</code>"
        send_message(msg, channel_id=admin_id)


def test_connection() -> bool:
    """Verify bot token is valid."""
    try:
        resp = requests.get(f"{BASE_URL}/getMe", timeout=10)
        data = resp.json()
        if data.get("ok"):
            bot_name = data["result"]["username"]
            logger.info(f"Bot connected: @{bot_name}")
            return True
        else:
            logger.error(f"Bot token invalid: {data}")
            return False
    except Exception as e:
        logger.error(f"Bot connection test failed: {e}")
        return False
