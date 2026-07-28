"""
Daily Digital Competition Law Digest
-------------------------------------
Pulls recent news/press releases about digital-competition-law developments
(EU, UN, UK, USA, and other jurisdictions) from official RSS feeds and
Google News RSS, filters for relevance, and emails a daily HTML digest.

Runs for free on a schedule via GitHub Actions (see .github/workflows/daily-digest.yml).
"""

import os
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote

import feedparser

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# How far back to look for "new" items (in hours). Set a bit over 24h to
# absorb feeds that publish slightly late or skip a day.
LOOKBACK_HOURS = 30

# Keywords used to decide if a story is relevant to "digital competition law".
# Matched case-insensitively against title + summary.
KEYWORDS = [
    "digital market", "digital markets act", "dma ", "gatekeeper",
    "antitrust", "anti-trust", "competition law", "competition authority",
    "merger control", "abuse of dominance", "monopoly", "monopolization",
    "big tech", "app store", "self-preferencing", "interoperability",
    "data portability", "algorithmic collusion", "platform regulation",
    "digital markets unit", "strategic market status", "ex ante regulation",
    "online platform", "search engine dominance", "ad tech antitrust",
    "cloud competition", "ai competition", "competition probe",
    "competition investigation", "fine", "cartel",
]

# Official regulator RSS/Atom feeds (broad feeds — filtered by KEYWORDS below).
OFFICIAL_FEEDS = {
    "European Commission (Press Corner)": "https://ec.europa.eu/commission/presscorner/api/rss",
    "UK CMA (GOV.UK news)": "https://www.gov.uk/search/news-and-communications.atom?organisations%5B%5D=competition-and-markets-authority",
    "US DOJ (Justice News)": "https://www.justice.gov/feeds/opa/justice-news.xml",
    "US FTC (Press Releases)": "https://www.ftc.gov/feeds/press-release.xml",
}

# Countries / bodies to cover via Google News RSS (no API key needed).
# Add or remove queries freely.
GOOGLE_NEWS_QUERIES = {
    "European Union": "EU digital markets act OR EU antitrust Big Tech",
    "United Kingdom": "UK CMA digital markets antitrust",
    "United States": "US antitrust Big Tech digital markets",
    "United Nations / UNCTAD": "UNCTAD competition policy digital markets",
    "India": "India CCI antitrust digital markets",
    "Japan": "Japan JFTC antitrust digital platform",
    "South Korea": "South Korea KFTC antitrust digital platform",
    "China": "China SAMR antitrust digital platform",
    "Australia": "Australia ACCC digital platforms antitrust",
    "Germany": "Germany Bundeskartellamt digital antitrust",
    "Brazil": "Brazil CADE antitrust digital platform",
    "Canada": "Canada Competition Bureau digital platform antitrust",
    "Turkey": "Turkey competition authority digital platform",
    "South Africa": "South Africa competition commission digital platform",
}

GOOGLE_NEWS_TEMPLATE = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

# ---------------------------------------------------------------------------
# EMAIL CONFIG (read from environment / GitHub Secrets — do not hardcode)
# ---------------------------------------------------------------------------
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))


def is_relevant(title, summary):
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in KEYWORDS)


def parse_entry_date(entry):
    for field in ("published_parsed", "updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            return datetime(*val[:6], tzinfo=timezone.utc)
    return None


def fetch_feed(name, url, cutoff, keyword_filter=True):
    items = []
    try:
        parsed = feedparser.parse(url)
    except Exception as e:
        print(f"[WARN] Failed to fetch {name}: {e}")
        return items

    for entry in parsed.entries:
        title = getattr(entry, "title", "").strip()
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        link = getattr(entry, "link", "")
        pub_date = parse_entry_date(entry)

        # Skip items we can't date, and items older than the cutoff.
        if pub_date and pub_date < cutoff:
            continue

        if keyword_filter and not is_relevant(title, summary):
            continue

        items.append({
            "source": name,
            "title": title,
            "link": link,
            "date": pub_date.strftime("%d %b %Y") if pub_date else "",
        })
    return items


def gather_all_items():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    all_items = []

    # Official regulator feeds — apply keyword filter since these feeds
    # cover ALL agency news, not just competition/digital topics.
    for name, url in OFFICIAL_FEEDS.items():
        all_items.extend(fetch_feed(name, url, cutoff, keyword_filter=True))

    # Google News searches are already topic-scoped by the query itself,
    # so we skip the keyword filter (it would over-reject good results).
    for country, query in GOOGLE_NEWS_QUERIES.items():
        url = GOOGLE_NEWS_TEMPLATE.format(q=quote(query))
        all_items.extend(fetch_feed(f"Google News — {country}", url, cutoff, keyword_filter=False))

    # Deduplicate by title (case-insensitive, trimmed)
    seen = set()
    deduped = []
    for item in all_items:
        key = item["title"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped


def build_html(items):
    today_str = datetime.now(timezone.utc).strftime("%A, %d %B %Y")

    if not items:
        body = "<p>No new digital-competition-law developments were found in the last 24-30 hours.</p>"
    else:
        # Group by source for readability
        grouped = {}
        for item in items:
            grouped.setdefault(item["source"], []).append(item)

        sections = []
        for source, entries in grouped.items():
            rows = "".join(
                f'<li style="margin-bottom:10px;">'
                f'<a href="{e["link"]}" style="color:#1a0dab;text-decoration:none;font-weight:600;">{e["title"]}</a>'
                f'<br><span style="color:#666;font-size:12px;">{e["date"]}</span></li>'
                for e in entries
            )
            sections.append(
                f'<h3 style="border-bottom:2px solid #eee;padding-bottom:4px;margin-top:24px;">{source}</h3>'
                f'<ul style="list-style:none;padding-left:0;">{rows}</ul>'
            )
        body = "".join(sections)

    html = f"""
    <html>
    <body style="font-family:Arial, sans-serif; max-width:720px; margin:auto; color:#222;">
        <h1 style="font-size:22px;">Digital Competition Law — Daily Digest</h1>
        <p style="color:#555;">{today_str}</p>
        <p style="color:#555;font-size:13px;">
            Covering EU, UK, US, UN, and other jurisdictions' digital-competition
            developments (Digital Markets Act, antitrust probes, mergers, fines, etc.)
        </p>
        {body}
        <hr style="margin-top:30px;">
        <p style="font-size:11px;color:#999;">
            Automated digest built from public RSS feeds and Google News.
            Always verify against the original source before citing.
        </p>
    </body>
    </html>
    """
    return html, today_str


def send_email(html_body, today_str):
    if not (SENDER_EMAIL and SENDER_APP_PASSWORD and RECIPIENT_EMAIL):
        raise RuntimeError(
            "Missing email credentials. Set SENDER_EMAIL, SENDER_APP_PASSWORD, "
            "RECIPIENT_EMAIL as environment variables / GitHub Secrets."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Digital Competition Law Digest — {today_str}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())

    print(f"Email sent to {RECIPIENT_EMAIL}")


def main():
    items = gather_all_items()
    print(f"Found {len(items)} relevant items.")
    html_body, today_str = build_html(items)
    send_email(html_body, today_str)


if __name__ == "__main__":
    main()
