"""Context-Aware Synthetic Canary & Honeytoken Generator for Data Leakage Detection."""

import hashlib
import hmac
import uuid
import re
from typing import Dict, Any, List, Optional, Tuple
from faker import Faker

fake = Faker()
Faker.seed(42)

CANARY_SECRET_KEY = "DLD-ENTERPRISE-CANARY-SECRET-2026"
CANARY_TRAP_DOMAINS = ["corp-audit-relay.io", "sec-monitor-vault.net", "honey-mesh-telemetry.org"]


def generate_canary_token(agent_id: str, salt: Optional[str] = None) -> str:
    """Generate a deterministic, unique HMAC-based canary token for an agent."""
    if not salt:
        salt = uuid.uuid4().hex[:8]
    data = f"{agent_id}:{salt}".encode("utf-8")
    token_hash = hmac.new(CANARY_SECRET_KEY.encode("utf-8"), data, hashlib.sha256).hexdigest()[:12]
    return f"CNR-{agent_id[:4].upper()}-{salt.upper()}-{token_hash.upper()}"


def generate_trap_email(agent_id: str, first_name: str, last_name: str, canary_token: str) -> str:
    """Create a realistic-looking email containing a hidden agent identifier watermark."""
    domain = CANARY_TRAP_DOMAINS[hash(agent_id) % len(CANARY_TRAP_DOMAINS)]
    short_token = canary_token.split("-")[-1].lower()[:6]
    clean_first = re.sub(r'[^a-zA-Z0-9]', '', first_name).lower()
    clean_last = re.sub(r'[^a-zA-Z0-9]', '', last_name).lower()
    return f"{clean_first}.{clean_last}.{short_token}@{domain}"


def generate_synthetic_canary_record(
    schema_sample: Dict[str, Any],
    agent_id: str,
    category: str = "Fintech"
) -> Dict[str, Any]:
    """Generate a context-aware synthetic record mirroring the schema, embedded with an agent canary."""
    canary_token = generate_canary_token(agent_id)
    record_id = f"CNR-REC-{uuid.uuid4().hex[:8].upper()}"

    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"
    trap_email = generate_trap_email(agent_id, first_name, last_name, canary_token)

    record: Dict[str, Any] = {
        "_is_canary": True,
        "_canary_agent_id": agent_id,
        "_canary_token": canary_token,
        "_record_id": record_id
    }

    # Dynamically populate fields based on schema_sample keys
    for key, sample_val in schema_sample.items():
        if key.startswith("_"):
            continue
        key_lower = key.lower()
        
        if "id" in key_lower and key_lower != "id":
            record[key] = f"ID-{fake.random_number(digits=6, fix_len=True)}"
        elif key_lower in ["id", "uid", "record_id", "patient_id", "customer_id", "emp_id"]:
            record[key] = f"CUST-{fake.random_number(digits=6, fix_len=True)}"
        elif "first_name" in key_lower:
            record[key] = first_name
        elif "last_name" in key_lower:
            record[key] = last_name
        elif "name" in key_lower:
            record[key] = full_name
        elif "email" in key_lower:
            record[key] = trap_email
        elif "phone" in key_lower:
            record[key] = fake.phone_number()
        elif "ssn" in key_lower or "tax" in key_lower:
            record[key] = fake.ssn()
        elif "address" in key_lower or "street" in key_lower:
            record[key] = fake.street_address()
        elif "city" in key_lower:
            record[key] = fake.city()
        elif "state" in key_lower:
            record[key] = fake.state_abbr()
        elif "zip" in key_lower or "postal" in key_lower:
            record[key] = fake.zipcode()
        elif "country" in key_lower:
            record[key] = "United States"
        elif "credit_score" in key_lower or "score" in key_lower:
            record[key] = fake.random_int(min=580, max=820)
        elif "balance" in key_lower or "salary" in key_lower or "amount" in key_lower:
            record[key] = round(fake.random_number(digits=5) + 0.45, 2)
        elif "diagnosis" in key_lower or "condition" in key_lower:
            record[key] = fake.random_element(["Type 2 Diabetes", "Hypertension", "Asthma", "Arrhythmia", "Osteoarthritis"])
        elif "department" in key_lower:
            record[key] = fake.random_element(["Engineering", "Security", "Marketing", "Finance", "Legal"])
        elif "role" in key_lower or "title" in key_lower:
            record[key] = fake.job()
        elif "status" in key_lower:
            record[key] = fake.random_element(["Active", "Verified", "Pending", "Approved"])
        elif "card" in key_lower or "account" in key_lower:
            record[key] = fake.credit_card_number(card_type=None)
        elif isinstance(sample_val, int):
            record[key] = fake.random_int(min=18, max=75)
        elif isinstance(sample_val, float):
            record[key] = round(fake.random_number(digits=3) * 1.25, 2)
        else:
            record[key] = fake.word().capitalize()

    return record


def extract_canary_from_record(record: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """
    Check if a record is a canary honeytoken.
    Returns (agent_id, canary_token) if verified, or None.
    """
    if record.get("_is_canary") and record.get("_canary_agent_id"):
        return record["_canary_agent_id"], record.get("_canary_token", "UNKNOWN_TOKEN")
    
    # Check email field for trap domain signatures
    for val in record.values():
        if isinstance(val, str):
            for domain in CANARY_TRAP_DOMAINS:
                if f"@{domain}" in val:
                    # Found a trap email canary!
                    return "CANARY_TRAP_DOMAIN_MATCH", val
            if val.startswith("CNR-"):
                return "CANARY_TOKEN_MATCH", val
    return None
