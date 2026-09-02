"""Dataset allocation and canary injection endpoints."""

import io
import csv
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Response
from backend.engine.models import AllocationConfig, AllocationResult
from backend.engine.allocation import allocate_dataset
from backend.api.state import state

router = APIRouter(prefix="/api/allocations", tags=["Allocations"])


@router.get("/{dataset_id}", response_model=AllocationResult)
def get_allocation_for_dataset(dataset_id: str):
    """Retrieve allocation matrix metadata for a given dataset."""
    if dataset_id not in state.allocations:
        raise HTTPException(status_code=404, detail="No allocation found for this dataset. Run allocation first.")
    return state.allocations[dataset_id]


@router.post("", response_model=AllocationResult)
def create_allocation(config: AllocationConfig):
    """Execute data allocation across selected agents with synthetic canary honeytokens."""
    if config.dataset_id not in state.datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    raw_records = state.raw_records.get(config.dataset_id, [])
    if not raw_records:
        raise HTTPException(status_code=400, detail="Dataset has no records to allocate.")

    selected_agents = [state.agents[a_id] for a_id in config.agent_ids if a_id in state.agents]
    if not selected_agents:
        raise HTTPException(status_code=400, detail="No valid agents selected for allocation.")

    dataset_meta = state.datasets[config.dataset_id]

    alloc_result, agent_pkgs = allocate_dataset(
        dataset_id=config.dataset_id,
        records=raw_records,
        agents=selected_agents,
        config=config,
        category=dataset_meta.category
    )

    state.allocations[config.dataset_id] = alloc_result
    state.agent_packages[config.dataset_id] = agent_pkgs

    return alloc_result


@router.get("/{dataset_id}/agent/{agent_id}/records")
def get_agent_allocated_records(dataset_id: str, agent_id: str):
    """View allocated records for a specific agent (including canaries)."""
    if dataset_id not in state.agent_packages or agent_id not in state.agent_packages[dataset_id]:
        raise HTTPException(status_code=404, detail="No allocation found for this agent.")
    return state.agent_packages[dataset_id][agent_id]


@router.get("/{dataset_id}/agent/{agent_id}/download")
def download_agent_package(dataset_id: str, agent_id: str, format: str = "csv"):
    """Export the distributed dataset slice for an agent as CSV."""
    if dataset_id not in state.agent_packages or agent_id not in state.agent_packages[dataset_id]:
        raise HTTPException(status_code=404, detail="Package not found for this agent.")

    records = state.agent_packages[dataset_id][agent_id]
    if not records:
        raise HTTPException(status_code=400, detail="No records in package.")

    # Strip internal tracking fields for realistic export
    clean_records = []
    for r in records:
        c = {k: v for k, v in r.items() if not k.startswith("_")}
        clean_records.append(c)

    fieldnames = list(clean_records[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(clean_records)

    agent_name = state.agents[agent_id].name.replace(" ", "_") if agent_id in state.agents else agent_id
    filename = f"{agent_name}_dataset_export.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
