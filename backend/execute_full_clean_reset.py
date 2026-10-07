import os
import shutil
import sqlite3
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

CANONICAL_DB_PATH = BACKEND_DIR / "mplads_sentinel.db"
ROOT_DB_PATH = PROJECT_ROOT / "mplads_sentinel.db"

BACKUP_DIR = BACKEND_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_FILE_PATH = BACKUP_DIR / "mplads_sentinel_before_full_reset.db"

# 1. Backup canonical DB
if CANONICAL_DB_PATH.exists():
    shutil.copy2(CANONICAL_DB_PATH, BACKUP_FILE_PATH)
    print(f"Backed up canonical DB to: {BACKUP_FILE_PATH.resolve()}")

# 2. Clear Canonical DB rows
def clear_db(db_path, db_label):
    if not db_path.exists():
        print(f"[{db_label}] DB file does not exist: {db_path}")
        return
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';").fetchall()]
    
    for tbl in tables:
        cur.execute(f"DELETE FROM {tbl};")
    
    # Reset sqlite_sequence if present
    has_seq = cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';").fetchone()[0]
    if has_seq > 0:
        for tbl in tables:
            cur.execute("DELETE FROM sqlite_sequence WHERE name=?;", (tbl,))
            
    con.commit()
    
    # Verification
    counts = {tbl: cur.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0] for tbl in tables}
    print(f"[{db_label}] Cleared {db_path.name} -> Counts: {counts}")
    con.close()

clear_db(CANONICAL_DB_PATH, "CANONICAL DB")
clear_db(ROOT_DB_PATH, "ROOT DB")

