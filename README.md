# European Energy News Robot
### An AI workflow that reads energy news every morning and writes a trader's brief

> Put a screenshot of a **real** `reports/latest.html` here once the robot has run.

---

## What it does
Every day at 07:00 (Dubai time), with no human involved:

1. **Collects** European gas, power and carbon headlines from Google News RSS
2. **Labels** each one with the Claude API in a fixed format: market, country,
   price direction (up/down/unclear), importance 1–5, a one-line summary, and the reason
3. **Stores** everything in a SQLite database, which builds my own news dataset over time
4. **Writes** a one-page HTML morning brief: news mood per market, a chart, and the top 5 stories
5. **Runs automatically** in the cloud with GitHub Actions

Then I **test it**:
- **Does the news mood predict prices?** I compare daily power-news mood with
  next-day German power price changes (prices from my
  [wind forecast project](../wind-surprise-project)).
- **Is the AI right?** I labelled 30 headlines by hand and compared them with the AI.

## Results  *(fill in after 2+ weeks of real data)*
| Check | Result |
|---|---|
| Articles collected | _[ ]_ |
| AI agreed with my hand labels | _[ ]% of 30_ |
| Correlation: news mood vs next-day price change | _[ ]_ |
| Mood got the direction right | _[ ]% of days (50% = coin flip)_ |

**Where the AI got it wrong:** _[1–2 examples from step 5 and why]_

## Why structured output matters
The AI is forced to fill a **form** (a tool with a JSON schema), so every answer
has the same columns. That means the results go straight into a database and
charts, with no messy text to clean up.

## Limitations
- Headlines only, not full articles, so some nuance is lost
- Google News results vary, and some stories repeat across outlets
- The news mood is a rough signal. Prices also react to weather, outages
  and many other things the news doesn't cover
- A few weeks of data is too short for strong conclusions

## Next steps
- Read full article text for better labels
- Remove duplicate stories that report the same event
- Add official sources: REMIT outage messages and ENTSO-E unavailability data
- Weight the mood by importance

---

## How to run it (Windows)
1. Install Python 3.11+ from python.org (tick *Add Python to PATH*).
2. Open this folder, type `cmd` in the address bar, and press Enter.
3. `pip install -r requirements.txt`
4. **Practice first, with no keys and no internet:**
   `python run_daily.py practice`
   Then double-click `reports/latest.html`.
5. **Real mode:** put your Claude API key in `anthropic_key.txt`, delete
   `data/news.db` (to remove the practice articles), then run:
   `python run_daily.py`
6. After 2+ weeks: `python step4_news_vs_price.py`
7. Check the AI: `python step5_check_ai.py make`, fill in the sheet in Excel,
   then `python step5_check_ai.py score`

### Make it run every morning on GitHub
1. Put this folder on GitHub (make the repository **public** so employers can see it).
2. Go to the repo's **Settings → Secrets and variables → Actions → New repository secret**.
   Name: `ANTHROPIC_API_KEY`. Value: your key.
3. Go to the **Actions** tab and enable workflows.
   Click **Daily energy brief → Run workflow** to test it.

| File | What it does |
|---|---|
| `settings.py` | Searches, AI model, file locations |
| `step1_collect_news.py` | Collects headlines from RSS |
| `step2_ai_label.py` | AI fills in a fixed form for each headline |
| `step3_make_report.py` | Builds the HTML morning brief |
| `step4_news_vs_price.py` | Tests whether the news mood predicts prices |
| `step5_check_ai.py` | Checks the AI against your own labels |
| `run_daily.py` | Runs steps 1–3 |
| `.github/workflows/daily.yml` | The daily "alarm clock" |
