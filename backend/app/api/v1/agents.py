"""Agents API — Third-Party Vendor Registry."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_auth
from backend.app.models.agent import Agent
from backend.app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse

router = APIRouter(prefix="/agents", tags=["Agents & Vendors"])


@router.get("", response_model=List[AgentResponse], summary="List All Third-Party Agents")
def list_agents(db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    return db.query(Agent).filter(Agent.is_active == True).order_by(Agent.created_at.desc()).all()


@router.post("", response_model=AgentResponse, summary="Register New Agent / Vendor")
def create_agent(
    req: AgentCreate,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    agent_id = f"AGT-{uuid.uuid4().hex[:6].upper()}"
    agent = Agent(
        id=agent_id,
        name=req.name,
        organization=req.organization,
        contact_email=req.contact_email,
        risk_level=req.risk_level,
        trust_score=req.trust_score,
        notes=req.notes
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse, summary="Get Single Agent")
def get_agent(agent_id: str, db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse, summary="Update Agent")
def update_agent(
    agent_id: str,
    req: AgentUpdate,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(agent, field, val)
        
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}", summary="Delete / Deactivate Agent")
def delete_agent(agent_id: str, db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.is_active = False
    db.commit()
    return {"status": "success", "message": f"Agent {agent_id} deactivated"}
