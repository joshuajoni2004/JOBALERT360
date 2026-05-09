"""
bot_handler.py
Handles all incoming Telegram commands from users:
  /start  — welcome message
  /latest — last 5 jobs posted
  /status — bot health check
  /help   — command list

Also sets up the webhook automatically on startup.
"""
import os
import requests
import logging
from database import get_jobs, get_stats

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE  = f"https://api.telegram.org/bot{TOKEN}"


# ── Send reply to a specific user/chat ──────────────────────────────
def reply(chat_id: int, text: str):
    requests.post(f"{BASE}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }, timeout=10)


# ── Command handlers ─────────────────────────────────────────────────
def handle_start(chat_id: int):
    stats = get_stats()
    msg = (
        "👋 <b>Welcome to Jobs Alert 360 Bot!</b>\n\n"
        "🚀 I auto-fetch verified fresher jobs every 3 hours\n"
        "✅ Direct apply links — no screenshots, no spam\n\n"
        f"📊 <b>Stats:</b>\n"
        f"• Total jobs posted: <b>{stats['total']}</b>\n"
        f"• Posted today: <b>{stats['today']}</b>\n\n"
        "📌 <b>Commands:</b>\n"
        "/latest — See last 5 jobs\n"
        "/status — Bot health check\n"
        "/help   — All commands\n\n"
        "👉 Join the channel: @AsyncHireJobs"
    )
    reply(chat_id, msg)


def handle_latest(chat_id: int):
    jobs = get_jobs(limit=5)
    if not jobs:
        reply(chat_id, "⏳ No jobs posted yet. Check back in a few hours!")
        return
    reply(chat_id, "🔥 <b>Latest 5 Jobs:</b>\n")
    for job in jobs:
        msg = (
            f"📢 <b>{job.get('company','?')}</b>\n"
            f"💼 {job.get('role','?')}\n"
            f"📍 {job.get('location','India')}\n"
            f"🔗 <a href='{job.get('apply_link','#')}'>Apply Here</a>\n"
            f"━━━━━━━━━━━━━━━"
        )
        reply(chat_id, msg)


def handle_status(chat_id: int):
    stats = get_stats()
    sources = ", ".join([f"{s[0]}({s[1]})" for s in stats['by_source']]) or "None yet"
    msg = (
        "✅ <b>Bot Status: ONLINE</b>\n\n"
        f"📦 Total jobs in DB: <b>{stats['total']}</b>\n"
        f"📅 Posted today: <b>{stats['today']}</b>\n"
        f"🗂 Sources: {sources}\n\n"
        "⏱ Pipeline runs every 3 hours automatically."
    )
    reply(chat_id, msg)


def handle_help(chat_id: int):
    msg = (
        "📖 <b>Jobs Alert 360 — Commands</b>\n\n"
        "/start  — Welcome + stats\n"
        "/latest — Last 5 jobs posted\n"
        "/status — Bot health check\n"
        "/help   — This message\n\n"
        "🤖 Bot auto-posts jobs every 3 hours.\n"
        "📢 Channel: @AsyncHireJobs"
    )
    reply(chat_id, msg)


# ── Main update dispatcher ───────────────────────────────────────────
def handle_update(update: dict):
    """Called from Flask webhook route with the Telegram update dict."""
    try:
        message = update.get("message") or update.get("channel_post")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip().lower()

        if text.startswith("/start"):
            handle_start(chat_id)
        elif text.startswith("/latest"):
            handle_latest(chat_id)
        elif text.startswith("/status"):
            handle_status(chat_id)
        elif text.startswith("/help"):
            handle_help(chat_id)

    except Exception as e:
        logger.error(f"handle_update error: {e}")


# ── Webhook setup ────────────────────────────────────────────────────
def set_webhook(app_url: str) -> bool:
    """
    Register this app's URL as Telegram webhook.
    Call once on startup. app_url = your Railway URL.
    """
    webhook_url = f"{app_url.rstrip('/')}/telegram-webhook"
    try:
        resp = requests.post(f"{BASE}/setWebhook", json={
            "url": webhook_url,
            "allowed_updates": ["message", "channel_post"],
            "drop_pending_updates": True,
        }, timeout=10)
        data = resp.json()
        if data.get("ok"):
            logger.info(f"Webhook set: {webhook_url}")
            return True
        else:
            logger.error(f"Webhook failed: {data}")
            return False
    except Exception as e:
        logger.error(f"set_webhook error: {e}")
        return False


def delete_webhook():
    try:
        requests.post(f"{BASE}/deleteWebhook", timeout=5)
    except Exception:
        pass
