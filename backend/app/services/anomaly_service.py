from datetime import date, datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.baseline_service import get_peer_baseline
from app.ml.isolation_forest_service import run_isolation_forest_pipeline

def evaluate_project_anomaly(
    project: Project, 
    db: Session, 
    ml_signal: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes explainable anomaly score, review priority, and Isolation Forest ML signal for a single project.
    Strictly uses neutral terminology: 'Normal', 'Review Recommended', 'High Review Priority'.
    ML Signal produces strictly: 'NORMAL' | 'ML_ANOMALY' | 'UNAVAILABLE'.
    """
    t_sanc = float(project.sanctioned_amount) if project.sanctioned_amount is not None else 0.0
    t_exp = float(project.expenditure) if project.expenditure is not None else 0.0
    
    # Baseline comparison
    baseline = get_peer_baseline(project.district, project.project_type, db)
    
    reasons = []
    anomaly_score = 0.0

    # Rule 1: Cost Deviation
    cost_diff = t_exp - t_sanc
    if cost_diff > 0:
        pct_over = round((cost_diff / t_sanc) * 100, 1) if t_sanc > 0 else 0.0
        if pct_over >= 15.0:
            reasons.append(f"Expenditure significantly exceeds sanctioned budget by {pct_over}% (₹{cost_diff:,.0f}).")
            anomaly_score += 0.55
        else:
            reasons.append(f"Expenditure exceeds sanctioned budget by {pct_over}% (₹{cost_diff:,.0f}).")
            anomaly_score += 0.35
    elif baseline.get("sufficient_peers") and baseline.get("expenditure"):
        upper_bnd = baseline["expenditure"].get("upper_bound", 0.0)
        if t_exp > upper_bnd:
            reasons.append(f"Expenditure (₹{t_exp:,.0f}) exceeds upper peer baseline threshold (₹{upper_bnd:,.0f}).")
            anomaly_score += 0.35

    # Rule 2: Timeline / Delay Deviation
    today = date.today()
    if project.status == "In Progress" and project.expected_completion_date:
        if today > project.expected_completion_date:
            delay_days = (today - project.expected_completion_date).days
            reasons.append(f"Project delayed by {delay_days} days beyond expected completion date ({project.expected_completion_date}).")
            anomaly_score += 0.35
        elif (project.progress_percent or 0.0) < 50.0 and project.sanction_date:
            elapsed = (today - project.sanction_date).days
            tot_exp = (project.expected_completion_date - project.sanction_date).days
            if tot_exp > 0 and (elapsed / tot_exp) > 0.6:
                reasons.append(f"Physical progress ({project.progress_percent}%) is lagging behind time elapsed.")
                anomaly_score += 0.25

    # Rule 3: Evidence Completeness
    if not project.supporting_document:
        reasons.append("Supporting document/completion record is missing.")
        anomaly_score += 0.15

    # Rule 4: Isolation Forest ML Signal Integration
    if ml_signal is None:
        try:
            ml_map = run_isolation_forest_pipeline(db)
            ml_signal = ml_map.get(project.project_id, "UNAVAILABLE")
        except Exception:
            ml_signal = "UNAVAILABLE"

    if ml_signal == "ML_ANOMALY":
        reasons.append("Isolation Forest detected an unusual multivariate project pattern.")
        if anomaly_score < 0.50:
            anomaly_score = min(0.45, anomaly_score + 0.20)
        else:
            anomaly_score = min(1.0, anomaly_score + 0.10)

    # Determine Severity & Priority Label
    anomaly_score = min(1.0, round(anomaly_score, 2))

    if anomaly_score >= 0.50:
        review_severity = "High Review Priority"
        confidence = "High"
    elif anomaly_score >= 0.20:
        review_severity = "Review Recommended"
        confidence = "Medium"
    else:
        review_severity = "Normal"
        confidence = "High"
        if not reasons:
            reasons.append("Project expenditure and progress align with peer cohort standards.")

    # Calculate financial variance vs median
    peer_median = baseline["expenditure"]["median"] if (baseline.get("sufficient_peers") and baseline.get("expenditure")) else t_sanc
    exp_vs_median_pct = round(((t_exp - peer_median) / peer_median) * 100, 1) if peer_median > 0 else 0.0

    return {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "district": project.district,
        "project_type": project.project_type,
        "sanctioned_amount": t_sanc,
        "expenditure": t_exp,
        "progress_percent": project.progress_percent,
        "status": project.status,
        "sanction_date": project.sanction_date.strftime("%Y-%m-%d") if project.sanction_date else None,
        "expected_completion_date": project.expected_completion_date.strftime("%Y-%m-%d") if project.expected_completion_date else None,
        "actual_completion_date": project.actual_completion_date.strftime("%Y-%m-%d") if project.actual_completion_date else None,
        "supporting_document": project.supporting_document,
        "data_source": project.data_source or "CONTROLLED_TEST",
        "audit_status": project.audit_status or "Pending Review",
        "anomaly_score": anomaly_score,
        "review_severity": review_severity,
        "ml_signal": ml_signal,
        "confidence": confidence,
        "reasons": reasons,
        "peer_median_expenditure": peer_median,
        "exp_vs_median_pct": exp_vs_median_pct,
        "next_step": "Human verification / audit recommended." if review_severity != "Normal" else "Routine monitoring."
    }
