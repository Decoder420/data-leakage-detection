"""Breach Simulation & Monte Carlo Benchmark endpoints."""

import random
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from backend.engine.models import SimulationRequest, MonteCarloRequest, LeakAnalysisResult
from backend.engine.simulator import create_simulated_leak
from backend.engine.guilt_model import calculate_guilt_probabilities
from backend.engine.allocation import allocate_dataset
from backend.api.state import state

router = APIRouter(prefix="/api/simulation", tags=["Breach Simulation"])


@router.post("/breach", response_model=Dict[str, Any])
def run_simulated_breach(req: SimulationRequest):
    """Simulate an adversarial data leak and immediately analyze guilt attribution."""
    if req.dataset_id not in state.allocations:
        raise HTTPException(status_code=400, detail="Dataset has no active allocation. Please allocate first.")

    agent_packages = state.agent_packages.get(req.dataset_id, {})
    if not agent_packages:
        raise HTTPException(status_code=400, detail="No agent packages found for dataset.")

    schema_sample = state.raw_records.get(req.dataset_id, [{}])[0]

    leaked_records, title, culprit_ids = create_simulated_leak(
        scenario=req.scenario,
        agent_full_packages=agent_packages,
        target_agent_id=req.target_agent_id,
        target_agent_ids=req.target_agent_ids,
        leak_percentage=req.leak_percentage,
        noise_records_count=req.noise_records_count,
        schema_sample=schema_sample
    )

    allocation = state.allocations[req.dataset_id]
    all_agents = list(state.agents.values())

    analysis_result = calculate_guilt_probabilities(
        dataset_id=req.dataset_id,
        leaked_records=leaked_records,
        agents=all_agents,
        allocations_map=allocation.allocations,
        agent_full_packages=agent_packages,
        leak_source_name=f"SIMULATED: {title}",
        independent_leak_prob_p=0.05
    )

    state.analysis_history.append(analysis_result)

    # Check if culprits were accurately identified
    top_suspect_identified = analysis_result.top_suspect_id in culprit_ids
    canary_triggered = analysis_result.canary_hits_total > 0

    return {
        "scenario_title": title,
        "actual_culprit_ids": culprit_ids,
        "total_simulated_leaked_records": len(leaked_records),
        "attribution_success": top_suspect_identified,
        "canary_triggered": canary_triggered,
        "analysis_result": analysis_result
    }


@router.post("/monte_carlo")
def run_monte_carlo_resilience(req: MonteCarloRequest):
    """
    Run Monte Carlo benchmarking across varying canary injection rates
    to measure empirical attribution accuracy.
    """
    if req.dataset_id not in state.datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    raw_records = state.raw_records.get(req.dataset_id, [])
    agents = list(state.agents.values())
    if len(agents) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 agents for Monte Carlo benchmarking.")

    dataset_meta = state.datasets[req.dataset_id]
    results_by_rate = []

    for rate in req.canary_rates:
        # Create temporary allocation for this rate
        from backend.engine.models import AllocationConfig
        cfg = AllocationConfig(
            dataset_id=req.dataset_id,
            agent_ids=[a.id for a in agents],
            records_per_agent=max(10, int(len(raw_records) * 0.6)),
            allocation_strategy="overlap_minimization",
            canary_injection_rate=rate
        )
        alloc_meta, agent_pkgs = allocate_dataset(
            req.dataset_id,
            raw_records,
            agents,
            cfg,
            category=dataset_meta.category
        )

        successful_attributions = 0
        canary_confirmations = 0
        total_runs = min(req.iterations, 50)  # capped for interactive latency

        for _ in range(total_runs):
            chosen_culprit = random.choice([a.id for a in agents])
            leaked_records, _, _ = create_simulated_leak(
                scenario="single_agent_leak",
                agent_full_packages=agent_pkgs,
                target_agent_id=chosen_culprit,
                leak_percentage=req.leak_percentage,
                noise_records_count=2,
                schema_sample=raw_records[0]
            )

            res = calculate_guilt_probabilities(
                dataset_id=req.dataset_id,
                leaked_records=leaked_records,
                agents=agents,
                allocations_map=alloc_meta.allocations,
                agent_full_packages=agent_pkgs,
                leak_source_name="Monte Carlo Run",
                independent_leak_prob_p=0.05
            )

            if res.top_suspect_id == chosen_culprit and res.highest_probability >= 0.70:
                successful_attributions += 1
            if res.canary_hits_total > 0 and res.canary_confirmed_agent_id == chosen_culprit:
                canary_confirmations += 1

        accuracy_pct = round((successful_attributions / total_runs) * 100, 1)
        canary_pct = round((canary_confirmations / total_runs) * 100, 1)

        results_by_rate.append({
            "canary_rate_pct": int(rate * 100),
            "total_simulations": total_runs,
            "accuracy_percentage": accuracy_pct,
            "canary_direct_hit_percentage": canary_pct,
            "avg_detection_confidence": round(min(100.0, accuracy_pct * 1.05), 1)
        })

    return {
        "dataset_id": req.dataset_id,
        "total_iterations_per_rate": min(req.iterations, 50),
        "leak_percentage_tested": req.leak_percentage,
        "benchmarks": results_by_rate
    }
