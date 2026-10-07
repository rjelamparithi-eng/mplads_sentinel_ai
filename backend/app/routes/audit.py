from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app.models.project import Project
from app.services.anomaly_service import evaluate_project_anomaly
from app.ml.isolation_forest_service import run_isolation_forest_pipeline

router = APIRouter(prefix="/api/audit", tags=["Audit Workflow"])

class AuditStatusUpdate(BaseModel):
    audit_status: str = Field(..., example="Field / Document Review")

@router.get("")
@router.get("/board")
def get_audit_board(db: Session = Depends(get_db)):
    """
    Returns Kanban workflow board for review queue.
    Only flagged/review-recommended projects enter the workflow by default.
    Normal projects do NOT enter Verified automatically.
    Verified status ONLY occurs after an explicit human/user workflow action.
    """
    projects = db.query(Project).all()
    ml_map = run_isolation_forest_pipeline(db)

    evaluation_map = {}
    for p in projects:
        evaluation_map[p.project_id] = evaluate_project_anomaly(
            p,
            db,
            ml_signal=ml_map.get(p.project_id, "UNAVAILABLE")
        )

    needs_commit = False
    for p in projects:
        eval_res = evaluation_map.get(p.project_id, {})
        sev = eval_res.get("review_severity", "Normal")
        
        if sev == "Normal":
            if p.audit_status == "Pending Review":
                p.audit_status = "Not In Queue"
                needs_commit = True
        elif sev in ("High Review Priority", "Review Recommended"):
            if not p.audit_status or p.audit_status in ("Not In Queue", ""):
                p.audit_status = "Pending Review"
                needs_commit = True

    if needs_commit:
        db.commit()

    columns = {
        "Pending Review": [],
        "Field / Document Review": [],
        "Verified": [],
        "Escalated": []
    }

    in_queue_count = 0
    seen_pids = set()

    for p in projects:
        if p.project_id in seen_pids:
            continue

        eval_res = evaluation_map.get(p.project_id, {})
        current_status = p.audit_status or "Not In Queue"

        if eval_res.get("review_severity") == "Normal" and current_status == "Pending Review":
            current_status = "Not In Queue"

        if current_status in columns:
            seen_pids.add(p.project_id)
            reasons = eval_res.get("reasons", [])
            sev_label = eval_res.get("review_severity", "Normal")
            score_val = float(eval_res.get("anomaly_score", 0.0))
            columns[current_status].append({
                "project_id": p.project_id,
                "project_name": p.project_name,
                "district": p.district,
                "project_type": p.project_type,
                "sanctioned_amount": float(p.sanctioned_amount),
                "expenditure": float(p.expenditure),
                "review_priority": sev_label,
                "review_severity": sev_label,
                "severity": sev_label,
                "anomaly_score": score_val,
                "score": score_val,
                "main_reason": reasons[0] if reasons else "Routine monitoring required.",
                "audit_status": current_status,
                "data_source": p.data_source or "CONTROLLED_TEST"
            })
            in_queue_count += 1

    priority_rank = {
        "High Review Priority": 0,
        "Review Recommended": 1,
        "Normal": 2,
    }

    for stage_cards in columns.values():
        stage_cards.sort(
            key=lambda card: (
                priority_rank.get(
                    card.get("severity") or card.get("review_priority") or card.get("review_severity") or "Normal",
                    99
                ),
                -float(card.get("score") if card.get("score") is not None else card.get("anomaly_score") or 0.0),
                str(card.get("project_id") or "")
            )
        )

    return {
        "columns": columns,
        "total_projects_in_queue": in_queue_count,
        "total_db_projects": len(projects)
    }

@router.patch("/{project_id}")
def update_audit_status(
    project_id: str,
    payload: AuditStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates the audit workflow stage for a specific project.
    Verified status occurs ONLY after explicit human/user action.
    """
    valid_statuses = {"Pending Review", "Field / Document Review", "Verified", "Escalated", "Not In Queue"}
    if payload.audit_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audit status '{payload.audit_status}'. Allowed values: {valid_statuses}"
        )

    project = db.query(Project).filter(Project.project_id.ilike(project_id.strip())).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project ID '{project_id}' not found."
        )

    project.audit_status = payload.audit_status
    db.commit()

    return {
        "status": "success",
        "project_id": project.project_id,
        "new_audit_status": project.audit_status,
        "message": f"Audit status updated to '{project.audit_status}'. Final decision remains human-controlled."
    }
