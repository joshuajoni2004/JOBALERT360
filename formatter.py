"""
formatter.py — NO AI NEEDED. Pure Python. Never fails.
Formats jobs perfectly using only the data scraped.
"""
import logging
logger = logging.getLogger(__name__)


def format_job(job: dict) -> dict | None:
    company  = (job.get("company") or "").strip() or "See listing"
    role     = (job.get("title")   or "").strip() or "Fresher Role"
    location = (job.get("location")or "").strip() or "India"
    link     = (job.get("link")    or "").strip()
    summary  = (job.get("summary") or "").strip()
    source   = (job.get("source")  or "").strip()

    # Detect batch year
    text  = (role + " " + summary).lower()
    batch = "2024 / 2025 / 2026"
    if "2026" in text: batch = "2024 / 2025 / 2026"
    elif "2025" in text: batch = "2024 / 2025"

    # Detect package
    package = "Not specified"
    for kw in ["lpa","lakh","₹","stipend","salary","ctc","per annum","per month"]:
        if kw in text:
            package = "As per company standards"
            break

    # Detect degree
    degree = "B.Tech / BE / BCA / BSc (CS/IT) or equivalent"
    for kw in ["mba","mca","m.tech","msc"]:
        if kw in text:
            degree = "Any Graduate / PG"
            break

    msg = (
        f"📢 <b>COMPANY:</b> {company}\n\n"
        f"💼 <b>ROLE:</b> {role}\n\n"
        f"🎓 <b>ELIGIBILITY:</b>\n"
        f"• Degree: {degree}\n"
        f"• Batch: {batch}\n"
        f"• Freshers eligible (0–2 years)\n\n"
        f"📍 <b>LOCATION:</b> {location}\n\n"
        f"💰 <b>PACKAGE:</b> {package}\n\n"
        f"📅 <b>LAST DATE:</b> Apply ASAP\n\n"
        f"🔗 <b>APPLY HERE:</b>\n{link}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ React fast — roles close quickly!\n"
        f"📤 Share with batchmates who need jobs 🚀\n"
        f"📢 Channel: @AsyncHireJobs"
    )

    return {
        "telegram_msg": msg,
        "company":  company,
        "role":     role,
        "location": location,
        "batch":    batch,
    }


def verify_job_is_real(job: dict) -> bool:
    """Filter using keywords only — no API needed."""
    title = (job.get("title") or "").lower()
    # Block obvious spam
    spam = ["invest","earn profit","mlm","network market",
            "make money","work from home earn","part time earn"]
    return not any(s in title for s in spam)
