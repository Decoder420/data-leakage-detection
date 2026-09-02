"""Adversarial Breach Simulator & Monte Carlo Resilience Benchmark Engine."""

import random
from typing import List, Dict, Any, Tuple
from faker import Faker

from .models import SimulationRequest, MonteCarloRequest
from .canary import generate_synthetic_canary_record

fake = Faker()


def create_simulated_leak(
    scenario: str,
    agent_full_packages: Dict[str, List[Dict[str, Any]]],
    target_agent_id: str = None,
    target_agent_ids: List[str] = None,
    leak_percentage: float = 0.6,
    noise_records_count: int = 5,
    schema_sample: Dict[str, Any] = None
) -> Tuple[List[Dict[str, Any]], str, List[str]]:
    """
    Generates a simulated breach dataset based on realistic cyber attack scenarios.
    
    Returns:
        (List of leaked records, Scenario description title, List of actual culprit agent IDs)
    """
    available_agents = list(agent_full_packages.keys())
    if not available_agents:
        raise ValueError("No allocated agent packages found for simulation.")

    culprit_ids: List[str] = []
    leaked_pool: List[Dict[str, Any]] = []
    title: str = ""

    if scenario == "two_agent_collusion":
        if target_agent_ids and len(target_agent_ids) >= 2:
            chosen_agents = target_agent_ids[:2]
        else:
            chosen_agents = random.sample(available_agents, min(2, len(available_agents)))
        culprit_ids = chosen_agents
        title = f"Collusion Leak: Combined Exfiltration by {', '.join(chosen_agents)}"

        for a_id in chosen_agents:
            pkg = agent_full_packages[a_id]
            sample_size = max(1, int(len(pkg) * leak_percentage))
            leaked_pool.extend(random.sample(pkg, sample_size))

    elif scenario == "noisy_darkweb_leak":
        target = target_agent_id if (target_agent_id and target_agent_id in agent_full_packages) else random.choice(available_agents)
        culprit_ids = [target]
        title = f"Noisy Dark Web Dump: {target} data mixed with {noise_records_count} decoy records"

        pkg = agent_full_packages[target]
        sample_size = max(1, int(len(pkg) * leak_percentage))
        leaked_pool.extend(random.sample(pkg, sample_size))

        # Add independent random noise records
        sample_rec = schema_sample or (pkg[0] if pkg else {})
        for _ in range(noise_records_count):
            noise_rec = generate_synthetic_canary_record(sample_rec, "INDEPENDENT_NOISE")
            noise_rec["_is_canary"] = False
            noise_rec["_canary_agent_id"] = None
            noise_rec["_canary_token"] = None
            leaked_pool.append(noise_rec)

    elif scenario == "subsample_leak":
        target = target_agent_id if (target_agent_id and target_agent_id in agent_full_packages) else random.choice(available_agents)
        culprit_ids = [target]
        title = f"Evasive Subsample Leak: Attacker dropped 70% of rows from {target}"

        pkg = agent_full_packages[target]
        sample_size = max(1, int(len(pkg) * 0.3))
        leaked_pool.extend(random.sample(pkg, sample_size))

    else:  # Default: Single Agent Leak
        target = target_agent_id if (target_agent_id and target_agent_id in agent_full_packages) else random.choice(available_agents)
        culprit_ids = [target]
        title = f"Direct Exfiltration Leak from Agent {target}"

        pkg = agent_full_packages[target]
        sample_size = max(1, int(len(pkg) * leak_percentage))
        leaked_pool.extend(random.sample(pkg, sample_size))

    # Deduplicate by record ID if collusion merged identical records
    seen_ids = set()
    deduped_leak = []
    for r in leaked_pool:
        r_id = r.get("_record_id") or str(r)
        if r_id not in seen_ids:
            seen_ids.add(r_id)
            deduped_leak.append(r)

    random.shuffle(deduped_leak)
    return deduped_leak, title, culprit_ids
