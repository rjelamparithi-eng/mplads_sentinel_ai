import time
import requests
import threading
import uvicorn
from app.main import app
from unittest.mock import patch

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(2)

BASE_URL = "http://127.0.0.1:8001"

print("==========================================")
print("TESTING OPTIONAL COMPONENT FAIL-SAFES")
print("==========================================")

# 1. Test Isolation Forest Failure Fallback
with patch("app.ml.isolation_forest_service.run_isolation_forest_pipeline", side_effect=Exception("Simulated ML Failure")):
    res = requests.get(f"{BASE_URL}/api/anomaly/list")
    print(f"ML Failure Fallback -> /api/anomaly/list status: {res.status_code}")
    data = res.json()
    if data:
        print(f"  First project ML Signal: {data[0].get('ml_signal')} (Expected: UNAVAILABLE)")
        print(f"  First project Severity: {data[0].get('review_severity')}")

# 2. Test TF-IDF Failure Fallback
with patch("app.services.text_similarity_service.compute_project_text_similarity_matrix", side_effect=Exception("Simulated TF-IDF Failure")):
    res = requests.get(f"{BASE_URL}/api/spatial/projects?radius_meters=1000")
    print(f"TF-IDF Failure Fallback -> /api/spatial/projects status: {res.status_code}")
    data = res.json()
    print(f"  Mapped projects count: {data.get('total_mapped_projects')}")

# 3. Test Risk Passport with Missing PDF Evidence
res = requests.get(f"{BASE_URL}/api/anomaly/passport/ERD-ROAD-101")
print(f"Evidence Missing Fallback -> /api/anomaly/passport/ERD-ROAD-101 status: {res.status_code}")
ev = res.json().get("evidence_validation", {})
print(f"  Document Available: {ev.get('document_available')} (Expected: False)")
print(f"  Evidence Confidence: {ev.get('evidence_confidence')} (Expected: LOW)")
print(f"  Issues: {ev.get('issues')}")

print("==========================================")
