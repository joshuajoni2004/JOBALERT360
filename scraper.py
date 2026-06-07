"""
scraper.py — focuses on sources that actually work from server IPs
Primary: LinkedIn guest API (confirmed working — returned 7 jobs)
Secondary: Indeed RSS, Internshala, company pages via Indeed
"""
import requests, feedparser, logging, time, re
from bs4 import BeautifulSoup

logger  = logging.getLogger(__name__)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

INCLUDE = ['fresher','freshers','junior','graduate','trainee','entry level',
           'entry-level','0-2','0-1','2024','2025','2026','intern',
           'associate engineer','graduate engineer','campus','apprentice']
EXCLUDE = ['senior','5+ year','7+ year','8+ year','10+ year','head of',
           'vp ','director','manager','principal','staff engineer',
           '3+ year','4+ year','6+ year','lead engineer']

def is_fresher(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    if any(k in text for k in EXCLUDE): return False
    return any(k in text for k in INCLUDE)

def safe_get(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.warning(f"GET [{url[:55]}]: {e}")
        return None


# ══ 1. LINKEDIN GUEST API — confirmed working ═══════════════════════
def fetch_linkedin():
    jobs, queries = [], [
        "fresher software engineer India",
        "graduate trainee IT India",
        "associate engineer fresher India",
        "junior python developer India",
        "fresher web developer India",
        "entry level QA engineer India",
        "fresher java developer India",
        "associate software engineer 2025 India",
        "campus fresher engineer India",
        "fresher data analyst India",
    ]
    for q in queries:
        url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
               f"?keywords={requests.utils.quote(q)}&location=India&start=0&f_E=1,2")
        r = safe_get(url, 18)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all("li")[:6]:
            t  = card.find("h3")
            c  = card.find("h4")
            lo = card.find("span", class_=re.compile(r"location"))
            lk = card.find("a", href=True)
            if not t: continue
            title = t.get_text(strip=True)
            if not is_fresher(title): continue
            link = lk["href"].split("?")[0] if lk else ""
            jobs.append({"title": title,
                         "company":  c.get_text(strip=True)  if c  else "",
                         "location": lo.get_text(strip=True) if lo else "India",
                         "link": link, "summary": "", "source": "LinkedIn"})
        time.sleep(2)
    logger.info(f"LinkedIn → {len(jobs)}")
    return jobs


# ══ 2. INDEED RSS ════════════════════════════════════════════════════
def fetch_indeed():
    jobs, queries = [], [
        "fresher software engineer",
        "fresher python developer",
        "graduate trainee IT",
        "associate engineer fresher",
        "junior web developer India",
        "fresher QA engineer",
        "fresher java developer",
        "entry level data analyst",
    ]
    for q in queries:
        url = f"https://in.indeed.com/rss?q={q.replace(' ','+')}&l=India&fromage=14"
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:4]:
                title   = e.get("title","")
                summary = BeautifulSoup(e.get("summary",""),"html.parser").get_text()
                if is_fresher(title, summary):
                    jobs.append({"title": title,
                                 "company":  e.get("author",""),
                                 "location": "India",
                                 "link":     e.get("link",""),
                                 "summary":  summary[:300],
                                 "source":   "Indeed"})
            time.sleep(1)
        except Exception as ex:
            logger.warning(f"Indeed '{q}': {ex}")
    logger.info(f"Indeed → {len(jobs)}")
    return jobs


# ══ 3. INTERNSHALA ═══════════════════════════════════════════════════
def fetch_internshala():
    jobs = []
    for url in [
        "https://internshala.com/jobs/computer-science-engineering-jobs/",
        "https://internshala.com/jobs/web-development-jobs/",
        "https://internshala.com/jobs/python-jobs/",
    ]:
        r = safe_get(url)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        cards = (soup.find_all("div", class_=re.compile(r"individual_internship")) or
                 soup.find_all("div", attrs={"data-internship_id": True}))
        for card in cards[:5]:
            t  = card.find(["h3","h2"], class_=re.compile(r"title|profile|heading"))
            c  = card.find(class_=re.compile(r"company-name|company"))
            lk = card.find("a", href=True)
            if not t: continue
            link = lk["href"] if lk else url
            if link.startswith("/"): link = "https://internshala.com" + link
            jobs.append({"title":   t.get_text(strip=True),
                         "company": c.get_text(strip=True) if c else "",
                         "location":"India", "link": link,
                         "summary": "", "source": "Internshala"})
        time.sleep(1.5)
    logger.info(f"Internshala → {len(jobs)}")
    return jobs


# ══ 4. COMPANY PAGES via Indeed RSS ══════════════════════════════════
def _company_via_indeed(company, query, fallback_url, days=90):
    jobs = []
    url  = f"https://in.indeed.com/rss?q={query.replace(' ','+')}&l=India&fromage={days}"
    try:
        feed = feedparser.parse(url)
        for e in feed.entries[:3]:
            title  = e.get("title","")
            author = e.get("author","").lower()
            if company.lower()[:4] in title.lower() or company.lower()[:4] in author:
                jobs.append({"title":   title,
                             "company": company,
                             "location":"India",
                             "link":    e.get("link", fallback_url),
                             "summary": BeautifulSoup(e.get("summary",""),"html.parser").get_text()[:200],
                             "source":  f"{company} Careers"})
    except Exception as ex:
        logger.warning(f"{company}: {ex}")
    return jobs[:2]

