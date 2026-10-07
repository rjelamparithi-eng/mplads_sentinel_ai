import math
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.project import Project
from app.services.anomaly_service import evaluate_project_anomaly
from app.services.text_similarity_service import (
    compute_project_text_similarity_matrix,
    calculate_pair_similarity,
    determine_relationship_status
)

router = APIRouter(prefix="/api/spatial", tags=["Spatial Intelligence"])

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance between two lat/long points in meters using Haversine formula."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

@router.get("/projects")
def get_spatial_projects(
    radius_meters: float = Query(1000.0),
    db: Session = Depends(get_db)
):
    """
    Returns mapped projects with valid coordinates, computing TF-IDF text similarity + Haversine geographic distance.
    """
    all_projects = db.query(Project).all()
    valid_mapped = []
    for p in all_projects:
        try:
            if p.latitude is not None and p.longitude is not None:
                lat, lon = float(p.latitude), float(p.longitude)
                if not math.isnan(lat) and not math.isnan(lon):
                    valid_mapped.append(p)
        except Exception:
            continue

    try:
        pid_to_idx, sim_matrix = compute_project_text_similarity_matrix(valid_mapped)
    except Exception:
        pid_to_idx, sim_matrix = {}, None

    from app.ml.isolation_forest_service import run_isolation_forest_pipeline
    try:
        ml_map = run_isolation_forest_pipeline(db)
    except Exception:
        ml_map = {}

    features = []
    proximity_pairs = []

    for i, p in enumerate(valid_mapped):
        try:
            eval_res = evaluate_project_anomaly(p, db, ml_signal=ml_map.get(p.project_id, "UNAVAILABLE"))
            rev_sev = eval_res.get("review_severity", "Normal")
        except Exception:
            rev_sev = "Normal"

        nearby_candidates = []
        for j, other in enumerate(valid_mapped):
            if i != j:
                try:
                    dist = haversine_distance_meters(float(p.latitude), float(p.longitude), float(other.latitude), float(other.longitude))
                except Exception:
                    continue

                text_sim = 0.0
                if sim_matrix is not None:
                    try:
                        text_sim = calculate_pair_similarity(p, other, pid_to_idx, sim_matrix)
                    except Exception:
                        text_sim = 0.0

                sim_pct = round(text_sim * 100.0, 1)
                rel_label, note = determine_relationship_status(dist, radius_meters, text_sim)

                if dist <= radius_meters:
                    nearby_candidates.append({
                        "other_project_id": other.project_id,
                        "other_project_name": other.project_name,
                        "distance_meters": round(dist, 1),
                        "text_similarity_score": text_sim,
                        "text_similarity_percent": sim_pct,
                        "similarity_status": rel_label,
                        "relationship_status": rel_label,
                        "note": note
                    })
                    if i < j:
                        proximity_pairs.append({
                            "project_1": p.project_id,
                            "project_2": other.project_id,
                            "distance_meters": round(dist, 1),
                            "text_similarity_score": text_sim,
                            "text_similarity_percent": sim_pct,
                            "relationship_status": rel_label,
                            "note": note
                        })

        features.append({
            "project_id": p.project_id,
            "project_name": p.project_name,
            "district": p.district,
            "project_type": p.project_type,
            "latitude": float(p.latitude),
            "longitude": float(p.longitude),
            "sanctioned_amount": float(p.sanctioned_amount),
            "expenditure": float(p.expenditure),
            "review_priority": rev_sev,
            "data_source": p.data_source or "CONTROLLED_TEST",
            "nearby_candidates": nearby_candidates
        })

    return {
        "total_mapped_projects": len(features),
        "radius_meters_used": radius_meters,
        "features": features,
        "proximity_pairs": proximity_pairs,
        "note": "Spatial intelligence combines Haversine geographic distance with TF-IDF text similarity."
    }
