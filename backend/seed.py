import os
import sys
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

# Ensure app package is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models.project import Project
from app.models.public_work import PublicMpladsWork
from app.routes.anomaly import run_anomaly_pipeline

def seed_controlled_records(csv_path: str = None):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    if not csv_path and len(sys.argv) > 1:
        csv_path = sys.argv[1]

    if not csv_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path48 = os.path.join(base_dir, "test_data", "MPLADS_Controlled_48_Table_Compatible(1).csv")
        if os.path.exists(path48):
            csv_path = path48
        else:
            csv_path = os.path.join(base_dir, "test_data", "mplads_controlled_60.csv")

    if not os.path.exists(csv_path):
        print(f"[SEED ERROR] Controlled dataset file not found at: {csv_path}")
        db.close()
        return

    try:
        # Clear existing records for fresh controlled demo state
        db.query(Project).delete()
        db.query(PublicMpladsWork).delete()
        db.commit()

        df = pd.read_csv(csv_path)
        sample_projects = []

        for idx, row in df.iterrows():
            s_date = datetime.strptime(str(row["sanction_date"]).strip(), "%Y-%m-%d").date()
            exp_date = datetime.strptime(str(row["expected_completion_date"]).strip(), "%Y-%m-%d").date()
            act_date = None
            if pd.notna(row.get("actual_completion_date")) and str(row["actual_completion_date"]).strip() != "":
                act_date = datetime.strptime(str(row["actual_completion_date"]).strip(), "%Y-%m-%d").date()

            doc = str(row["supporting_document"]).strip() if pd.notna(row.get("supporting_document")) else None

            p = Project(
                project_id=str(row["project_id"]).strip(),
                project_name=str(row["project_name"]).strip(),
                district=str(row["district"]).strip().title(),
                project_type=str(row["project_type"]).strip().title(),
                sanctioned_amount=float(row["sanctioned_amount"]),
                expenditure=float(row["expenditure"]),
                sanction_date=s_date,
                expected_completion_date=exp_date,
                actual_completion_date=act_date,
                progress_percent=float(row["progress_percent"]),
                latitude=float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
                longitude=float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
                status=str(row["status"]).strip().title(),
                supporting_document=doc,
                data_source="CONTROLLED_TEST",
                audit_status="Not In Queue"
            )
            sample_projects.append(p)

        db.add_all(sample_projects)
        db.commit()

        print(f"[SEED SUCCESS] Inserted {len(sample_projects)} controlled test records into database.")

        # Run initial anomaly pipeline to sync review priorities and initial audit statuses
        anom_res = run_anomaly_pipeline(db)
        print(f"[SEED PIPELINE] Anomaly detection executed across {anom_res['total_analysed']} projects:")
        print(f"               - High Review Priority: {anom_res['high_priority_count']}")
        print(f"               - Review Recommended:   {anom_res['review_recommended_count']}")
        print(f"               - Normal:               {anom_res['normal_count']}")

    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to seed records: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_controlled_records()
