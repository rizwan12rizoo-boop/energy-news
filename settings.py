# =====================================================================
# settings.py  -  all the "knobs" of the News Robot live here.
# =====================================================================
import os
from pathlib import Path

# ---- Which news to collect (Google News RSS searches) --------------
# Each line is one search. Add or remove searches here.
SEARCHES = [
    "European gas prices",
    "TTF gas",
    "German power prices",
    "Germany electricity market",
    "EU carbon price EUA",
    "Norway gas outage",
    "LNG Europe",
    "German wind power",
    "Netherlands electricity prices",
    "Dutch power market TenneT",
]
NEWS_DAYS_BACK = 2           # only keep articles from the last 2 days

# ---- AI settings -----------------------------------------------------
# Your Claude API key: put it in a file called anthropic_key.txt,
# or (on GitHub) in a secret called ANTHROPIC_API_KEY.
API_KEY_FILE = Path("anthropic_key.txt")
AI_MODEL = "claude-haiku-5-5"     # small, fast and cheap model
MAX_ARTICLES_PER_RUN = 60         # safety limit so you never overspend

# ---- Files and folders ---------------------------------------------
DATA_DIR = Path("data")
REPORT_DIR = Path("reports")
DATABASE = DATA_DIR / "news.db"            # all articles + AI labels
CHECK_SHEET = DATA_DIR / "check_sheet.csv"  # for checking the AI by hand
PRACTICE_NEWS = Path("practice_news.json")

# Where Project 1's clean price data lives (for step 4)
PROJECT1_PRICES = Path("../wind-surprise-project/data/clean_hourly.csv")

DATA_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)


def read_api_key():
    """Find the Claude API key. Returns None if there isn't one."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key.strip()
    if API_KEY_FILE.exists():
        key = API_KEY_FILE.read_text().strip()
        if key and "PASTE" not in key.upper():
            return key
    return None
