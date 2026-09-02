"""Comprehensive Pytest test suite for Data Leakage Detection Engine and APIs."""

import pytest
from fastapi.testclient import TestClient

from backend.engine.models import Agent, AllocationConfig
from backend.engine.canary import generate_synthetic_canary_record, extract_canary_from_record, generate_canary_token
from backend.engine.allocation import allocate_dataset
from backend.engine.guilt_model import calculate_guilt_probabilities
from backend.engine.simulator import create_simulated_leak
from backend.api.main import app
from backend.api.state import state

client = TestClient(app)


def test_canary_token_and_record_generation():
    """Verify HMAC canary token generation and synthetic record creation."""
    agent_id = "AGT-TEST-01"
    token = generate_canary_token(agent_id)
    assert token.startswith("CNR-")
    assert len(token.split("-")) >= 3

    schema_sample = {
        "customer_id": "CUST-100",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "credit_score": 750,
        "account_balance": 15000.50
    }

    canary_rec = generate_synthetic_canary_record(schema_sample, agent_id, category="Fintech")
    assert canary_rec["_is_canary"] is True
    assert canary_rec["_canary_agent_id"] == agent_id
    assert "email" in canary_rec
    assert "corp-audit-relay.io" in canary_rec["email"] or "sec-monitor-vault.net" in canary_rec["email"] or "honey-mesh-telemetry.org" in canary_rec["email"]

    # Verify detection
    extracted = extract_canary_from_record(canary_rec)
    assert extracted is not None
    assert extracted[0] == agent_id


def test_allocation_with_canaries():
    """Verify smart allocation distributes records and injects canaries."""
    agents = [
        Agent(id="AGT-1", name="Agent 1", organization="Org 1", contact_email="a1@test.com"),
        Agent(id="AGT-2", name="Agent 2", organization="Org 2", contact_email="a2@test.com"),
        Agent(id="AGT-3", name="Agent 3", organization="Org 3", contact_email="a3@test.com")
    ]
    records = [{"_record_id": f"REC-{i:03d}", "name": f"Person {i}", "email": f"p{i}@test.com"} for i in range(50)]

    config = AllocationConfig(
        dataset_id="DS-TEST",
        agent_ids=["AGT-1", "AGT-2", "AGT-3"],
        records_per_agent=25,
        allocation_strategy="overlap_minimization",
        canary_injection_rate=0.08  # 8% of 25 is ~2 canaries
    )

    result_meta, agent_pkgs = allocate_dataset("DS-TEST", records, agents, config, "Fintech")

    assert result_meta.dataset_id == "DS-TEST"
    assert len(agent_pkgs) == 3
    for a_id in ["AGT-1", "AGT-2", "AGT-3"]:
        pkg = agent_pkgs[a_id]
        # 25 genuine records + 2 canaries = 27 total
        assert len(pkg) == 27
        canary_count = sum(1 for r in pkg if r.get("_is_canary"))
        assert canary_count == 2


def test_guilt_attribution_model_accuracy():
    """Verify that an agent who leaks data is accurately flagged as top suspect with 100% canary confidence."""
    agents = [
        Agent(id="AGT-A", name="Vendor Alpha", organization="Alpha Corp", contact_email="a@test.com"),
        Agent(id="AGT-B", name="Vendor Beta", organization="Beta Corp", contact_email="b@test.com"),
        Agent(id="AGT-C", name="Vendor Gamma", organization="Gamma Corp", contact_email="c@test.com")
    ]
    records = [{"_record_id": f"REC-{i:03d}", "email": f"client{i}@corp.com", "balance": 1000 + i} for i in range(60)]

    config = AllocationConfig(
        dataset_id="DS-TEST-2",
        agent_ids=["AGT-A", "AGT-B", "AGT-C"],
        records_per_agent=30,
        allocation_strategy="overlap_minimization",
        canary_injection_rate=0.05
    )

    result_meta, agent_pkgs = allocate_dataset("DS-TEST-2", records, agents, config, "Fintech")

    # Find the canary record for Alpha and ensure it's in the leak
    alpha_pkg = agent_pkgs["AGT-A"]
    canary_recs = [r for r in alpha_pkg if r.get("_is_canary")]
    genuine_recs = [r for r in alpha_pkg if not r.get("_is_canary")]

    leaked_dump = genuine_recs[:18] + canary_recs

    analysis = calculate_guilt_probabilities(
        dataset_id="DS-TEST-2",
        leaked_records=leaked_dump,
        agents=agents,
        allocations_map=result_meta.allocations,
        agent_full_packages=agent_pkgs,
        leak_source_name="Dark Web Alpha Dump",
        independent_leak_prob_p=0.05
    )

    assert analysis.top_suspect_id == "AGT-A"
    assert analysis.highest_probability == 1.0
    assert analysis.canary_confirmed_agent_id == "AGT-A"
    assert analysis.agent_scores[0].verdict == "CONFIRMED_LEAKER"

    # Also test genuine-only attribution (without canary)
    analysis_no_canary = calculate_guilt_probabilities(
        dataset_id="DS-TEST-2",
        leaked_records=genuine_recs[:20],
        agents=agents,
        allocations_map=result_meta.allocations,
        agent_full_packages=agent_pkgs,
        leak_source_name="Dark Web Alpha Dump (No Canaries)",
        independent_leak_prob_p=0.05
    )
    assert analysis_no_canary.top_suspect_id == "AGT-A"
    assert analysis_no_canary.highest_probability >= 0.90


def test_api_health():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_datasets_and_agents():
    """Test dataset and agent API endpoints."""
    res_ds = client.get("/api/datasets")
    assert res_ds.status_code == 200
    assert len(res_ds.json()) >= 2

    res_ag = client.get("/api/agents")
    assert res_ag.status_code == 200
    assert len(res_ag.json()) >= 4


def test_api_simulation_and_report():
    """Test live breach simulation and forensic report generation."""
    sim_payload = {
        "dataset_id": "DS-FINTECH-01",
        "scenario": "single_agent_leak",
        "target_agent_id": "AGT-ALPHA",
        "leak_percentage": 0.6,
        "noise_records_count": 2
    }
    res_sim = client.post("/api/simulation/breach", json=sim_payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert sim_data["actual_culprit_ids"] == ["AGT-ALPHA"]
    assert sim_data["attribution_success"] is True

    analysis_id = sim_data["analysis_result"]["analysis_id"]

    # Test HTML report endpoint
    res_html = client.get(f"/api/reports/{analysis_id}/html")
    assert res_html.status_code == 200
    assert "Data Breach Attribution Forensic Report" in res_html.text

    # Test SIEM webhook simulation
    res_siem = client.post("/api/reports/siem-test", json={"analysis_id": analysis_id, "siem_type": "Splunk"})
    assert res_siem.status_code == 200
    assert res_siem.json()["event_type"] == "DATA_LEAKAGE_ATTRIBUTION_ALERT"
