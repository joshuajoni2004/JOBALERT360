import os
import re
import time
import logging
import requests

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-2.0-flash"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={GEMINI_API_KEY}"
)


def _call_gemini(prompt: str, max_tokens: int = 700, retries: int = 3):

    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY missing")
        return None

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": max_tokens,
            "topP": 0.9,
            "topK": 40
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    for attempt in range(retries):

        try:

            response = requests.post(
                GEMINI_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            if "candidates" not in data:
                logger.error(f"No Gemini candidates: {data}")
                return None

            return (
                data["candidates"][0]
                ["content"]["parts"][0]["text"]
                .strip()
            )

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")

        time.sleep(2)

    return None


def _clean_text(text: str):

    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _fallback_format(job: dict):

    title = job.get("title", "Unknown Role")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "India")
    link = job.get("link", "#")

    return f"""
🚀 FRESHER JOB ALERT

🏢 COMPANY: {company}

💼 ROLE: {title}

📍 LOCATION: {location}

🎓 ELIGIBILITY:
• Freshers Eligible
• 2024 / 2025 / 2026 Batch

💰 PACKAGE: Not specified

📅 LAST DATE:
Apply ASAP

🔗 APPLY HERE:
{link}

⚡ React fast — applications close quickly!
📤 Share with friends 🚀
""".strip()


def format_job(job: dict):

    prompt = f"""
You are an expert Telegram job formatter for Indian freshers.

Create a HIGH-QUALITY Telegram post.

STRICT RULES:
- Output ONLY the formatted post
- No markdown code blocks
- No explanations
- Keep under 1200 characters

RAW JOB DATA:

Title: {job.get('title', '')}
Company: {job.get('company', '')}
Location: {job.get('location', '')}
Summary: {job.get('summary', '')[:800]}
Source: {job.get('source', '')}
Link: {job.get('link', '')}
"""

    text = _call_gemini(prompt)

    if not text:
        logger.warning("Gemini failed → using fallback")
        text = _fallback_format(job)

    text = _clean_text(text)

    return {
        "telegram_msg": text,
        "company": job.get("company", ""),
        "role": job.get("title", ""),
        "location": job.get("location", ""),
        "batch": "2024/2025/2026"
    }


def verify_job_is_real(job: dict):

    title = job.get("title", "").lower()
    summary = job.get("summary", "").lower()

    bad_keywords = [
        "senior",
        "manager",
        "director",
        "lead engineer",
        "5 years",
        "7 years"
    ]

    for word in bad_keywords:
        if word in title or word in summary:
            return False

    return True
