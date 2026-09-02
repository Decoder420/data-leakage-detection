"""Dataset and DatasetRecord SQLAlchemy models."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="Fintech")  # Fintech, Healthcare, Enterprise HR
    description = Column(Text, nullable=True)
    total_records = Column(Integer, default=0)
    columns = Column(JSON, default=list)
    schema_meta = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    records = relationship("DatasetRecord", back_populates="dataset", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="dataset", cascade="all, delete-orphan")
    analyses = relationship("LeakAnalysis", back_populates="dataset", cascade="all, delete-orphan")


class DatasetRecord(Base):
    __tablename__ = "dataset_records"

    id = Column(String(64), primary_key=True, index=True)
    dataset_id = Column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    record_hash = Column(String(128), index=True, nullable=False)
    data = Column(JSON, nullable=False)
    is_canary = Column(Boolean, default=False, index=True)
    canary_agent_id = Column(String(64), nullable=True, index=True)
    canary_token = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    dataset = relationship("Dataset", back_populates="records")
