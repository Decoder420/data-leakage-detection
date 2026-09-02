"""FastAPI Application Main Entry Point — DecodeX Security Technologies Private Limited."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import init_db, SessionLocal
from backend.app.api.v1.router import api_router
from backend.api.main import app as legacy_app
from backend.app.models.agent import Agent
from backend.app.models.dataset import Dataset, DatasetRecord
from backend.app.models.integration_setting import IntegrationSetting
from faker import Faker

fake = Faker()
Faker.seed(42)


def seed_default_data():
    """Seed initial demo datasets, vendors, and integration settings if empty."""
    db = SessionLocal()
    try:
        # 1. Seed Integration Setting
        if not db.query(IntegrationSetting).first():
            setting = IntegrationSetting(
                id="cfg_decodex_default",
                target_name="DecodeX Threat Hunting Platform",
                endpoint_url="http://localhost:8001/api/v1/alerts",
                is_enabled=True
            )
            db.add(setting)

        # 2. Seed Agents
        if db.query(Agent).count() == 0:
            demo_agents = [
                Agent(id="AGT-ALPHA", name="Alpha Analytics Corp", organization="Alpha Corp", contact_email="security@alpha-analytics.io", risk_level="Medium", trust_score=88.0),
                Agent(id="AGT-BETA", name="Beta Cloud Solutions", organization="Beta Cloud LLC", contact_email="compliance@betacloud.com", risk_level="Low", trust_score=94.0),
                Agent(id="AGT-GAMMA", name="Gamma AI Research Labs", organization="Gamma AI", contact_email="data@gamma-research.org", risk_level="High", trust_score=72.0),
                Agent(id="AGT-DELTA", name="Delta Growth Marketing", organization="Delta Media", contact_email="ops@deltagrowth.io", risk_level="Critical", trust_score=65.0),
            ]
            for a in demo_agents:
                db.add(a)

        # 3. Seed Fintech Dataset
        if db.query(Dataset).count() == 0:
            fintech_id = "DS-FINTECH-01"
            fintech_ds = Dataset(
                id=fintech_id,
                name="Global Banking & Wealth Customer PII",
                category="Fintech",
                description="High-value client financial records, SSNs, credit ratings, and KYC status.",
                total_records=100,
                columns=["id", "customer_name", "email", "ssn", "credit_score", "account_balance", "account_tier"]
            )
            db.add(fintech_ds)
            db.flush()

            for i in range(100):
                first_name = fake.first_name()
                last_name = fake.last_name()
                rec = {
                    "id": f"REC-FIN-{i+1:04d}",
                    "customer_name": f"{first_name} {last_name}",
                    "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
                    "ssn": fake.ssn(),
                    "credit_score": fake.random_int(min=590, max=830),
                    "account_balance": round(fake.random_number(digits=5) + 0.50, 2),
                    "account_tier": fake.random_element(["Platinum", "Gold", "Preferred"])
                }
                dr = DatasetRecord(
                    id=f"dr_{i+1:04d}",
                    dataset_id=fintech_id,
                    record_hash=f"REC-FIN-{i+1:04d}",
                    data=rec,
                    is_canary=False
                )
                db.add(dr)

        db.commit()
    finally:
        db.close()


# Initialize Database tables and demo data on load
init_db()
seed_default_data()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_default_data()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Enterprise Data Leakage Detection & Cyber Attribution Platform. "
        "Exposes REST API endpoints for seamless integration with the DecodeX Threat Hunting SOC. "
        "Developed by DecodeX Security Technologies Private Limited."
    ),
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount /api/v1 Router
app.include_router(api_router)

# Mount legacy router for backward compatibility with existing UI
app.mount("/api_legacy", legacy_app)


@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "owning_organization": settings.OWNING_ORGANIZATION,
        "copyright": settings.COPYRIGHT,
        "api_docs": "/docs",
        "api_v1": "/api/v1/health",
        "integration_target": "DecodeX Threat Hunting SOC"
    }


# Static Frontend Mount
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
