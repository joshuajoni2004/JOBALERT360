import sqlite3
import hashlib
import os

DB_PATH = os.getenv("DB_PATH", "jobs.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_hash TEXT UNIQUE NOT NULL,
            company TEXT,
            role TEXT,
            location TEXT,
            apply_link TEXT,
            formatted_message TEXT,
            source TEXT,
            batch TEXT,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def make_hash(title: str, company: str, link: str) -> str:
    raw = f"{title.strip().lower()}{company.strip().lower()}{link.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def job_exists(job_hash: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM jobs WHERE job_hash = ?", (job_hash,))
    result = c.fetchone()
    conn.close()
    return result is not None


def save_job(job_hash, company, role, location, apply_link, formatted_message, source, batch=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO jobs (job_hash, company, role, location, apply_link, formatted_message, source, batch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (job_hash, company, role, location, apply_link, formatted_message, source, batch))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_jobs(search=None, limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if search:
        q = f"%{search}%"
        c.execute('''
            SELECT * FROM jobs
            WHERE company LIKE ? OR role LIKE ? OR location LIKE ? OR source LIKE ?
            ORDER BY posted_at DESC LIMIT ?
        ''', (q, q, q, q, limit))
    else:
        c.execute("SELECT * FROM jobs ORDER BY posted_at DESC LIMIT ?", (limit,))
    jobs = [dict(row) for row in c.fetchall()]
    conn.close()
    return jobs


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM jobs WHERE DATE(posted_at) = DATE('now')")
    today = c.fetchone()[0]
    c.execute("SELECT source, COUNT(*) as cnt FROM jobs GROUP BY source ORDER BY cnt DESC")
    by_source = c.fetchall()
    conn.close()
    return {"total": total, "today": today, "by_source": by_source}
