import re
import numpy as np
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.project import Project

def normalize_text(text: str) -> str:
    """Normalizes project description text by converting to lowercase and stripping punctuation/extra whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def compute_project_text_similarity_matrix(projects: List[Project]) -> Tuple[Dict[str, int], np.ndarray]:
    """
    Computes TF-IDF vector representations and pairwise Cosine Similarity matrix for given list of projects.
    Returns tuple of (project_id_to_index_map, cosine_similarity_matrix).
    """
    if not projects:
        return {}, np.zeros((0, 0))

    pid_to_idx = {p.project_id: i for i, p in enumerate(projects)}
    corpus = []

    for p in projects:
        # Combine project_name + project_type for TF-IDF feature extraction
        combined_text = f"{p.project_name or ''} {p.project_type or ''}"
        corpus.append(normalize_text(combined_text))

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
        sim_matrix = cosine_similarity(tfidf_matrix)
    except Exception:
        # Fallback if corpus is empty or invalid
        n = len(projects)
        sim_matrix = np.eye(n)

    return pid_to_idx, sim_matrix

def calculate_pair_similarity(
    p1: Project, 
    p2: Project, 
    pid_to_idx: Dict[str, int], 
    sim_matrix: np.ndarray
) -> float:
    """Returns pairwise cosine similarity score between 0.0 and 1.0."""
    try:
        idx1 = pid_to_idx[p1.project_id]
        idx2 = pid_to_idx[p2.project_id]
        score = float(sim_matrix[idx1, idx2])
        return min(1.0, max(0.0, round(score, 4)))
    except Exception:
        return 0.0

def determine_relationship_status(
    distance_meters: float, 
    radius_meters: float, 
    text_sim_score: float
) -> Tuple[str, str]:
    """
    Combines geographic Haversine distance + TF-IDF Cosine text similarity.
    Returns (relationship_status_label, explanatory_note).
    Uses strictly neutral terminology — no fraud conclusions.
    """
    within_radius = (distance_meters <= radius_meters)
    sim_percent = round(text_sim_score * 100, 1)

    if within_radius and text_sim_score >= 0.40:
        label = "Possible Overlap Candidate — Verification Required"
        note = f"High description similarity ({sim_percent}%) within {round(distance_meters, 0)}m distance radius. Field inspection recommended to verify physical boundaries."
    elif within_radius:
        label = "Geographic Proximity Candidate — Verification Required"
        note = f"Projects located within {round(distance_meters, 0)}m distance radius with {sim_percent}% description similarity."
    elif text_sim_score >= 0.50:
        label = "Similar Work Description — Separate Location"
        note = f"High description similarity ({sim_percent}%) but separated by {round(distance_meters / 1000.0, 1)}km."
    else:
        label = "Isolated Location"
        note = f"Distance {round(distance_meters, 0)}m, description similarity {sim_percent}%."

    return label, note
