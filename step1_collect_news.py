# =====================================================================
# STEP 1 - Collect the news (scraping)
#
# What this does:
#   1. Asks Google News for each search in settings.py (RSS feed).
#   2. Keeps only articles from the last 2 days.
#   3. Saves new articles into the database (skips ones we already have).
#
# No internet / want to practise?  Run:  python step1_collect_news.py practice
#   -> loads made-up articles from practice_news.json instead.
#
# Run it:   python step1_collect_news.py
# =====================================================================
import json
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from database import connect
from settings import NEWS_DAYS_BACK, PRACTICE_NEWS, SEARCHES

now = datetime.now(timezone.utc)


def google_news_url(search):
    """Build the RSS address for one Google News search."""
    return (f"https://news.google.com/rss/search?q={quote_plus(search)}"
            f"+when:{NEWS_DAYS_BACK}d&hl=en-GB&gl=GB&ceid=GB:en")


def collect_real():
    import feedparser
    found = []
    for search in SEARCHES:
        feed = feedparser.parse(google_news_url(search))
        print(f"  {len(feed.entries):3d} articles for '{search}'")
        for e in feed.entries:
            if getattr(e, "published_parsed", None):
                published = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
            else:
                published = now
            if now - published > timedelta(days=NEWS_DAYS_BACK):
                continue
            source = e.get("source", {}).get("title", "")
            found.append({"link": e.link, "title": e.title, "source": source,
                          "published": published.isoformat(), "is_practice": 0})
    return found


def collect_practice():
    print("PRACTICE mode: loading made-up articles from practice_news.json")
    items = json.loads(PRACTICE_NEWS.read_text(encoding="utf-8"))
    for i, item in enumerate(items):
        # spread the practice articles over the last day
        item["published"] = (now - timedelta(minutes=37 * i)).isoformat()
        item["is_practice"] = 1
    return items


if __name__ == "__main__":
    practice = len(sys.argv) > 1 and sys.argv[1] == "practice"
    articles = collect_practice() if practice else collect_real()

    db = connect()
    before = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    for a in articles:
        db.execute("""INSERT OR IGNORE INTO articles
                      (link, title, source, published, collected_at, is_practice)
                      VALUES (?, ?, ?, ?, ?, ?)""",
                   (a["link"], a["title"], a["source"], a["published"],
                    now.isoformat(), a["is_practice"]))
    db.commit()
    after = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    print(f"\nFound {len(articles)} articles, {after - before} were NEW.")
    print(f"Database now holds {after} articles in total.")
