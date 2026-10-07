import os
import shutil
import sqlite3
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
CANONICAL_DB_PATH = BACKEND_DIR / "mplads_sentinel.db"
BACKUP_DIR = BACKEND_DIR / "backups"
BACKUP_FILE_PATH = BACKUP_DIR / "mplads_sentinel_before_full_reset.db"

# 1. BACKUP FIRST
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
if CANONICAL_DB_PATH.exists():
    shutil.copy2(CANONICAL_DB_PATH, BACKUP_FILE_PATH)
    print(f"Backup created successfully at: {BACKUP_FILE_PATH.resolve()}")

# 2. CONNECT TO CANONICAL DATABASE
conn = sqlite3.connect(CANONICAL_DB_PATH)
cursor = conn.cursor()

# 3. DISCOVER DATA TABLES
raw_tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';").fetchall()
discovered_tables = [r[0] for r in raw_tables]
print("Discovered Tables in Canonical Database:", discovered_tables)

# 4. CLEAR ALL PROJECT DATA (ROWS ONLY)
cleared_counts = {}
for tbl in discovered_tables:
    count_before = cursor.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0]
    cursor.execute(f"DELETE FROM {tbl};")
    cleared_counts[tbl] = count_before

conn.commit()

# 7. RESET SQLITE AUTOINCREMENT IF SAFE
has_seq = cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';").fetchone()[0]
if has_seq > 0:
    for tbl in discovered_tables:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name=?;", (tbl,))
    conn.commit()
    print("Reset sqlite_sequence for cleared tables.")

# 6. VERIFY EMPTY STATE IN DB
verification_counts = {}
for tbl in discovered_tables:
    cnt = cursor.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0]
    verification_counts[tbl] = cnt

print("Post-reset DB Record Verification:", verification_counts)

conn.close()
