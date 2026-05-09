```python
"""
formatter.py — Advanced Gemini formatter for Jobs Alert 360
Stable version with:
- Gemini 2.0 Flash support
- Retry handling
- Fallback formatting
- Better parsing
- Safe response extraction
- Cleaner Telegram output
"""

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


# =========================================================
# GEMINI CALL
# =========================================================

def _call_gemini(prompt: str, max_tokens: int = 700, retries: int = 3) -> str | None:
    """
    Safe Gemini request with retries and fallback handling.
    """

    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY missing")
        return None

    headers = {
        "Content-Type": "application/json"
    }

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
                logger.error(f"No candidates in Gemini response: {data}")
                return None

            text = (
                data["candidates"][0]
                ["content"]["parts"][0]["text"]
                .strip()
            )

            return text

        except requests.exceptions.Timeout:
            logger.warning(f"Gemini timeout (attempt {attempt+1})")

        except requests.exceptions.HTTPError as e:
            logger.error(f"Gemini HTTP error: {e}")

        except Exception as e:
            logger.error(f"Gemini unknown error: {e}")

        time.sleep(2)

    return None


# =========================================================
# CLEANUP
# =========================================================

def _clean_text(text: str) -> str:
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# =========================================================
# FALLBACK FORMATTER
# =========================================================

def _fallback_format(job: dict) -> str:

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

⚡ Join @AsyncHireJobs for daily verified jobs
📤 Share with friends 🚀
""".strip()


# =========================================================
# MAIN FORMATTER
# =========================================================

def format_job(job: dict) -> dict | None:

    prompt = f"""
You are an expert Telegram job formatter for Indian freshers.

Create a HIGH-QUALITY Telegram post.

STRICT RULES:
- Output ONLY the formatted post
- No markdown code blocks
- No explanations
- Keep under 1200 characters
- Use emojis professionally
- Make it highly readable
- Mention fresher eligibility
- Mention if remote/hybrid if available

FORMAT STYLE:

🚀 FRESHER JOB ALERT

🏢 COMPANY: ...

💼 ROLE: ...

📍 LOCATION: ...

🎓 ELIGIBILITY:
• ...
• ...

💰 PACKAGE: ...

📅 LAST DATE: ...

🔗 APPLY HERE:
...

⚡ React fast — applications close quickly!

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
        logger.warning("Gemini failed → using fallback formatter")
        text = _fallback_format(job)

    text = _clean_text(text)

    company = _extract_field(text, "COMPANY:")
    role = _extract_field(text, "ROLE:")
    location = _extract_field(text, "LOCATION:")

    return {
        "telegram_msg": text,
        "company": company or job.get("company", ""),
        "role": role or job.get("title", ""),
        "location": location or job.get("location", ""),
        "batch": "2024/2025/2026",
    }


# =========================================================
# VERIFY JOB
# =========================================================

def verify_job_is_real(job: dict) -> bool:

    title = job.get("title", "").lower()
    summary = job.get("summary", "").lower()

    bad_keywords = [
        "senior",
        "5 years",
        "7 years",
        "director",
        "manager",
        "lead engineer",
        "principal engineer"
    ]

    for word in bad_keywords:
        if word in title or word in summary:
            return False

    return True


# =========================================================
# FIELD EXTRACTOR
# =========================================================

def _extract_field(text: str, label: str) -> str:

    for line in text.splitlines():

        if label.lower() in line.lower():

            parts = line.split(":", 1)

            if len(parts) == 2:
                return parts[1].strip()

    return ""
```
