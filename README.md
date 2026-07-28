# Digital Competition Law — Daily Digest (Free)

Sends you a daily email (default 9:00 AM IST) with the latest digital-competition
law news from the EU, UK, US, UN, and other jurisdictions — pulled from official
regulator RSS feeds + Google News.

**Cost: $0.** Runs on GitHub Actions' free tier (2,000 minutes/month for private
repos — this job takes under 1 minute/day, so you'll never hit the limit).

---

## Setup (10 minutes, one-time)

### 1. Create a Gmail "App Password"
Regular Gmail passwords won't work for sending mail from a script. You need an App Password:
1. Go to https://myaccount.google.com/security
2. Turn on **2-Step Verification** if it isn't already on
3. Go to https://myaccount.google.com/apppasswords
4. Create an app password (name it e.g. "digest-bot"), copy the 16-character code

> Using Outlook instead? Say so and I'll swap the SMTP settings in `digest.py`
> (`SMTP_SERVER`/`SMTP_PORT`) — Outlook also supports app passwords.

### 2. Create a GitHub repository
1. Go to https://github.com/new
2. Name it anything, e.g. `competition-law-digest`
3. Make it **Private** (recommended, since secrets live there) or Public — either works
4. Upload all the files in this folder (`digest.py`, `requirements.txt`,
   `.github/workflows/daily-digest.yml`) preserving the folder structure —
   easiest way: on the repo page, click "Add file → Upload files" and drag
   the whole folder in (GitHub preserves the `.github/workflows/` path).

### 3. Add your secrets
In your new repo: **Settings → Secrets and variables → Actions → New repository secret**
Add three secrets:
| Name | Value |
|---|---|
| `SENDER_EMAIL` | your Gmail address |
| `SENDER_APP_PASSWORD` | the 16-character app password from step 1 |
| `RECIPIENT_EMAIL` | the email address you want the digest sent to (can be the same Gmail) |

### 4. Test it
Go to the **Actions** tab → "Daily Digital Competition Digest" → **Run workflow**
(this uses the `workflow_dispatch` trigger built into the workflow file, so you
don't have to wait until 9 AM to see if it works). Check your inbox after ~30 seconds.

### 5. Done
From now on it runs automatically every day at 9:00 AM IST. No server, no
computer needs to be on — GitHub runs it in the cloud for free.

---

## Customizing

- **Add/remove countries:** edit the `GOOGLE_NEWS_QUERIES` dict in `digest.py`.
- **Add/remove official feeds:** edit `OFFICIAL_FEEDS` in `digest.py`.
- **Change keywords/relevance filter:** edit the `KEYWORDS` list.
- **Change the time:** edit the `cron` line in `.github/workflows/daily-digest.yml`.
  GitHub cron is always UTC — subtract 5:30 from your desired IST time.
  (e.g. 9:00 AM IST → `30 3 * * *`)

## Notes & limitations

- Google News RSS is unofficial but free and has no API key requirement; it can
  occasionally be rate-limited or change format. If a query stops returning
  results, it'll just show fewer/no items for that country that day, not break the workflow.
- The digest only includes items published within the last ~30 hours, so nothing
  is missed or duplicated between days.
- If you ever want more advanced source coverage (e.g. scraping specific case
  registries or court dockets that don't offer RSS), that's a bigger build —
  happy to extend this if you tell me which specific sites you need.
