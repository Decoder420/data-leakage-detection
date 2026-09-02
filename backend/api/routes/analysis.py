"""Leak Analysis & Probabilistic Guilt Attribution endpoints."""

import io
import csv
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from backend.engine.models import LeakAnalysisRequest, LeakAnalysisResult
from backend.engine.guilt_model import calculate_guilt_probabilities
from backend.api.state import state

router = APIRouter(prefix="/api/analysis", tags=["Leak Analysis"])


@router.get("/history", response_model=List[LeakAnalysisResult])
def get_analysis_history():
    """Get history of past leak analysis assessments."""
    return state.analysis_history[::-1]


@router.post("/json", response_model=LeakAnalysisResult)
def analyze_leaked_json(req: LeakAnalysisRequest):
    """Analyze a leaked record dump passed directly as JSON."""
    if req.dataset_id not in state.allocations:
        raise HTTPException(status_code=400, detail="No active allocation found for this dataset. Please allocate data first.")

    allocation = state.allocations[req.dataset_id]
    agent_packages = state.agent_packages.get(req.dataset_id, {})
    all_agents = list(state.agents.values())

    result = calculate_guilt_probabilities(
        dataset_id=req.dataset_id,
        leaked_records=req.leaked_records,
        agents=all_agents,
        allocations_map=allocation.allocations,
        agent_full_packages=agent_packages,
        leak_source_name=req.leak_source_name,
        independent_leak_prob_p=req.independent_leak_prob_p
    )

    state.analysis_history.append(result)
    return result


@router.post("/file", response_model=LeakAnalysisResult)
async def analyze_leaked_file(
    dataset_id: str = Form(...),
    leak_source_name: str = Form("Dark Web Breach Dump"),
    independent_leak_prob_p: float = Form(0.05),
    file: UploadFile = File(...)
):
    """Upload and analyze a leaked CSV or JSON file."""
    if dataset_id not in state.allocations:
        raise HTTPException(status_code=400, detail="No active allocation found for this dataset. Please allocate data first.")

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

    if not leaked_records:
        raise HTTPException(status_code=400, detail="Leaked file contains no records.")

    allocation = state.allocations[dataset_id]
    agent_packages = state.agent_packages.get(dataset_id, {})
    all_agents = list(state.agents.values())

    result = calculate_guilt_probabilities(
        dataset_id=dataset_id,
        leaked_records=leaked_records,
        agents=all_agents,
        allocations_map=allocation.allocations,
        agent_full_packages=agent_packages,
        leak_source_name=f"{leak_source_name} ({filename})",
        independent_leak_prob_p=independent_leak_prob_p
    )

    state.analysis_history.append(result)
    return result


@router.get("/{analysis_id}", response_model=LeakAnalysisResult)
def get_analysis_by_id(analysis_id: str):
    """Retrieve details for a past analysis by ID."""
    for item in state.analysis_history:
        if item.analysis_id == analysis_id:
            return item
    raise HTTPException(status_code=404, detail="Analysis result not found")
