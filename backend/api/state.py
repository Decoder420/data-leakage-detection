"""In-memory state and repository for datasets, agents, allocations, and analysis results."""

import uuid
from typing import Dict, List, Any
from faker import Faker

from backend.engine.models import (
    Agent,
    DatasetMeta,
    AllocationConfig,
    AllocationResult,
    LeakAnalysisResult
)
from backend.engine.allocation import allocate_dataset

fake = Faker()
Faker.seed(42)


class AppState:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.datasets: Dict[str, DatasetMeta] = {}
        self.raw_records: Dict[str, List[Dict[str, Any]]] = {}
        self.allocations: Dict[str, AllocationResult] = {}
        self.agent_packages: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}  # dataset_id -> {agent_id: [records]}
        self.analysis_history: List[LeakAnalysisResult] = []
        self._initialize_demo_data()

    def _initialize_demo_data(self):
        """Pre-populate realistic demo enterprise data so the system works out-of-the-box."""
        # 1. Initialize 4 Third-Party Vendors / Agents
        demo_agents = [
            Agent(id="AGT-ALPHA", name="Alpha Analytics Corp", organization="Alpha Corp", contact_email="security@alpha-analytics.io", risk_level="Medium", trust_score=88.0),
            Agent(id="AGT-BETA", name="Beta Cloud Solutions", organization="Beta Cloud LLC", contact_email="compliance@betacloud.com", risk_level="Low", trust_score=94.0),
            Agent(id="AGT-GAMMA", name="Gamma AI Research Labs", organization="Gamma AI", contact_email="data@gamma-research.org", risk_level="High", trust_score=72.0),
            Agent(id="AGT-DELTA", name="Delta Growth Marketing", organization="Delta Media", contact_email="ops@deltagrowth.io", risk_level="Critical", trust_score=65.0),
        ]
        for a in demo_agents:
            self.agents[a.id] = a

        # 2. Initialize Fintech Dataset (100 records)
        fintech_records = []
        for i in range(100):
            first_name = fake.first_name()
            last_name = fake.last_name()
            rec = {
                "_record_id": f"REC-FIN-{i+1:04d}",
                "customer_id": f"CUST-99{i+1:03d}",
                "full_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
                "phone": fake.phone_number(),
                "ssn": fake.ssn(),
                "credit_score": fake.random_int(min=590, max=830),
                "account_balance": round(fake.random_number(digits=5) + 0.50, 2),
                "account_tier": fake.random_element(["Platinum", "Gold", "Silver", "Preferred"]),
                "kyc_status": "Verified"
            }
            fintech_records.append(rec)

        fintech_meta = DatasetMeta(
            id="DS-FINTECH-01",
            name="Global Banking & Wealth Customer PII",
            category="Fintech",
            description="High-value client financial records, SSNs, credit ratings, and KYC status.",
            total_records=len(fintech_records),
            columns=list(fintech_records[0].keys())
        )
        self.datasets[fintech_meta.id] = fintech_meta
        self.raw_records[fintech_meta.id] = fintech_records

        # 3. Initialize Healthcare Dataset (80 records)
        health_records = []
        for i in range(80):
            first_name = fake.first_name()
            last_name = fake.last_name()
            rec = {
                "_record_id": f"REC-MED-{i+1:04d}",
                "patient_id": f"MED-PAT-{i+1:04d}",
                "patient_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
                "primary_diagnosis": fake.random_element(["Type 2 Diabetes", "Coronary Artery Disease", "Asthma", "Hypertension", "Rheumatoid Arthritis"]),
                "treating_physician": f"Dr. {fake.last_name()}, MD",
                "insurance_provider": fake.random_element(["BlueCross BlueShield", "UnitedHealthcare", "Aetna", "Kaiser Permanente"]),
                "treatment_status": fake.random_element(["Active Outpatient", "In Remission", "Observation", "Scheduled Surgery"])
            }
            health_records.append(rec)

        health_meta = DatasetMeta(
            id="DS-HEALTH-02",
            name="Clinical Patient Treatment & EHR Records",
            category="Healthcare",
            description="Confidential HIPAA-regulated electronic health records and diagnosis histories.",
            total_records=len(health_records),
            columns=list(health_records[0].keys())
        )
        self.datasets[health_meta.id] = health_meta
        self.raw_records[health_meta.id] = health_records

        # 4. Pre-compute Default Allocation for Fintech Dataset across all 4 agents
        alloc_config = AllocationConfig(
            dataset_id=fintech_meta.id,
            agent_ids=[a.id for a in demo_agents],
            records_per_agent=65,
            allocation_strategy="overlap_minimization",
            canary_injection_rate=0.03
        )
        alloc_meta, agent_pkgs = allocate_dataset(
            fintech_meta.id,
            fintech_records,
            demo_agents,
            alloc_config,
            category="Fintech"
        )
        self.allocations[fintech_meta.id] = alloc_meta
        self.agent_packages[fintech_meta.id] = agent_pkgs


state = AppState()
