from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Numeric, Boolean
from sqlalchemy.sql import func
from app.database import Base

class PublicMpladsWork(Base):
    __tablename__ = "public_mplads_works"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    internal_record_key = Column(String(100), unique=True, index=True, nullable=False)
    mp_name = Column(String(255), nullable=True)
    work_description = Column(String(500), nullable=True)
    normalized_work = Column(String(255), nullable=True)
    source_category = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True, index=True)
    constituency = Column(String(100), nullable=True, index=True)
    implementing_district_authority = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    ward = Column(String(100), nullable=True)
    block = Column(String(100), nullable=True)
    village = Column(String(100), nullable=True)
    location_text = Column(String(500), nullable=True)
    recommended_date = Column(Date, nullable=True)
    recommended_amount = Column(Numeric(12, 2), nullable=True)
    ida_approval_status = Column(String(100), nullable=True)
    work_status = Column(String(100), nullable=True)
    house = Column(String(50), nullable=True)
    exact_source_duplicate = Column(Boolean, default=False)
    source_row_number = Column(Integer, nullable=True)
    data_quality_status = Column(String(100), nullable=True)
    data_source = Column(String(100), nullable=False, default="PUBLIC_MPLADS_DERIVED")
    import_batch_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
