import time
import requests
import threading
import uvicorn
from app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8004, log_level="warning")

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(2)

BASE_URL = "http://127.0.0.1:8004"

print("==========================================")
print("VERIFYING API EMPTY STATE")
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

all_passed = True

for method, path in endpoints:
    url = BASE_URL + path
    if method == "GET":
        res = requests.get(url)
    else:
        res = requests.post(url, json={})

    data = res.json() if "application/json" in res.headers.get("content-type", "") else {}

    print(f"[{method}] {path} -> HTTP {res.status_code}")

    if path == "/api/projects/count":
        cnt = data.get("total_projects")
        print(f"  total_projects: {cnt}")
        if cnt != 0: all_passed = False
    elif path == "/api/dashboard":
        analysed = data.get("projects_analysed")
        print(f"  projects_analysed: {analysed}")
        if analysed != 0: all_passed = False
    elif path.startswith("/api/spatial"):
        mapped = data.get("total_mapped_projects")
        print(f"  total_mapped_projects: {mapped}")
        if mapped != 0: all_passed = False
    elif path == "/api/audit":
        queue = data.get("total_projects_in_queue")
        print(f"  total_projects_in_queue: {queue}")
        if queue != 0: all_passed = False
    elif path == "/api/baselines/options":
        districts = data.get("districts", [])
        types = data.get("project_types", [])
        print(f"  districts: {districts}, project_types: {types}")
        if len(districts) != 0 or len(types) != 0: all_passed = False
    elif path == "/api/anomaly/list":
        print(f"  records: {len(data)}")
        if len(data) != 0: all_passed = False

    if res.status_code != 200:
        all_passed = False

    print("-" * 50)

if all_passed:
    print("ALL API ENDPOINTS VERIFIED AT CLEAN EMPTY STATE (HTTP 200, COUNTS = 0)!")
else:
    print("VERIFICATION FAILED: NON-ZERO COUNTS OR NON-200 STATUS DETECTED.")
