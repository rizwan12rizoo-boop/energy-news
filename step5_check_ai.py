# =====================================================================
# STEP 5 - Check the AI's work (don't trust it blindly!)
#
# Two-part step:
#
#   Part A:  python step5_check_ai.py make
#       -> picks 30 random articles and saves data/check_sheet.csv
#          Open it in Excel. For each row, type YOUR answer in the
#          column "my_direction" (up / down / unclear). Save as CSV.
#
#   Part B:  python step5_check_ai.py score
#       -> compares your answers with the AI's and tells you how
#          often the AI agreed with you. Put this number in your README!
# =====================================================================
import sys

import pandas as pd

from database import connect
from settings import CHECK_SHEET

mode = sys.argv[1] if len(sys.argv) > 1 else "make"

if mode == "make":
    df = pd.read_sql("""SELECT link, title, market, direction AS ai_direction
                        FROM articles WHERE relevant = 1""", connect())
    if df.empty:
        sys.exit("No labelled articles yet. Run steps 1 and 2 first.")
    sheet = df.sample(min(30, len(df)), random_state=7)[["title", "market", "ai_direction", "link"]]
    sheet.insert(2, "my_direction", "")      # YOU fill this column
    sheet.to_csv(CHECK_SHEET, index=False)
    print(f"Saved {len(sheet)} articles to {CHECK_SHEET}.")
    print("Open it in Excel, fill in 'my_direction' (up/down/unclear), save as CSV,")
    print("then run:  python step5_check_ai.py score")
    print("Tip: hide the 'ai_direction' column while you fill it in, so it doesn't influence you.")

elif mode == "score":
    sheet = pd.read_csv(CHECK_SHEET)
    sheet["my_direction"] = sheet["my_direction"].astype(str).str.strip().str.lower()
    filled = sheet[sheet["my_direction"].isin(["up", "down", "unclear"])]
    if filled.empty:
        sys.exit("You haven't filled in 'my_direction' yet.")
    agree = (filled["my_direction"] == filled["ai_direction"]).mean()
    print(f"You checked {len(filled)} articles.")
    print(f"The AI agreed with you on {agree:.0%} of them.\n")
    print("Where you disagreed (study these - they make great interview stories):")
    wrong = filled[filled["my_direction"] != filled["ai_direction"]]
    for _, r in wrong.iterrows():
        print(f"  you: {r['my_direction']:7}  AI: {r['ai_direction']:7}  {r['title'][:70]}")
else:
    print("Use:  python step5_check_ai.py make   or   python step5_check_ai.py score")
