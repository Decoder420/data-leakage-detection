"""Leak Analysis & Guilt Attribution schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    dataset_id: str
    leaked_records: List[Dict[str, Any]]
    leak_source_name: Optional[str] = "Dark Web Breach Dump"
    independent_leak_prob_p: float = Field(default=0.05, ge=0.001, le=0.999)


class AgentScoreSchema(BaseModel):
    agent_id: str
    agent_name: str
    guilt_probability: float
    matching_records_count: int
    matching_genuine_count: int
    canary_records_found: int
    triggered_canary_tokens: List[str]
    verdict: str  # CONFIRMED_LEAKER, HIGH_SUSPICION, MODERATE_SUSPICION, UNLIKELY, CLEARED
    explanation: str


class AnalyzeResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    leak_source_name: str
    status: str
    total_leaked_records: int
    matched_leaked_records: int
    unmatched_leaked_records: int
    canary_hits_total: int
    independent_leak_prob_p: float
    top_suspect_id: Optional[str]
    top_suspect_name: Optional[str]
    highest_probability: float
    canary_confirmed_agent_id: Optional[str]
    agent_scores: List[AgentScoreSchema]
    overlap_matrix: Dict[str, Dict[str, int]]
    created_at: Any
