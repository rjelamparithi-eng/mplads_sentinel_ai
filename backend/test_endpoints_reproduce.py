import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, method, path, json_payload=None):
    url = BASE_URL + path
    print(f"\n==========================================")
    print(f"Testing {name}: {method} {path}")
    print(f"==========================================")
    print(f"method: {method}")
    print(f"URL: {url}")
    try:
        if method == "POST":
            res = requests.post(url, json=json_payload)
        else:
            res = requests.get(url)
        print(f"status code: {res.status_code}")
        content_type = res.headers.get("content-type", "N/A")
        print(f"content-type: {content_type}")
        print(f"first 500 characters of response: {res.text[:500]}")
        
        try:
            data = res.json()
            print("JSON parse success/failure: SUCCESS")
            if isinstance(data, list):
                print(f"Parsed JSON summary: List of {len(data)} items")
            elif isinstance(data, dict):
                print(f"Parsed JSON summary: Dict with keys {list(data.keys())}")
        except Exception as json_err:
            print(f"JSON parse success/failure: FAILURE ({json_err})")
            
    except Exception as e:
        print(f"Exception calling endpoint: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_endpoint("Health", "GET", "/health")
    test_endpoint("Projects Count", "GET", "/api/projects/count")
    test_endpoint("Anomaly Detection Run", "POST", "/api/anomaly/run")
    test_endpoint("Spatial Intelligence", "GET", "/api/spatial/projects")
    test_endpoint("Audit Workflow", "GET", "/api/audit")
    
    # Dynamically fetch an active project_id from active database
    sample_pid = "DEMO-ERO-ROAD-01"
    try:
        r = requests.get(BASE_URL + "/api/projects")
        if r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0:
            sample_pid = r.json()[0]["project_id"]
    except Exception:
        pass

    test_endpoint("Risk Passport", "GET", f"/api/anomaly/passport/{sample_pid}")
    test_endpoint("Executive Dashboard", "GET", "/api/dashboard")

