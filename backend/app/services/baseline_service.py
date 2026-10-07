import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.project import Project
from app.config.baseline_config import MIN_PEER_COUNT, IQR_MULTIPLIER

def get_baseline_filter_options(db: Session) -> Dict[str, List[str]]:
    """Returns distinct list of districts and project types stored in database."""
    districts = [
        r[0] for r in db.query(Project.district).distinct().order_by(Project.district).all() if r[0]
    ]
    project_types = [
        r[0] for r in db.query(Project.project_type).distinct().order_by(Project.project_type).all() if r[0]
    ]
    return {
        "districts": districts,
        "project_types": project_types
    }

def calculate_robust_stats(values: List[float]) -> Optional[Dict[str, float]]:
    """Calculates median, Q1, Q3, IQR, lower bound (clamped to >=0), and upper bound."""
    clean_vals = [float(v) for v in values if v is not None and not pd.isna(v)]
    if not clean_vals:
        return None

    arr = np.array(clean_vals)
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    median = float(np.median(arr))
    iqr = q3 - q1

    lower_bnd = max(0.0, q1 - (IQR_MULTIPLIER * iqr))
    upper_bnd = q3 + (IQR_MULTIPLIER * iqr)

    return {
        "median": round(median, 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "lower_bound": round(lower_bnd, 2),
        "upper_bound": round(upper_bnd, 2),
        "records_used": len(clean_vals)
    }

def get_peer_baseline(
    district: str, 
    project_type: str, 
    db: Session
) -> Dict[str, Any]:
    """
    Computes robust peer baseline with 3-level fallback hierarchy:
    Level 1: Same District + Same Project Type
    Level 2: Same Project Type (across all districts)
    Level 3: Insufficient Data
    """
    # Level 1 Query
    level1_query = db.query(Project).filter(
        Project.district.ilike(district.strip()),
        Project.project_type.ilike(project_type.strip())
    ).all()

    peer_level = "DISTRICT_AND_TYPE"
    selected_peers = level1_query

    # Level 2 Fallback Check
    if len(selected_peers) < MIN_PEER_COUNT:
        level2_query = db.query(Project).filter(
            Project.project_type.ilike(project_type.strip())
        ).all()
        
        if len(level2_query) >= MIN_PEER_COUNT:
            peer_level = "TYPE_ONLY_FALLBACK"
            selected_peers = level2_query
        else:
            peer_level = "INSUFFICIENT_DATA"

    peer_count = len(selected_peers)
    sufficient_peers = (peer_count >= MIN_PEER_COUNT)

    if not sufficient_peers:
        return {
            "district": district,
            "project_type": project_type,
            "peer_level": "INSUFFICIENT_DATA",
            "peer_count": peer_count,
            "sufficient_peers": False,
            "sanctioned_amount": None,
            "expenditure": None,
            "timeline": None,
            "progress": None,
            "peer_projects": [
                {
                    "project_id": p.project_id,
                    "district": p.district,
                    "project_type": p.project_type,
                    "sanctioned_amount": float(p.sanctioned_amount),
                    "expenditure": float(p.expenditure),
                    "progress_percent": p.progress_percent,
                    "status": p.status
                } for p in selected_peers
            ],
            "note": f"Insufficient peer records (found {peer_count}, minimum required: {MIN_PEER_COUNT}). Baseline calculation suspended."
        }

    # Extract series for statistical calculation
    sanctioned_vals = [p.sanctioned_amount for p in selected_peers]
    expenditure_vals = [p.expenditure for p in selected_peers]
    progress_vals = [p.progress_percent for p in selected_peers]

    duration_days_list = []
    for p in selected_peers:
        if p.sanction_date and p.expected_completion_date:
            dur = (p.expected_completion_date - p.sanction_date).days
            if dur > 0:
                duration_days_list.append(dur)

    sanctioned_stats = calculate_robust_stats(sanctioned_vals)
    expenditure_stats = calculate_robust_stats(expenditure_vals)

    timeline_summary = None
    if duration_days_list:
        timeline_summary = {
            "median_expected_days": round(float(np.median(duration_days_list)), 1),
            "records_used": len(duration_days_list)
        }

    progress_summary = None
    clean_prog = [v for v in progress_vals if v is not None and not pd.isna(v)]
    if clean_prog:
        progress_summary = {
            "median_percent": round(float(np.median(clean_prog)), 1),
            "records_used": len(clean_prog)
        }

    peer_projects_list = [
        {
            "project_id": p.project_id,
            "district": p.district,
            "project_type": p.project_type,
            "sanctioned_amount": float(p.sanctioned_amount),
            "expenditure": float(p.expenditure),
            "progress_percent": p.progress_percent,
            "status": p.status
        } for p in selected_peers
    ]

    note_text = "Baseline calculated from exact district and project type cohort."
    if peer_level == "TYPE_ONLY_FALLBACK":
        note_text = "Exact district peers were insufficient. Baseline uses same project type across available districts."

    return {
        "district": district,
        "project_type": project_type,
        "peer_level": peer_level,
        "peer_count": peer_count,
        "sufficient_peers": True,
        "sanctioned_amount": sanctioned_stats,
        "expenditure": expenditure_stats,
        "timeline": timeline_summary,
        "progress": progress_summary,
        "peer_projects": peer_projects_list,
        "note": note_text
    }

def compare_project_against_peers(
    project_id: str, 
    db: Session
) -> Dict[str, Any]:
    """
    Compares a single project against its peer baseline and returns neutral review comparison indicators.
    """
    target = db.query(Project).filter(Project.project_id.ilike(project_id.strip())).first()
    if not target:
        raise ValueError(f"Project ID '{project_id}' not found in database.")

    # Calculate baseline for target's district & project_type
    baseline = get_peer_baseline(target.district, target.project_type, db)

    t_exp = float(target.expenditure)
    t_sanc = float(target.sanctioned_amount)

    comparison_details = {
        "expenditure_vs_peer_median_percent": None,
        "expenditure_outside_expected_range": False,
        "sanctioned_outside_expected_range": False,
        "cost_variance_ratio": round((t_exp / t_sanc), 2) if t_sanc > 0 else 1.0
    }

    interpretation = "Project metrics align with expected peer baseline limits."

    if baseline["sufficient_peers"] and baseline["expenditure"]:
        exp_stats = baseline["expenditure"]
        exp_median = exp_stats["median"]
        
        if exp_median > 0:
            pct_diff = round(((t_exp - exp_median) / exp_median) * 100, 1)
            comparison_details["expenditure_vs_peer_median_percent"] = pct_diff

        is_outside = (t_exp < exp_stats["lower_bound"]) or (t_exp > exp_stats["upper_bound"])
        comparison_details["expenditure_outside_expected_range"] = is_outside

        if is_outside:
            interpretation = "Expenditure is outside the current peer range. This is a review indicator, not a fraud conclusion."
    elif not baseline["sufficient_peers"]:
        interpretation = "Insufficient peer records available for reliable range comparison."

    return {
        "project_id": target.project_id,
        "project_name": target.project_name,
        "district": target.district,
        "project_type": target.project_type,
        "sanctioned_amount": t_sanc,
        "expenditure": t_exp,
        "progress_percent": target.progress_percent,
        "peer_level_used": baseline["peer_level"],
        "peer_count": baseline["peer_count"],
        "comparison": comparison_details,
        "interpretation": interpretation
    }
