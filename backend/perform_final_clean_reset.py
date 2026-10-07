import os
import sys
import shutil
import sqlite3

backend_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(backend_dir, ".."))

backup_dir = os.path.join(backend_dir, "backups")
os.makedirs(backup_dir, exist_ok=True)

canonical_db = os.path.join(backend_dir, "mplads_sentinel.db")
backup_db = os.path.join(backup_dir, "mplads_sentinel_before_full_reset.db")

print("1. BACKING UP CANONICAL DATABASE...")
if os.path.exists(canonical_db):
    shutil.copy2(canonical_db, backup_db)
    print(f"Backed up {canonical_db} -> {backup_db}")
else:
    print(f"ERROR: Canonical DB not found at {canonical_db}")
    sys.exit(1)

print("\n2. CLEARING ALL ROWS FROM CANONICAL DB...")
conn = sqlite3.connect(canonical_db)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
print("Tables in canonical DB:", tables)

for t in tables:
    if t != 'sqlite_sequence':
        cur.execute(f"DELETE FROM {t};")
        print(f"  Cleared table: {t}")

if 'sqlite_sequence' in tables:
    cur.execute("DELETE FROM sqlite_sequence;")
    print("  Cleared sqlite_sequence")

conn.commit()
conn.close()

# Also clear secondary root db copy if exists
root_db = os.path.join(project_root, "mplads_sentinel.db")
if os.path.exists(root_db) and os.path.abspath(root_db) != os.path.abspath(canonical_db):
    print(f"\n3. CLEARING SECONDARY DB AT ROOT: {root_db}")
    shutil.copy2(root_db, os.path.join(backup_dir, "root_mplads_sentinel_before_reset.db"))
    rconn = sqlite3.connect(root_db)
    rcur = rconn.cursor()
    rcur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    rtables = [r[0] for r in rcur.fetchall()]
    for t in rtables:
        if t != 'sqlite_sequence':
            rcur.execute(f"DELETE FROM {t};")
    if 'sqlite_sequence' in rtables:
        rcur.execute("DELETE FROM sqlite_sequence;")
    rconn.commit()
    rconn.close()

print("\n4. VERIFYING TABLE COUNTS POST-RESET:")
vconn = sqlite3.connect(canonical_db)
vcur = vconn.cursor()
vcur.execute("SELECT name FROM sqlite_master WHERE type='table';")
vtables = [r[0] for r in vcur.fetchall()]
for t in vtables:
    if t != 'sqlite_sequence':
        vcur.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = vcur.fetchone()[0]
        print(f"  {t}: {cnt} rows")
vconn.close()
print("RESET COMPLETE!")
