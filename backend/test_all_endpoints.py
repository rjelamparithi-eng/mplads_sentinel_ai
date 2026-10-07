import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("==========================================")
print("FASTAPI BACKEND ENDPOINT TIMING & SMOKE TEST")
print("==========================================")

endpoints = [
    ("GET", "/health", None),
    ("GET", "/api/projects/count", None),
    ("GET", "/api/baselines/options", None),
    ("POST", "/api/anomaly/run", None),  # Execution safeguard: Run anomaly detection first
    ("GET", "/api/anomaly/list", None),
    ("GET", "/api/spatial/projects?radius_meters=1000", None),
    ("GET", "/api/audit", None),
    ("GET", "/api/dashboard", None),
]

first_pid = None

for method, url, body in endpoints:
    t0 = time.time()
    if method == "GET":
        res = client.get(url)
    elif method == "POST":
        res = client.post(url, json=body)
    t1 = time.time()

    elapsed = round((t1 - t0) * 1000, 1) # ms
    content_type = res.headers.get("content-type", "")

    data = res.json() if "application/json" in content_type else res.text

    print(f"[{method}] {url}")
    print(f"  Status: {res.status_code}")
    print(f"  Response Time: {elapsed} ms")
    print(f"  Content-Type: {content_type}")

    if url == "/api/projects/count":
        print(f"  Projects count: {data.get('total_projects')}")
    elif url == "/api/anomaly/run":
        print(f"  High Priority: {data.get('high_priority_count')}, Recommended: {data.get('review_recommended_count')}, Normal: {data.get('normal_count')}")
    elif url == "/api/anomaly/list":
        if isinstance(data, list) and len(data) > 0:
            first_pid = data[0]["project_id"]
            print(f"  Total Anomalies Listed: {len(data)}, First PID: {first_pid}")
    elif url.startswith("/api/spatial"):
        print(f"  Mapped Projects: {data.get('total_mapped_projects')}, Proximity Pairs: {len(data.get('proximity_pairs', []))}")
    elif url == "/api/audit":
        print(f"  Queue Total: {data.get('total_projects_in_queue')}, DB Total: {data.get('total_db_projects')}")
    elif url == "/api/dashboard":
        print(f"  Projects Analysed: {data.get('projects_analysed')}, High Priority Queue: {len(data.get('high_priority_queue', []))}")
    print("-" * 50)

if first_pid:
    url = f"/api/anomaly/passport/{first_pid}"
    t0 = time.time()
    res = client.get(url)
    t1 = time.time()
    elapsed = round((t1 - t0) * 1000, 1)
    print(f"[GET] {url}")
    print(f"  Status: {res.status_code}")
    print(f"  Response Time: {elapsed} ms")
    print(f"  Project ID: {res.json().get('project_id')}")
    print(f"  Severity: {res.json().get('review_severity')}")
    print("=" * 50)
