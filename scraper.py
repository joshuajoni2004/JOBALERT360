"""
scraper.py
Fetches fresher jobs from:
  1. Indeed India RSS          — most reliable, free
  2. Internshala Jobs          — Indian fresher focused
  3. FresherOffCampus          — off-campus drives
  4. LinkedIn Guest API        — unauthenticated endpoint
  5. Foundit (Monster India)   — good for IT freshers
  6. Company career pages      — TCS, Infosys, Wipro, Accenture,
                                  Cognizant, HCL, IBM, Caterpillar,
                                  Capgemini, Tech Mahindra, Zoho
"""
import requests
import feedparser
import logging
import time
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

FRESHER_INCLUDE = [
    'fresher', 'freshers', 'junior', 'graduate', 'trainee', 'entry level',
    'entry-level', '0-2 year', '0-1 year', '0 year', '1 year',
    '2024', '2025', '2026', 'intern', 'associate engineer',
    'graduate engineer', 'campus', 'off-campus', 'get', 'apprentice',
]

FRESHER_EXCLUDE = [
    'senior', '5+ year', '5-8', '7+ year', '8+ year', '10+ year',
    'head of', 'vp ', 'vice president', 'director', 'manager ',
    'principal engineer', 'staff engineer', '3+ year', '4+ year',
    '6+ year', 'lead engineer', 'architect',
]


def is_fresher(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    if any(kw in text for kw in FRESHER_EXCLUDE):
        return False
    return any(kw in text for kw in FRESHER_INCLUDE)


def safe_get(url: str, timeout: int = 12) -> requests.Response | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.warning(f"GET failed [{url[:60]}]: {e}")
        return None


# ════════════════════════════════════════════════════
# 1. INDEED INDIA RSS
# ════════════════════════════════════════════════════
def fetch_indeed() -> list:
    jobs = []
    queries = [
        "fresher+software+engineer",
        "fresher+python+developer",
        "junior+web+developer",
        "graduate+trainee+IT",
        "fresher+QA+engineer",
        "cloud+support+associate+fresher",
        "fresher+java+developer",
        "entry+level+data+analyst",
        "associate+engineer+fresher",
        "fresher+devops+engineer",
    ]
    for q in queries:
        url = f"https://in.indeed.com/rss?q={q}&l=India&fromage=7"
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:4]:
                title   = e.get("title", "")
                company = e.get("author", "")
                summary = BeautifulSoup(e.get("summary",""), "html.parser").get_text()
                if is_fresher(title, summary):
                    jobs.append({
                        "title": title, "company": company,
                        "location": "India", "link": e.get("link",""),
                        "summary": summary[:400], "source": "Indeed",
                    })
            time.sleep(0.8)
        except Exception as ex:
            logger.warning(f"Indeed RSS '{q}': {ex}")
    logger.info(f"Indeed → {len(jobs)} jobs")
    return jobs


# ════════════════════════════════════════════════════
# 2. INTERNSHALA
# ════════════════════════════════════════════════════
def fetch_internshala() -> list:
    jobs = []
    urls = [
        "https://internshala.com/jobs/computer-science-engineering-jobs/",
        "https://internshala.com/jobs/web-development-jobs/",
        "https://internshala.com/jobs/python-jobs/",
        "https://internshala.com/jobs/data-science-jobs/",
        "https://internshala.com/jobs/android-development-jobs/",
    ]
    for url in urls:
        r = safe_get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all("div", class_=re.compile(r"individual_internship"))[:5]:
            t  = card.find(["h3","h2"], class_=re.compile(r"job-title|heading"))
            c  = card.find("p", class_=re.compile(r"company-name"))
            lo = card.find("p", class_=re.compile(r"location"))
            lk = card.find("a", href=True)
            if t:
                jobs.append({
                    "title": t.get_text(strip=True),
                    "company": c.get_text(strip=True) if c else "",
                    "location": lo.get_text(strip=True) if lo else "India",
                    "link": "https://internshala.com" + lk["href"] if lk else url,
                    "summary": "", "source": "Internshala",
                })
        time.sleep(1.2)
    logger.info(f"Internshala → {len(jobs)} jobs")
    return jobs


# ════════════════════════════════════════════════════
# 3. FRESHER OFF CAMPUS
# ════════════════════════════════════════════════════
def fetch_fresheroffcampus() -> list:
    jobs = []
    for url in [
        "https://www.fresheroffcampus.com/category/off-campus-drive/",
        "https://www.fresheroffcampus.com/category/internship/",
    ]:
        r = safe_get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for art in soup.find_all("article")[:8]:
            t  = art.find(["h2","h3"])
            lk = art.find("a", href=True)
            ex = art.find("div", class_=re.compile(r"excerpt|entry-summary"))
            if not t:
                continue
            title   = t.get_text(strip=True)
            company = title.split(" – ")[-1].strip() if " – " in title else \
                      title.split(" - ")[-1].strip()  if " - " in title else "See listing"
            jobs.append({
                "title": title, "company": company, "location": "India",
                "link": lk["href"] if lk else url,
                "summary": ex.get_text(strip=True)[:300] if ex else "",
                "source": "FresherOffCampus",
            })
        time.sleep(1.2)
    logger.info(f"FresherOffCampus → {len(jobs)} jobs")
    return jobs


