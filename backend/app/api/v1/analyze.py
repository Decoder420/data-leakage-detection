"""Analyze API — Probabilistic Guilt Attribution & Threat Alert Dispatch."""

import io
import csv
import json
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_auth
from backend.app.models.dataset import Dataset, DatasetRecord
from backend.app.models.agent import Agent
from backend.app.models.allocation import Allocation, AgentAllocation
from backend.app.models.leak_analysis import LeakAnalysis, AgentGuiltScoreRecord
from backend.app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, AgentScoreSchema
from backend.app.engine.guilt_calculator import compute_vectorized_guilt_probabilities
from backend.app.services.event_service import emit_security_event

router = APIRouter(prefix="/analyze", tags=["Leak Analysis & Attribution"])


def _extract_hashes_from_records(records: List[Dict[str, Any]]) -> List[str]:
    hashes = []
    for idx, r in enumerate(records):
        r_hash = r.get("id") or r.get("_record_id") or r.get("customer_id") or r.get("patient_id") or r.get("email")
        if r_hash:
            hashes.append(str(r_hash))
        else:
            # Hash values
            hashes.append(str(idx))
    return hashes


@router.post("", response_model=AnalyzeResponse, summary="Analyze Leaked Records (JSON)")
def analyze_leak_json(
    req: AnalyzeRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    allocations = db.query(AgentAllocation).join(Allocation).filter(Allocation.dataset_id == req.dataset_id).all()
    if not allocations:
        raise HTTPException(status_code=400, detail="No active allocation found for this dataset")

    agent_record_map = {a.agent_id: set(a.allocated_record_hashes) for a in allocations}
    
    # Canary map
    canary_records = db.query(DatasetRecord).filter(
        DatasetRecord.dataset_id == req.dataset_id,
        DatasetRecord.is_canary == True
    ).all()
    canary_ownership_map = {c.record_hash: c.canary_agent_id for c in canary_records if c.canary_agent_id}

    leaked_hashes = _extract_hashes_from_records(req.leaked_records)

    # Execute Vectorized Guilt Engine
    scores_dict = compute_vectorized_guilt_probabilities(
        leaked_record_hashes=leaked_hashes,
        agent_record_map=agent_record_map,
        canary_ownership_map=canary_ownership_map,
        independent_leak_prob_p=req.independent_leak_prob_p
    )

    analysis_id = f"LEAK-ANL-{uuid.uuid4().hex[:8].upper()}"
    agents = {a.id: a.name for a in db.query(Agent).all()}

    agent_scores_list = []
    top_suspect_id = None
    top_suspect_name = None
    highest_prob = 0.0
    canary_confirmed_agent_id = None
    total_canary_hits = 0

    for a_id, res in scores_dict.items():
        ag_name = agents.get(a_id, a_id)
        c_found = res["canary_records_found"]
        total_canary_hits += c_found
        prob = res["guilt_probability"]

        if c_found > 0:
            canary_confirmed_agent_id = a_id

        if prob > highest_prob or (c_found > 0 and highest_prob < 1.0):
            highest_prob = prob
            top_suspect_id = a_id
            top_suspect_name = ag_name

        agent_scores_list.append(AgentScoreSchema(
            agent_id=a_id,
            agent_name=ag_name,
            guilt_probability=prob,
            matching_records_count=res["matching_records_count"],
            matching_genuine_count=max(0, res["matching_records_count"] - c_found),
            canary_records_found=c_found,
            triggered_canary_tokens=res.get("triggered_canaries", []),
            verdict=res["verdict"],
            explanation=res["explanation"]
        ))

    agent_scores_list.sort(key=lambda s: (s.canary_records_found > 0, s.guilt_probability), reverse=True)

    # Compute overlap matrix between agents & leak
    overlap_matrix: Dict[str, Dict[str, int]] = {}
    leaked_set = set(leaked_hashes)
    for a1 in agent_record_map:
        overlap_matrix[a1] = {
            "LEAK_DUMP": len(agent_record_map[a1].intersection(leaked_set))
        }
        for a2 in agent_record_map:
            overlap_matrix[a1][a2] = len(agent_record_map[a1].intersection(agent_record_map[a2]))

    # Persist analysis
    analysis_db = LeakAnalysis(
        id=analysis_id,
        dataset_id=req.dataset_id,
        leak_source_name=req.leak_source_name or "Dark Web Forum",
        status="COMPLETED",
        progress=1.0,
        total_leaked_records=len(leaked_hashes),
        matched_leaked_records=sum(s.matching_records_count for s in agent_scores_list),
        unmatched_leaked_records=max(0, len(leaked_hashes) - sum(s.matching_records_count for s in agent_scores_list)),
        canary_hits_total=total_canary_hits,
        independent_leak_prob_p=req.independent_leak_prob_p,
        top_suspect_id=top_suspect_id,
        top_suspect_name=top_suspect_name,
        highest_probability=highest_prob,
        canary_confirmed_agent_id=canary_confirmed_agent_id,
        overlap_matrix=overlap_matrix,
        summary_verdict=agent_scores_list[0].explanation if agent_scores_list else "No suspects"
    )
    db.add(analysis_db)
    db.commit()
    db.refresh(analysis_db)

    # EMIT SECURITY EVENT & TRIGGER OUTBOUND ADAPTER (DecodeX SOC Integration)
    if canary_confirmed_agent_id:
        emit_security_event(
            event_type="canary_triggered",
            severity="critical",
            confidence_score=1.0,
            source_dataset=dataset.name,
            implicated_agent=f"{top_suspect_name} ({top_suspect_id})",
            evidence={
                "analysis_id": analysis_id,
                "canary_hits": total_canary_hits,
                "verdict": "CONFIRMED_LEAKER",
                "leak_source": req.leak_source_name
            },
            db=db
        )
    elif highest_prob >= 0.75:
        emit_security_event(
            event_type="guilt_detection",
            severity="high" if highest_prob >= 0.90 else "medium",
            confidence_score=highest_prob,
            source_dataset=dataset.name,
            implicated_agent=f"{top_suspect_name} ({top_suspect_id})",
            evidence={
                "analysis_id": analysis_id,
                "guilt_probability": highest_prob,
                "matched_rows": agent_scores_list[0].matching_records_count if agent_scores_list else 0,
                "verdict": agent_scores_list[0].verdict if agent_scores_list else "HIGH_SUSPICION"
            },
            db=db
        )

    return AnalyzeResponse(
        analysis_id=analysis_db.id,
        dataset_id=analysis_db.dataset_id,
        leak_source_name=analysis_db.leak_source_name,
        status=analysis_db.status,
        total_leaked_records=analysis_db.total_leaked_records,
        matched_leaked_records=analysis_db.matched_leaked_records,
        unmatched_leaked_records=analysis_db.unmatched_leaked_records,
        canary_hits_total=analysis_db.canary_hits_total,
        independent_leak_prob_p=analysis_db.independent_leak_prob_p,
        top_suspect_id=analysis_db.top_suspect_id,
        top_suspect_name=analysis_db.top_suspect_name,
        highest_probability=analysis_db.highest_probability,
        canary_confirmed_agent_id=analysis_db.canary_confirmed_agent_id,
        agent_scores=agent_scores_list,
        overlap_matrix=overlap_matrix,
        created_at=analysis_db.created_at
    )


@router.post("/file", response_model=AnalyzeResponse, summary="Upload & Analyze Leaked CSV File")
async def analyze_leak_file(
    dataset_id: str = Form(...),
    leak_source_name: str = Form("Dark Web Breach Dump"),
    independent_leak_prob_p: float = Form(0.05),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    contents = await file.read()
    filename = file.filename or "leak.csv"
    leaked_records = []

    try:
        if filename.endswith(".json"):
            leaked_records = json.loads(contents.decode("utf-8"))
        else:
            decoded = contents.decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded))
            leaked_records = [dict(row) for row in reader]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse leaked file: {str(e)}")

    req = AnalyzeRequest(
        dataset_id=dataset_id,
        leaked_records=leaked_records,
        leak_source_name=f"{leak_source_name} ({filename})",
        independent_leak_prob_p=independent_leak_prob_p
    )
    return analyze_leak_json(req, db, auth)


