from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class BaselineOptionsResponse(BaseModel):
    districts: List[str]
    project_types: List[str]

class StatsSummary(BaseModel):
    median: float
    q1: float
    q3: float
    iqr: float
    lower_bound: float
    upper_bound: float
    records_used: int

class TimelineSummary(BaseModel):
    median_expected_days: float
    records_used: int

class ProgressSummary(BaseModel):
    median_percent: float
    records_used: int

class BaselineResponse(BaseModel):
    district: str
    project_type: str
    peer_level: str  # DISTRICT_AND_TYPE, TYPE_ONLY_FALLBACK, INSUFFICIENT_DATA
    peer_count: int
    sufficient_peers: bool
    sanctioned_amount: Optional[StatsSummary] = None
    expenditure: Optional[StatsSummary] = None
    timeline: Optional[TimelineSummary] = None
    progress: Optional[ProgressSummary] = None
    peer_projects: List[Dict[str, Any]] = []
    note: str

class ProjectComparisonResponse(BaseModel):
    project_id: str
    project_name: str
    district: str
    project_type: str
    sanctioned_amount: float
    expenditure: float
    progress_percent: float
    peer_level_used: str
    peer_count: int
    comparison: Dict[str, Any]
    interpretation: str
