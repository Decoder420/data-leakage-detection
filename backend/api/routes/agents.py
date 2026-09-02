"""Agent & Vendor registry API endpoints."""

import uuid
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.engine.models import Agent
from backend.api.state import state

router = APIRouter(prefix="/api/agents", tags=["Agents"])


class CreateAgentRequest(BaseModel):
    name: str
    organization: str
    contact_email: str
    risk_level: str = "Medium"
    trust_score: float = 85.0


@router.get("", response_model=List[Agent])
def list_agents():
    """List all registered third-party agents and vendors."""
    return list(state.agents.values())


@router.post("", response_model=Agent)
def create_agent(req: CreateAgentRequest):
    """Register a new third-party agent/vendor."""
    new_id = f"AGT-{uuid.uuid4().hex[:6].upper()}"
    agent = Agent(
        id=new_id,
        name=req.name,
        organization=req.organization,
        contact_email=req.contact_email,
        risk_level=req.risk_level,
        trust_score=req.trust_score
    )
    state.agents[new_id] = agent
    return agent


@router.get("/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    """Get single agent details."""
    if agent_id not in state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return state.agents[agent_id]


@router.put("/{agent_id}", response_model=Agent)
def update_agent(agent_id: str, req: CreateAgentRequest):
    """Update agent risk level and trust rating."""
    if agent_id not in state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    existing = state.agents[agent_id]
    existing.name = req.name
    existing.organization = req.organization
    existing.contact_email = req.contact_email
    existing.risk_level = req.risk_level
    existing.trust_score = req.trust_score
    return existing


@router.delete("/{agent_id}")
def delete_agent(agent_id: str):
    """Remove an agent from the registry."""
    if agent_id not in state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    del state.agents[agent_id]
    return {"status": "success", "message": f"Agent {agent_id} removed"}
