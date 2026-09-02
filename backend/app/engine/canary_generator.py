"""Synthetic Canary Honeytoken Generator — DecodeX Security Technologies."""

import uuid
import hmac
import hashlib
import re
from typing import Dict, Any, Optional, Tuple
from faker import Faker

fake = Faker()
Faker.seed(42)

CANARY_SECRET_KEY = "DECODEX-CANARY-HONEYTOKEN-SECRET-2026"
CANARY_TRAP_DOMAINS = [
    "corp-audit-relay.io",
    "sec-monitor-vault.net",
    "honey-mesh-telemetry.org",
    "decodex-trap.internal"
]


def generate_luhn_credit_card() -> str:
    """Generate a realistic 16-digit credit card number passing Luhn checksum verification."""
    # Prefix 4 for Visa or 5 for Mastercard
    prefix = fake.random_element(["4532", "5425", "4111", "5105"])
    digits = [int(d) for d in prefix]
    while len(digits) < 15:
        digits.append(fake.random_int(min=0, max=9))
    
    # Compute Luhn check digit
    total = 0
    for idx, d in enumerate(reversed(digits)):
        if idx % 2 == 0:
            doubled = d * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += d
    check_digit = (10 - (total % 10)) % 10
    digits.append(check_digit)
    return "".join(map(str, digits))


def generate_canary_token(agent_id: str, salt: Optional[str] = None) -> str:
    """Generate an HMAC-SHA256 authenticated canary token."""
    if not salt:
        salt = uuid.uuid4().hex[:8]
    data = f"{agent_id}:{salt}".encode("utf-8")
    token_hash = hmac.new(CANARY_SECRET_KEY.encode("utf-8"), data, hashlib.sha256).hexdigest()[:12]
    return f"CNR-{agent_id[:4].upper()}-{salt.upper()}-{token_hash.upper()}"


def generate_trap_email(agent_id: str, first_name: str, last_name: str, canary_token: str) -> str:
    domain = CANARY_TRAP_DOMAINS[hash(agent_id) % len(CANARY_TRAP_DOMAINS)]
    short_token = canary_token.split("-")[-1].lower()[:6]
    clean_first = re.sub(r'[^a-zA-Z0-9]', '', first_name).lower()
    clean_last = re.sub(r'[^a-zA-Z0-9]', '', last_name).lower()
    return f"{clean_first}.{clean_last}.{short_token}@{domain}"


def generate_canary_api_key(agent_id: str) -> str:
    token = generate_canary_token(agent_id)
    return f"dld_canary_live_{token.lower().replace('-', '_')}"


def generate_synthetic_canary(
    schema_sample: Dict[str, Any],
    agent_id: str,
    category: str = "Fintech"
) -> Dict[str, Any]:
    """
    Generates a context-aware synthetic record mirroring the schema
    and embedded with an agent-specific canary token.
    """
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

    for key, sample_val in schema_sample.items():
        if key.startswith("_"):
            continue
        key_lower = key.lower()

        if key_lower in ["id", "uid", "record_id", "patient_id", "customer_id", "emp_id", "user_id"]:
            record[key] = f"ID-{fake.random_number(digits=6, fix_len=True)}"
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
        elif "credit_card" in key_lower or "card_number" in key_lower or "pan" in key_lower:
            record[key] = generate_luhn_credit_card()
        elif "api_key" in key_lower or "token" in key_lower or "secret" in key_lower:
            record[key] = generate_canary_api_key(agent_id)
        elif "address" in key_lower or "street" in key_lower:
            record[key] = fake.street_address()
        elif "city" in key_lower:
            record[key] = fake.city()
        elif "state" in key_lower:
            record[key] = fake.state_abbr()
        elif "zip" in key_lower:
            record[key] = fake.zipcode()
        elif "credit_score" in key_lower:
            record[key] = fake.random_int(min=600, max=830)
        elif "balance" in key_lower or "amount" in key_lower:
            record[key] = round(fake.random_number(digits=5) + 0.50, 2)
        elif "diagnosis" in key_lower:
            record[key] = fake.random_element(["Type 2 Diabetes", "Hypertension", "Arrhythmia", "Asthma"])
        elif isinstance(sample_val, int):
            record[key] = fake.random_int(min=20, max=80)
        elif isinstance(sample_val, float):
            record[key] = round(fake.random_number(digits=3) * 1.5, 2)
        else:
            record[key] = fake.word().capitalize()

    return record


def extract_canary(record: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """
    Examines a leaked record for canary honeytoken signatures.
    Returns: (agent_id, canary_token) or None
    """
    if record.get("_is_canary") and record.get("_canary_agent_id"):
        return record["_canary_agent_id"], record.get("_canary_token", "UNKNOWN_TOKEN")

    for val in record.values():
        if isinstance(val, str):
            for domain in CANARY_TRAP_DOMAINS:
                if f"@{domain}" in val:
                    return "TRAP_DOMAIN_MATCH", val
            if val.startswith("CNR-"):
                return "CANARY_TOKEN_MATCH", val
            if val.startswith("dld_canary_live_"):
                return "CANARY_API_KEY_MATCH", val
    return None
