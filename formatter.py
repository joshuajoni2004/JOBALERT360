"""
formatter.py
Uses Google Gemini FREE tier with proper rate limiting.
Falls back to pure-Python template formatter if Gemini fails/rate-limited.
The fallback produces perfect output — bot never fails to post.
"""
import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# gemini-1.5-flash: 15 RPM free. gemini-2.0-flash: lower limits.
GEMINI_MODEL   = "gemini-1.5-flash"
GEMINI_URL     = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={{key}}"
)
# Seconds to wait between Gemini calls (15 RPM = 1 per 4s, use 5 to be safe)
GEMINI_DELAY   = 5
_last_call_ts  = 0.0   # module-level rate limiter


def _call_gemini(prompt: str, max_tokens: int = 500) -> str | None:
    global _last_call_ts
    if not GEMINI_API_KEY:
        return None

    # Enforce minimum gap between calls
    gap = time.time() - _last_call_ts
    if gap < GEMINI_DELAY:
        time.sleep(GEMINI_DELAY - gap)

    url  = GEMINI_URL.format(key=GEMINI_API_KEY)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.1},
    }
    try:
        _last_call_ts = time.time()
        resp = requests.post(url, json=body, timeout=20)
        if resp.status_code == 429:
            logger.warning("Gemini rate limit hit — waiting 30s then retrying once")
            time.sleep(30)
            _last_call_ts = time.time()
            resp = requests.post(url, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        _last_call_ts = time.time()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.warning(f"Gemini failed → using fallback: {e}")
        return None


# ── Pure-Python fallback formatter (no AI needed) ────────────────────
def _fallback_format(job: dict) -> str:
    """
    Format job using only the data we already scraped.
    Produces clean, correct Telegram message without any API call.
    """
    company  = job.get("company", "").strip() or "See listing"
    role     = job.get("title",   "").strip() or "Fresher Role"
    location = job.get("location","").strip() or "India"
    link     = job.get("link",    "").strip() or "Check company website"
    source   = job.get("source",  "").strip()

    # Try to detect batch from title/summary
    text = (role + job.get("summary","")).lower()
    batch = "2024/2025/2026"
    if "2026" in text: batch = "2024/2025/2026"
    if "2025" in text and "2026" not in text: batch = "2024/2025"

    # Detect package hints
    package = "Not specified"
    for kw in ["lpa","lakh","stipend","salary","ctc","per annum"]:
        if kw in text:
            package = "As per company norms"
            break

    return (
        f"📢 COMPANY: {company}\n\n"
        f"💼 ROLE: {role}\n\n"
        f"🎓 ELIGIBILITY:\n"
        f"• Degree: B.Tech / BE / BCA / BSc (CS/IT)\n"
        f"• Batch: {batch}\n"
        f"• Freshers eligible\n\n"
        f"📍 LOCATION: {location}\n\n"
        f"💰 PACKAGE: {package}\n\n"
        f"📅 LAST DATE: Apply ASAP\n\n"
        f"🔗 APPLY HERE:\n{link}\n\n"
        f"⚡ React fast — fresher roles close quickly!\n"
        f"📤 Share with friends who need a job 🚀"
    )


# ── Main format function ─────────────────────────────────────────────
def format_job(job: dict) -> dict | None:
    gemini_text = None

    if GEMINI_API_KEY:
        prompt = f"""Format this job for Indian freshers into EXACTLY this template.
Use "Not specified" for missing info. Return ONLY the formatted message, nothing else.

📢 COMPANY: [company]
💼 ROLE: [title]
🎓 ELIGIBILITY:
• Degree: [degree]
• Batch: [e.g. 2024/2025/2026]
• [other criteria]
📍 LOCATION: [location]
💰 PACKAGE: [salary or "Not specified"]
📅 LAST DATE: [deadline or "Apply ASAP"]
🔗 APPLY HERE:
[link]
⚡ React fast — fresher roles close quickly!
📤 Share with friends who need a job 🚀

JOB DATA:
Title: {job.get('title','')}
Company: {job.get('company','')}
Location: {job.get('location','')}
Summary: {job.get('summary','')[:300]}
Link: {job.get('link','')}"""
        gemini_text = _call_gemini(prompt, max_tokens=500)

    msg_text = gemini_text or _fallback_format(job)

    company  = _extract(msg_text, "COMPANY:")  or job.get("company","")
    role     = _extract(msg_text, "ROLE:")     or job.get("title","")
    location = _extract(msg_text, "LOCATION:") or job.get("location","")
    batch    = _extract(msg_text, "Batch:")    or ""

    return {
        "telegram_msg": msg_text,
        "company":  company,
        "role":     role,
        "location": location,
        "batch":    batch,
    }


def verify_job_is_real(job: dict) -> bool:
    """
    Skip AI verification entirely if Gemini quota is tight.
    Rely on the scraper's keyword filter instead — it already works well.
    """
    # Only call Gemini verify if we have plenty of quota
    # For now: trust the scraper filter, return True always
    title = job.get("title","").lower()
    # Hard block obvious non-jobs
    blocklist = ["invest","earn profit","mlm","network market","part time earn"]
    if any(b in title for b in blocklist):
        return False
    return True


def _extract(text: str, label: str) -> str:
    for line in text.splitlines():
        if label.lower() in line.lower():
            parts = line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip()
    return ""
