import os
import threading
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from database import init_db, get_jobs, get_stats
from pipeline import run_pipeline
from telegram_poster import test_connection
from bot_handler import handle_update, set_webhook
from admin import admin_bp

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(admin_bp)


# ── Website routes ───────────────────────────────────────────────────
@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    source = request.args.get("source", "").strip()
    jobs   = get_jobs(search=search or None)
    if source:
        jobs = [j for j in jobs if j.get("source","").lower() == source.lower()]
    stats   = get_stats()
    sources = sorted({j["source"] for j in get_jobs(limit=500) if j.get("source")})
    telegram_channel = os.getenv("TELEGRAM_CHANNEL_USERNAME", "AsyncHireJobs")
    return render_template("index.html", jobs=jobs, stats=stats, search=search,
                           sources=sources, active_source=source,
                           telegram_channel=telegram_channel)


@app.route("/api/jobs")
def api_jobs():
    search = request.args.get("q", "").strip()
    limit  = min(int(request.args.get("limit", 50)), 200)
    jobs   = get_jobs(search=search or None, limit=limit)
    return jsonify({"success": True, "count": len(jobs), "jobs": jobs})


@app.route("/api/stats")
def api_stats():
    return jsonify({"success": True, "stats": get_stats()})


@app.route("/api/trigger", methods=["POST"])
def manual_trigger():
    if request.headers.get("X-Secret","") != os.getenv("TRIGGER_SECRET","changemeplease"):
        return jsonify({"error": "Unauthorized"}), 401
    threading.Thread(target=lambda: run_pipeline(post_header=False), daemon=True).start()
    return jsonify({"success": True, "message": "Pipeline running in background"})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


# ── TELEGRAM WEBHOOK (receives bot commands from users) ──────────────
@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    try:
        update = request.get_json(force=True)
        if update:
            handle_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return jsonify({"ok": True})


# ── Scheduler ────────────────────────────────────────────────────────
def start_scheduler():
    sched = BackgroundScheduler(timezone="Asia/Kolkata")
    sched.add_job(lambda: run_pipeline(post_header=False),
                  "interval", hours=3, id="sweep", replace_existing=True)
    sched.add_job(lambda: run_pipeline(post_header=True),
                  "cron", hour=9, minute=0, id="morning", replace_existing=True)
    sched.start()
    logger.info("Scheduler started — 3h sweeps + 9 AM morning run")
    return sched


# ── Startup ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting Jobs Alert 360...")
    init_db()

    if not test_connection():
        logger.warning("Telegram token invalid — check .env")

    # Set Telegram webhook so bot responds to /start /latest /status
    app_url = os.getenv("RAILWAY_STATIC_URL") or os.getenv("APP_URL", "")
    if app_url:
        threading.Thread(
            target=lambda: set_webhook(app_url), daemon=True
        ).start()
    else:
        logger.warning("APP_URL not set — webhook not registered. Bot won't respond to commands.")

    start_scheduler()

    # Initial pipeline run after 10s delay
    def first_run():
        import time; time.sleep(10)
        run_pipeline(post_header=True)
    threading.Thread(target=first_run, daemon=True).start()

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