@router.get("/{analysis_id}", response_model=AnalyzeResponse, summary="Get Analysis Result")
def get_analysis_result(analysis_id: str, db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    la = db.query(LeakAnalysis).filter(LeakAnalysis.id == analysis_id).first()
    if not la:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    scores = db.query(AgentGuiltScoreRecord).filter(AgentGuiltScoreRecord.analysis_id == analysis_id).all()
    score_schemas = [
        AgentScoreSchema(
            agent_id=s.agent_id,
            agent_name=s.agent_name,
            guilt_probability=s.guilt_probability,
            matching_records_count=s.matching_records_count,
            matching_genuine_count=s.matching_genuine_count,
            canary_records_found=s.canary_records_found,
            triggered_canary_tokens=s.triggered_canary_tokens or [],
            verdict=s.verdict,
            explanation=s.explanation or ""
        )
        for s in scores
    ]

    return AnalyzeResponse(
        analysis_id=la.id,
        dataset_id=la.dataset_id,
        leak_source_name=la.leak_source_name,
        status=la.status,
        total_leaked_records=la.total_leaked_records,
        matched_leaked_records=la.matched_leaked_records,
        unmatched_leaked_records=la.unmatched_leaked_records,
        canary_hits_total=la.canary_hits_total,
        independent_leak_prob_p=la.independent_leak_prob_p,
        top_suspect_id=la.top_suspect_id,
        top_suspect_name=la.top_suspect_name,
        highest_probability=la.highest_probability,
        canary_confirmed_agent_id=la.canary_confirmed_agent_id,
        agent_scores=score_schemas,
        overlap_matrix=la.overlap_matrix or {},
        created_at=la.created_at
    )


@router.get("/{analysis_id}/status", summary="Poll Analysis Status")
def poll_analysis_status(analysis_id: str, db: Session = Depends(get_db)):
    la = db.query(LeakAnalysis).filter(LeakAnalysis.id == analysis_id).first()
    if not la:
        raise HTTPException(status_code=404, detail="Analysis task not found")
    return {
        "analysis_id": la.id,
        "status": la.status,
        "progress": la.progress,
        "is_ready": la.status == "COMPLETED"
    }
