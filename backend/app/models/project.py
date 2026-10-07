from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Numeric
from sqlalchemy.sql import func
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(String(50), unique=True, index=True, nullable=False)
    project_name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    project_type = Column(String(100), nullable=False, index=True)
    sanctioned_amount = Column(Numeric(12, 2), nullable=False)
    expenditure = Column(Numeric(12, 2), nullable=False)
    sanction_date = Column(Date, nullable=False)
    expected_completion_date = Column(Date, nullable=False)
    actual_completion_date = Column(Date, nullable=True)
    progress_percent = Column(Float, nullable=False, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="In Progress")
    supporting_document = Column(String(255), nullable=True)
    data_source = Column(String(50), nullable=False, default="CONTROLLED_TEST")
    import_batch_id = Column(String(100), nullable=True)
    audit_status = Column(String(50), nullable=False, default="Not In Queue")
    review_priority = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
