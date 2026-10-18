# =====================================================================
# STEP 2 - Send each article to AI and get a neat, structured answer
#
# This is the most important step for the Cobblestone job:
#   "turn unstructured news into structured data".
#
# For every article the AI fills in a FIXED form:
#   relevant   - is it about European gas/power/carbon prices?
#   market     - gas / power / carbon / other
#   country    - e.g. Germany, Norway, EU
#   direction  - will it push prices up, down, or unclear?
#   importance - 1 (tiny) to 5 (huge)
#   summary    - one short line
#   reason     - why the AI chose that direction
#
# We force the AI to fill a "form" (a tool with a schema), so the answer
# is ALWAYS in the same shape. No messy text to clean up.
#
# No API key yet?  The script uses simple keyword rules instead, so you
# can practise. (Rules are much dumber than AI - that's the point!)
#
# Run it:   python step2_ai_label.py
# =====================================================================
from database import connect
from settings import AI_MODEL, MAX_ARTICLES_PER_RUN, read_api_key

# ---- The "form" the AI must fill in ---------------------------------
FORM = {
    "name": "save_label",
    "description": "Save the analysis of one energy news headline.",
    "input_schema": {
        "type": "object",
        "properties": {
            "relevant": {"type": "boolean",
                         "description": "True only if it can affect European gas, power or carbon prices."},
            "market": {"type": "string", "enum": ["gas", "power", "carbon", "other"]},
            "country": {"type": "string", "description": "Main country or region, e.g. Germany, Norway, EU."},
            "direction": {"type": "string", "enum": ["up", "down", "unclear"],
                          "description": "Likely short-term effect on that market's price."},
            "importance": {"type": "integer", "minimum": 1, "maximum": 5,
                           "description": "1 = minor, 5 = market-moving."},
            "summary": {"type": "string", "description": "One plain sentence, max 20 words."},
            "reason": {"type": "string", "description": "One sentence: why this direction."},
        },
        "required": ["relevant", "market", "country", "direction",
                     "importance", "summary", "reason"],
    },
}

INSTRUCTIONS = """You are a junior analyst on a European energy trading desk.
Read the news headline and fill in the form. Think like a trader:
- Less supply (outages, cold weather, low wind, strikes) -> price UP.
- More supply or less demand (mild weather, high wind, new LNG) -> price DOWN.
- If you honestly can't tell, say 'unclear'. Do not guess.
Only mark it relevant if it could move European gas, power or carbon prices."""


def label_with_ai(client, title, source):
    reply = client.messages.create(
        model=AI_MODEL,
        max_tokens=400,
        system=INSTRUCTIONS,
        tools=[FORM],
        tool_choice={"type": "tool", "name": "save_label"},   # MUST fill the form
        messages=[{"role": "user", "content": f"Headline: {title}\nSource: {source}"}],
    )
    for block in reply.content:
        if block.type == "tool_use":
            return block.input
    raise ValueError("AI did not fill the form")


# ---- Practice labeler (simple keyword rules, no AI) -----------------
UP_WORDS = ["outage", "cut", "strike", "cold", "freeze", "low wind", "shortage",
            "maintenance", "disruption", "surge", "jump", "soar", "tight"]
DOWN_WORDS = ["mild", "warm", "windy", "record wind", "full storage", "fall",
              "drop", "slump", "ease", "new lng", "arrive", "surplus", "weak demand"]


def label_with_rules(title):
    t = title.lower()
    market = ("gas" if any(w in t for w in ["gas", "lng", "ttf"]) else
              "carbon" if any(w in t for w in ["carbon", "eua", "emission"]) else
              "power" if any(w in t for w in ["power", "electric", "wind", "solar", "nuclear"]) else
              "other")
    ups = sum(w in t for w in UP_WORDS)
    downs = sum(w in t for w in DOWN_WORDS)
    direction = "up" if ups > downs else "down" if downs > ups else "unclear"
    country = next((c for c in ["Germany", "Norway", "France", "Netherlands", "UK", "EU"]
                    if c.lower() in t or (c == "Germany" and "german" in t)), "Europe")
    return {"relevant": market != "other", "market": market, "country": country,
            "direction": direction, "importance": min(1 + ups + downs, 5),
            "summary": title[:120], "reason": "keyword rules (practice mode)"}


# ---------------------------------------------------------------------
if __name__ == "__main__":
    db = connect()
    todo = db.execute("""SELECT link, title, source FROM articles
                         WHERE labelled_by IS NULL
                         ORDER BY published DESC LIMIT ?""",
                      (MAX_ARTICLES_PER_RUN,)).fetchall()
    print(f"{len(todo)} articles need a label.")

    key = read_api_key()
    if key:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        labeller = AI_MODEL
        print(f"Using AI model: {AI_MODEL}")
    else:
        client = None
        labeller = "practice-rules"
        print("No API key found -> using simple PRACTICE keyword rules.")

    done = 0
    for link, title, source in todo:
        try:
            lab = label_with_ai(client, title, source) if client else label_with_rules(title)
        except Exception as error:
            print(f"  could not label: {title[:60]}...  ({error})")
            continue
        db.execute("""UPDATE articles SET relevant=?, market=?, country=?, direction=?,
                      importance=?, summary=?, reason=?, labelled_by=? WHERE link=?""",
                   (int(lab["relevant"]), lab["market"], lab["country"], lab["direction"],
                    int(lab["importance"]), lab["summary"], lab["reason"], labeller, link))
        done += 1
        arrow = {"up": "↑", "down": "↓"}.get(lab["direction"], "?")
        print(f"  {arrow} [{lab['market']:6}] imp {lab['importance']}  {title[:70]}")
    db.commit()
    print(f"\nLabelled {done} articles.")
