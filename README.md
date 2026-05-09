# JobPulse — Automated Fresher Job Bot + Website

Auto-fetches verified fresher jobs from Indeed, Internshala, LinkedIn, Foundit & FresherOffCampus
→ Formats them with Claude AI into clean posts
→ Posts to your Telegram channel every 3 hours
→ Displays everything on a public job board website

---

## What you get

| Feature | Detail |
|---|---|
| Auto job fetching | 5 sources, runs every 3 hours |
| AI formatting | Claude Haiku formats each job into your template |
| Duplicate detection | SQLite prevents same job posting twice |
| Telegram posting | Direct to your channel, 12 jobs max per sweep |
| Public website | Clean job board with search + filter |
| Admin dashboard | `/admin` page to monitor + manual trigger |
| Free hosting | Runs on Railway free tier |

---

## Setup in 4 steps

### Step 1 — Get your API keys

**Telegram Bot:**
1. Open Telegram → search `@BotFather` → start chat
2. Send `/newbot`
3. Give it a name (e.g. `JobPulse Bot`) and username (e.g. `jobpulse_bot`)
4. Copy the token it gives you → this is `TELEGRAM_TOKEN`
5. Create a Telegram channel (public, e.g. `@jobpulse2026`)
6. Add your bot to the channel as **Admin** with "Post Messages" permission
7. Your `TELEGRAM_CHANNEL_ID` = `@jobpulse2026`
8. Your `TELEGRAM_CHANNEL_USERNAME` = `jobpulse2026` (no @)

**Claude API:**
1. Go to https://console.anthropic.com
2. Sign up / log in
3. Go to API Keys → Create Key
4. Copy it → this is `CLAUDE_API_KEY`
5. Add a small amount of credits ($5 will last weeks for this bot)

---

### Step 2 — Deploy to Railway (free hosting)

1. Go to https://github.com → create a new repository called `jobpulse`
2. Upload all project files to that repo
3. Go to https://railway.app → Sign up with GitHub
4. Click **New Project** → **Deploy from GitHub repo** → select `jobpulse`
5. Railway auto-detects Python and deploys

**Add environment variables in Railway:**
- Go to your project → Variables tab
- Add each variable from `.env.example` with your real values:

```
TELEGRAM_TOKEN          = your_bot_token
TELEGRAM_CHANNEL_ID     = @yourchannelname
TELEGRAM_CHANNEL_USERNAME = yourchannelname
CLAUDE_API_KEY          = sk-ant-...
TRIGGER_SECRET          = pick_any_secret_phrase
MAX_JOBS_PER_RUN        = 12
DELAY_BETWEEN_POSTS     = 45
```

6. Railway gives you a public URL like `https://jobpulse-production.up.railway.app`
   → This is your website URL

---

### Step 3 — Test it works

Once deployed:

1. Visit `https://your-railway-url.up.railway.app/health` → should return `{"status":"ok"}`
2. Visit `https://your-railway-url.up.railway.app/admin?key=YOUR_TRIGGER_SECRET`
3. Click **Run Pipeline Now** → enter your trigger secret
4. Check your Telegram channel — jobs should appear within 2 minutes

---

### Step 4 — Run locally (optional, for testing)

```bash
# Clone your repo
git clone https://github.com/yourusername/jobpulse
cd jobpulse

# Install dependencies
pip install -r requirements.txt

# Copy env file and fill in your keys
cp .env.example .env
# Edit .env with your actual keys

# Run
python app.py
```

Website will be at: http://localhost:5000

---

## Project structure

```
jobpulse/
├── app.py              ← Flask website + scheduler (main entry point)
├── pipeline.py         ← Orchestrates fetch → format → post → save
├── scraper.py          ← Fetches jobs from 5 sources
├── formatter.py        ← Claude AI formats each job
├── telegram_poster.py  ← Posts to Telegram channel
├── database.py         ← SQLite storage + deduplication
├── admin.py            ← Admin dashboard
├── templates/
│   └── index.html      ← Public job board website
├── requirements.txt
├── Procfile            ← Railway/Heroku start command
├── railway.json        ← Railway config
└── .env.example        ← Environment variable template
```

---

## How the pipeline works

```
Every 3 hours (auto) or manual trigger:

1. FETCH    → Scrape Indeed RSS + Internshala + FresherOffCampus + LinkedIn + Foundit
2. FILTER   → Remove senior/experienced roles
3. DEDUPE   → Skip if already in SQLite DB
4. VERIFY   → Claude checks: is this a real fresher job?
5. FORMAT   → Claude formats into your Telegram template
6. POST     → Send to Telegram channel (45s delay between posts)
7. SAVE     → Store in DB for website display
```

---

## Monetization (when you reach members)

| Members | What to do | Estimated income |
|---|---|---|
| 1,000 | Nothing yet. Just grow. | ₹0 |
| 5,000 | DM edtech companies for sponsored posts | ₹2,000–5,000/post |
| 10,000 | Charge recruiters for priority listings | ₹5,000–15,000/month |
| 25,000+ | Affiliate deals (Scaler, Newton School etc.) | ₹20,000–1L/month |

**Fastest growth tactic:** Message 10 college placement officers this week. Tell them you run a free verified jobs channel for their students. Ask them to share with their batch groups. This is free and compounds.

---

## Troubleshooting

**Bot not posting to channel:**
- Confirm bot is added as Admin in the channel
- Check `TELEGRAM_CHANNEL_ID` starts with `@` for public channels
- Run `/health` check first to confirm app is live

**Scraper getting 0 jobs:**
- Indeed RSS sometimes changes their URL format — check the URL in `scraper.py`
- Internshala's HTML class names can change — may need to update selectors
- This is normal with scraping; the RSS sources (Indeed) are most stable

**Claude API errors:**
- Check you have credits at https://console.anthropic.com/settings/billing
- Model name `claude-haiku-4-5-20251001` is correct as of May 2026

**Railway deploy fails:**
- Check all required env variables are set in Railway Variables tab
- Check build logs in Railway dashboard for specific error

---

## Upgrading later

- **Add company career pages** (TCS, Infosys, Wipro): Needs Playwright for JS rendering. Add as Phase 2 once bot is stable.
- **Add WhatsApp forwarding**: Set up a WhatsApp Business API or use Twilio's WhatsApp sandbox to forward jobs to WhatsApp group too.
- **Add email digest**: Weekly email with top jobs using Flask-Mail.
- **Add apply tracking**: Track click-throughs on each apply link using redirect URLs.
