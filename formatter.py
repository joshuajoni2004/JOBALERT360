import os
import re
import time
import logging
import requests

logger = logging.getLogger(**name**)

# =========================================================

# CONFIG

# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

MODEL = "gemini-2.0-flash"

GEMINI_URL = (
f"https://generativelanguage.googleapis.com/v1beta/models/"
f"{MODEL}:generateContent"
)

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# =========================================================

# GEMINI API CALL

# =========================================================

def _call_gemini(prompt: str, max_tokens: int = 700) -> str | None:

```
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
                {
                    "text": prompt
                }
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.3,
        "topP": 0.95,
        "topK": 40,
        "maxOutputTokens": max_tokens
    }
}

params = {
    "key": GEMINI_API_KEY
}

for attempt in range(MAX_RETRIES):

    try:

        response = requests.post(
            GEMINI_URL,
            headers=headers,
            params=params,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:
            logger.error(
                f"Gemini API HTTP {response.status_code}: {response.text[:300]}"
            )
            time.sleep(2)
            continue

        data = response.json()

        candidates = data.get("candidates")

        if not candidates:
            logger.error(f"No candidates returned: {data}")
            return None

        text = (
            candidates[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )

        if not text:
            logger.error("Gemini returned empty text")
            return None

        return text

    except requests.exceptions.Timeout:
        logger.warning(f"Gemini timeout attempt {attempt+1}")

    except Exception as e:
        logger.error(f"Gemini error: {e}")

    time.sleep(2)

return None
```

# =========================================================

# CLEANUP

# =========================================================

def _clean_text(text: str) -> str:

````
text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
text = re.sub(r'`+', '', text)
text = re.sub(r'\*\*', '', text)
text = re.sub(r'__', '', text)
text = re.sub(r'#+', '', text)

text = re.sub(r'\n{3,}', '\n\n', text)

return text.strip()
````

# =========================================================

# FALLBACK FORMATTER

# =========================================================

def _fallback_format(job: dict) -> str:

```
company = job.get("company") or "Unknown Company"
role = job.get("title") or "Unknown Role"
location = job.get("location") or "India"
link = job.get("link") or "#"

return f"""
```

🚀 FRESHER JOB ALERT

🏢 COMPANY: {company}

💼 ROLE: {role}

📍 LOCATION: {location}

🎓 ELIGIBILITY:
• Freshers Eligible
• 2024 / 2025 / 2026 Batch

💰 PACKAGE:
Not specified

📅 LAST DATE:
Apply ASAP

🔗 APPLY HERE:
{link}

⚡ React fast — applications close quickly!

📢 Follow @AsyncHireJobs for daily fresher jobs
""".strip()

# =========================================================

# MAIN FORMATTER

# =========================================================

def format_job(job: dict) -> dict | None:

```
prompt = f"""
```

You are a professional Telegram job post formatter.

Your task:
Create a premium-quality fresher job Telegram post.

STRICT RULES:

* Output ONLY the final formatted Telegram message
* No markdown code blocks
* No explanations
* No JSON
* Keep under 1200 characters
* Use clean formatting
* Use emojis professionally
* Mention fresher eligibility
* Mention remote/hybrid if available
* Mention package only if available
* Avoid fake hype language

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

Summary: {job.get('summary', '')[:700]}

Source: {job.get('source', '')}

Apply Link: {job.get('link', '')}
"""

```
text = _call_gemini(prompt)

if not text:
    logger.warning("Gemini failed — using fallback formatter")
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
```

# =========================================================

# JOB FILTER

# =========================================================

def verify_job_is_real(job: dict) -> bool:

```
title = (job.get("title") or "").lower()
summary = (job.get("summary") or "").lower()

blocked_words = [
    "senior",
    "principal",
    "manager",
    "director",
    "lead engineer",
    "staff engineer",
    "8 years",
    "10 years",
    "7 years",
    "walk-in sales",
    "insurance advisor"
]

for word in blocked_words:
    if word in title or word in summary:
        return False

return True
```

# =========================================================

# FIELD EXTRACTOR

# =========================================================

def _extract_field(text: str, label: str) -> str:

```
for line in text.splitlines():

    if label.lower() in line.lower():

        parts = line.split(":", 1)

        if len(parts) == 2:
            return parts[1].strip()

return ""
```
