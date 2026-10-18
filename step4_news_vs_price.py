# =====================================================================
# STEP 4 - The clever part: does the news mood predict prices?
#
# Question: "When the power news was mostly 'price up' on one day,
#            did the German power price really go up the NEXT day?"
#
# It needs:
#   * at least 14 days of news in the database (let the robot run daily)
#   * Project 1's price data in ../wind-surprise-project/data/
#
# Run it:   python step4_news_vs_price.py
# =====================================================================
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from database import connect
from settings import PROJECT1_PRICES, REPORT_DIR

MIN_DAYS = 14

# ---- 1. Daily news mood for the POWER market ---------------------------
news = pd.read_sql("""SELECT published, direction FROM articles
                      WHERE relevant = 1 AND market = 'power' AND is_practice = 0""",
                   connect())
if news.empty:
    sys.exit("No real power news yet. Let the robot run every day for 2+ weeks.")
news["date"] = pd.to_datetime(news["published"], utc=True).dt.tz_convert("Europe/Berlin").dt.date
news["score"] = news["direction"].map({"up": 1, "down": -1}).fillna(0)
mood = news.groupby("date").agg(mood=("score", "mean"), stories=("score", "size"))

if len(mood) < MIN_DAYS:
    sys.exit(f"Only {len(mood)} days of news so far - need {MIN_DAYS}. Keep the robot running!")

# ---- 2. Daily price change from Project 1 ------------------------------
if not PROJECT1_PRICES.exists():
    sys.exit(f"Can't find Project 1 prices at {PROJECT1_PRICES}. Run Project 1 first.")
prices = pd.read_csv(PROJECT1_PRICES)
daily = prices.groupby("date")["price_da"].mean()
daily.index = pd.to_datetime(daily.index).date
next_day_change = (daily.shift(-1) - daily).rename("next_day_change")

both = mood.join(next_day_change, how="inner").dropna()
if len(both) < MIN_DAYS:
    sys.exit(f"Only {len(both)} days where we have BOTH news and prices. "
             "Re-run Project 1 to download newer prices.")

# ---- 3. Results ------------------------------------------------------------
corr = both["mood"].corr(both["next_day_change"])
bull = both[both["mood"] > 0.2]["next_day_change"]
bear = both[both["mood"] < -0.2]["next_day_change"]
hit = ((both["mood"] > 0) == (both["next_day_change"] > 0))[both["mood"] != 0].mean()

lines = [
    f"Days compared: {len(both)}",
    f"Correlation (mood vs next-day price change): {corr:+.2f}   (0 = no link, +1 = perfect)",
    f"Mood got the direction right on {hit:.0%} of days (50% = coin flip)",
    f"After 'bullish' news days ({len(bull)}): price changed {bull.mean():+.1f} EUR/MWh on average",
    f"After 'bearish' news days ({len(bear)}): price changed {bear.mean():+.1f} EUR/MWh on average",
]
text = "\n".join(lines)
(REPORT_DIR / "news_vs_price.txt").write_text(text, encoding="utf-8")
print(text)

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(both["mood"], both["next_day_change"], alpha=0.7)
ax.axhline(0, color="black", lw=0.8)
ax.axvline(0, color="black", lw=0.8)
ax.set_xlabel("Power news mood  (-1 = all 'down' ... +1 = all 'up')")
ax.set_ylabel("Next-day change in German power price (EUR/MWh)")
ax.set_title(f"Does the news mood predict tomorrow's price?  (corr {corr:+.2f})")
fig.tight_layout()
fig.savefig(REPORT_DIR / "news_vs_price.png", dpi=130)
print(f"\nSaved {REPORT_DIR / 'news_vs_price.png'}")
