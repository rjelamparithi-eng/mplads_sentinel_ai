from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

class ProjectBase(BaseModel):
    project_id: str = Field(..., example="ERD-ROAD-001")
    project_name: str = Field(..., example="Construction of Bituminous Road at Perundurai")
    district: str = Field(..., example="Erode")
    project_type: str = Field(..., example="Road")
    sanctioned_amount: float = Field(..., example=2500000.00)
    expenditure: float = Field(..., example=2450000.00)
    sanction_date: date
    expected_completion_date: date
    actual_completion_date: Optional[date] = None
    progress_percent: float = Field(..., ge=0.0, le=100.0, example=100.0)
    latitude: Optional[float] = Field(None, example=11.2750)
    longitude: Optional[float] = Field(None, example=77.5833)
    status: str = Field("In Progress", example="Completed")
    supporting_document: Optional[str] = Field(None, example="completion_cert_erd001.pdf")
    data_source: Optional[str] = Field("CONTROLLED_TEST", example="CONTROLLED_TEST")
    import_batch_id: Optional[str] = Field(None, example="BATCH-20260906-001")
    audit_status: Optional[str] = Field("Pending Review", example="Pending Review")
    review_priority: Optional[str] = Field("Normal", example="High Review Priority")

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectCountResponse(BaseModel):
    total_projects: int
    environment: str = "SIH Prototype"
