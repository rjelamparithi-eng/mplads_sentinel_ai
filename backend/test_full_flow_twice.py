import time
import requests
import threading
import uvicorn
from app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(2)

BASE_URL = "http://127.0.0.1:8002"

def execute_full_pass(pass_number):
    print(f"\n--- EXECUTION PASS #{pass_number} ---")

    # 1. Dashboard
    t0 = time.time()
    r_dash = requests.get(f"{BASE_URL}/api/dashboard")
    t_dash = round((time.time() - t0) * 1000, 1)
    dash_data = r_dash.json()
    print(f"1. Dashboard: HTTP {r_dash.status_code} ({t_dash} ms) | Analysed: {dash_data.get('projects_analysed')}")

    # 2. Baselines
    t0 = time.time()
    r_base = requests.get(f"{BASE_URL}/api/baselines/options")
    t_base = round((time.time() - t0) * 1000, 1)
    base_data = r_base.json()
    print(f"2. Baselines Options: HTTP {r_base.status_code} ({t_base} ms) | Districts: {len(base_data.get('districts', []))}, Types: {len(base_data.get('project_types', []))}")

    # 3. Anomaly Detection Engine & List
    t0 = time.time()
    r_anom_run = requests.post(f"{BASE_URL}/api/anomaly/run")
    t_anom_run = round((time.time() - t0) * 1000, 1)
    anom_run_data = r_anom_run.json()
    print(f"3a. Anomaly Run: HTTP {r_anom_run.status_code} ({t_anom_run} ms) | High: {anom_run_data.get('high_priority_count')}, Rec: {anom_run_data.get('review_recommended_count')}, Norm: {anom_run_data.get('normal_count')}")

    t0 = time.time()
    r_anom_list = requests.get(f"{BASE_URL}/api/anomaly/list")
    t_anom_list = round((time.time() - t0) * 1000, 1)
    anom_list = r_anom_list.json()
    first_pid = anom_list[0]['project_id'] if anom_list else None
    print(f"3b. Anomaly List: HTTP {r_anom_list.status_code} ({t_anom_list} ms) | Total: {len(anom_list)}, First PID: {first_pid}")

    # 4. Risk Passport
    t_pass = 0
    if first_pid:
        t0 = time.time()
        r_pass = requests.get(f"{BASE_URL}/api/anomaly/passport/{first_pid}")
        t_pass = round((time.time() - t0) * 1000, 1)
        pass_data = r_pass.json()
        print(f"4. Risk Passport: HTTP {r_pass.status_code} ({t_pass} ms) | PID: {pass_data.get('project_id')}, Severity: {pass_data.get('review_severity')}")

    # 5. Spatial Intelligence
    t0 = time.time()
    r_spat = requests.get(f"{BASE_URL}/api/spatial/projects?radius_meters=1000")
    t_spat = round((time.time() - t0) * 1000, 1)
    spat_data = r_spat.json()
    print(f"5. Spatial Intelligence: HTTP {r_spat.status_code} ({t_spat} ms) | Mapped: {spat_data.get('total_mapped_projects')}, Pairs: {len(spat_data.get('proximity_pairs', []))}")

    # 6. Audit Workflow
    t0 = time.time()
    r_aud = requests.get(f"{BASE_URL}/api/audit")
    t_aud = round((time.time() - t0) * 1000, 1)
    aud_data = r_aud.json()
    print(f"6. Audit Workflow Board: HTTP {r_aud.status_code} ({t_aud} ms) | In Queue: {aud_data.get('total_projects_in_queue')}, Total DB: {aud_data.get('total_db_projects')}")

    # 7. Dashboard Refresh
    t0 = time.time()
    r_dash2 = requests.get(f"{BASE_URL}/api/dashboard")
    t_dash2 = round((time.time() - t0) * 1000, 1)
    dash2_data = r_dash2.json()
    print(f"7. Dashboard Refresh: HTTP {r_dash2.status_code} ({t_dash2} ms) | Analysed: {dash2_data.get('projects_analysed')}")

    return {
        "pass": pass_number,
        "dash_analysed": dash_data.get('projects_analysed'),
        "anom_total": len(anom_list),
        "audit_queue": aud_data.get('total_projects_in_queue'),
        "audit_db_total": aud_data.get('total_db_projects'),
        "anom_run_time": t_anom_run,
        "spatial_time": t_spat,
        "audit_time": t_aud,
        "dash_time": t_dash
    }

p1 = execute_full_pass(1)
p2 = execute_full_pass(2)

print("\n==========================================")
print("PASS 1 VS PASS 2 CONSISTENCY CHECK")
print("==========================================")
print(f"Pass 1 Projects Analysed: {p1['dash_analysed']} | Pass 2: {p2['dash_analysed']}")
print(f"Pass 1 Anomalies List: {p1['anom_total']} | Pass 2: {p2['anom_total']}")
print(f"Pass 1 Audit Queue: {p1['audit_queue']} | Pass 2: {p2['audit_queue']}")
print(f"Pass 1 Audit DB Total: {p1['audit_db_total']} | Pass 2: {p2['audit_db_total']}")

assert p1['dash_analysed'] == p2['dash_analysed'] == 60, "Project count inflation detected!"
assert p1['anom_total'] == p2['anom_total'] == 60, "Anomaly list mismatch!"
assert p1['audit_queue'] == p2['audit_queue'], "Audit queue count inflation detected!"
assert p1['audit_db_total'] == p2['audit_db_total'] == 60, "Audit DB total mismatch!"
print("PASSED 2-PASS CONSISTENCY CHECKS! ZERO INFLATION OR DUPLICATES.")
