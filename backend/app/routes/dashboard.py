from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from app.database import get_db
from app.models.project import Project
from app.models.public_work import PublicMpladsWork
from app.services.anomaly_service import evaluate_project_anomaly

router = APIRouter(prefix="/api/dashboard", tags=["Executive Dashboard"])

@router.get("")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Returns Executive Dashboard summary metrics derived strictly from current stored database records.
    """
    projects = db.query(Project).all()
    public_works_count = db.query(PublicMpladsWork).count()
    
    total_count = len(projects)

    controlled_count = sum(1 for p in projects if (p.data_source or "CONTROLLED_TEST") == "CONTROLLED_TEST")
    public_count = sum(1 for p in projects if p.data_source == "PUBLIC_RECORD") + public_works_count
    authorised_count = sum(1 for p in projects if p.data_source == "AUTHORISED_RECORD")

    high_priority_count = 0
    review_recommended_count = 0
    normal_count = 0
    evidence_pending_count = 0
    high_priority_queue = []

    from app.ml.isolation_forest_service import run_isolation_forest_pipeline
    ml_map = run_isolation_forest_pipeline(db)

    for p in projects:
        if not p.supporting_document:
            evidence_pending_count += 1

        eval_res = evaluate_project_anomaly(p, db, ml_signal=ml_map.get(p.project_id, "NORMAL"))
        severity = eval_res["review_severity"]

        if severity == "High Review Priority":
            high_priority_count += 1
            if len(high_priority_queue) < 5:
                high_priority_queue.append({
                    "project_id": p.project_id,
                    "project_name": p.project_name,
                    "district": p.district,
                    "project_type": p.project_type,
                    "expenditure": float(p.expenditure),
                    "sanctioned_amount": float(p.sanctioned_amount),
                    "main_reason": eval_res["reasons"][0] if eval_res["reasons"] else "Review priority flagged.",
                    "audit_status": p.audit_status or "Pending Review"
                })
        elif severity == "Review Recommended":
            review_recommended_count += 1
        else:
            normal_count += 1

    # District Distribution
    district_dist = {}
    for p in projects:
        district_dist[p.district] = district_dist.get(p.district, 0) + 1

    # Type Distribution
    type_dist = {}
    for p in projects:
        type_dist[p.project_type] = type_dist.get(p.project_type, 0) + 1

    # Spatial Proximity Overlaps Count (1000m radius)
    valid_coords = [p for p in projects if p.latitude is not None and p.longitude is not None]
    possible_overlaps_count = 0
    import math
    for i in range(len(valid_coords)):
        for j in range(i + 1, len(valid_coords)):
            lat1, lon1 = valid_coords[i].latitude, valid_coords[i].longitude
            lat2, lon2 = valid_coords[j].latitude, valid_coords[j].longitude
            dphi = math.radians(lat2 - lat1)
            dlamb = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlamb / 2.0)**2
            c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
            if 6371000.0 * c <= 1000.0:
                possible_overlaps_count += 1

    return {
        "projects_analysed": total_count,
        "controlled_test_count": controlled_count,
        "public_records_count": public_count,
        "authorised_records_count": authorised_count,
        "review_recommended_count": review_recommended_count,
        "high_priority_count": high_priority_count,
        "normal_count": normal_count,
        "evidence_pending_count": evidence_pending_count,
        "possible_overlaps_count": possible_overlaps_count,
        "district_distribution": district_dist,
        "type_distribution": type_dist,
        "high_priority_queue": high_priority_queue,
        "data_notice": "Summary generated strictly from local prototype database records. Controlled & Public MPLADS Dataset."
    }
