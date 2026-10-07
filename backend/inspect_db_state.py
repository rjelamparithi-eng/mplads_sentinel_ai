import os
import sys
import sqlite3
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.database import engine, DATABASE_URL

print("=== 1. VERIFY DATABASE USED BY RUNNING FASTAPI PROCESS ===")
print("DATABASE_URL:", DATABASE_URL)
print("Engine URL:", str(engine.url))
print("Runtime SQLite File Path:", engine.url.database)

canonical_db_path = os.path.abspath(engine.url.database) if engine.url.database else ""
print("Absolute Runtime DB Path:", canonical_db_path)

with engine.connect() as conn:
    tables = [row[0] for row in conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print("\nTables & Counts in Canonical DB:")
    for t in sorted(tables):
        if t != 'sqlite_sequence':
            cnt = conn.exec_driver_sql(f"SELECT COUNT(*) FROM {t}").scalar()
            print(f"  {t}: {cnt} rows")

print("\n=== 2. ALL DB FILES IN PROJECT ===")
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for root, dirs, files in os.walk(project_root):
    for f in files:
        if f.endswith(('.db', '.sqlite', '.sqlite3')):
            full_p = os.path.abspath(os.path.join(root, f))
            sz = os.path.getsize(full_p)
            pcnt = "N/A"
            try:
                sc = sqlite3.connect(full_p)
                cursor = sc.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tbls = [r[0] for r in cursor.fetchall()]
                if 'projects' in tbls:
                    cursor.execute("SELECT COUNT(*) FROM projects")
                    pcnt = cursor.fetchone()[0]
                sc.close()
            except Exception as e:
                pcnt = f"Error: {e}"
            print(f"Path: {full_p} | Size: {sz} bytes | projects count: {pcnt}")

print("\n=== 8. LIVE API ENDPOINTS STATUS ===")
endpoints = [
    ("GET /api/projects/count", "http://127.0.0.1:8000/api/projects/count"),
    ("GET /api/dashboard", "http://127.0.0.1:8000/api/dashboard"),
    ("GET /api/spatial/projects", "http://127.0.0.1:8000/api/spatial/projects"),
    ("GET /api/audit", "http://127.0.0.1:8000/api/audit"),
    ("GET /api/baselines/options", "http://127.0.0.1:8000/api/baselines/options"),
    ("GET /api/anomaly/list", "http://127.0.0.1:8000/api/anomaly/list"),
]

for label, url in endpoints:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, list):
                print(f"{label} => Status {resp.status}: list of {len(data)} items")
            elif isinstance(data, dict):
                # print concise dict summary
                keys_info = {k: (len(v) if isinstance(v, list) else v) for k, v in data.items()}
                print(f"{label} => Status {resp.status}: {keys_info}")
            else:
                print(f"{label} => Status {resp.status}: {data}")
    except Exception as e:
        print(f"{label} => ERROR: {e}")
