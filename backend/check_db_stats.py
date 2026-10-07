import sqlite3

conn = sqlite3.connect('mplads_sentinel.db')
cursor = conn.cursor()
tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
print("Tables in DB:", tables)

projects = cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
unique_proj = cursor.execute("SELECT COUNT(DISTINCT project_id) FROM projects").fetchone()[0]
coords = cursor.execute("SELECT COUNT(*) FROM projects WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchone()[0]
docs = cursor.execute("SELECT COUNT(*) FROM projects WHERE supporting_document IS NOT NULL AND supporting_document != ''").fetchone()[0]

anomalies = 0
if 'anomaly_results' in tables:
    anomalies = cursor.execute("SELECT COUNT(*) FROM anomaly_results").fetchone()[0]

audit = 0
if 'audit_workflow' in tables:
    audit = cursor.execute("SELECT COUNT(*) FROM audit_workflow").fetchone()[0]

print(f"projects count: {projects}")
print(f"unique project_id count: {unique_proj}")
print(f"projects with coordinates: {coords}")
print(f"projects with supporting_document: {docs}")
print(f"current anomaly results count: {anomalies}")
print(f"current audit workflow count: {audit}")
