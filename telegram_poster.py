import os, requests, logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Accept EITHER variable name — handles both TELEGRAM_TOKEN and TELEGRAM_BOT_TOKEN
TOKEN      = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
BASE       = f"https://api.telegram.org/bot{TOKEN}"


def send_message(text: str, chat_id: str = None) -> bool:
    chat = chat_id or CHANNEL_ID
    if not TOKEN or not chat:
        logger.error("TELEGRAM_TOKEN and TELEGRAM_CHANNEL_ID must be set")
        return False
    try:
        r = requests.post(f"{BASE}/sendMessage", json={
            "chat_id": chat, "text": text,
            "parse_mode": "HTML", "disable_web_page_preview": True,
        }, timeout=10)
        data = r.json()
        if not data.get("ok"):
            logger.error(f"Telegram API error: {data.get('description')}")
            return False
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_daily_header() -> bool:
    today = datetime.now().strftime("%d %b %Y")
    return send_message(
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗓 <b>FRESH JOBS — {today}</b>\n"
        f"✅ Verified • Direct Apply Links\n"
        f"👇 Scroll for today's openings\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def send_no_jobs_notice() -> bool:
    return send_message("🔍 No new fresher jobs this sweep. Checking again in 3 hours!")


def test_connection() -> bool:
    if not TOKEN:
        logger.error("No Telegram token found. Set TELEGRAM_TOKEN in Render environment.")
        return False
    try:
        r = requests.get(f"{BASE}/getMe", timeout=10)
        data = r.json()
        if data.get("ok"):
            logger.info(f"✅ Telegram connected: @{data['result']['username']}")
            return True
        logger.error(f"Bot token invalid: {data}")
        return False
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False
