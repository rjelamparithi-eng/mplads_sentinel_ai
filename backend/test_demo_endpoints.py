import requests

BASE_URL = "http://127.0.0.1:8000"

def test_demo_sprint_endpoints():
    print("--- 1. Testing GET /api/dashboard ---")
    resp = requests.get(f"{BASE_URL}/api/dashboard")
    assert resp.status_code == 200, f"Error: {resp.text}"
    db_summary = resp.json()
    print(f"[OK] Analysed: {db_summary['projects_analysed']}, High Priority: {db_summary['high_priority_count']}, Review Recommended: {db_summary['review_recommended_count']}")

    print("\n--- 2. Testing POST /api/anomaly/run ---")
    resp = requests.post(f"{BASE_URL}/api/anomaly/run")
    assert resp.status_code == 200, f"Error: {resp.text}"
    anom_run = resp.json()
    print(f"[OK] Analysed: {anom_run['total_analysed']}, High Priority: {anom_run['high_priority_count']}")

    print("\n--- 3. Testing GET /api/anomaly/passport/ERD-ROAD-105 ---")
    resp = requests.get(f"{BASE_URL}/api/anomaly/passport/ERD-ROAD-105")
    assert resp.status_code == 200, f"Error: {resp.text}"
    passp = resp.json()
    print(f"[OK] Passport ID: {passp['project_id']}, Severity: {passp['review_severity']}, Reasons: {len(passp['reasons'])}")

    print("\n--- 4. Testing GET /api/spatial/projects ---")
    resp = requests.get(f"{BASE_URL}/api/spatial/projects")
    assert resp.status_code == 200, f"Error: {resp.text}"
    spatial = resp.json()
    print(f"[OK] Mapped Projects: {spatial['total_mapped_projects']}, Proximity Pairs: {len(spatial['proximity_pairs'])}")

    print("\n--- 5. Testing GET /api/audit ---")
    resp = requests.get(f"{BASE_URL}/api/audit")
    assert resp.status_code == 200, f"Error: {resp.text}"
    audit_board = resp.json()
    print(f"[OK] Total Projects in Audit Queue: {audit_board['total_projects_in_queue']}, Pending: {len(audit_board['columns']['Pending Review'])}")

    print("\n--- 6. Testing PATCH /api/audit/ERD-ROAD-105 ---")
    resp = requests.patch(f"{BASE_URL}/api/audit/ERD-ROAD-105", json={"audit_status": "Field / Document Review"})
    assert resp.status_code == 200, f"Error: {resp.text}"
    print(f"[OK] Updated audit status: {resp.json()['new_audit_status']}")

    print("\n[SUCCESS] ALL DEMO SPRINT BACKEND API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_demo_sprint_endpoints()
