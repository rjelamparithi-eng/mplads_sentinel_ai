import requests

BASE_URL = "http://127.0.0.1:8000"

def test_baseline_endpoints():
    print("--- 1. Testing GET /api/baselines/options ---")
    resp = requests.get(f"{BASE_URL}/api/baselines/options")
    assert resp.status_code == 200, f"Error: {resp.text}"
    opts = resp.json()
    print(f"[OK] Districts found: {opts['districts']}, Project types found: {opts['project_types']}")

    print("\n--- 2. Test Case 1: Exact Peer Group (District + Type >= 3) ---")
    resp = requests.get(f"{BASE_URL}/api/baselines", params={"district": "Erode", "project_type": "Road"})
    assert resp.status_code == 200, f"Error: {resp.text}"
    data = resp.json()
    assert data["peer_level"] == "DISTRICT_AND_TYPE"
    assert data["sufficient_peers"] is True
    assert data["sanctioned_amount"]["median"] > 0
    print(f"[OK] Level: {data['peer_level']}, Peers: {data['peer_count']}, Median Expenditure: Rs. {data['expenditure']['median']}")

    print("\n--- 3. Test Case 2: Fallback Peer Group (Type Only Fallback) ---")
    # Query district with <3 records for a common project type
    resp = requests.get(f"{BASE_URL}/api/baselines", params={"district": "NonExistentDistrict", "project_type": "Road"})
    assert resp.status_code == 200, f"Error: {resp.text}"
    data = resp.json()
    assert data["peer_level"] == "TYPE_ONLY_FALLBACK"
    assert data["sufficient_peers"] is True
    print(f"[OK] Level: {data['peer_level']}, Note: {data['note']}")

    print("\n--- 4. Test Case 3: Insufficient Data (<3 records total) ---")
    resp = requests.get(f"{BASE_URL}/api/baselines", params={"district": "NonExistentDistrict", "project_type": "UnknownSector"})
    assert resp.status_code == 200, f"Error: {resp.text}"
    data = resp.json()
    assert data["peer_level"] == "INSUFFICIENT_DATA"
    assert data["sufficient_peers"] is False
    print(f"[OK] Level: {data['peer_level']}, Sufficient Peers: {data['sufficient_peers']}")

    print("\n--- 5. Test Case 4 & 5: High Expenditure & Project Comparison ---")
    # ERD-ROAD-105 has high expenditure relative to baseline
    resp = requests.get(f"{BASE_URL}/api/baselines/project/ERD-ROAD-105")
    assert resp.status_code == 200, f"Error: {resp.text}"
    comp = resp.json()
    assert "fraud" not in comp
    assert "risk_score" not in comp
    print(f"[OK] Project: {comp['project_id']}, Exp vs Median %: {comp['comparison']['expenditure_vs_peer_median_percent']}%, Interpretation: {comp['interpretation']}")

    print("\n--- 6. Test Case 6: Unknown Project ID Comparison ---")
    resp = requests.get(f"{BASE_URL}/api/baselines/project/UNKNOWN-999")
    assert resp.status_code == 404
    print("[OK] Unknown project returned clean HTTP 404 response.")

    print("\n[SUCCESS] ALL PHASE 4 BASELINE API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_baseline_endpoints()
