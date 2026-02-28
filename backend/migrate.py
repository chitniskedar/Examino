"""
migrate.py — One-time migration: adds missing columns to existing examino.db.
Run once from the backend/ folder:
    python migrate.py
"""

import sqlite3
import os

# Find the DB — same logic as database.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "examino.db")

if not os.path.exists(DB_PATH):
    # Try next to this script (some layouts keep it in backend/)
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examino.db")

if not os.path.exists(DB_PATH):
    print(f"❌  Could not find examino.db. Checked:\n  {DB_PATH}")
    print("    Set DB_PATH manually at the top of this script.")
    exit(1)

print(f"📂  Found DB at: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── Check existing columns ────────────────────────────────────────────────────
cur.execute("PRAGMA table_info(questions)")
existing_cols = {row[1] for row in cur.fetchall()}
print(f"    Existing columns: {sorted(existing_cols)}")

# ── Add text_hash if missing ──────────────────────────────────────────────────
if "text_hash" not in existing_cols:
    cur.execute("ALTER TABLE questions ADD COLUMN text_hash TEXT")
    conn.commit()
    print("✅  Added column: text_hash")
else:
    print("✓   text_hash already exists — nothing to do.")

conn.close()
print("\n✅  Migration complete. Run uvicorn main:app --reload")