from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ValidationIssue(BaseModel):
    row_number: int
    project_id: Optional[str] = None
    field: str
    issue_type: str  # MISSING_FIELD, INVALID_VALUE, DUPLICATE_ID, WARNING_MISSING_OPTIONAL
    message: str

class PreviewRow(BaseModel):
    row_number: int
    status: str  # VALID, WARNING, REJECTED
    data: Dict[str, Any]
    issues: List[ValidationIssue] = []

class IngestionPreviewResponse(BaseModel):
    dataset_type: str  # CONTROLLED_TEST or PUBLIC_MPLADS_DERIVED
    filename: str
    rows_received: int
    valid_rows: int
    warning_rows: int
    rejected_rows: int
    duplicate_rows: int
    missing_values: int
    clean_preview: List[PreviewRow]
    issues: List[ValidationIssue]

class IngestionCommitRequest(BaseModel):
    dataset_type: Optional[str] = "CONTROLLED_TEST"
    records: List[Dict[str, Any]]
    data_source: Optional[str] = "CONTROLLED_TEST"

class IngestionCommitResponse(BaseModel):
    inserted: int
    skipped_duplicates: int
    rejected: int
    batch_id: str
