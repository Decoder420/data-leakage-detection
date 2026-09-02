"""Data Allocation Strategies with Synthetic Canary Injection."""

import random
import uuid
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .models import Agent, AllocationConfig, AgentAllocation, AllocationResult
from .canary import generate_synthetic_canary_record


def calculate_jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 0.0
    union_len = len(set_a.union(set_b))
    if union_len == 0:
        return 0.0
    return len(set_a.intersection(set_b)) / union_len


def allocate_dataset(
    dataset_id: str,
    records: List[Dict[str, Any]],
    agents: List[Agent],
    config: AllocationConfig,
    category: str = "Fintech"
) -> Tuple[AllocationResult, Dict[str, List[Dict[str, Any]]]]:
    """
    Distributes records to agents using the specified allocation strategy
    and injects realistic synthetic canaries.
    
    Returns:
        (AllocationResult metadata, Dict[agent_id, List of full allocated records])
    """
    num_agents = len(agents)
    total_records = len(records)
    if num_agents == 0 or total_records == 0:
        raise ValueError("Agents list and dataset records cannot be empty.")

    target_count = config.records_per_agent or max(1, int(total_records * 0.7))
    target_count = min(target_count, total_records)

    # Ensure every record has a unique ID
    indexed_records: Dict[str, Dict[str, Any]] = {}
    for idx, rec in enumerate(records):
        rec_id = rec.get("_record_id") or rec.get("id") or f"REC-{idx:05d}"
        clean_rec = dict(rec)
        clean_rec["_record_id"] = str(rec_id)
        clean_rec["_is_canary"] = False
        indexed_records[str(rec_id)] = clean_rec

    record_ids = list(indexed_records.keys())
    agent_assigned_ids: Dict[str, List[str]] = {agent.id: [] for agent in agents}

    # Strategy 1: Overlap Minimization (Explicit Greedily-Balanced Strategy)
    if config.allocation_strategy == "overlap_minimization":
        # Track assignment frequency of each record across all agents
        record_frequencies = defaultdict(int)
        
        for agent in agents:
            # Sort record candidates by lowest assignment frequency first (to spread evenly)
            # Add random jitter to break ties fairly
            candidate_pool = list(record_ids)
            candidate_pool.sort(key=lambda r_id: (record_frequencies[r_id], random.random()))
            
            chosen_ids = candidate_pool[:target_count]
            agent_assigned_ids[agent.id] = chosen_ids
            for r_id in chosen_ids:
                record_frequencies[r_id] += 1

    # Strategy 2: Zero Overlap / Disjoint Partitioning (if capacity allows)
    elif config.allocation_strategy == "zero_overlap":
        shuffled = list(record_ids)
        random.shuffle(shuffled)
        step = len(shuffled) // num_agents
        for i, agent in enumerate(agents):
            start = i * step
            end = start + step if i < num_agents - 1 else len(shuffled)
            agent_assigned_ids[agent.id] = shuffled[start:end]

    # Strategy 3: Random Allocation
    else:
        for agent in agents:
            chosen = random.sample(record_ids, target_count)
            agent_assigned_ids[agent.id] = chosen

    # Synthetic Canary Honeytoken Injection
    agent_full_packages: Dict[str, List[Dict[str, Any]]] = {}
    agent_allocations_meta: Dict[str, AgentAllocation] = {}
    total_canaries_count = 0
    schema_sample = records[0] if records else {}

    for agent in agents:
        genuine_ids = agent_assigned_ids[agent.id]
        genuine_records = [indexed_records[r_id] for r_id in genuine_ids]
        
        # Calculate number of canary records to inject
        num_canaries = max(1, int(len(genuine_ids) * config.canary_injection_rate)) if config.canary_injection_rate > 0 else 0
        total_canaries_count += num_canaries
        
        canary_records = []
        canary_tokens = []
        for _ in range(num_canaries):
            c_rec = generate_synthetic_canary_record(schema_sample, agent.id, category)
            canary_records.append(c_rec)
            canary_tokens.append(c_rec["_canary_token"])

        # Combine genuine + canary records and shuffle so canaries are distributed naturally
        agent_package = genuine_records + canary_records
        random.shuffle(agent_package)
        agent_full_packages[agent.id] = agent_package

        all_ids_in_package = [r.get("_record_id") for r in agent_package]

        agent_allocations_meta[agent.id] = AgentAllocation(
            agent_id=agent.id,
            agent_name=agent.name,
            total_records=len(agent_package),
            genuine_records_count=len(genuine_records),
            canary_records_count=num_canaries,
            allocated_record_ids=all_ids_in_package,
            canary_tokens=canary_tokens
        )

    # Compute Pairwise Overlap & Jaccard Similarities
    pair_overlaps = []
    agent_ids_list = list(agent_assigned_ids.keys())
    for i in range(len(agent_ids_list)):
        for j in range(i + 1, len(agent_ids_list)):
            set_i = set(agent_assigned_ids[agent_ids_list[i]])
            set_j = set(agent_assigned_ids[agent_ids_list[j]])
            sim = calculate_jaccard_similarity(set_i, set_j)
            pair_overlaps.append(sim)

    avg_overlap = round(sum(pair_overlaps) / max(1, len(pair_overlaps)), 4) if pair_overlaps else 0.0

    all_unique_allocated = set()
    for ids in agent_assigned_ids.values():
        all_unique_allocated.update(ids)

    result_meta = AllocationResult(
        allocation_id=f"ALLOC-{uuid.uuid4().hex[:8].upper()}",
        dataset_id=dataset_id,
        strategy_used=config.allocation_strategy,
        allocations=agent_allocations_meta,
        total_unique_records_allocated=len(all_unique_allocated),
        average_pairwise_overlap=avg_overlap,
        total_canaries_injected=total_canaries_count
    )

    return result_meta, agent_full_packages
