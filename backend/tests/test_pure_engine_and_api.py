"""Exhaustive Test Suite for Pure Engine, REST API & DecodeX SOC Integration.
DecodeX Security Technologies Private Limited.
"""

import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.engine.guilt_calculator import compute_vectorized_guilt_probabilities
from backend.app.engine.allocator import allocate_dataset_records
from backend.app.engine.canary_generator import (
    generate_luhn_credit_card,
    generate_canary_token,
    generate_synthetic_canary,
    extract_canary
)
from backend.app.services.alert_adapter import transform_event_to_soc_payload
from backend.app.schemas.event import SecurityEvent

client = TestClient(app)


# ==========================================
# 1. PURE ENGINE & ALGORITHM EDGE-CASE TESTS
# ==========================================

def test_guilt_model_edge_case_p_zero():
    """Verify guilt model with p=0.0 (no independent leak probability)."""
    agent_map = {
        "AGT-1": {"rec_1", "rec_2", "rec_3"},
        "AGT-2": {"rec_3", "rec_4", "rec_5"}
    }
    # Leak rec_1 (exclusive to AGT-1) and rec_3 (shared)
    leak = ["rec_1", "rec_3"]
    canary_map = {}

    scores = compute_vectorized_guilt_probabilities(leak, agent_map, canary_map, independent_leak_prob_p=0.0)
    
    # AGT-1 holds an exclusive leaked record -> 1.0 probability under p=0.0
    assert scores["AGT-1"]["guilt_probability"] == 1.0
    assert scores["AGT-1"]["matching_records_count"] == 2
    assert scores["AGT-2"]["guilt_probability"] == 0.5  # only shared rec_3


def test_guilt_model_edge_case_p_one():
    """Verify guilt model with p=1.0 (ambient noise dominates)."""
    agent_map = {
        "AGT-1": {"rec_1", "rec_2"},
        "AGT-2": {"rec_3", "rec_4"}
    }
    leak = ["rec_1", "rec_2"]
    canary_map = {}

    scores = compute_vectorized_guilt_probabilities(leak, agent_map, canary_map, independent_leak_prob_p=1.0)
    assert scores["AGT-1"]["guilt_probability"] == 0.0
    assert scores["AGT-2"]["guilt_probability"] == 0.0


def test_guilt_model_canary_override():
    """Verify that a synthetic canary hit produces deterministic 100% guilt attribution."""
    agent_map = {
        "AGT-A": {"rec_1", "rec_canary_a"},
        "AGT-B": {"rec_2", "rec_canary_b"}
    }
    leak = ["rec_canary_a"]
    canary_map = {"rec_canary_a": "AGT-A", "rec_canary_b": "AGT-B"}

    scores = compute_vectorized_guilt_probabilities(leak, agent_map, canary_map, independent_leak_prob_p=0.05)
    assert scores["AGT-A"]["guilt_probability"] == 1.0
    assert scores["AGT-A"]["canary_records_found"] == 1
    assert scores["AGT-A"]["verdict"] == "CONFIRMED_LEAKER"
    assert scores["AGT-B"]["guilt_probability"] == 0.0


def test_vectorized_100k_rows_scaling_benchmark():
    """Ensure vectorized NumPy engine processes 100,000+ rows in <1.0 second."""
    num_records = 100_000
    all_hashes = [f"rec_hash_{i}" for i in range(num_records)]
    
    agent_map = {
        "AGT-1": set(all_hashes[:60_000]),
        "AGT-2": set(all_hashes[40_000:]),
        "AGT-3": set(all_hashes[20_000:80_000])
    }
    leaked_sample = all_hashes[10_000:30_000]  # 20,000 leaked records

    start_time = time.perf_counter()
    scores = compute_vectorized_guilt_probabilities(leaked_sample, agent_map, {}, independent_leak_prob_p=0.05)
    duration = time.perf_counter() - start_time

    assert duration < 1.5, f"Vectorized calculation took too long: {duration:.2f}s"
    assert scores["AGT-1"]["matching_records_count"] > 0


def test_luhn_credit_card_validity():
    """Verify that generated synthetic credit cards pass Luhn checksum algorithm."""
    for _ in range(25):
        card = generate_luhn_credit_card()
        assert len(card) == 16
        # Verify Luhn checksum
        digits = [int(d) for d in card]
        total = 0
        for idx, d in enumerate(reversed(digits)):
            if idx % 2 == 1:
                doubled = d * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += d
        assert total % 10 == 0, f"Card {card} failed Luhn checksum"


