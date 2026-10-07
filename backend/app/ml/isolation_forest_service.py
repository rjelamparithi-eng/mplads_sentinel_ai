import numpy as np
import pandas as pd
from datetime import date
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.baseline_service import get_peer_baseline

def extract_project_features(project: Project, db: Session) -> Optional[List[float]]:
    """
    Extracts 4 quantitative features for Isolation Forest:
    1. expenditure_ratio = expenditure / sanctioned_amount
    2. peer_deviation_percent = (expenditure - peer_median) / peer_median * 100
    3. delay_days = days delayed past expected_completion_date (0 if not delayed)
    4. progress_percent
    """
    try:
        t_sanc = float(project.sanctioned_amount) if project.sanctioned_amount is not None else 0.0
        t_exp = float(project.expenditure) if project.expenditure is not None else 0.0

        # Feature 1: expenditure_ratio (handle division by zero safely)
        if t_sanc > 0:
            expenditure_ratio = float(t_exp / t_sanc)
        else:
            expenditure_ratio = 1.0

        # Feature 2: peer_deviation_percent
        baseline = get_peer_baseline(project.district, project.project_type, db)
        if baseline.get("sufficient_peers") and baseline.get("expenditure") and baseline["expenditure"].get("median", 0) > 0:
            peer_median = float(baseline["expenditure"]["median"])
            peer_deviation_percent = float(((t_exp - peer_median) / peer_median) * 100.0)
        else:
            peer_deviation_percent = 0.0

        # Feature 3: delay_days
        today = date.today()
        delay_days = 0.0
        if project.status == "In Progress" and project.expected_completion_date:
            if today > project.expected_completion_date:
                delay_days = float((today - project.expected_completion_date).days)
        elif project.status == "Completed" and project.actual_completion_date and project.expected_completion_date:
            if project.actual_completion_date > project.expected_completion_date:
                delay_days = float((project.actual_completion_date - project.expected_completion_date).days)

        # Feature 4: progress_percent
        progress_pct = float(project.progress_percent) if project.progress_percent is not None else 0.0

        # Clean NaN or infinity to safe defaults
        feats = [expenditure_ratio, peer_deviation_percent, delay_days, progress_pct]
        cleaned_feats = []
        for f in feats:
            if np.isnan(f) or np.isinf(f):
                cleaned_feats.append(0.0)
            else:
                cleaned_feats.append(float(f))

        return cleaned_feats
    except Exception:
        return [1.0, 0.0, 0.0, 0.0]


def run_isolation_forest_pipeline(db: Session) -> Dict[str, str]:
    """
    Fits scikit-learn IsolationForest on current valid project records in database.
    Returns dictionary mapping project_id -> 'NORMAL' | 'ML_ANOMALY' | 'UNAVAILABLE'.
    Safely falls back to 'UNAVAILABLE' if ML computation error occurs or dataset too small.
    """
    try:
        projects = db.query(Project).all()
        if not projects:
            return {}

        if len(projects) < 5:
            # Insufficient dataset size for ML fitting; fall back to rule-based evaluation
            return {p.project_id: "UNAVAILABLE" for p in projects}

        valid_pids = []
        feature_matrix = []

        for p in projects:
            feats = extract_project_features(p, db)
            if feats is not None and len(feats) == 4:
                valid_pids.append(p.project_id)
                feature_matrix.append(feats)

        if len(feature_matrix) < 5:
            return {p.project_id: "UNAVAILABLE" for p in projects}

        X = np.array(feature_matrix, dtype=float)

        # Ensure no NaN / infinity entered matrix
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        # Fit IsolationForest model
        model = IsolationForest(
            n_estimators=100,
            contamination=0.15,
            random_state=42
        )

        preds = model.fit_predict(X)
        # IsolationForest output: 1 = inlier ('NORMAL'), -1 = outlier ('ML_ANOMALY')

        results = {}
        for pid, pred in zip(valid_pids, preds):
            results[pid] = "ML_ANOMALY" if pred == -1 else "NORMAL"

        for p in projects:
            if p.project_id not in results:
                results[p.project_id] = "UNAVAILABLE"

        return results
    except Exception:
        # Fallback gracefully if any ML error occurs
        try:
            return {p.project_id: "UNAVAILABLE" for p in db.query(Project).all()}
        except Exception:
            return {}


