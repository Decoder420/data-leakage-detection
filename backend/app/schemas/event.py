"""Standard Security Event Schema for DecodeX SOC and SIEM Interoperability."""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def get_utc_iso():
    return datetime.now(timezone.utc).isoformat()


class SecurityEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier (e.g. evt_01HZX...)")
    event_type: Literal[
        "guilt_detection",
        "canary_triggered",
        "leak_analysis_complete",
        "high_risk_allocation"
    ] = Field(..., description="Standardized security event category")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Event threat severity rating"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Attribution confidence score between 0.0 and 1.0"
    )
    source_dataset: str = Field(..., description="Name or identifier of source compromised dataset")
    implicated_agent: Optional[str] = Field(None, description="Name or identifier of attributed suspect vendor")
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Forensic evidentiary breakdown including matched rows and canary hashes"
    )
    timestamp: str = Field(default_factory=get_utc_iso, description="ISO8601 UTC timestamp")


class SecurityEventFilter(BaseModel):
    event_type: Optional[str] = None
    severity: Optional[str] = None
    implicated_agent: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
