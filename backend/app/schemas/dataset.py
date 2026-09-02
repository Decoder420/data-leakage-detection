"""Dataset Pydantic schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def get_utc_iso():
    return datetime.now(timezone.utc).isoformat()


class DatasetBase(BaseModel):
    name: str
    category: str = "Fintech"
    description: Optional[str] = None


class DatasetCreate(DatasetBase):
    pass


class DatasetGenerateRequest(BaseModel):
    name: str = "Enterprise Banking Master PII"
    category: str = "Fintech"  # Fintech, Healthcare, Enterprise HR, E-Commerce
    num_records: int = Field(default=100, ge=10, le=5000)


class DatasetResponse(DatasetBase):
    id: str
    total_records: int
    columns: List[str]
    created_at: Any

    class Config:
        from_attributes = True


class DatasetDetailResponse(DatasetResponse):
    sample_records: List[Dict[str, Any]]
