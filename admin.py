from flask import Blueprint, request, render_template_string, jsonify
import os
from database import get_jobs, get_stats

admin_bp = Blueprint("admin", __name__)

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>JobPulse Admin</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#07070f;color:#e8e8f0;font-family:'DM Sans',sans-serif;padding:28px 20px;max-width:900px;margin:0 auto}
h1{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;margin-bottom:4px}
.sub{color:#7878a0;font-size:13px;margin-bottom:28px}
.sub a{color:#4fffb0;text-decoration:none}
.btn-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px}
.btn{display:inline-flex;align-items:center;gap:8px;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;padding:11px 22px;border-radius:9px;border:none;cursor:pointer;transition:opacity .2s}
.btn-green{background:#4fffb0;color:#07070f}
.btn-blue{background:#5bc4ff;color:#07070f}
.btn-red{background:#ff5f7e;color:#fff}
.btn:hover{opacity:.85}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin-bottom:28px}
.card{background:#0f0f1a;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:16px}
.card-val{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#4fffb0;margin-bottom:4px}
.card-label{font-size:11px;color:#7878a0;letter-spacing:.5px}
.section{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;margin-bottom:10px;margin-top:20px;color:#e8e8f0}
.source-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:13px}
.source-row:last-child{border:none}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;padding:9px 10px;color:#7878a0;border-bottom:1px solid rgba(255,255,255,.07);font-weight:500}
td{padding:9px 10px;border-bottom:1px solid rgba(255,255,255,.03);vertical-align:top}
td:first-child{font-family:'DM Mono',monospace;font-size:10px;color:#7878a0;white-space:nowrap}
.role{color:#fff;font-weight:500}
.co{color:#7878a0;font-size:11px}
.badge{font-size:10px;padding:2px 8px;border-radius:100px;font-family:'DM Mono',monospace;background:rgba(124,111,255,.15);color:#7c6fff}
.link a{color:#4fffb0;font-size:11px}
.config-box{background:#0f0f1a;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:16px;margin-bottom:20px}
.config-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:12px}
.config-row:last-child{border:none}
.config-key{font-family:'DM Mono',monospace;color:#7878a0}
.ok{color:#4fffb0;font-weight:600}
.missing{color:#ff5f7e;font-weight:600}
.log{background:#0f0f1a;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:14px;font-family:'DM Mono',monospace;font-size:11px;color:#4fffb0;min-height:60px;white-space:pre-wrap;margin-top:8px}
</style></head><body>

<h1>⚡ JobPulse Admin</h1>
<p class="sub"><a href="/">← Back to site</a></p>

<div class="btn-row">
  <button class="btn btn-green" onclick="trigger('general')">▶ Run General Pipeline</button>
  <button class="btn btn-blue" onclick="trigger('da')">▶ Run DA Pipeline</button>
  <button class="btn btn-red" onclick="checkConfig()">🔍 Check Config</button>
</div>

<div id="log" class="log" style="display:none"></div>

<div class="grid">
  <div class="card"><div class="card-val">{{ stats.total }}</div><div class="card-label">Total jobs in DB</div></div>
  <div class="card"><div class="card-val">{{ stats.today }}</div><div class="card-label">Posted today</div></div>
  <div class="card"><div class="card-val">{{ jobs|length }}</div><div class="card-label">Showing recent</div></div>
</div>

<div class="section">Channel Configuration</div>
<div class="config-box">
  <div class="config-row">
    <span class="config-key">TELEGRAM_TOKEN</span>
    <span class="{{ 'ok' if config.token else 'missing' }}">{{ '✓ Set' if config.token else '✗ MISSING' }}</span>
  </div>
  <div class="config-row">
    <span class="config-key">TELEGRAM_CHANNEL_ID (General)</span>
    <span class="{{ 'ok' if config.general_channel else 'missing' }}">{{ config.general_channel or '✗ MISSING' }}</span>
  </div>
  <div class="config-row">
    <span class="config-key">TELEGRAM_DA_CHANNEL_ID</span>
    <span class="{{ 'ok' if config.da_channel else 'missing' }}">{{ config.da_channel or '✗ NOT SET — DA pipeline disabled' }}</span>
  </div>
  <div class="config-row">
    <span class="config-key">TELEGRAM_DA_CHANNEL_USERNAME</span>
    <span class="{{ 'ok' if config.da_username else 'missing' }}">{{ config.da_username or '✗ NOT SET' }}</span>
  </div>
</div>

<div class="section">By Source</div>
{% for source, count in stats.by_source %}
<div class="source-row"><span>{{ source }}</span><span style="color:#4fffb0;font-family:'DM Mono',monospace">{{ count }}</span></div>
{% endfor %}

<div class="section">Recent 30 Jobs</div>
<table>
  <tr><th>Posted</th><th>Role</th><th>Source</th><th>Link</th></tr>
  {% for job in jobs %}
  <tr>
    <td>{{ job.posted_at[:16] if job.posted_at else '-' }}</td>
    <td><div class="role">{{ job.role[:45] }}</div><div class="co">{{ job.company }}</div></td>
    <td><span class="badge">{{ job.source }}</span></td>
    <td class="link">{% if job.apply_link %}<a href="{{ job.apply_link }}" target="_blank">Apply ↗</a>{% endif %}</td>
  </tr>
  {% endfor %}
</table>

<script>
const SECRET = '{{ secret }}';

async function trigger(jobType) {
  const log = document.getElementById('log');
  log.style.display = 'block';
  log.textContent = `Starting ${jobType} pipeline...`;
  try {
    const r = await fetch('/api/trigger', {
      method: 'POST',
      headers: {'X-Secret': SECRET, 'Content-Type': 'application/json'},
      body: JSON.stringify({job_type: jobType})
    });
    const d = await r.json();
    log.textContent = JSON.stringify(d, null, 2);
  } catch(e) {
    log.textContent = 'Error: ' + e.message;
  }
}

async function checkConfig() {
  const log = document.getElementById('log');
  log.style.display = 'block';
  log.textContent = 'Checking config...';
  try {
    const r = await fetch('/api/config-check', {headers: {'X-Secret': SECRET}});
    const d = await r.json();
    log.textContent = JSON.stringify(d, null, 2);
  } catch(e) {
    log.textContent = 'Error: ' + e.message;
  }
}
</script>
</body></html>"""


@admin_bp.route("/admin")
def admin():
    key = request.args.get("key","")
    if key != os.getenv("TRIGGER_SECRET","changemeplease"):
        return "Unauthorized", 401

    import requests as req
    token = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN","")

    config = {
        "token":           bool(token),
        "general_channel": os.getenv("TELEGRAM_CHANNEL_ID",""),
        "da_channel":      os.getenv("TELEGRAM_DA_CHANNEL_ID",""),
        "da_username":     os.getenv("TELEGRAM_DA_CHANNEL_USERNAME",""),
    }

    jobs  = get_jobs(limit=30)
    stats = get_stats()
    return render_template_string(ADMIN_HTML, jobs=jobs, stats=stats,
                                  config=config, secret=key)


@admin_bp.route("/api/config-check")
def config_check():
    if request.headers.get("X-Secret","") != os.getenv("TRIGGER_SECRET","changemeplease"):
        return jsonify({"error":"Unauthorized"}), 401

    import requests as req
    token = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN","")
    base  = f"https://api.telegram.org/bot{token}"

    result = {
        "token_set": bool(token),
        "general_channel": os.getenv("TELEGRAM_CHANNEL_ID","NOT SET"),
        "da_channel":      os.getenv("TELEGRAM_DA_CHANNEL_ID","NOT SET"),
        "da_username":     os.getenv("TELEGRAM_DA_CHANNEL_USERNAME","NOT SET"),
        "bot_info": None,
        "general_channel_ok": False,
        "da_channel_ok":      False,
        "da_channel_error":   None,
    }

    # Check bot token
    try:
        r = req.get(f"{base}/getMe", timeout=8).json()
        result["bot_info"] = r.get("result",{}).get("username","invalid token")
    except Exception as e:
        result["bot_info"] = f"error: {e}"

    # Check general channel
    general = os.getenv("TELEGRAM_CHANNEL_ID","")
    if general:
        try:
            r = req.post(f"{base}/sendChatAction",
                json={"chat_id": general, "action": "typing"}, timeout=8).json()
            result["general_channel_ok"] = r.get("ok", False)
        except Exception as e:
            result["general_channel_ok"] = False

    # Check DA channel
    da = os.getenv("TELEGRAM_DA_CHANNEL_ID","")
    if da:
        try:
            r = req.post(f"{base}/sendChatAction",
                json={"chat_id": da, "action": "typing"}, timeout=8).json()
            result["da_channel_ok"]    = r.get("ok", False)
            result["da_channel_error"] = None if r.get("ok") else r.get("description","unknown error")
        except Exception as e:
            result["da_channel_ok"]    = False
            result["da_channel_error"] = str(e)
    else:
        result["da_channel_error"] = "TELEGRAM_DA_CHANNEL_ID not set in Render"

    return jsonify(result)
