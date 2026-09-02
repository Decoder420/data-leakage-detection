"""Probabilistic Guilt Attribution Model for Data Leakage Detection.
Based on the Papadimitriou & Garcia-Molina formulation with Canary Honeytoken Attribution.
"""

import uuid
import math
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict

from .models import (
    Agent,
    AgentAllocation,
    AgentGuiltScore,
    LeakAnalysisResult,
    RecordOverlapDetail
)
from .canary import extract_canary_from_record


def generate_record_hash(record: Dict[str, Any]) -> str:
    """Create a normalized composite hash of identifying fields in a record."""
    if "_record_id" in record and record["_record_id"]:
        return str(record["_record_id"])
    if "id" in record and record["id"]:
        return str(record["id"])

    # Fallback to normalized identifying keys (e.g. email, ssn, name)
    identifying_parts = []
    for k in sorted(record.keys()):
        if k.startswith("_"):
            continue
        v = str(record[k]).strip().lower()
        if k.lower() in ["email", "ssn", "name", "phone", "patient_id", "customer_id"]:
            identifying_parts.append(f"{k}:{v}")
    
    if identifying_parts:
        return "|".join(identifying_parts)
    # If no key fields, hash all non-metadata values
    return "|".join(f"{k}:{str(v).strip().lower()}" for k, v in sorted(record.items()) if not k.startswith("_"))


