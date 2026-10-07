import time
import requests
import threading
import uvicorn
from app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="warning")

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(2)

BASE_URL = "http://127.0.0.1:8003"

print("==========================================")
print("VERIFYING EMPTY DATABASE ENDPOINTS")
print("==========================================")

endpoints = [
    ("GET", "/health"),
    ("GET", "/api/projects/count"),
    ("GET", "/api/baselines/options"),
    ("POST", "/api/anomaly/run"),
    ("GET", "/api/anomaly/list"),
    ("GET", "/api/spatial/projects?radius_meters=1000"),
    ("GET", "/api/audit"),
    ("GET", "/api/dashboard")
]

endpoint_results = {}

for method, path in endpoints:
    url = BASE_URL + path
    t0 = time.time()
    if method == "GET":
        res = requests.get(url)
    else:
        res = requests.post(url, json={})
    t1 = time.time()
    
    elapsed_ms = round((t1 - t0) * 1000, 1)
    data = res.json() if "application/json" in res.headers.get("content-type", "") else {}
    
    endpoint_results[path] = {
        "status": res.status_code,
        "time_ms": elapsed_ms,
        "data": data
    }
    
    print(f"[{method}] {path}")
    print(f"  Status: {res.status_code}")
    print(f"  Response Time: {elapsed_ms} ms")
    if path == "/api/projects/count":
        print(f"  Total Projects: {data.get('total_projects')}")
    elif path == "/api/dashboard":
        print(f"  Analysed: {data.get('projects_analysed')}, Controlled: {data.get('controlled_test_count')}, Public: {data.get('public_records_count')}")
    elif path.startswith("/api/spatial"):
        print(f"  Mapped Projects: {data.get('total_mapped_projects')}")
    elif path == "/api/audit":
        print(f"  Queue Total: {data.get('total_projects_in_queue')}, DB Total: {data.get('total_db_projects')}")
    print("-" * 50)
