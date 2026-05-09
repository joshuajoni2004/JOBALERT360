import logging
import time
import os
from scraper import fetch_all_jobs
from formatter import format_job, verify_job_is_real
from database import make_hash, job_exists, save_job, init_db
from telegram_poster import send_message, send_daily_header, send_no_jobs_notice, send_error_alert

logger = logging.getLogger(__name__)

MAX_JOBS_PER_RUN = int(os.getenv("MAX_JOBS_PER_RUN", "12"))
DELAY_BETWEEN_POSTS = int(os.getenv("DELAY_BETWEEN_POSTS", "45"))  # seconds


def run_pipeline(post_header: bool = False) -> dict:
    """
    Full pipeline: Fetch → Verify → Deduplicate → Format → Post → Save.
    Returns summary dict.
    """
    logger.info("═══ Pipeline started ═══")
    summary = {"fetched": 0, "skipped_duplicate": 0, "skipped_fake": 0, "posted": 0, "failed": 0}

    try:
        # 1. Fetch from all sources
        raw_jobs = fetch_all_jobs()
        summary["fetched"] = len(raw_jobs)

        if not raw_jobs:
            logger.warning("No jobs fetched from any source.")
            send_no_jobs_notice()
            return summary

        # 2. Optional daily header
        if post_header:
            send_daily_header()
            time.sleep(3)

        posted_this_run = 0

        for job in raw_jobs:
            if posted_this_run >= MAX_JOBS_PER_RUN:
                logger.info(f"Reached max posts per run ({MAX_JOBS_PER_RUN}). Stopping.")
                break

            # 3. Deduplicate via DB hash
            job_hash = make_hash(job["title"], job["company"], job["link"])
            if job_exists(job_hash):
                summary["skipped_duplicate"] += 1
                continue

            # 4. Claude verification (skip obvious spam)
            if not verify_job_is_real(job):
                logger.info(f"Skipped (Claude flagged fake): {job['title']}")
                summary["skipped_fake"] += 1
                continue

            # 5. Claude formatting
            result = format_job(job)
            if not result:
                logger.warning(f"Formatter returned None for: {job['title']}")
                summary["failed"] += 1
                continue

            # 6. Post to Telegram
            success = send_message(result["telegram_msg"])
            if not success:
                summary["failed"] += 1
                continue

            # 7. Save to DB
            save_job(
                job_hash=job_hash,
                company=result["company"],
                role=result["role"],
                location=result["location"],
                apply_link=job.get("link", ""),
                formatted_message=result["telegram_msg"],
                source=job.get("source", "Unknown"),
                batch=result.get("batch", ""),
            )

            summary["posted"] += 1
            posted_this_run += 1

            # Delay to avoid Telegram rate limiting
            time.sleep(DELAY_BETWEEN_POSTS)

    except Exception as e:
        logger.error(f"Pipeline crashed: {e}", exc_info=True)
        send_error_alert(str(e))

    logger.info(f"═══ Pipeline done: {summary} ═══")
    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    init_db()
    result = run_pipeline(post_header=True)
    print(f"\nResult: {result}")
