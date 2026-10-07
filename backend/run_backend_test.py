import time
import threading
import requests
import uvicorn
from app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(2) # Allow uvicorn server to start

BASE_URL = "http://127.0.0.1:8000"

print("==========================================")
print("FASTAPI BACKEND ENDPOINT TIMING & SMOKE TEST")
print("==========================================")

endpoints = [
    ("GET", "/health", None),
    ("GET", "/api/projects/count", None),
    ("GET", "/api/baselines/options", None),
    ("POST", "/api/anomaly/run", None),  # Mandatory: Run anomaly detection first
    ("GET", "/api/anomaly/list", None),
    ("GET", "/api/spatial/projects?radius_meters=1000", None),
    ("GET", "/api/audit", None),
    ("GET", "/api/dashboard", None),
]

first_pid = None
results_summary = {}

for method, path, body in endpoints:
    url = BASE_URL + path
    t0 = time.time()
    if method == "GET":
        res = requests.get(url)
    elif method == "POST":
        res = requests.post(url, json=body)
    t1 = time.time()

    elapsed_ms = round((t1 - t0) * 1000, 1)
    content_type = res.headers.get("content-type", "")

    data = res.json() if "application/json" in content_type else {}

    results_summary[path] = {
        "status": res.status_code,
        "time_ms": elapsed_ms,
        "content_type": content_type
    }

    print(f"[{method}] {path}")
    print(f"  Status: {res.status_code}")
    print(f"  Response Time: {elapsed_ms} ms")
    print(f"  Content-Type: {content_type}")

    if path == "/api/projects/count":
        results_summary[path]["total_projects"] = data.get("total_projects")
        print(f"  Projects Count: {data.get('total_projects')}")
    elif path == "/api/anomaly/run":
        results_summary[path]["high"] = data.get("high_priority_count")
        results_summary[path]["recommended"] = data.get("review_recommended_count")
        results_summary[path]["normal"] = data.get("normal_count")
        print(f"  High Priority: {data.get('high_priority_count')}, Recommended: {data.get('review_recommended_count')}, Normal: {data.get('normal_count')}")
    elif path == "/api/anomaly/list":
        if isinstance(data, list) and len(data) > 0:
            first_pid = data[0]["project_id"]
            results_summary[path]["count"] = len(data)
            print(f"  Anomalies Listed: {len(data)}, First PID: {first_pid}")
    elif path.startswith("/api/spatial"):
        results_summary[path]["mapped_projects"] = data.get("total_mapped_projects")
        results_summary[path]["proximity_pairs"] = len(data.get("proximity_pairs", []))
        print(f"  Mapped Projects: {data.get('total_mapped_projects')}, Proximity Pairs: {len(data.get('proximity_pairs', []))}")
    elif path == "/api/audit":
        results_summary[path]["queue_total"] = data.get("total_projects_in_queue")
        results_summary[path]["db_total"] = data.get("total_db_projects")
        print(f"  Queue Total: {data.get('total_projects_in_queue')}, DB Total: {data.get('total_db_projects')}")
    elif path == "/api/dashboard":
        results_summary[path]["analysed"] = data.get("projects_analysed")
        print(f"  Projects Analysed: {data.get('projects_analysed')}")
    print("-" * 50)

if first_pid:
    passport_path = f"/api/anomaly/passport/{first_pid}"
    url = BASE_URL + passport_path
    t0 = time.time()
    res = requests.get(url)
    t1 = time.time()
    elapsed_ms = round((t1 - t0) * 1000, 1)

    data = res.json()
    results_summary[passport_path] = {
        "status": res.status_code,
        "time_ms": elapsed_ms,
        "project_id": data.get("project_id"),
        "review_severity": data.get("review_severity")
    }
    print(f"[GET] {passport_path}")
    print(f"  Status: {res.status_code}")
    print(f"  Response Time: {elapsed_ms} ms")
    print(f"  Project ID: {data.get('project_id')}")
    print(f"  Severity: {data.get('review_severity')}")
    print("=" * 50)
