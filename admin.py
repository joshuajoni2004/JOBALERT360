"""
Admin dashboard route — add this to app.py or run standalone.
Access at /admin?key=YOUR_TRIGGER_SECRET
Shows: pipeline history, source breakdown, last 20 posts, manual trigger button.
"""
from flask import Blueprint, request, render_template_string, jsonify, redirect
import os
from database import get_jobs, get_stats

admin_bp = Blueprint("admin", __name__)

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>JobPulse Admin</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet"/>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#07070f;color:#e8e8f0;font-family:'DM Sans',sans-serif;padding:32px 24px;max-width:900px;margin:0 auto}
  h1{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;margin-bottom:4px}
  .sub{color:#7878a0;font-size:13px;margin-bottom:32px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:32px}
  .card{background:#0f0f1a;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:18px}
  .card-val{font-family:'Syne',sans-serif;font-size:32px;font-weight:800;color:#4fffb0;margin-bottom:4px}
  .card-label{font-size:12px;color:#7878a0}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{text-align:left;padding:10px 12px;color:#7878a0;border-bottom:1px solid rgba(255,255,255,0.07);font-weight:500}
  td{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.04);vertical-align:top}
  td:first-child{font-family:'DM Mono',monospace;font-size:11px;color:#7878a0;white-space:nowrap}
  .role{color:#fff;font-weight:500}
  .company{color:#7878a0;font-size:12px}
  .badge{font-size:10px;padding:2px 8px;border-radius:100px;font-family:'DM Mono',monospace;background:rgba(124,111,255,0.15);color:#7c6fff}
  .btn{display:inline-block;background:#4fffb0;color:#07070f;font-family:'Syne',sans-serif;font-weight:700;font-size:13px;padding:10px 22px;border-radius:8px;border:none;cursor:pointer;text-decoration:none;margin-bottom:24px}
  .btn:hover{opacity:0.85}
  .section-title{font-family:'Syne',sans-serif;font-size:16px;font-weight:700;margin-bottom:12px;margin-top:24px}
  .source-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:13px}
  .source-row:last-child{border:none}
  a{color:#4fffb0;text-decoration:none}
  .link-cell a{color:#7878a0;font-size:11px}
  .link-cell a:hover{color:#4fffb0}
</style>
</head>
<body>

<h1>⚡ JobPulse Admin</h1>
<p class="sub">Bot control panel · <a href="/">← Back to site</a></p>

<a href="/api/trigger" onclick="triggerPipeline(event)" class="btn">▶ Run Pipeline Now</a>

<div class="grid">
  <div class="card">
    <div class="card-val">{{ stats.total }}</div>
    <div class="card-label">Total jobs in DB</div>
  </div>
  <div class="card">
    <div class="card-val">{{ stats.today }}</div>
    <div class="card-label">Posted today</div>
  </div>
  <div class="card">
    <div class="card-val">{{ jobs|length }}</div>
    <div class="card-label">Showing recent</div>
  </div>
</div>

<div class="section-title">By Source</div>
{% for source, count in stats.by_source %}
<div class="source-row">
  <span>{{ source }}</span>
  <span style="color:#4fffb0;font-family:'DM Mono',monospace">{{ count }}</span>
</div>
{% endfor %}

<div class="section-title">Recent 30 Jobs</div>
<table>
  <tr>
    <th>Posted</th>
    <th>Role</th>
    <th>Source</th>
    <th>Link</th>
  </tr>
  {% for job in jobs %}
  <tr>
    <td>{{ job.posted_at[:16] if job.posted_at else '-' }}</td>
    <td>
      <div class="role">{{ job.role[:40] }}</div>
      <div class="company">{{ job.company }}</div>
    </td>
    <td><span class="badge">{{ job.source }}</span></td>
    <td class="link-cell">
      {% if job.apply_link %}
      <a href="{{ job.apply_link }}" target="_blank">Apply ↗</a>
      {% endif %}
    </td>
  </tr>
  {% endfor %}
</table>

<script>
async function triggerPipeline(e) {
  e.preventDefault();
  const secret = prompt('Enter TRIGGER_SECRET:');
  if (!secret) return;
  const r = await fetch('/api/trigger', {
    method: 'POST',
    headers: {'X-Secret': secret}
  });
  const d = await r.json();
  alert(d.message || d.error);
}
</script>
</body>
</html>
"""


@admin_bp.route("/admin")
def admin():
    key = request.args.get("key", "")
    if key != os.getenv("TRIGGER_SECRET", "changemeplease"):
        return "Unauthorized", 401
    jobs = get_jobs(limit=30)
    stats = get_stats()
    return render_template_string(ADMIN_HTML, jobs=jobs, stats=stats)
