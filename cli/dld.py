#!/usr/bin/env python3
"""
DecodeX Data Leakage Detection & Attribution CLI (dld).
Proprietary Work Product of DecodeX Security Technologies Private Limited.
Copyright (c) 2026 DecodeX Security Technologies Private Limited. All rights reserved.
"""

import sys
import os
import csv
import json
import click
from tabulate import tabulate
from datetime import datetime, timezone

from backend.app.engine.guilt_calculator import compute_vectorized_guilt_probabilities
from backend.app.engine.allocator import allocate_dataset_records
from backend.app.engine.canary_generator import generate_synthetic_canary
from backend.app.services.alert_adapter import dispatch_event_to_decodex_soc
from backend.app.schemas.event import SecurityEvent


HEADER = """
================================================================================
  DECODEX DATA LEAKAGE DETECTION & ATTRIBUTION CLI (dld v2.1)
  DecodeX Security Technologies Private Limited
================================================================================
"""


@click.group()
def cli():
    """DecodeX DLD Command Line Interface for Data Leakage Attribution."""
    pass


@cli.command(name="distribute")
@click.option("--input", "-i", "input_file", required=True, type=click.Path(exists=True), help="Input CSV or JSON dataset path")
@click.option("--agents", "-a", required=True, help="Comma-separated agent/vendor names (e.g. vendorA,vendorB,vendorC)")
@click.option("--strategy", "-s", default="overlap_minimization", type=click.Choice(["overlap_minimization", "implicit", "zero_overlap"]), help="Allocation strategy")
@click.option("--canary-rate", "-c", default=0.03, type=float, help="Synthetic canary injection fraction (default: 0.03)")
@click.option("--output", "-o", "output_dir", default="./dist", type=click.Path(), help="Output directory for allocated agent packages")
def distribute_cmd(input_file, agents, strategy, canary_rate, output_dir):
    """Distribute dataset records across third-party agents with synthetic canary traps."""
    click.echo(HEADER)
    agent_list = [a.strip() for a in agents.split(",") if a.strip()]
    if not agent_list:
        click.secho("[-] Error: At least one agent required.", fg="red")
        sys.exit(1)

    # Read input records
    records = []
    if input_file.endswith(".json"):
        with open(input_file, "r") as f:
            records = json.load(f)
    else:
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)

    if not records:
        click.secho("[-] Error: Input file is empty.", fg="red")
        sys.exit(1)

    click.secho(f"[*] Loaded {len(records)} records from {input_file}", fg="cyan")
    click.secho(f"[*] Allocating across {len(agent_list)} agents using '{strategy}' strategy...", fg="cyan")

    record_hashes = [str(r.get("id") or r.get("_record_id") or idx) for idx, r in enumerate(records)]
    record_lookup = {h: r for h, r in zip(record_hashes, records)}

    allocations, avg_overlap, matrix = allocate_dataset_records(
        record_hashes=record_hashes,
        agent_ids=agent_list,
        strategy=strategy
    )

    os.makedirs(output_dir, exist_ok=True)
    summary_table = []
    schema_sample = records[0]

    manifest = {
        "dataset": os.path.basename(input_file),
        "allocated_at": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "avg_overlap": avg_overlap,
        "agents": {}
    }

    for agent_id in agent_list:
        assigned_hashes = allocations[agent_id]
        canary_count = max(1, int(len(assigned_hashes) * canary_rate)) if canary_rate > 0 else 0
        
        agent_records = [record_lookup[h] for h in assigned_hashes if h in record_lookup]
        canaries = []

        for _ in range(canary_count):
            c_rec = generate_synthetic_canary(schema_sample, agent_id)
            agent_records.append(c_rec)
            canaries.append(c_rec.get("_canary_token"))

        # Write agent CSV
        agent_out_file = os.path.join(output_dir, f"{agent_id}_package.csv")
        clean_keys = [k for k in agent_records[0].keys() if not k.startswith("_")]
        with open(agent_out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=clean_keys)
            writer.writeheader()
            for r in agent_records:
                writer.writerow({k: r.get(k, "") for k in clean_keys})

        summary_table.append([agent_id, len(agent_records), len(assigned_hashes), canary_count, agent_out_file])
        manifest["agents"][agent_id] = {
            "record_count": len(agent_records),
            "genuine_count": len(assigned_hashes),
            "canary_count": canary_count,
            "canary_tokens": canaries,
            "file": agent_out_file
        }

    # Save manifest for attribution
    manifest_path = os.path.join(output_dir, "allocation_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    click.echo("\n" + tabulate(summary_table, headers=["Agent / Vendor", "Total Slices", "Genuine", "Canaries", "Export File"], tablefmt="grid"))
    click.secho(f"\n[+] Allocation successfully complete! Manifest saved to {manifest_path}", fg="green", bold=True)
    click.secho(f"[+] Average Pairwise Inter-Vendor Overlap: {avg_overlap * 100:.1f}%\n", fg="cyan")


@cli.command(name="analyze")
@click.option("--leaked", "-l", required=True, type=click.Path(exists=True), help="Path to leaked CSV dump")
@click.option("--manifest", "-m", default="./dist/allocation_manifest.json", type=click.Path(exists=True), help="Allocation manifest JSON")
@click.option("--threshold", "-t", default=0.75, type=float, help="Guilt confidence threshold for alert triggering (default: 0.75)")
@click.option("--noise-p", "-p", default=0.05, type=float, help="Independent leak probability parameter p (default: 0.05)")
def analyze_cmd(leaked, manifest, threshold, noise_p):
    """Analyze a leaked breach dump and attribute guilt scores to third-party vendors."""
    click.echo(HEADER)
    click.secho(f"[*] Loading manifest from {manifest}...", fg="cyan")
    
    with open(manifest, "r") as f:
        manifest_data = json.load(f)

    # Reconstruct agent records map
    agent_record_map = {}
    canary_ownership_map = {}

    for agent_id, a_meta in manifest_data["agents"].items():
        file_path = a_meta["file"]
        if not os.path.exists(file_path):
            file_path = os.path.join(os.path.dirname(manifest), os.path.basename(file_path))
        
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rec_hashes = [r.get("id") or r.get("email") or str(idx) for idx, r in enumerate(reader)]
            agent_record_map[agent_id] = set(rec_hashes)

        for token in a_meta.get("canary_tokens", []):
            canary_ownership_map[token] = agent_id

    # Read leaked records
    with open(leaked, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        leaked_records = list(reader)

    leaked_hashes = [r.get("id") or r.get("email") or str(idx) for idx, r in enumerate(leaked_records)]
    click.secho(f"[*] Intercepted {len(leaked_hashes)} leaked records. Running vectorized guilt attribution model...", fg="cyan")

    scores = compute_vectorized_guilt_probabilities(
        leaked_record_hashes=leaked_hashes,
        agent_record_map=agent_record_map,
        canary_ownership_map=canary_ownership_map,
        independent_leak_prob_p=noise_p
    )

    table_data = []
    top_agent = None
    top_score = 0.0
    canary_found = False

    for agent_id, res in sorted(scores.items(), key=lambda x: (x[1]["canary_records_found"] > 0, x[1]["guilt_probability"]), reverse=True):
        prob = res["guilt_probability"]
        canaries = res["canary_records_found"]
        verdict = res["verdict"]

        if prob > top_score:
            top_score = prob
            top_agent = agent_id
        if canaries > 0:
            canary_found = True

        table_data.append([
            agent_id,
            f"{prob * 100:.1f}%",
            res["matching_records_count"],
            canaries,
            verdict
        ])

    click.echo("\n" + tabulate(table_data, headers=["Agent / Vendor", "Guilt Probability", "Matched Rows", "Canary Hits", "Verdict"], tablefmt="grid"))

    if canary_found or top_score >= threshold:
        click.secho(f"\n[!] HIGH CONFIDENCE ATTRIBUTION: Culprit identified as {top_agent} ({top_score*100:.1f}%)", fg="red", bold=True)
    else:
        click.secho("\n[?] Inconclusive attribution. Guilt scores remain below alert threshold.", fg="yellow")


@cli.command(name="test-soc")
@click.option("--url", "-u", default="http://localhost:8001/api/v1/alerts", help="DecodeX Threat Hunting SOC URL")
@click.option("--key", "-k", default="", help="Bearer API key")
def test_soc_cmd(url, key):
    """Test outbound alert delivery to DecodeX Threat Hunting SOC."""
    click.echo(HEADER)
    click.secho(f"[*] Sending synthetic alert probe to {url}...", fg="cyan")

    test_event = SecurityEvent(
        event_id=f"evt_cli_test_{os.urandom(4).hex()}",
        event_type="guilt_detection",
        severity="high",
        confidence_score=0.975,
        source_dataset="CLI Telemetry Probe",
        implicated_agent="Gamma AI Labs",
        evidence={"cli_invoked": True},
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    success, status, detail = dispatch_event_to_decodex_soc(test_event, db=None, max_retries=2)
    if success:
        click.secho(f"[+] Alert successfully delivered to DecodeX SOC! HTTP {status}", fg="green", bold=True)
    else:
        click.secho(f"[-] Delivery failed (Status: {status}): {detail}", fg="red")


if __name__ == "__main__":
    cli()