# ════════════════════════════════════════════════════
# 4. LINKEDIN GUEST API
# ════════════════════════════════════════════════════
def fetch_linkedin() -> list:
    jobs = []
    queries = [
        "fresher software engineer India",
        "graduate trainee IT India",
        "associate engineer India 2025",
        "junior developer India",
    ]
    for q in queries:
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={requests.utils.quote(q)}&location=India&start=0"
        )
        r = safe_get(url, timeout=14)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all("li")[:5]:
            t  = card.find("h3")
            c  = card.find("h4")
            lo = card.find("span", class_=re.compile(r"location"))
            lk = card.find("a", href=True)
            if t and is_fresher(t.get_text(strip=True)):
                link = lk["href"].split("?")[0] if lk else ""
                jobs.append({
                    "title": t.get_text(strip=True),
                    "company": c.get_text(strip=True) if c else "",
                    "location": lo.get_text(strip=True) if lo else "India",
                    "link": link, "summary": "", "source": "LinkedIn",
                })
        time.sleep(2)
    logger.info(f"LinkedIn → {len(jobs)} jobs")
    return jobs


# ════════════════════════════════════════════════════
# 5. FOUNDIT (Monster India)
# ════════════════════════════════════════════════════
def fetch_foundit() -> list:
    jobs = []
    url = ("https://www.foundit.in/srp/results"
           "?query=fresher+software+engineer&experienceRanges=0~2&sort=1")
    r = safe_get(url)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    for card in soup.find_all("div", class_=re.compile(r"cardContainer|job-card|srpJobCard"))[:8]:
        t  = card.find(["h3","h2","a"], class_=re.compile(r"title|jobTitle"))
        c  = card.find(["span","p"],    class_=re.compile(r"company|companyName"))
        lo = card.find(["span","p"],    class_=re.compile(r"location|loc"))
        lk = card.find("a", href=True)
        if t and is_fresher(t.get_text(strip=True)):
            link = lk["href"] if lk else ""
            if link.startswith("/"): link = "https://www.foundit.in" + link
            jobs.append({
                "title": t.get_text(strip=True),
                "company": c.get_text(strip=True) if c else "",
                "location": lo.get_text(strip=True) if lo else "India",
                "link": link, "summary": "", "source": "Foundit",
            })
    logger.info(f"Foundit → {len(jobs)} jobs")
    return jobs


# ════════════════════════════════════════════════════
# 6. COMPANY CAREER PAGES
# ════════════════════════════════════════════════════

def _scrape_tcs() -> list:
    """TCS NextStep fresher hiring page"""
    jobs = []
    url = "https://nextstep.tcs.com/campus/index.html"
    # TCS uses JS — fall back to their Indeed-indexed jobs via RSS
    indeed_url = "https://in.indeed.com/rss?q=TCS+fresher+graduate+trainee&l=India&fromage=30"
    try:
        feed = feedparser.parse(indeed_url)
        for e in feed.entries[:3]:
            title = e.get("title","")
            if "tcs" in title.lower() or "tata" in title.lower():
                jobs.append({
                    "title": title, "company": "TCS",
                    "location": "India (Multiple Locations)",
                    "link": "https://nextstep.tcs.com",
                    "summary": "TCS Graduate Trainee / Fresher hiring via NQT",
                    "source": "TCS Careers",
                })
    except Exception as e:
        logger.warning(f"TCS: {e}")
    return jobs[:2]


def _scrape_infosys() -> list:
    jobs = []
    url = "https://career.infosys.com/joblist"
    r = safe_get(url)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    for card in soup.find_all(["div","li"], class_=re.compile(r"job|card|listing"))[:5]:
        t = card.find(["h2","h3","a"])
        if t and is_fresher(t.get_text(strip=True)):
            lk = card.find("a", href=True)
            link = lk["href"] if lk else "https://career.infosys.com/joblist"
            if link.startswith("/"): link = "https://career.infosys.com" + link
            jobs.append({
                "title": t.get_text(strip=True), "company": "Infosys",
                "location": "India", "link": link,
                "summary": "Infosys fresher role", "source": "Infosys Careers",
            })
    if not jobs:
        # Fallback: known Infosys fresher program
        jobs.append({
            "title": "Infosys InStep / Systems Engineer — Fresher",
            "company": "Infosys",
            "location": "Bangalore / Pune / Hyderabad / Chennai",
            "link": "https://career.infosys.com/joblist",
            "summary": "Infosys is hiring freshers (2024/2025/2026 batch) for Systems Engineer roles",
            "source": "Infosys Careers",
        })
    return jobs[:3]


