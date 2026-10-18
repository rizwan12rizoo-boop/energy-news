# Small helper: opens the database and makes the table if it doesn't exist.
# The database is ONE file (data/news.db). Think of it as an Excel sheet
# that Python can read and write very fast.
import sqlite3

from settings import DATABASE

COLUMNS = """
    link          TEXT PRIMARY KEY,   -- web address (unique, so no duplicates)
    title         TEXT,
    source        TEXT,
    published     TEXT,               -- when the article was published (UTC)
    collected_at  TEXT,               -- when OUR robot found it
    is_practice   INTEGER DEFAULT 0,  -- 1 = made-up practice article
    -- filled in by the AI in step 2:
    relevant      INTEGER,            -- 1 = about European energy prices
    market        TEXT,               -- gas / power / carbon / other
    country       TEXT,
    direction     TEXT,               -- up / down / unclear
    importance    INTEGER,            -- 1 (small) to 5 (huge)
    summary       TEXT,
    reason        TEXT,
    labelled_by   TEXT                -- which AI model (or 'practice-rules')
"""


def connect():
    db = sqlite3.connect(DATABASE)
    db.execute(f"CREATE TABLE IF NOT EXISTS articles ({COLUMNS})")
    return db
