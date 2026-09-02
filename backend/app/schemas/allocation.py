"""Allocation Pydantic schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DistributeRequest(BaseModel):
    dataset_id: str
    agent_ids: List[str]
    records_per_agent: Optional[int] = None
    strategy: str = Field(
        default="overlap_minimization",
        description="Allocation strategy: overlap_minimization, implicit_random, zero_overlap"
    )
    canary_injection_rate: float = Field(
        default=0.03,
        ge=0.0,
        le=0.20,
        description="Fraction of synthetic honeytokens to embed (0.0 to 0.20)"
    )
    canary_type: str = "smart_honeytoken"


class AgentAllocationDetail(BaseModel):
    agent_id: str
    agent_name: str
    total_records: int
    genuine_records_count: int
    canary_records_count: int
    canary_tokens: List[str]
    download_url: Optional[str] = None


class DistributeResponse(BaseModel):
    allocation_id: str
    dataset_id: str
    strategy_used: str
    canary_injection_rate: float
    total_unique_records_allocated: int
    average_pairwise_overlap: float
    total_canaries_injected: int
    allocations: Dict[str, AgentAllocationDetail]
    created_at: Any
