"""LeakAnalysis and AgentGuiltScoreRecord SQLAlchemy models."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class LeakAnalysis(Base):
    __tablename__ = "leak_analyses"

    id = Column(String(64), primary_key=True, index=True)
    dataset_id = Column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    leak_source_name = Column(String(255), default="Dark Web Leak Dump")
    status = Column(String(50), default="COMPLETED")  # PENDING, PROCESSING, COMPLETED, FAILED
    progress = Column(Float, default=1.0)
    total_leaked_records = Column(Integer, default=0)
    matched_leaked_records = Column(Integer, default=0)
    unmatched_leaked_records = Column(Integer, default=0)
    canary_hits_total = Column(Integer, default=0)
    independent_leak_prob_p = Column(Float, default=0.05)
    
    top_suspect_id = Column(String(64), nullable=True)
    top_suspect_name = Column(String(255), nullable=True)
    highest_probability = Column(Float, default=0.0)
    canary_confirmed_agent_id = Column(String(64), nullable=True)
    
    overlap_matrix = Column(JSON, default=dict)
    summary_verdict = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    dataset = relationship("Dataset", back_populates="analyses")
    guilt_scores = relationship("AgentGuiltScoreRecord", back_populates="analysis", cascade="all, delete-orphan")


class AgentGuiltScoreRecord(Base):
    __tablename__ = "agent_guilt_scores"

    id = Column(String(64), primary_key=True, index=True)
    analysis_id = Column(String(64), ForeignKey("leak_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)
    guilt_probability = Column(Float, default=0.0)
    matching_records_count = Column(Integer, default=0)
    matching_genuine_count = Column(Integer, default=0)
    canary_records_found = Column(Integer, default=0)
    triggered_canary_tokens = Column(JSON, default=list)
    verdict = Column(String(64), default="CLEARED")
    explanation = Column(Text, nullable=True)

    analysis = relationship("LeakAnalysis", back_populates="guilt_scores")
