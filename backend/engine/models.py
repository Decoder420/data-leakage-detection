"""Pydantic data models for Data Leakage Detection & Attribution System."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def get_utc_iso():
    return datetime.now(timezone.utc).isoformat()


class Agent(BaseModel):
    id: str
    name: str
    organization: str
    contact_email: str
    risk_level: str = "Medium"  # Low, Medium, High, Critical
    trust_score: float = Field(default=85.0, ge=0.0, le=100.0)
    created_at: str = Field(default_factory=get_utc_iso)


class DatasetRecord(BaseModel):
    id: str
    data: Dict[str, Any]
    is_canary: bool = False
    canary_agent_id: Optional[str] = None
    canary_token: Optional[str] = None


class DatasetMeta(BaseModel):
    id: str
    name: str
    category: str  # Fintech, Healthcare, Enterprise HR, E-Commerce
    description: str
    total_records: int
    columns: List[str]
    created_at: str = Field(default_factory=get_utc_iso)


class AllocationConfig(BaseModel):
    dataset_id: str
    agent_ids: List[str]
    records_per_agent: Optional[int] = None
    allocation_strategy: str = "overlap_minimization"  # random, overlap_minimization, zero_overlap
    canary_injection_rate: float = Field(default=0.03, ge=0.0, le=0.20)  # 0% to 20%
    canary_type: str = "smart_honeytoken"  # smart_honeytoken, trap_email, api_key


class AgentAllocation(BaseModel):
    agent_id: str
    agent_name: str
    total_records: int
    genuine_records_count: int
    canary_records_count: int
    allocated_record_ids: List[str]
    canary_tokens: List[str]
    allocated_at: str = Field(default_factory=get_utc_iso)


class AllocationResult(BaseModel):
    allocation_id: str
    dataset_id: str
    strategy_used: str
    allocations: Dict[str, AgentAllocation]
    total_unique_records_allocated: int
    average_pairwise_overlap: float
    total_canaries_injected: int
    created_at: str = Field(default_factory=get_utc_iso)


class LeakAnalysisRequest(BaseModel):
    dataset_id: str
    leaked_records: List[Dict[str, Any]]
    leak_source_name: Optional[str] = "Dark Web Forum Leak"
    independent_leak_prob_p: float = Field(default=0.1, ge=0.001, le=0.999)


class AgentGuiltScore(BaseModel):
    agent_id: str
    agent_name: str
    guilt_probability: float  # 0.0 to 1.0 (or percentage)
    matching_records_count: int
    matching_genuine_count: int
    canary_records_found: int
    triggered_canary_tokens: List[str]
    verdict: str  # "CONFIRMED_LEAKER", "HIGH_SUSPICION", "MODERATE_SUSPICION", "UNLIKELY", "CLEARED"
    explanation: str


class RecordOverlapDetail(BaseModel):
    record_id: str
    is_canary: bool
    canary_owner: Optional[str] = None
    present_in_leak: bool
    allocated_to_agents: List[str]


class LeakAnalysisResult(BaseModel):
    analysis_id: str
    dataset_id: str
    leak_source_name: str
    total_leaked_records: int
    matched_leaked_records: int
    unmatched_leaked_records: int
    canary_hits_total: int
    independent_leak_prob_p: float
    agent_scores: List[AgentGuiltScore]
    top_suspect_id: Optional[str]
    top_suspect_name: Optional[str]
    highest_probability: float
    canary_confirmed_agent_id: Optional[str]
    overlap_matrix: Dict[str, Dict[str, int]]
    analyzed_at: str = Field(default_factory=get_utc_iso)


class SimulationRequest(BaseModel):
    dataset_id: str
    scenario: str = "single_agent_leak"  # "single_agent_leak", "two_agent_collusion", "noisy_darkweb_leak", "subsample_leak"
    target_agent_id: Optional[str] = None
    target_agent_ids: Optional[List[str]] = None
    leak_percentage: float = Field(default=0.6, ge=0.05, le=1.0)
    noise_records_count: int = Field(default=5, ge=0, le=50)


class MonteCarloRequest(BaseModel):
    dataset_id: str
    iterations: int = Field(default=50, ge=10, le=200)
    canary_rates: List[float] = [0.0, 0.02, 0.05, 0.10]
    leak_percentage: float = 0.5