def _scrape_zoho():
    jobs = []
    r = safe_get("https://careers.zohocorp.com/jobs/Careers")
    if not r: return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    for row in soup.find_all(["tr","div"], class_=re.compile(r"job|odd|even|career"))[:10]:
        t  = row.find(["td","h3","a"])
        lk = row.find("a", href=True)
        if not t: continue
        title = t.get_text(strip=True)
        if len(title) < 5 or any(bad in title.lower() for bad in
            ["location","experience","skills","posted","type","view"]): continue
        link = lk["href"] if lk else "https://careers.zohocorp.com"
        if link.startswith("/"): link = "https://careers.zohocorp.com" + link
        jobs.append({"title": title, "company": "Zoho",
                     "location": "Chennai / Coimbatore / Remote",
                     "link": link, "summary": "", "source": "Zoho Careers"})
    logger.info(f"Zoho → {len(jobs)}")
    return jobs[:4]

def fetch_company_pages():
    all_jobs = []
    companies = [
        ("TCS",           "TCS graduate trainee NQT fresher 2025",       "https://nextstep.tcs.com"),
        ("Infosys",       "Infosys systems engineer fresher 2025",        "https://career.infosys.com"),
        ("Wipro",         "Wipro engineer trainee fresher 2025",          "https://careers.wipro.com"),
        ("Accenture",     "Accenture associate software engineer fresher","https://www.accenture.com/in-en/careers"),
        ("Cognizant",     "Cognizant programmer analyst fresher 2025",    "https://careers.cognizant.com"),
        ("HCL",           "HCL technologies graduate trainee fresher",    "https://www.hcltech.com/careers"),
        ("Capgemini",     "Capgemini analyst fresher 2025",               "https://www.capgemini.com/in-en/careers"),
        ("Tech Mahindra", "Tech Mahindra associate fresher 2025",         "https://careers.techmahindra.com"),
    ]
    for name, query, url in companies:
        try:
            all_jobs.extend(_company_via_indeed(name, query, url))
            time.sleep(1)
        except Exception as e:
            logger.warning(f"{name}: {e}")
    try:
        all_jobs.extend(_scrape_zoho())
    except Exception as e:
        logger.warning(f"Zoho: {e}")
    logger.info(f"Company pages → {len(all_jobs)}")
    return all_jobs


# ══ MASTER FUNCTION ═══════════════════════════════════════════════════
def fetch_all_jobs() -> list:
    raw = []
    raw += fetch_linkedin()   # most reliable — confirmed returning 7 jobs
    raw += fetch_indeed()
    raw += fetch_internshala()
    raw += fetch_company_pages()

    seen, unique = set(), []
    for job in raw:
        key = (job.get("link","").strip() or
               f"{job.get('title','')}{job.get('company','')}")
        if key and key not in seen:
            seen.add(key)
            unique.append(job)

    logger.info(f"Total unique jobs: {len(unique)}")
    return unique


# ════════════════════════════════════════════════════════════════════
# DATA ANALYST CHANNEL — dedicated scraper
# ════════════════════════════════════════════════════════════════════

DA_KEYWORDS = [
    'data analyst', 'business analyst', 'analyst intern', 'sql analyst',
    'bi analyst', 'data intern', 'junior analyst', 'data associate',
    'analytics analyst', 'power bi analyst', 'tableau analyst',
    'reporting analyst', 'mis analyst', 'insights analyst',
    'junior data', 'analyst trainee',
]

def is_da_job(title: str, summary: str = "") -> bool:
    """Must be DA-related AND fresher-level."""
    return any(kw in title.lower() for kw in DA_KEYWORDS) and is_fresher(title, summary)


def fetch_da_jobs() -> list:
    jobs, queries = [], [
        "data analyst fresher India",
        "junior data analyst India 2025",
        "data analyst intern India 2026",
        "business analyst fresher India",
        "SQL data analyst fresher India",
        "Power BI analyst fresher India",
        "Tableau analyst fresher India",
        "MIS analyst fresher India",
        "analytics associate fresher India",
        "reporting analyst fresher India",
        "data analyst trainee India 2026",
        "Excel data analyst fresher India",
        "entry level data analyst India",
        "data analyst associate India 2025",
    ]
    for q in queries:
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={__import__('requests').utils.quote(q)}&location=India&start=0&f_E=1,2"
        )
        r = safe_get(url, 18)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all("li")[:6]:
            t  = card.find("h3")
            c  = card.find("h4")
            lo = card.find("span", class_=re.compile(r"location"))
            lk = card.find("a", href=True)
            if not t: continue
            title = t.get_text(strip=True)
            if not is_da_job(title): continue
            link = lk["href"].split("?")[0] if lk else ""
            jobs.append({"title": title,
                         "company": c.get_text(strip=True) if c else "",
                         "location": lo.get_text(strip=True) if lo else "India",
                         "link": link, "summary": "", "source": "LinkedIn"})
        time.sleep(2)
    logger.info(f"DA LinkedIn → {len(jobs)}")
    return jobs


def fetch_all_da_jobs() -> list:
    raw  = fetch_da_jobs()
    seen, unique = set(), []
    for job in raw:
        key = job.get("link","").strip() or f"{job['title']}{job.get('company','')}"
        if key and key not in seen:
            seen.add(key)
            unique.append(job)
    logger.info(f"DA total unique: {len(unique)}")
    return unique
