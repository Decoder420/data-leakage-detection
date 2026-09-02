"""Allocation and AgentAllocation SQLAlchemy models."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(String(64), primary_key=True, index=True)
    dataset_id = Column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy = Column(String(100), default="overlap_minimization")
    canary_injection_rate = Column(Float, default=0.03)
    records_per_agent = Column(Integer, nullable=True)
    total_unique_records = Column(Integer, default=0)
    average_pairwise_overlap = Column(Float, default=0.0)
    total_canaries_injected = Column(Integer, default=0)
    meta_info = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    dataset = relationship("Dataset", back_populates="allocations")
    agent_allocations = relationship("AgentAllocation", back_populates="allocation", cascade="all, delete-orphan")


class AgentAllocation(Base):
    __tablename__ = "agent_allocations"

    id = Column(String(64), primary_key=True, index=True)
    allocation_id = Column(String(64), ForeignKey("allocations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    total_records = Column(Integer, default=0)
    genuine_records_count = Column(Integer, default=0)
    canary_records_count = Column(Integer, default=0)
    allocated_record_hashes = Column(JSON, default=list)
    canary_tokens = Column(JSON, default=list)
    export_file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    allocation = relationship("Allocation", back_populates="agent_allocations")
    agent = relationship("Agent", back_populates="allocations")
