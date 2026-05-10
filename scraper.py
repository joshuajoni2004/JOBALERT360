"""
scraper.py — Fixed version
Indeed, LinkedIn, Internshala, Naukri (via RSS), company career pages
"""
import requests, feedparser, logging, time, re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

INCLUDE = ['fresher','freshers','junior','graduate','trainee','entry level',
           'entry-level','0-2','0-1','2024','2025','2026','intern',
           'associate engineer','graduate engineer','campus','apprentice','get']
EXCLUDE = ['senior','5+ year','7+ year','8+ year','10+ year','head of',
           'vp ','director','manager ','principal','staff engineer',
           '3+ year','4+ year','6+ year','lead engineer']

def is_fresher(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    if any(k in text for k in EXCLUDE): return False
    return any(k in text for k in INCLUDE)

def safe_get(url, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.warning(f"GET failed [{url[:55]}]: {e}")
        return None


# ══ 1. INDEED INDIA ══════════════════════════════════════════════════
def fetch_indeed():
    jobs, queries = [], [
        "fresher software engineer",
        "fresher python developer",
        "junior web developer",
        "graduate trainee IT",
        "fresher QA engineer",
        "associate engineer fresher",
        "fresher java developer",
        "entry level data analyst India",
        "fresher devops engineer",
        "fresher cloud support",
    ]
    for q in queries:
        enc = q.replace(" ", "+")
        url = f"https://in.indeed.com/rss?q={enc}&l=India&fromage=14"
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:4]:
                title   = e.get("title","")
                summary = BeautifulSoup(e.get("summary",""),"html.parser").get_text()
                if is_fresher(title, summary):
                    jobs.append({"title":title,"company":e.get("author",""),"location":"India",
                                 "link":e.get("link",""),"summary":summary[:300],"source":"Indeed"})
            time.sleep(1)
        except Exception as ex:
            logger.warning(f"Indeed '{q}': {ex}")
    logger.info(f"Indeed → {len(jobs)}")
    return jobs


# ══ 2. LINKEDIN GUEST API ════════════════════════════════════════════
def fetch_linkedin():
    jobs, queries = [], [
        "fresher software engineer India",
        "graduate trainee IT India",
        "associate engineer fresher India",
        "junior developer India 2025",
        "fresher python developer India",
    ]
    for q in queries:
        url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
               f"?keywords={requests.utils.quote(q)}&location=India&start=0&f_E=1")
        r = safe_get(url, 15)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all("li")[:5]:
            t  = card.find("h3")
            c  = card.find("h4")
            lo = card.find("span", class_=re.compile(r"location"))
            lk = card.find("a", href=True)
            if t and is_fresher(t.get_text(strip=True)):
                link = lk["href"].split("?")[0] if lk else ""
                jobs.append({"title":t.get_text(strip=True),
                             "company":c.get_text(strip=True) if c else "",
                             "location":lo.get_text(strip=True) if lo else "India",
                             "link":link,"summary":"","source":"LinkedIn"})
        time.sleep(2)
    logger.info(f"LinkedIn → {len(jobs)}")
    return jobs


# ══ 3. INTERNSHALA ═══════════════════════════════════════════════════
def fetch_internshala():
    jobs = []
    urls = [
        "https://internshala.com/jobs/computer-science-engineering-jobs/",
        "https://internshala.com/jobs/web-development-jobs/",
        "https://internshala.com/jobs/python-jobs/",
        "https://internshala.com/jobs/data-science-jobs/",
    ]
    for url in urls:
        r = safe_get(url)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        # Try multiple selector patterns since Internshala updates HTML
        cards = (soup.find_all("div", class_=re.compile(r"individual_internship")) or
                 soup.find_all("div", class_=re.compile(r"internship_meta")) or
                 soup.find_all("div", attrs={"data-internship_id": True}))
        for card in cards[:5]:
            t  = (card.find(class_=re.compile(r"job-title|title|profile")) or
                  card.find(["h3","h2","strong"]))
            c  = card.find(class_=re.compile(r"company-name|company"))
            lk = card.find("a", href=True)
            if t:
                link = "https://internshala.com" + lk["href"] if lk and lk["href"].startswith("/") else (lk["href"] if lk else url)
                jobs.append({"title":t.get_text(strip=True),
                             "company":c.get_text(strip=True) if c else "",
                             "location":"India","link":link,"summary":"","source":"Internshala"})
        time.sleep(1.5)
    logger.info(f"Internshala → {len(jobs)}")
    return jobs


# ══ 4. NAUKRI RSS (via Indeed mirror) ════════════════════════════════
def fetch_naukri_via_rss():
    """Naukri doesn't have public RSS — use their structured search page"""
    jobs = []
    urls = [
        "https://www.naukri.com/fresher-jobs?k=fresher&experience=0",
        "https://www.naukri.com/python-developer-jobs-for-freshers",
    ]
    for url in urls:
        r = safe_get(url, 15)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all(["article","div"], class_=re.compile(r"jobTuple|job-tuple|srp-jobtuple"))[:5]:
            t  = card.find(class_=re.compile(r"title|jobTitle"))
            c  = card.find(class_=re.compile(r"comp-name|company"))
            lo = card.find(class_=re.compile(r"loc|location"))
            lk = card.find("a", href=True)
            if t and is_fresher(t.get_text(strip=True)):
                link = lk["href"] if lk else url
                jobs.append({"title":t.get_text(strip=True),
                             "company":c.get_text(strip=True) if c else "",
                             "location":lo.get_text(strip=True) if lo else "India",
                             "link":link,"summary":"","source":"Naukri"})
        time.sleep(2)
    logger.info(f"Naukri → {len(jobs)}")
    return jobs


