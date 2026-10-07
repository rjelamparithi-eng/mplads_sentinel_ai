from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.baseline import (
    BaselineOptionsResponse,
    BaselineResponse,
    ProjectComparisonResponse
)
from app.services.baseline_service import (
    get_baseline_filter_options,
    get_peer_baseline,
    compare_project_against_peers
)

router = APIRouter(prefix="/api/baselines", tags=["Rules & Peer Baselines"])

@router.get("/options", response_model=BaselineOptionsResponse)
def get_baseline_options(db: Session = Depends(get_db)):
    """
    Returns distinct list of districts and project types stored in prototype database.
    """
    return get_baseline_filter_options(db)

@router.get("", response_model=BaselineResponse)
def compute_baseline(
    district: str = Query(..., example="Erode"),
    project_type: str = Query(..., example="Road"),
    db: Session = Depends(get_db)
):
    """
    Computes robust statistical peer baselines for the given district and project type.
    """
    if not district or not project_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'district' and 'project_type' query parameters are required."
        )

    return get_peer_baseline(district, project_type, db)

@router.get("/project/{project_id}", response_model=ProjectComparisonResponse)
def compare_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Compares a specific project against its relevant peer group and returns review indicators.
    """
    try:
        return compare_project_against_peers(project_id, db)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