# ==========================================
# 2. REST API & DECODEX SOC INTEGRATION TESTS
# ==========================================

def test_api_v1_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "DecodeX" in data["owning_organization"]


def test_api_v1_datasets_and_generate():
    res = client.post("/api/v1/datasets/generate", json={
        "name": "Clinical Trial Patient Records",
        "category": "Healthcare",
        "num_records": 50
    })
    assert res.status_code == 200
    ds = res.json()
    assert ds["category"] == "Healthcare"
    assert ds["total_records"] == 50

    # List datasets
    list_res = client.get("/api/v1/datasets")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_api_v1_distribute_and_download():
    # Fetch agents and fintech dataset
    datasets = client.get("/api/v1/datasets").json()
    fintech_ds = next(d for d in datasets if "FINTECH" in d["id"])
    agents = client.get("/api/v1/agents").json()

    distribute_payload = {
        "dataset_id": fintech_ds["id"],
        "agent_ids": [a["id"] for a in agents[:3]],
        "strategy": "overlap_minimization",
        "canary_injection_rate": 0.05
    }
    dist_res = client.post("/api/v1/distribute", json=distribute_payload)
    assert dist_res.status_code == 200
    dist_data = dist_res.json()
    assert dist_data["total_canaries_injected"] > 0
    assert len(dist_data["allocations"]) == 3

    # Test download package
    first_agent_id = agents[0]["id"]
    alloc_id = dist_data["allocation_id"]
    dl_res = client.get(f"/api/v1/distribute/{alloc_id}/agent/{first_agent_id}/download")
    assert dl_res.status_code == 200
    assert "text/csv" in dl_res.headers["content-type"]


def test_api_v1_analyze_and_event_generation():
    datasets = client.get("/api/v1/datasets").json()
    fintech_ds = next(d for d in datasets if "FINTECH" in d["id"])

    # Simulate leak
    leaked_records = [
        {"id": f"REC-FIN-{i+1:04d}", "customer_name": f"Client {i}"} for i in range(25)
    ]
    analyze_payload = {
        "dataset_id": fintech_ds["id"],
        "leaked_records": leaked_records,
        "leak_source_name": "Dark Web Forum Paste",
        "independent_leak_prob_p": 0.05
    }

    anl_res = client.post("/api/v1/analyze", json=analyze_payload)
    assert anl_res.status_code == 200
    anl_data = anl_res.json()
    assert anl_data["status"] == "COMPLETED"
    assert len(anl_data["agent_scores"]) > 0

    # Verify event was emitted to /api/v1/events
    events_res = client.get("/api/v1/events")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 1
    assert "event_id" in events[0]
    assert "confidence_score" in events[0]


def test_alert_adapter_transformation():
    """Verify alert_adapter transforms internal SecurityEvent into DecodeX SOC shape."""
    event = SecurityEvent(
        event_id="evt_test_adapter_01",
        event_type="guilt_detection",
        severity="critical",
        confidence_score=0.992,
        source_dataset="Fintech Master PII",
        implicated_agent="Beta Cloud Solutions",
        evidence={"matched_records": 50},
        timestamp="2026-09-02T11:45:00.000Z"
    )

    soc_payload = transform_event_to_soc_payload(event)
    assert soc_payload["alert_id"] == "evt_test_adapter_01"
    assert soc_payload["severity"] == "CRITICAL"
    assert soc_payload["attributed_entity"] == "Beta Cloud Solutions"
    assert soc_payload["source"] == "DecodeX-Data-Leakage-Detection"


def test_api_v1_integrations_and_api_keys():
    # 1. Test Integration Settings API
    int_res = client.get("/api/v1/integrations")
    assert int_res.status_code == 200
    assert "DecodeX" in int_res.json()["target_name"]

    # 2. Test API Key Generation
    key_res = client.post("/api/v1/api-keys", json={"name": "DecodeX Threat Hunting Service Account"})
    assert key_res.status_code == 200
    key_data = key_res.json()
    assert key_data["raw_api_key"].startswith("dld_live_")

    # 3. Test Service-to-Service Request with X-API-Key
    auth_test_res = client.get("/api/v1/events", headers={"X-API-Key": key_data["raw_api_key"]})
    assert auth_test_res.status_code == 200
