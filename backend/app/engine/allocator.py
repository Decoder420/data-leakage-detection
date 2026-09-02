"""Data Allocation Strategies Engine — DecodeX Security Technologies."""

import random
from typing import List, Dict, Set, Tuple, Any
from collections import defaultdict


def calculate_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a and not set_b:
        return 0.0
    union = set_a.union(set_b)
    if not union:
        return 0.0
    return len(set_a.intersection(set_b)) / len(union)


def allocate_dataset_records(
    record_hashes: List[str],
    agent_ids: List[str],
    strategy: str = "overlap_minimization",
    records_per_agent: int = None,
    overlap_percentage: float = 0.20
) -> Tuple[Dict[str, List[str]], float, Dict[str, Dict[str, float]]]:
    """
    Allocates records to agents based on the selected distribution strategy.
    
    Strategies:
      1. overlap_minimization (Explicit): Greedily balances frequency of each record.
      2. implicit_controlled: Allocates a controlled shared overlap fraction alpha.
      3. zero_overlap: Partitions dataset into mutually disjoint subsets.
      
    Returns:
      (Dict[agent_id, List of allocated record hashes], average_pairwise_overlap, overlap_matrix)
    """
    num_agents = len(agent_ids)
    total_records = len(record_hashes)
    if num_agents == 0 or total_records == 0:
        raise ValueError("Agents list and record list cannot be empty.")

    target_count = records_per_agent or max(1, int(total_records * 0.65))
    target_count = min(target_count, total_records)

    agent_assignments: Dict[str, List[str]] = {a_id: [] for a_id in agent_ids}

    # Strategy 1: Explicit Overlap Minimization (Greedy Frequency Balancing)
    if strategy == "overlap_minimization":
        record_frequencies = defaultdict(int)
        for a_id in agent_ids:
            pool = list(record_hashes)
            # Sort by lowest assignment frequency first with random tiebreaker
            pool.sort(key=lambda r: (record_frequencies[r], random.random()))
            chosen = pool[:target_count]
            agent_assignments[a_id] = chosen
            for r in chosen:
                record_frequencies[r] += 1

    # Strategy 2: Implicit Controlled Overlap
    elif strategy == "implicit_controlled" or strategy == "implicit":
        overlap_count = max(1, int(target_count * overlap_percentage))
        disjoint_count = max(0, target_count - overlap_count)
        
        # Shared core pool
        shared_pool = random.sample(record_hashes, min(overlap_count, len(record_hashes)))
        remaining_pool = [r for r in record_hashes if r not in set(shared_pool)]
        
        for i, a_id in enumerate(agent_ids):
            if len(remaining_pool) >= disjoint_count:
                unique_sample = random.sample(remaining_pool, disjoint_count)
            else:
                unique_sample = remaining_pool[:disjoint_count]
            agent_assignments[a_id] = list(set(shared_pool + unique_sample))

    # Strategy 3: Zero Overlap / Disjoint
    elif strategy == "zero_overlap":
        shuffled = list(record_hashes)
        random.shuffle(shuffled)
        step = max(1, len(shuffled) // num_agents)
        for i, a_id in enumerate(agent_ids):
            start = i * step
            end = start + step if i < num_agents - 1 else len(shuffled)
            agent_assignments[a_id] = shuffled[start:end]

    # Strategy 4: Random Sampling Fallback
    else:
        for a_id in agent_ids:
            agent_assignments[a_id] = random.sample(record_hashes, target_count)

    # Calculate Pairwise Overlap Matrix (Jaccard similarity)
    pairwise_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
    all_similarities = []

    for i, a1 in enumerate(agent_ids):
        s1 = set(agent_assignments[a1])
        for j, a2 in enumerate(agent_ids):
            s2 = set(agent_assignments[a2])
            sim = calculate_jaccard_similarity(s1, s2)
            pairwise_matrix[a1][a2] = round(sim, 4)
            if i < j:
                all_similarities.append(sim)

    avg_overlap = round(sum(all_similarities) / max(1, len(all_similarities)), 4) if all_similarities else 0.0

    return agent_assignments, avg_overlap, pairwise_matrix