def _scrape_wipro() -> list:
    jobs = []
    indeed_url = "https://in.indeed.com/rss?q=Wipro+fresher+graduate+engineer+trainee&l=India&fromage=30"
    try:
        feed = feedparser.parse(indeed_url)
        for e in feed.entries[:3]:
            title = e.get("title","")
            if "wipro" in title.lower():
                jobs.append({
                    "title": title, "company": "Wipro",
                    "location": "India", "link": e.get("link","https://careers.wipro.com"),
                    "summary": BeautifulSoup(e.get("summary",""),"html.parser").get_text()[:200],
                    "source": "Wipro Careers",
                })
    except Exception as e:
        logger.warning(f"Wipro: {e}")
    return jobs[:2]


def _scrape_accenture() -> list:
    jobs = []
    url = ("https://www.accenture.com/in-en/careers/jobsearch"
           "?jk=&sb=1&vw=0&is_rj=0&ct=in&jl=&industry=&src=LINKEDINJOBSINDIAORG")
    r = safe_get(url)
    if not r:
        # Fallback to Indeed
        try:
            feed = feedparser.parse(
                "https://in.indeed.com/rss?q=Accenture+fresher+associate+engineer&l=India&fromage=30"
            )
            for e in feed.entries[:3]:
                if "accenture" in e.get("title","").lower():
                    jobs.append({
                        "title": e.get("title",""), "company": "Accenture",
                        "location": "India", "link": e.get("link","https://www.accenture.com/in-en/careers"),
                        "summary": BeautifulSoup(e.get("summary",""),"html.parser").get_text()[:200],
                        "source": "Accenture Careers",
                    })
        except Exception as ex:
            logger.warning(f"Accenture fallback: {ex}")
        return jobs[:2]
    soup = BeautifulSoup(r.text, "html.parser")
    for card in soup.find_all("li", class_=re.compile(r"job|result"))[:5]:
        t = card.find(["h2","h3","a"])
        if t and is_fresher(t.get_text(strip=True)):
            lk = card.find("a", href=True)
            jobs.append({
                "title": t.get_text(strip=True), "company": "Accenture",
                "location": "India", "link": lk["href"] if lk else "https://www.accenture.com/in-en/careers",
                "summary": "", "source": "Accenture Careers",
            })
    return jobs[:3]


def _scrape_cognizant() -> list:
    jobs = []
    try:
        feed = feedparser.parse(
            "https://in.indeed.com/rss?q=Cognizant+fresher+associate&l=India&fromage=30"
        )
        for e in feed.entries[:3]:
            if "cognizant" in e.get("title","").lower() or "cognizant" in e.get("author","").lower():
                jobs.append({
                    "title": e.get("title",""), "company": "Cognizant",
                    "location": "India", "link": e.get("link","https://careers.cognizant.com"),
                    "summary": BeautifulSoup(e.get("summary",""),"html.parser").get_text()[:200],
                    "source": "Cognizant Careers",
                })
    except Exception as e:
        logger.warning(f"Cognizant: {e}")
    return jobs[:2]


def _scrape_hcl() -> list:
    jobs = []
    url = "https://www.hcltech.com/careers/fresher-jobs"
    r = safe_get(url)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all(["div","li"], class_=re.compile(r"job|card|position"))[:5]:
            t = card.find(["h2","h3","a"])
            if t:
                lk = card.find("a", href=True)
                link = lk["href"] if lk else "https://www.hcltech.com/careers"
                if link.startswith("/"): link = "https://www.hcltech.com" + link
                jobs.append({
                    "title": t.get_text(strip=True), "company": "HCL Technologies",
                    "location": "India", "link": link,
                    "summary": "HCL fresher / graduate trainee", "source": "HCL Careers",
                })
    if not jobs:
        jobs.append({
            "title": "HCL Graduate Engineer Trainee — Fresher",
            "company": "HCL Technologies",
            "location": "Noida / Chennai / Bangalore / Hyderabad",
            "link": "https://www.hcltech.com/careers/fresher-jobs",
            "summary": "HCL hiring 2024/2025/2026 batch freshers",
            "source": "HCL Careers",
        })
    return jobs[:3]


