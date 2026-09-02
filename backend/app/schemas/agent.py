"""Agent & Vendor Pydantic schemas."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    name: str
    organization: str
    contact_email: str
    risk_level: str = "Medium"  # Low, Medium, High, Critical
    trust_score: float = Field(default=85.0, ge=0.0, le=100.0)
    notes: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    organization: Optional[str] = None
    contact_email: Optional[str] = None
    risk_level: Optional[str] = None
    trust_score: Optional[float] = None
    notes: Optional[str] = None


class AgentResponse(AgentBase):
    id: str
    is_active: bool
    created_at: Any

    class Config:
        from_attributes = True