def calculate_guilt_probabilities(
    dataset_id: str,
    leaked_records: List[Dict[str, Any]],
    agents: List[Agent],
    allocations_map: Dict[str, AgentAllocation],
    agent_full_packages: Dict[str, List[Dict[str, Any]]],
    leak_source_name: str = "Dark Web Breach Dump",
    independent_leak_prob_p: float = 0.05
) -> LeakAnalysisResult:
    """
    Computes mathematical guilt probability for each agent given a leaked dataset dump.
    """
    total_leaked = len(leaked_records)
    if total_leaked == 0:
        raise ValueError("Leaked dataset cannot be empty.")

    # 1. Build lookup index for all distributed records across all agents
    # record_hash -> set of agent_ids who received this record
    record_distribution_map: Dict[str, Set[str]] = defaultdict(set)
    # record_hash -> record metadata
    all_known_records_by_hash: Dict[str, Dict[str, Any]] = {}

    for agent_id, pkg in agent_full_packages.items():
        for rec in pkg:
            r_hash = generate_record_hash(rec)
            record_distribution_map[r_hash].add(agent_id)
            if r_hash not in all_known_records_by_hash:
                all_known_records_by_hash[r_hash] = rec

    # 2. Analyze leaked records: match against distributed pool & detect canaries
    matched_hashes: Set[str] = set()
    unmatched_count = 0
    canary_hits_by_agent: Dict[str, List[str]] = defaultdict(list)
    leaked_record_hashes: Set[str] = set()

    for l_rec in leaked_records:
        l_hash = generate_record_hash(l_rec)
        leaked_record_hashes.add(l_hash)

        # Check if record is an injected canary honeytoken
        canary_check = extract_canary_from_record(l_rec)
        if canary_check:
            c_agent, c_token = canary_check
            if c_agent in allocations_map:
                canary_hits_by_agent[c_agent].append(c_token)
            else:
                # Find matching token in all agent allocations
                for a_id, alloc in allocations_map.items():
                    if any(t in str(l_rec) for t in alloc.canary_tokens):
                        canary_hits_by_agent[a_id].append(c_token)

        if l_hash in record_distribution_map:
            matched_hashes.add(l_hash)
        else:
            unmatched_count += 1

    # 3. Calculate Guilt Probability per Agent using Papadimitriou & Garcia-Molina formulation
    agent_scores: List[AgentGuiltScore] = []
    agent_lookup = {a.id: a for a in agents}
    p = max(0.001, min(0.999, independent_leak_prob_p))

    canary_confirmed_agent_id = None
    highest_prob = 0.0
    top_suspect_id = None
    top_suspect_name = None

    for agent_id, allocation in allocations_map.items():
        agent = agent_lookup.get(agent_id)
        agent_name = agent.name if agent else allocation.agent_name

        # Find intersection: records possessed by this agent that also appear in the leak
        agent_pkg = agent_full_packages.get(agent_id, [])
        agent_record_hashes = {generate_record_hash(r): r for r in agent_pkg}
        
        intersecting_hashes = leaked_record_hashes.intersection(set(agent_record_hashes.keys()))
        matching_count = len(intersecting_hashes)

        # Separate genuine vs canary matches
        canary_found_count = len(canary_hits_by_agent[agent_id])
        matching_genuine_count = matching_count - canary_found_count

        # Compute probability product:
        # P(G_i | S) = 1 - product_{t in S intersect R_i} (1 - (1 - p) / (|V_t|*(1 - p) + p))
        log_not_guilty = 0.0

        for r_hash in intersecting_hashes:
            rec_obj = agent_record_hashes[r_hash]
            is_canary = rec_obj.get("_is_canary", False) or r_hash in canary_hits_by_agent[agent_id]
            
            if is_canary:
                # Canary token uniquely owned by this agent -> 100% deterministic attribution
                log_not_guilty = -float("inf")
                break
            else:
                # Count agents sharing this record
                num_agents_with_record = len(record_distribution_map.get(r_hash, {agent_id}))
                prob_agent_leaked_t = (1.0 - p) / (num_agents_with_record * (1.0 - p) + p)
                prob_agent_leaked_t = min(0.9999, max(0.0001, prob_agent_leaked_t))
                log_not_guilty += math.log(1.0 - prob_agent_leaked_t)

        if math.isinf(log_not_guilty) and log_not_guilty < 0:
            guilt_probability = 1.0
        else:
            guilt_probability = round(1.0 - math.exp(log_not_guilty), 4)

        # Direct canary override if any canary token was triggered
        if canary_found_count > 0:
            guilt_probability = 1.0
            canary_confirmed_agent_id = agent_id

        # Determine Verdict & Explanation
        if canary_found_count > 0:
            verdict = "CONFIRMED_LEAKER"
            explanation = (
                f"Definitive breach attribution. {canary_found_count} unique synthetic canary token(s) "
                f"assigned exclusively to {agent_name} were identified in the leaked data dump."
            )
        elif guilt_probability >= 0.85:
            verdict = "HIGH_SUSPICION"
            explanation = (
                f"High mathematical probability ({guilt_probability * 100:.1f}%) based on "
                f"{matching_count} matching records with low cross-agent overlap."
            )
        elif guilt_probability >= 0.40:
            verdict = "MODERATE_SUSPICION"
            explanation = (
                f"Moderate probability ({guilt_probability * 100:.1f}%). {matching_count} records matched, "
                "but high overlap with other distributed agent datasets reduces certainty."
            )
        elif matching_count > 0:
            verdict = "UNLIKELY"
            explanation = (
                f"Low probability ({guilt_probability * 100:.1f}%). Only {matching_count} records matched "
                "which are widely distributed across multiple other trusted agents."
            )
        else:
            verdict = "CLEARED"
            explanation = f"Zero matching records found between the leaked dump and {agent_name}'s dataset."

        score_obj = AgentGuiltScore(
            agent_id=agent_id,
            agent_name=agent_name,
            guilt_probability=guilt_probability,
            matching_records_count=matching_count,
            matching_genuine_count=max(0, matching_genuine_count),
            canary_records_found=canary_found_count,
            triggered_canary_tokens=canary_hits_by_agent[agent_id],
            verdict=verdict,
            explanation=explanation
        )
        agent_scores.append(score_obj)

    # Sort agent scores descending by guilt probability
    agent_scores.sort(key=lambda s: (s.canary_records_found > 0, s.guilt_probability, s.matching_records_count), reverse=True)

    if agent_scores:
        top_suspect = agent_scores[0]
        highest_prob = top_suspect.guilt_probability
        top_suspect_id = top_suspect.agent_id
        top_suspect_name = top_suspect.agent_name

    # 4. Generate Overlap Matrix (Agent vs Agent & Agent vs Leak)
    overlap_matrix: Dict[str, Dict[str, int]] = defaultdict(dict)
    all_agent_ids = list(allocations_map.keys())
    
    for a1 in all_agent_ids:
        a1_hashes = {generate_record_hash(r) for r in agent_full_packages.get(a1, [])}
        overlap_matrix[a1]["LEAK_DUMP"] = len(a1_hashes.intersection(leaked_record_hashes))
        for a2 in all_agent_ids:
            a2_hashes = {generate_record_hash(r) for r in agent_full_packages.get(a2, [])}
            overlap_matrix[a1][a2] = len(a1_hashes.intersection(a2_hashes))

    return LeakAnalysisResult(
        analysis_id=f"LEAK-ANL-{uuid.uuid4().hex[:8].upper()}",
        dataset_id=dataset_id,
        leak_source_name=leak_source_name,
        total_leaked_records=total_leaked,
        matched_leaked_records=len(matched_hashes),
        unmatched_leaked_records=unmatched_count,
        canary_hits_total=sum(len(hits) for hits in canary_hits_by_agent.values()),
        independent_leak_prob_p=p,
        agent_scores=agent_scores,
        top_suspect_id=top_suspect_id,
        top_suspect_name=top_suspect_name,
        highest_probability=highest_prob,
        canary_confirmed_agent_id=canary_confirmed_agent_id,
        overlap_matrix=overlap_matrix
    )
