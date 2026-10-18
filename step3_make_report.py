# =====================================================================
# STEP 3 - Make the one-page morning report, automatically
#
# Reads the labelled articles from the last 24 hours and writes:
#   reports/report_YYYY-MM-DD.html   (one per day, kept forever)
#   reports/latest.html              (always today's report)
#
# The report shows:
#   * the "news mood" for gas, power and carbon (more up or more down?)
#   * a small chart
#   * the top 5 most important stories
#
# Open the .html file by double-clicking it - it opens in your browser.
#
# Run it:   python step3_make_report.py
# =====================================================================
import base64
import html
import io
from datetime import datetime, timedelta, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from database import connect
from settings import REPORT_DIR

now = datetime.now(timezone.utc)
since = (now - timedelta(hours=24)).isoformat()

df = pd.read_sql("""SELECT * FROM articles
                    WHERE published >= ? AND relevant = 1""", connect(), params=(since,))
practice = bool(len(df)) and df["is_practice"].max() == 1
print(f"{len(df)} relevant articles in the last 24 hours.")

# ---- 1. News mood per market ---------------------------------------
markets = ["gas", "power", "carbon"]
mood_rows = []
for m in markets:
    d = df[df["market"] == m]
    up, down = (d["direction"] == "up").sum(), (d["direction"] == "down").sum()
    total = len(d)
    # mood score: +1 = all stories say "up", -1 = all say "down"
    score = (up - down) / total if total else 0
    mood_rows.append({"market": m, "up": up, "down": down,
                      "unclear": total - up - down, "score": score})
mood = pd.DataFrame(mood_rows)


def mood_word(score):
    if score > 0.2:
        return "Bullish (prices up)", "#b42318"
    if score < -0.2:
        return "Bearish (prices down)", "#067647"
    return "Mixed", "#6b7280"


# ---- 2. Chart: up vs down stories per market -----------------------
fig, ax = plt.subplots(figsize=(6, 2.8))
ax.barh(mood["market"], mood["up"], color="#d9534f", label="price up")
ax.barh(mood["market"], -mood["down"], color="#2e9e6b", label="price down")
ax.axvline(0, color="black", lw=0.8)
ax.set_xlabel("← stories saying DOWN    |    stories saying UP →")
ax.legend(loc="lower right", fontsize=8)
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
fig.tight_layout()
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=130)
plt.close(fig)
chart = base64.b64encode(buf.getvalue()).decode()   # put the picture inside the html

# ---- 3. Top 5 stories ------------------------------------------------
top = df.sort_values(["importance", "published"], ascending=False).head(5)

# ---- 4. Write the HTML page -------------------------------------------
cards = ""
for _, r in mood.iterrows():
    word, color = mood_word(r["score"])
    cards += f"""<div class="card"><div class="mk">{r['market'].upper()}</div>
      <div class="mood" style="color:{color}">{word}</div>
      <div class="small">{r['up']} up · {r['down']} down · {r['unclear']} unclear</div></div>"""

stories = ""
for _, r in top.iterrows():
    arrow = {"up": "▲", "down": "▼"}.get(r["direction"], "●")
    color = {"up": "#b42318", "down": "#067647"}.get(r["direction"], "#6b7280")
    stories += f"""<li><span style="color:{color}">{arrow}</span>
      <b>[{html.escape(r['market'])} · {html.escape(r['country'] or '')} · importance {r['importance']}/5]</b>
      <a href="{html.escape(r['link'])}">{html.escape(r['summary'] or r['title'])}</a>
      <div class="small">Why: {html.escape(r['reason'] or '')} — {html.escape(r['source'] or '')}</div></li>"""
if not stories:
    stories = "<li>No relevant stories in the last 24 hours.</li>"

banner = ('<div class="banner">PRACTICE DATA — made-up headlines, labelled by keyword '
          'rules, not AI. Not real market news.</div>') if practice else ""
model = ", ".join(sorted(df["labelled_by"].dropna().unique())) or "-"

page = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Energy Morning Brief {now:%d %b %Y}</title>
<style>
 body{{font-family:Segoe UI,Arial,sans-serif;max-width:820px;margin:24px auto;padding:0 16px;color:#1f2937;background:#fff}}
 h1{{margin-bottom:0}} .small{{color:#6b7280;font-size:13px}}
 .cards{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}}
 .card{{flex:1;min-width:180px;border:1px solid #e5e7eb;border-radius:10px;padding:12px}}
 .mk{{font-size:12px;letter-spacing:1px;color:#6b7280}} .mood{{font-size:18px;font-weight:600;margin:4px 0}}
 li{{margin-bottom:12px}} a{{color:#1d4ed8;text-decoration:none}}
 .banner{{background:#fef3c7;border:1px solid #f59e0b;padding:8px 12px;border-radius:8px;margin-top:12px}}
 img{{max-width:100%}}
</style></head><body>
<h1>European Energy Morning Brief</h1>
<div class="small">{now:%A %d %B %Y, %H:%M} UTC · {len(df)} relevant stories in the last 24h · labelled by {html.escape(model)}</div>
{banner}
<div class="cards">{cards}</div>
<img src="data:image/png;base64,{chart}" alt="Up vs down stories per market">
<h2>Top 5 stories</h2><ol>{stories}</ol>
<div class="small">Built automatically by the Energy News Robot (Python + Claude API).</div>
</body></html>"""

for path in [REPORT_DIR / f"report_{now:%Y-%m-%d}.html", REPORT_DIR / "latest.html"]:
    path.write_text(page, encoding="utf-8")
print(f"Report saved: {REPORT_DIR / 'latest.html'}")
print(mood.to_string(index=False))
