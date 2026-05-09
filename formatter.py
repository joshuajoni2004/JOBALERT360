"""
formatter.py — Uses Google Gemini (FREE) instead of Claude.
Free tier: 1,500 requests/day. Your bot uses ~96/day. Plenty.
Get key at: https://aistudio.google.com → Get API Key
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)


def _call_gemini(prompt: str, max_tokens: int = 600) -> str | None:
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set in .env")
        return None

    url = GEMINI_URL.format(key=GEMINI_API_KEY)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.2,
        },
    }
    try:
        resp = requests.post(url, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        return None


def format_job(job: dict) -> dict | None:
    prompt = f"""You are a job listing formatter for Indian freshers (2024-2026 batch).

Given raw job data, format it into EXACTLY this template. Use "Not specified" for missing fields.
Return ONLY the formatted message. No explanation, no extra text.

📢 COMPANY: [company name]

💼 ROLE: [job title]

🎓 ELIGIBILITY:
• Degree: [degree required]
• Batch: [batch year e.g. 2024/2025/2026]
• [any other key criteria on separate bullet]

📍 LOCATION: [location]

💰 PACKAGE: [salary/stipend or "Not specified"]

📅 LAST DATE: [deadline or "Apply ASAP"]

🔗 APPLY HERE:
[apply link]

⚡ React fast — fresher roles close quickly!
📤 Share with friends who need a job 🚀

---
RAW JOB DATA:
Title: {job.get('title', 'Not provided')}
Company: {job.get('company', 'Not provided')}
Location: {job.get('location', 'Not provided')}
Summary: {job.get('summary', 'Not provided')[:400]}
Source: {job.get('source', 'Not provided')}
Link: {job.get('link', 'Not provided')}"""

    text = _call_gemini(prompt, max_tokens=600)
    if not text:
        return None

    company  = _extract_field(text, "COMPANY:")
    role     = _extract_field(text, "ROLE:")
    location = _extract_field(text, "LOCATION:")
    batch    = _extract_field(text, "Batch:")

    return {
        "telegram_msg": text,
        "company":  company  or job.get("company", ""),
        "role":     role     or job.get("title", ""),
        "location": location or job.get("location", ""),
        "batch":    batch    or "",
    }


def verify_job_is_real(job: dict) -> bool:
    prompt = f"""Is this a real, legitimate job for freshers in India (not spam, not fake, not senior-only)?
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Summary: {job.get('summary', '')[:200]}
Link: {job.get('link', '')}

Reply with ONLY the word YES or NO."""

    answer = _call_gemini(prompt, max_tokens=5)
    if answer is None:
        return True
    return answer.strip().upper().startswith("Y")


def _extract_field(text: str, label: str) -> str:
    for line in text.splitlines():
        if label.lower() in line.lower():
            parts = line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip()
    return ""
