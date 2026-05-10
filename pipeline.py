"""
pipeline.py — with concurrency lock to prevent double-runs
"""
import logging, time, os, threading
from scraper import fetch_all_jobs
from formatter import format_job, verify_job_is_real
from database import make_hash, job_exists, save_job
from telegram_poster import send_message, send_daily_header, send_no_jobs_notice

logger = logging.getLogger(__name__)

MAX_JOBS  = int(os.getenv("MAX_JOBS_PER_RUN", "10"))
DELAY     = int(os.getenv("DELAY_BETWEEN_POSTS", "30"))
_lock     = threading.Lock()   # prevents two pipeline runs at the same time


def run_pipeline(post_header: bool = False) -> dict:
    if not _lock.acquire(blocking=False):
        logger.info("Pipeline already running — skipping this trigger")
        return {"skipped": True}

    summary = {"fetched":0,"duplicate":0,"spam":0,"posted":0,"failed":0}
    try:
        logger.info("═══ Pipeline start ═══")

        jobs = fetch_all_jobs()
        summary["fetched"] = len(jobs)

        if not jobs:
            logger.warning("0 jobs fetched from all sources")
            send_no_jobs_notice()
            return summary

        if post_header:
            send_daily_header()
            time.sleep(3)

        posted = 0
        for job in jobs:
            if posted >= MAX_JOBS:
                break

            # Spam check
            if not verify_job_is_real(job):
                summary["spam"] += 1
                continue

            # Duplicate check
            jh = make_hash(job["title"], job.get("company",""), job["link"])
            if job_exists(jh):
                summary["duplicate"] += 1
                continue

            # Format (pure Python — never fails)
            result = format_job(job)
            if not result:
                summary["failed"] += 1
                continue

            # Post to Telegram
            ok = send_message(result["telegram_msg"])
            if not ok:
                summary["failed"] += 1
                continue

            # Save to DB
            save_job(jh, result["company"], result["role"], result["location"],
                     job.get("link",""), result["telegram_msg"],
                     job.get("source",""), result.get("batch",""))

            summary["posted"] += 1
            posted += 1
            time.sleep(DELAY)

        if summary["posted"] == 0 and summary["fetched"] > 0:
            logger.warning("Jobs were fetched but none posted — check Telegram token and channel ID")

    except Exception as e:
        logger.error(f"Pipeline crashed: {e}", exc_info=True)
    finally:
        _lock.release()

    logger.info(f"═══ Pipeline done: {summary} ═══")
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    from database import init_db
    init_db()
    print(run_pipeline(post_header=True))
