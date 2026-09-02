"""Vectorized Probabilistic Guilt Calculation Engine — DecodeX Security Technologies.
Implements the Papadimitriou & Garcia-Molina formulation with NumPy vectorization.
"""

import math
import numpy as np
from typing import Dict, List, Set, Any, Tuple, Optional


def compute_vectorized_guilt_probabilities(
    leaked_record_hashes: List[str],
    agent_record_map: Dict[str, Set[str]],
    canary_ownership_map: Dict[str, str],  # canary_record_hash -> agent_id
    independent_leak_prob_p: float = 0.05
) -> Dict[str, Dict[str, Any]]:
    """
    Vectorized Papadimitriou & Garcia-Molina guilt attribution calculator.
    
    Formula:
      P(G_i | S) = 1 - product_{t in S intersect R_i} (1 - (1 - p) / (1 - p + sum_{j != i, t in R_j} 1))
      
    Edge Cases Handled:
      - p = 0.0: Strict attribution (no independent leak probability).
      - p = 1.0: Independent noise dominates (guilt probability -> 0.0).
      - S empty: Guilt probability = 0.0 for all agents.
      - S intersect R_i empty: Guilt probability = 0.0.
      - Canary record present: Deterministic override to 1.0 (100% confidence).
    """
    p = float(np.clip(independent_leak_prob_p, 0.0, 1.0))
    leaked_set = set(leaked_record_hashes)
    total_leaked = len(leaked_set)

    if total_leaked == 0 or not agent_record_map:
        return {
            agent_id: {
                "guilt_probability": 0.0,
                "matching_records_count": 0,
                "canary_records_found": 0,
                "verdict": "CLEARED"
            }
            for agent_id in agent_record_map
        }

    # Step 1: Precompute frequency of each record across all agents
    # frequency_map[t] = |{j | t in R_j}|
    record_freq: Dict[str, int] = {}
    for agent_id, rec_set in agent_record_map.items():
        for r_hash in rec_set:
            record_freq[r_hash] = record_freq.get(r_hash, 0) + 1

    results: Dict[str, Dict[str, Any]] = {}

    # Step 2: Vectorized probability calculation per agent
    for agent_id, agent_records in agent_record_map.items():
        # Intersect leaked set with agent records
        intersected = list(leaked_set.intersection(agent_records))
        matched_count = len(intersected)

        if matched_count == 0:
            results[agent_id] = {
                "guilt_probability": 0.0,
                "matching_records_count": 0,
                "canary_records_found": 0,
                "triggered_canaries": [],
                "verdict": "CLEARED",
                "explanation": f"Zero matching records found between leak and Agent {agent_id}."
            }
            continue

        # Check for Canary Honeytoken Hits
        triggered_canaries = []
        for r_hash in intersected:
            if r_hash in canary_ownership_map and canary_ownership_map[r_hash] == agent_id:
                triggered_canaries.append(r_hash)

        canary_hit_count = len(triggered_canaries)

        if canary_hit_count > 0:
            # Deterministic Canary Trigger -> 100% Certainty
            results[agent_id] = {
                "guilt_probability": 1.0,
                "matching_records_count": matched_count,
                "canary_records_found": canary_hit_count,
                "triggered_canaries": triggered_canaries,
                "verdict": "CONFIRMED_LEAKER",
                "explanation": (
                    f"Definitive breach attribution. {canary_hit_count} synthetic canary token(s) "
                    f"assigned exclusively to Agent {agent_id} were identified in the leak."
                )
            }
            continue

        # Edge Case: p = 1.0 (All data is assumed independently leaked)
        if math.isclose(p, 1.0):
            results[agent_id] = {
                "guilt_probability": 0.0,
                "matching_records_count": matched_count,
                "canary_records_found": 0,
                "triggered_canaries": [],
                "verdict": "UNLIKELY",
                "explanation": "Independent leakage probability is 1.0 (ambient noise dominates)."
            }
            continue

        # Vectorized probability calculation across genuine matched records
        # For each t: V_t = record_freq[t]
        # prob_leak_t = (1 - p) / (|V_t| * (1 - p) + p)
        v_t_array = np.array([record_freq[t] for t in intersected], dtype=np.float64)

        if math.isclose(p, 0.0):
            # When p = 0: prob_leak_t = 1.0 / V_t
            prob_leak_t = 1.0 / v_t_array
        else:
            prob_leak_t = (1.0 - p) / (v_t_array * (1.0 - p) + p)

        # Clip for numeric safety
        prob_leak_t = np.clip(prob_leak_t, 1e-7, 1.0 - 1e-7)

        # log(1 - prob_leak_t) using np.log1p(-x) for maximum numerical precision
        log_terms = np.log1p(-prob_leak_t)
        sum_log = np.sum(log_terms)

        # P(G_i | S) = 1 - exp(sum_log)
        guilt_prob = float(1.0 - np.exp(sum_log))
        guilt_prob = round(float(np.clip(guilt_prob, 0.0, 1.0)), 4)

        # Classify verdict
        if guilt_prob >= 0.85:
            verdict = "HIGH_SUSPICION"
            explanation = f"High mathematical probability ({guilt_prob*100:.1f}%) across {matched_count} matching records."
        elif guilt_prob >= 0.40:
            verdict = "MODERATE_SUSPICION"
            explanation = f"Moderate probability ({guilt_prob*100:.1f}%) with cross-vendor record overlap."
        elif matched_count > 0:
            verdict = "UNLIKELY"
            explanation = f"Low probability ({guilt_prob*100:.1f}%). Records are widely distributed."
        else:
            verdict = "CLEARED"
            explanation = "Zero matching records found."

        results[agent_id] = {
            "guilt_probability": guilt_prob,
            "matching_records_count": matched_count,
            "canary_records_found": 0,
            "triggered_canaries": [],
            "verdict": verdict,
            "explanation": explanation
        }

    return results
