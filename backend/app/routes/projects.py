from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectResponse, ProjectCountResponse

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
def get_all_projects(db: Session = Depends(get_db)):
    """
    Retrieve all controlled sample project records stored in prototype database.
    """
    projects = db.query(Project).all()
    return projects

@router.get("/count", response_model=ProjectCountResponse)
def get_project_count(db: Session = Depends(get_db)):
    """
    Return total count of controlled sample projects in prototype database.
    """
    count = db.query(Project).count()
    return {
        "total_projects": count,
        "environment": "SIH Prototype"
    }

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_by_id(project_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific project record by its unique project_id string.
    """
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project ID '{project_id}' not found in prototype database"
        )
    return project
