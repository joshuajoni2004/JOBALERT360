import os, threading, logging
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from database import init_db, get_jobs, get_stats
from pipeline import run_pipeline
from telegram_poster import test_connection
from bot_handler import handle_update, set_webhook
from admin import admin_bp

load_dotenv()
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(admin_bp)

SITE_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Jobs Alert 360 — Verified Fresher Jobs</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&family=DM+Mono:wght@400&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#07070f;color:#e8e8f0;font-family:'DM Sans',sans-serif;min-height:100vh}
a{color:inherit;text-decoration:none}
header{position:sticky;top:0;z-index:99;background:rgba(7,7,15,.9);backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,.07);padding:0 20px}
.nav{max-width:1100px;margin:0 auto;display:flex;align-items:center;height:60px;gap:16px}
.logo{font-family:'Syne',sans-serif;font-weight:800;font-size:18px;display:flex;align-items:center;gap:8px}
.dot{width:8px;height:8px;border-radius:50%;background:#4fffb0;animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.pills{display:flex;gap:8px;margin-left:auto}
.pill{font-family:'DM Mono',monospace;font-size:11px;background:#0f0f1a;border:1px solid rgba(255,255,255,.07);border-radius:100px;padding:4px 12px;color:#7878a0}
.pill span{color:#4fffb0}
.hero{max-width:1100px;margin:0 auto;padding:48px 20px 32px}
.tag{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:#4fffb0;background:rgba(79,255,176,.08);border:1px solid rgba(79,255,176,.2);border-radius:100px;padding:4px 12px;margin-bottom:18px}
h1{font-family:'Syne',sans-serif;font-size:clamp(28px,5vw,48px);font-weight:800;line-height:1.1;letter-spacing:-1px;margin-bottom:12px}
h1 em{font-style:normal;color:#4fffb0}
.sub{color:#7878a0;font-size:15px;margin-bottom:28px;max-width:480px}
.search-row{display:flex;gap:10px;max-width:540px}
.search-wrap{position:relative;flex:1}
.search-wrap svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#7878a0;width:16px;height:16px;pointer-events:none}
input[type=text]{width:100%;background:#0f0f1a;border:1px solid rgba(255,255,255,.09);border-radius:10px;color:#e8e8f0;font-family:'DM Sans',sans-serif;font-size:14px;padding:11px 14px 11px 38px;outline:none;transition:border-color .2s}
input[type=text]:focus{border-color:#4fffb0}
input::placeholder{color:#7878a0}
.btn{background:#4fffb0;color:#07070f;border:none;border-radius:10px;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;padding:11px 22px;cursor:pointer;transition:opacity .2s}
.btn:hover{opacity:.85}
.filters{max-width:1100px;margin:0 auto;padding:0 20px 24px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.flabel{font-size:12px;color:#7878a0;margin-right:4px}
.chip{font-size:12px;font-weight:500;padding:5px 14px;border-radius:100px;border:1px solid rgba(255,255,255,.07);background:#0f0f1a;color:#7878a0;transition:all .2s}
.chip:hover,.chip.active{border-color:#7c6fff;color:#7c6fff;background:rgba(124,111,255,.08)}
.chip.all.active{border-color:#4fffb0;color:#4fffb0;background:rgba(79,255,176,.08)}
main{max-width:1100px;margin:0 auto;padding:0 20px 60px}
.rinfo{font-size:13px;color:#7878a0;margin-bottom:18px}
.rinfo b{color:#e8e8f0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:#0f0f1a;border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:12px;transition:border-color .2s,transform .2s;position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#4fffb0,#7c6fff);opacity:0;transition:opacity .2s}
.card:hover{border-color:rgba(79,255,176,.2);transform:translateY(-2px)}
.card:hover::before{opacity:1}
.ctop{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.clogo{width:40px;height:40px;border-radius:9px;background:#16162a;border:1px solid rgba(255,255,255,.07);display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:15px;font-weight:800;color:#7c6fff;flex-shrink:0}
.cmeta{flex:1;min-width:0}
.crole{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#fff;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:3px}
.cco{font-size:12px;color:#7878a0}
.badge{font-family:'DM Mono',monospace;font-size:10px;padding:3px 9px;border-radius:100px}
.b-linkedin{background:rgba(10,102,194,.12);color:#68a8f5;border:1px solid rgba(10,102,194,.2)}
.b-default{background:rgba(124,111,255,.1);color:#7c6fff;border:1px solid rgba(124,111,255,.18)}
.tags{display:flex;flex-wrap:wrap;gap:6px}
.itag{display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#7878a0;background:#16162a;border-radius:6px;padding:3px 9px}
.cbot{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:auto;padding-top:4px;border-top:1px solid rgba(255,255,255,.05)}
.ctime{font-family:'DM Mono',monospace;font-size:10px;color:#7878a0}
.abtn{display:inline-flex;align-items:center;gap:5px;background:#4fffb0;color:#07070f;font-family:'Syne',sans-serif;font-size:12px;font-weight:700;padding:7px 16px;border-radius:7px;transition:opacity .2s}
.abtn:hover{opacity:.85}
.empty{grid-column:1/-1;text-align:center;padding:60px 20px}
.empty h3{font-family:'Syne',sans-serif;font-size:20px;margin-bottom:8px}
.empty p{color:#7878a0;font-size:13px}
.channels{max-width:1100px;margin:0 auto 40px;padding:0 20px;display:grid;grid-template-columns:1fr 1fr;gap:14px}
.chan-card{background:#0f0f1a;border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:20px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.chan-info h4{font-family:'Syne',sans-serif;font-size:15px;font-weight:700;margin-bottom:4px}
.chan-info p{font-size:12px;color:#7878a0}
.tgbtn{display:inline-flex;align-items:center;gap:6px;background:#2AABEE;color:#fff;font-family:'Syne',sans-serif;font-size:12px;font-weight:700;padding:9px 18px;border-radius:9px;transition:opacity .2s;white-space:nowrap}
.tgbtn:hover{opacity:.88}
footer{border-top:1px solid rgba(255,255,255,.06);text-align:center;padding:20px;font-size:12px;color:#7878a0}
footer a{color:#4fffb0}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.card{animation:fadeUp .35s ease both}
@media(max-width:580px){.pills{display:none}.search-row{flex-direction:column}.grid{grid-template-columns:1fr}.channels{grid-template-columns:1fr}}
</style></head><body>
<header><div class="nav">
  <div class="logo"><div class="dot"></div>Jobs Alert 360</div>
  <div class="pills">
    <div class="pill">Total <span>{{ stats.total }}</span></div>
    <div class="pill">Today <span>{{ stats.today }}</span></div>
  </div>
</div></header>

<section class="hero">
  <div class="tag"><div style="width:6px;height:6px;border-radius:50%;background:#4fffb0"></div>Live · Verified · Direct Apply Links</div>
  <h1>Fresh jobs for<br/><em>2024–2026 batch</em></h1>
  <p class="sub">No spam. No fake posts. Verified fresher openings from LinkedIn — auto-updated every 3 hours.</p>
  <form class="search-row" action="/" method="get">
    <div class="search-wrap">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      <input type="text" name="q" placeholder="Search role, company…" value="{{ search }}"/>
    </div>
    <button type="submit" class="btn">Search</button>
  </form>
</section>

<div class="channels">
  <div class="chan-card">
    <div class="chan-info">
      <h4>All Fresher Jobs</h4>
      <p>Software, IT, Web Dev, Cloud — all roles</p>
    </div>
    <a href="https://t.me/{{ general_channel }}" target="_blank" class="tgbtn">Join ↗</a>
  </div>
  <div class="chan-card" style="border-color:rgba(79,255,176,.15)">
    <div class="chan-info">
      <h4 style="color:#4fffb0">Data Analyst Jobs</h4>
      <p>DA · BA · SQL · Power BI · Tableau</p>
    </div>
    <a href="https://t.me/{{ da_channel }}" target="_blank" class="tgbtn">Join ↗</a>
  </div>
</div>

<div class="filters">
  <span class="flabel">Source:</span>
  <a href="/?q={{ search }}" class="chip all {% if not active_source %}active{% endif %}">All</a>
  {% for src in sources %}
  <a href="/?source={{ src }}&q={{ search }}" class="chip {% if active_source==src %}active{% endif %}">{{ src }}</a>
  {% endfor %}
</div>

<main>
  <p class="rinfo">
    {% if search %}Showing <b>{{ jobs|length }}</b> for "<b>{{ search }}</b>" — <a href="/" style="color:#4fffb0">clear</a>
    {% else %}<b>{{ jobs|length }}</b> fresh jobs right now{% endif %}
  </p>
  <div class="grid">
    {% if jobs %}{% for job in jobs %}
    <div class="card" style="animation-delay:{{ loop.index0 * 0.04 }}s">
      <div class="ctop">
        <div class="clogo">{{ (job.company or 'J')[0].upper() }}</div>
        <div class="cmeta">
          <div class="crole" title="{{ job.role }}">{{ job.role or 'Software Engineer' }}</div>
          <div class="cco">{{ job.company or 'Company' }}</div>
        </div>
        <span class="badge b-{{ (job.source or 'default')|lower|replace(' ','') }}">{{ job.source or '?' }}</span>
      </div>
      <div class="tags">
        {% if job.location %}<span class="itag">📍 {{ job.location[:28] }}</span>{% endif %}
        {% if job.batch %}<span class="itag">🎓 {{ job.batch }}</span>{% endif %}
      </div>
      <div class="cbot">
        <span class="ctime">{{ job.posted_at[:10] if job.posted_at else 'Recent' }}</span>
        {% if job.apply_link %}<a href="{{ job.apply_link }}" target="_blank" class="abtn">Apply ↗</a>{% endif %}
      </div>
    </div>
    {% endfor %}{% else %}
    <div class="empty"><div style="font-size:40px;margin-bottom:12px">🔍</div>
      <h3>No jobs found</h3><p>Try a different search or check back soon.</p></div>
    {% endif %}
  </div>
</main>

<footer>Built for freshers · Updated every 3 hours · <a href="/api/jobs">API</a> · <a href="/admin?key={{ trigger_secret }}">Admin</a></footer>
</body></html>"""


@app.route("/")
def index():
    search = request.args.get("q","").strip()
    source = request.args.get("source","").strip()
    jobs   = get_jobs(search=search or None)
    if source:
        jobs = [j for j in jobs if j.get("source","").lower()==source.lower()]
    stats   = get_stats()
    sources = sorted({j["source"] for j in get_jobs(limit=500) if j.get("source")})
    return render_template_string(SITE_HTML, jobs=jobs, stats=stats, search=search,
        sources=sources, active_source=source,
        general_channel=os.getenv("TELEGRAM_CHANNEL_USERNAME","AsyncHireJobs"),
        da_channel=os.getenv("TELEGRAM_DA_CHANNEL_USERNAME","DataAnalystJobs360"),
        trigger_secret=os.getenv("TRIGGER_SECRET","jobalert2026"))

@app.route("/api/jobs")
def api_jobs():
    jobs = get_jobs(search=request.args.get("q","").strip() or None,
                    limit=min(int(request.args.get("limit",50)),200))
    return jsonify({"success":True,"count":len(jobs),"jobs":jobs})

@app.route("/api/stats")
def api_stats():
    return jsonify({"success":True,"stats":get_stats()})

@app.route("/api/trigger", methods=["POST"])
def manual_trigger():
    if request.headers.get("X-Secret","") != os.getenv("TRIGGER_SECRET","changemeplease"):
        return jsonify({"error":"Unauthorized"}),401
    job_type   = request.json.get("job_type","general") if request.is_json else "general"
    channel_id = os.getenv("TELEGRAM_DA_CHANNEL_ID") if job_type=="da" else None
    threading.Thread(
        target=lambda: run_pipeline(post_header=False, channel_id=channel_id, job_type=job_type),
        daemon=True
    ).start()
    return jsonify({"success":True,"message":f"[{job_type}] pipeline running"})

@app.route("/health")
def health():
    return jsonify({"status":"ok","time":datetime.utcnow().isoformat()})

@app.route("/ping")
def ping():
    return "pong",200

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    try:
        update = request.get_json(force=True)
        if update: handle_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return jsonify({"ok":True})

def start_scheduler():
    sched      = BackgroundScheduler(timezone="Asia/Kolkata")
    da_channel = os.getenv("TELEGRAM_DA_CHANNEL_ID")

    # General channel — every 3 hours
    sched.add_job(lambda: run_pipeline(False, None, "general"),
                  "interval", hours=3, id="general_sweep", replace_existing=True)
    sched.add_job(lambda: run_pipeline(True, None, "general"),
                  "cron", hour=9, minute=0, id="general_morning", replace_existing=True)

    # DA channel — every 4 hours (if configured)
    if da_channel:
        sched.add_job(lambda: run_pipeline(False, da_channel, "da"),
                      "interval", hours=4, id="da_sweep", replace_existing=True)
        sched.add_job(lambda: run_pipeline(True, da_channel, "da"),
                      "cron", hour=9, minute=30, id="da_morning", replace_existing=True)
        logger.info("DA channel scheduler started")

    # Keep-alive ping
    app_url = os.getenv("APP_URL","")
    if app_url:
        import requests as req
        def self_ping():
            try: req.get(f"https://{app_url.replace('https://','')}/ping",timeout=5)
            except: pass
        sched.add_job(self_ping,"interval",minutes=10,id="keepalive")

    sched.start()
    logger.info("Scheduler started")
    return sched

if __name__ == "__main__":
    logger.info("Starting Jobs Alert 360...")
    init_db()
    if not test_connection():
        logger.warning("⚠ TELEGRAM_TOKEN invalid")

    app_url = os.getenv("APP_URL","").replace("https://","").rstrip("/")
    if app_url:
        threading.Thread(
            target=lambda: set_webhook(f"https://{app_url}"), daemon=True
        ).start()

    start_scheduler()

    def first_run():
        import time; time.sleep(15)
        run_pipeline(True, None, "general")
        da = os.getenv("TELEGRAM_DA_CHANNEL_ID")
        if da:
            time.sleep(30)
            run_pipeline(True, da, "da")
    threading.Thread(target=first_run, daemon=True).start()

    port = int(os.getenv("PORT",5000))
    app.run(host="0.0.0.0",port=port,debug=False,use_reloader=False)
