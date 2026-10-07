from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.project import Project
from app.services.anomaly_service import evaluate_project_anomaly
from app.ml.isolation_forest_service import run_isolation_forest_pipeline
from app.services.evidence_service import validate_project_evidence

router = APIRouter(prefix="/api/anomaly", tags=["Anomaly Detection & Risk Passport"])

@router.get("/list")
@router.get("/all")
def get_all_anomalies(db: Session = Depends(get_db)):
    """
    Returns anomaly evaluation scores, Isolation Forest ML signals, and review priority labels for all projects.
    """
    projects = db.query(Project).all()
    ml_map = run_isolation_forest_pipeline(db)
    results = [evaluate_project_anomaly(p, db, ml_signal=ml_map.get(p.project_id, "UNAVAILABLE")) for p in projects]
    return results

@router.post("/run")
def run_anomaly_pipeline(db: Session = Depends(get_db)):
    """
    Executes Isolation Forest ML model & statistical rule-based anomaly detection across stored database projects.
    Updates project review priorities.
    """
    projects = db.query(Project).all()
    ml_map = run_isolation_forest_pipeline(db)

    high_count = 0
    recommended_count = 0
    normal_count = 0
    ml_anomaly_count = 0

    evaluations = []
    for p in projects:
        ml_sig = ml_map.get(p.project_id, "UNAVAILABLE")
        if ml_sig == "ML_ANOMALY":
            ml_anomaly_count += 1

        eval_res = evaluate_project_anomaly(p, db, ml_signal=ml_sig)
        sev = eval_res["review_severity"]
        p.review_priority = sev
        evaluations.append(eval_res)

        if sev == "Normal":
            if p.audit_status == "Pending Review":
                p.audit_status = "Not In Queue"
            normal_count += 1
        elif sev == "High Review Priority":
            if not p.audit_status or p.audit_status in ("Not In Queue", ""):
                p.audit_status = "Pending Review"
            high_count += 1
        elif sev == "Review Recommended":
            if not p.audit_status or p.audit_status in ("Not In Queue", ""):
                p.audit_status = "Pending Review"
            recommended_count += 1

    db.commit()

    return {
        "status": "success",
        "total_analysed": len(projects),
        "high_priority_count": high_count,
        "review_recommended_count": recommended_count,
        "normal_count": normal_count,
        "ml_anomaly_count": ml_anomaly_count,
        "evaluations": evaluations
    }

@router.get("/passport/{project_id}")
def get_risk_passport(project_id: str, db: Session = Depends(get_db)):
    """
    Returns detailed explainable Risk Passport for specified project.
    """
    project = db.query(Project).filter(Project.project_id.ilike(project_id.strip())).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project ID '{project_id}' not found."
        )

    ml_map = run_isolation_forest_pipeline(db)
    passport = evaluate_project_anomaly(project, db, ml_signal=ml_map.get(project.project_id, "UNAVAILABLE"))

    similar_peers = db.query(Project).filter(
        Project.project_id != project.project_id,
        (Project.district == project.district) | (Project.project_type == project.project_type)
    ).limit(3).all()

    passport["similar_projects"] = [
        {
            "project_id": sp.project_id,
            "project_name": sp.project_name,
            "district": sp.district,
            "project_type": sp.project_type,
            "sanctioned_amount": float(sp.sanctioned_amount),
            "expenditure": float(sp.expenditure),
            "progress_percent": sp.progress_percent
        } for sp in similar_peers
    ]

    evidence_res = validate_project_evidence(project)
    passport["evidence_validation"] = evidence_res

    passport["evidence_summary"] = {
        "available_records": ["Sanction Order", "Expenditure Log"] if project.supporting_document else ["Sanction Order"],
        "missing_records": [] if project.supporting_document else ["Completion Certificate / Bill Voucher"],
        "document_consistency": "Consistent" if evidence_res.get("evidence_confidence") == "HIGH" else "Verification Required",
        "evidence_confidence": evidence_res.get("evidence_confidence", "LOW"),
        "project_id_match": evidence_res.get("project_id_match", False),
        "amount_match": evidence_res.get("amount_match", False),
        "issues": evidence_res.get("issues", [])
    }

    return passport
