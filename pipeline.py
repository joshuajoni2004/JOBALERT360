"""
pipeline.py — supports multiple channels via channel_id + job_type params
  job_type="general"  → fetch_all_jobs()   → post to TELEGRAM_CHANNEL_ID
  job_type="da"       → fetch_all_da_jobs() → post to TELEGRAM_DA_CHANNEL_ID
"""
import logging, time, os, threading
from scraper import fetch_all_jobs, fetch_all_da_jobs
from formatter import format_job, verify_job_is_real
from database import make_hash, job_exists, save_job
from telegram_poster import send_message, send_daily_header, send_no_jobs_notice

logger   = logging.getLogger(__name__)
MAX_JOBS = int(os.getenv("MAX_JOBS_PER_RUN", "10"))
DELAY    = int(os.getenv("DELAY_BETWEEN_POSTS", "30"))
_lock_general = threading.Lock()
_lock_da      = threading.Lock()


def run_pipeline(post_header: bool = False,
                 channel_id:  str  = None,
                 job_type:    str  = "general") -> dict:

    lock = _lock_da if job_type == "da" else _lock_general
    if not lock.acquire(blocking=False):
        logger.info(f"[{job_type}] Pipeline already running — skipping")
        return {"skipped": True}

    summary = {"fetched":0,"duplicate":0,"spam":0,"posted":0,"failed":0}
    try:
        logger.info(f"═══ Pipeline start [{job_type}] ═══")

        # Pick correct fetcher
        jobs = fetch_all_da_jobs() if job_type == "da" else fetch_all_jobs()
        summary["fetched"] = len(jobs)

        if not jobs:
            send_no_jobs_notice(channel_id)
            return summary

        if post_header:
            send_daily_header(channel_id)
            time.sleep(3)

        posted = 0
        for job in jobs:
            if posted >= MAX_JOBS:
                break

            if not verify_job_is_real(job):
                summary["spam"] += 1
                continue

            # Include job_type in hash so same job can appear in both channels
            jh = make_hash(job["title"], job.get("company",""), job["link"] + job_type)
            if job_exists(jh):
                summary["duplicate"] += 1
                continue

            result = format_job(job)
            if not result:
                summary["failed"] += 1
                continue

            ok = send_message(result["telegram_msg"], chat_id=channel_id)
            if not ok:
                summary["failed"] += 1
                continue

            save_job(jh, result["company"], result["role"], result["location"],
                     job.get("link",""), result["telegram_msg"],
                     job.get("source",""), result.get("batch",""))

            summary["posted"] += 1
            posted += 1
            time.sleep(DELAY)

        if summary["posted"] == 0 and summary["fetched"] > 0:
            logger.warning(f"[{job_type}] Fetched but none posted — check Telegram token")

    except Exception as e:
        logger.error(f"[{job_type}] Pipeline crashed: {e}", exc_info=True)
    finally:
        lock.release()

    logger.info(f"═══ Pipeline done [{job_type}]: {summary} ═══")
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    from database import init_db
    init_db()
    print(run_pipeline(post_header=True))