# ══ 5. COMPANY CAREER PAGES ══════════════════════════════════════════

def _via_indeed_rss(company: str, query: str, career_url: str, days: int = 60) -> list:
    """Helper: find company jobs via Indeed RSS (most reliable method)"""
    jobs = []
    enc  = query.replace(" ", "+")
    url  = f"https://in.indeed.com/rss?q={enc}&l=India&fromage={days}"
    try:
        feed = feedparser.parse(url)
        for e in feed.entries[:3]:
            title = e.get("title","")
            if company.lower()[:4] in title.lower() or company.lower()[:4] in e.get("author","").lower():
                jobs.append({"title":title,"company":company,
                             "location":"India (Multiple Locations)",
                             "link":e.get("link", career_url),
                             "summary":BeautifulSoup(e.get("summary",""),"html.parser").get_text()[:200],
                             "source":f"{company} Careers"})
    except Exception as ex:
        logger.warning(f"{company} Indeed search: {ex}")
    return jobs[:2]


def _scrape_zoho() -> list:
    jobs = []
    r = safe_get("https://careers.zohocorp.com/jobs/Careers")
    if not r: return jobs
    soup = BeautifulSoup(r.text, "html.parser")
    for row in soup.find_all(["tr","div"], class_=re.compile(r"job|row|career|odd|even"))[:8]:
        t  = row.find(["td","h3","a"])
        lk = row.find("a", href=True)
        if t and t.get_text(strip=True) and len(t.get_text(strip=True)) > 5:
            link = lk["href"] if lk else "https://careers.zohocorp.com"
            if link.startswith("/"): link = "https://careers.zohocorp.com" + link
            title = t.get_text(strip=True)
            if any(bad in title.lower() for bad in ["location","experience","skills","posted"]): continue
            jobs.append({"title":title,"company":"Zoho",
                         "location":"Chennai / Coimbatore / Remote",
                         "link":link,"summary":"","source":"Zoho Careers"})
    logger.info(f"Zoho → {len(jobs)}")
    return jobs[:4]


def _scrape_caterpillar() -> list:
    """Caterpillar blocks direct scraping — use Indeed which indexes them"""
    return _via_indeed_rss("Caterpillar","Caterpillar associate engineer fresher India",
                           "https://careers.caterpillar.com", days=90)


def fetch_company_career_pages() -> list:
    all_jobs = []
    tasks = [
        ("TCS",           lambda: _via_indeed_rss("TCS","TCS graduate trainee fresher NQT",
                                                   "https://nextstep.tcs.com", 60)),
        ("Infosys",       lambda: _via_indeed_rss("Infosys","Infosys systems engineer fresher",
                                                   "https://career.infosys.com", 60)),
        ("Wipro",         lambda: _via_indeed_rss("Wipro","Wipro fresher engineer trainee",
                                                   "https://careers.wipro.com", 60)),
        ("Accenture",     lambda: _via_indeed_rss("Accenture","Accenture fresher associate",
                                                   "https://www.accenture.com/in-en/careers", 60)),
        ("Cognizant",     lambda: _via_indeed_rss("Cognizant","Cognizant fresher programmer analyst",
                                                   "https://careers.cognizant.com", 60)),
        ("HCL",           lambda: _via_indeed_rss("HCL","HCL technologies graduate fresher",
                                                   "https://www.hcltech.com/careers", 60)),
        ("Capgemini",     lambda: _via_indeed_rss("Capgemini","Capgemini fresher analyst",
                                                   "https://www.capgemini.com/in-en/careers", 60)),
        ("Tech Mahindra", lambda: _via_indeed_rss("Tech Mahindra","Tech Mahindra fresher associate",
                                                   "https://careers.techmahindra.com", 60)),
        ("Caterpillar",   _scrape_caterpillar),
        ("Zoho",          _scrape_zoho),
    ]
    for name, fn in tasks:
        try:
            jobs = fn()
            all_jobs.extend(jobs)
            time.sleep(1.5)
        except Exception as e:
            logger.warning(f"{name}: {e}")
    logger.info(f"Company pages → {len(all_jobs)}")
    return all_jobs


# ══ MASTER FUNCTION ═══════════════════════════════════════════════════
def fetch_all_jobs() -> list:
    raw = []
    raw += fetch_indeed()
    raw += fetch_linkedin()
    raw += fetch_internshala()
    raw += fetch_naukri_via_rss()
    raw += fetch_company_career_pages()

    seen, unique = set(), []
    for job in raw:
        key = job.get("link","").strip() or f"{job['title']}{job.get('company','')}"
        if key and key not in seen:
            seen.add(key)
            unique.append(job)

    logger.info(f"Total unique this run: {len(unique)}")
    return unique