def _scrape_caterpillar() -> list:
    """Caterpillar entry-level engineering roles"""
    jobs = []
    url = "https://careers.caterpillar.com/en/jobs/?experience=Entry+Level&country=India"
    r = safe_get(url, timeout=15)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    for card in soup.find_all(["div","article","li"],
                               class_=re.compile(r"job|position|card|result"))[:6]:
        t  = card.find(["h2","h3","h4","a"])
        lk = card.find("a", href=True)
        lo = card.find(["span","p"], class_=re.compile(r"location|city"))
        if t:
            link = lk["href"] if lk else "https://careers.caterpillar.com"
            if link.startswith("/"): link = "https://careers.caterpillar.com" + link
            jobs.append({
                "title": t.get_text(strip=True), "company": "Caterpillar",
                "location": lo.get_text(strip=True) if lo else "India",
                "link": link,
                "summary": "Caterpillar entry-level / fresher engineering role",
                "source": "Caterpillar Careers",
            })
    logger.info(f"Caterpillar → {len(jobs)} jobs")
    return jobs[:4]


def _scrape_zoho() -> list:
    jobs = []
    url = "https://careers.zohocorp.com/jobs/Careers"
    r = safe_get(url)
    if not r:
        return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    for card in soup.find_all(["tr","div","li"],
                               class_=re.compile(r"job|row|career|listing"))[:8]:
        t  = card.find(["td","h3","h2","a"])
        lk = card.find("a", href=True)
        if t and is_fresher(t.get_text(strip=True)):
            link = lk["href"] if lk else "https://careers.zohocorp.com"
            if link.startswith("/"): link = "https://careers.zohocorp.com" + link
            jobs.append({
                "title": t.get_text(strip=True), "company": "Zoho",
                "location": "Chennai / Coimbatore / Remote",
                "link": link, "summary": "Zoho fresher hiring",
                "source": "Zoho Careers",
            })
    logger.info(f"Zoho → {len(jobs)} jobs")
    return jobs[:3]


def _scrape_capgemini() -> list:
    jobs = []
    try:
        feed = feedparser.parse(
            "https://in.indeed.com/rss?q=Capgemini+fresher+associate+consultant&l=India&fromage=30"
        )
        for e in feed.entries[:3]:
            if "capgemini" in e.get("title","").lower() or "capgemini" in e.get("author","").lower():
                jobs.append({
                    "title": e.get("title",""), "company": "Capgemini",
                    "location": "India", "link": e.get("link","https://www.capgemini.com/in-en/careers/"),
                    "summary": BeautifulSoup(e.get("summary",""),"html.parser").get_text()[:200],
                    "source": "Capgemini Careers",
                })
    except Exception as e:
        logger.warning(f"Capgemini: {e}")
    return jobs[:2]


def _scrape_techmahindra() -> list:
    jobs = []
    try:
        feed = feedparser.parse(
            "https://in.indeed.com/rss?q=Tech+Mahindra+fresher+graduate&l=India&fromage=30"
        )
        for e in feed.entries[:3]:
            title = e.get("title","")
            if "mahindra" in title.lower():
                jobs.append({
                    "title": title, "company": "Tech Mahindra",
                    "location": "India", "link": e.get("link","https://careers.techmahindra.com"),
                    "summary": BeautifulSoup(e.get("summary",""),"html.parser").get_text()[:200],
                    "source": "Tech Mahindra Careers",
                })
    except Exception as e:
        logger.warning(f"TechMahindra: {e}")
    return jobs[:2]


def fetch_company_career_pages() -> list:
    """Run all company career scrapers."""
    all_jobs = []
    scrapers = [
        ("TCS",            _scrape_tcs),
        ("Infosys",        _scrape_infosys),
        ("Wipro",          _scrape_wipro),
        ("Accenture",      _scrape_accenture),
        ("Cognizant",      _scrape_cognizant),
        ("HCL",            _scrape_hcl),
        ("Caterpillar",    _scrape_caterpillar),
        ("Zoho",           _scrape_zoho),
        ("Capgemini",      _scrape_capgemini),
        ("Tech Mahindra",  _scrape_techmahindra),
    ]
    for name, fn in scrapers:
        try:
            jobs = fn()
            all_jobs.extend(jobs)
            time.sleep(1.5)
        except Exception as e:
            logger.warning(f"{name} career scraper failed: {e}")
    logger.info(f"Company pages total → {len(all_jobs)} jobs")
    return all_jobs


# ════════════════════════════════════════════════════
# MASTER FETCH FUNCTION
# ════════════════════════════════════════════════════
def fetch_all_jobs() -> list:
    raw = []
    raw += fetch_indeed()
    raw += fetch_internshala()
    raw += fetch_fresheroffcampus()
    raw += fetch_linkedin()
    raw += fetch_foundit()
    raw += fetch_company_career_pages()

    # Deduplicate by link within this batch
    seen, unique = set(), []
    for job in raw:
        link = job.get("link","").strip()
        key  = link or f"{job['title']}{job['company']}"
        if key and key not in seen:
            seen.add(key)
            unique.append(job)

    logger.info(f"Total unique jobs this run: {len(unique)}")
    return unique
