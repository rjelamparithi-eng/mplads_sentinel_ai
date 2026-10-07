import requests

BASE_URL = "http://127.0.0.1:8000"

def run_ingestion_tests():
    print("--- 1. Testing GET /api/ingestion/template ---")
    resp = requests.get(f"{BASE_URL}/api/ingestion/template")
    assert resp.status_code == 200
    print("[OK] Template download returned HTTP 200")

    print("\n--- 2. Testing Preview with valid_projects.csv ---")
    with open("test_data/valid_projects.csv", "rb") as f:
        files = {"file": ("valid_projects.csv", f, "text/csv")}
        resp = requests.post(f"{BASE_URL}/api/ingestion/preview", files=files)
    
    assert resp.status_code == 200, f"Error: {resp.text}"
    preview_valid = resp.json()
    print(f"[OK] Received: {preview_valid['rows_received']}, Valid: {preview_valid['valid_rows']}, Rejected: {preview_valid['rejected_rows']}")

    print("\n--- 3. Testing Commit with valid records ---")
    commit_payload = {
        "records": preview_valid["clean_preview"],
        "data_source": "CONTROLLED_TEST"
    }
    resp = requests.post(f"{BASE_URL}/api/ingestion/commit", json=commit_payload)
    assert resp.status_code == 200, f"Error: {resp.text}"
    commit_res = resp.json()
    print(f"[OK] Inserted: {commit_res['inserted']}, Skipped Duplicates: {commit_res['skipped_duplicates']}, Batch ID: {commit_res['batch_id']}")

    print("\n--- 4. Testing Preview with mixed_quality_projects.csv ---")
    with open("test_data/mixed_quality_projects.csv", "rb") as f:
        files = {"file": ("mixed_quality_projects.csv", f, "text/csv")}
        resp = requests.post(f"{BASE_URL}/api/ingestion/preview", files=files)
    
    assert resp.status_code == 200, f"Error: {resp.text}"
    preview_mixed = resp.json()
    print(f"[OK] Received: {preview_mixed['rows_received']}, Valid: {preview_mixed['valid_rows']}, Warnings: {preview_mixed['warning_rows']}, Rejected: {preview_mixed['rejected_rows']}, Duplicates: {preview_mixed['duplicate_rows']}")

    print("\n--- 5. Checking updated project count ---")
    resp = requests.get(f"{BASE_URL}/api/projects/count")
    assert resp.status_code == 200
    print(f"[OK] Total database project count: {resp.json()['total_projects']}")

    print("\n[SUCCESS] ALL PHASE 3 INGESTION API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_ingestion_tests()
