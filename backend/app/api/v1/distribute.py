"""Distribute API — Smart Allocation & Synthetic Canary Injection."""

import io
import csv
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_auth
from backend.app.models.dataset import Dataset, DatasetRecord
from backend.app.models.agent import Agent
from backend.app.models.allocation import Allocation, AgentAllocation
from backend.app.schemas.allocation import DistributeRequest, DistributeResponse, AgentAllocationDetail
from backend.app.engine.allocator import allocate_dataset_records
from backend.app.engine.canary_generator import generate_synthetic_canary

router = APIRouter(prefix="/distribute", tags=["Distribute & Allocate"])


@router.post("", response_model=DistributeResponse, summary="Execute Smart Data Allocation")
def distribute_dataset(
    req: DistributeRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    genuine_records = db.query(DatasetRecord).filter(
        DatasetRecord.dataset_id == req.dataset_id,
        DatasetRecord.is_canary == False
    ).all()

    if not genuine_records:
        raise HTTPException(status_code=400, detail="No records available to allocate")

    agents = db.query(Agent).filter(Agent.id.in_(req.agent_ids), Agent.is_active == True).all()
    if not agents:
        raise HTTPException(status_code=400, detail="No active agents selected")

    record_hashes = [r.record_hash for r in genuine_records]
    agent_id_list = [a.id for a in agents]

    # Run Pure Allocation Strategy
    allocations_by_agent, avg_overlap, matrix = allocate_dataset_records(
        record_hashes=record_hashes,
        agent_ids=agent_id_list,
        strategy=req.strategy,
        records_per_agent=req.records_per_agent
    )

    allocation_id = f"ALLOC-{uuid.uuid4().hex[:8].upper()}"
    total_canaries = 0
    allocations_detail: Dict[str, AgentAllocationDetail] = {}

    schema_sample = genuine_records[0].data if genuine_records else {}

    alloc_db = Allocation(
        id=allocation_id,
        dataset_id=req.dataset_id,
        strategy=req.strategy,
        canary_injection_rate=req.canary_injection_rate,
        records_per_agent=req.records_per_agent,
        total_unique_records=len(set().union(*[set(v) for v in allocations_by_agent.values()])),
        average_pairwise_overlap=avg_overlap,
        total_canaries_injected=0,
        meta_info={"overlap_matrix": matrix}
    )
    db.add(alloc_db)
    db.flush()

    agent_lookup = {a.id: a.name for a in agents}

    for a_id in agent_id_list:
        assigned_genuine_hashes = allocations_by_agent[a_id]
        canary_count = max(1, int(len(assigned_genuine_hashes) * req.canary_injection_rate)) if req.canary_injection_rate > 0 else 0
        total_canaries += canary_count

        canary_hashes = []
        canary_tokens = []

        for _ in range(canary_count):
            canary_rec = generate_synthetic_canary(schema_sample, a_id, dataset.category)
            c_hash = str(canary_rec.get("id") or canary_rec.get("_record_id"))
            canary_token = canary_rec.get("_canary_token")
            
            canary_hashes.append(c_hash)
            canary_tokens.append(canary_token)

            # Store canary record in DB
            dr = DatasetRecord(
                id=f"dr_canary_{uuid.uuid4().hex[:12]}",
                dataset_id=req.dataset_id,
                record_hash=c_hash,
                data=canary_rec,
                is_canary=True,
                canary_agent_id=a_id,
                canary_token=canary_token
            )
            db.add(dr)

        all_hashes_for_agent = assigned_genuine_hashes + canary_hashes

        agent_alloc_db = AgentAllocation(
            id=f"aa_{uuid.uuid4().hex[:12]}",
            allocation_id=allocation_id,
            agent_id=a_id,
            total_records=len(all_hashes_for_agent),
            genuine_records_count=len(assigned_genuine_hashes),
            canary_records_count=canary_count,
            allocated_record_hashes=all_hashes_for_agent,
            canary_tokens=canary_tokens
        )
        db.add(agent_alloc_db)

        allocations_detail[a_id] = AgentAllocationDetail(
            agent_id=a_id,
            agent_name=agent_lookup.get(a_id, a_id),
            total_records=len(all_hashes_for_agent),
            genuine_records_count=len(assigned_genuine_hashes),
            canary_records_count=canary_count,
            canary_tokens=canary_tokens,
            download_url=f"/api/v1/distribute/{allocation_id}/agent/{a_id}/download"
        )

    alloc_db.total_canaries_injected = total_canaries
    db.commit()
    db.refresh(alloc_db)

    return DistributeResponse(
        allocation_id=alloc_db.id,
        dataset_id=alloc_db.dataset_id,
        strategy_used=alloc_db.strategy,
        canary_injection_rate=alloc_db.canary_injection_rate,
        total_unique_records_allocated=alloc_db.total_unique_records,
        average_pairwise_overlap=alloc_db.average_pairwise_overlap,
        total_canaries_injected=total_canaries,
        allocations=allocations_detail,
        created_at=alloc_db.created_at
    )


@router.get("/{allocation_id}/agent/{agent_id}/download", summary="Download Agent Allocated Package")
def download_agent_package(
    allocation_id: str,
    agent_id: str,
    format: str = "csv",
    db: Session = Depends(get_db)
):
    aa = db.query(AgentAllocation).filter(
        AgentAllocation.allocation_id == allocation_id,
        AgentAllocation.agent_id == agent_id
    ).first()

    if not aa:
        raise HTTPException(status_code=404, detail="Agent allocation slice not found")

    hashes = set(aa.allocated_record_hashes)
    records = db.query(DatasetRecord).filter(DatasetRecord.record_hash.in_(hashes)).all()

    clean_records = []
    for r in records:
        c = {k: v for k, v in r.data.items() if not k.startswith("_")}
        clean_records.append(c)

    if not clean_records:
        raise HTTPException(status_code=400, detail="Package is empty")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(clean_records[0].keys()))
    writer.writeheader()
    writer.writerows(clean_records)

    agent_name = agent_id
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent:
        agent_name = agent.name.replace(" ", "_")

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{agent_name}_dataset_package.csv"'}
    )
