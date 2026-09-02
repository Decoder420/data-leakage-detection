"""Dataset management API endpoints."""

import io
import csv
import json
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from faker import Faker

from backend.engine.models import DatasetMeta
from backend.api.state import state

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])
fake = Faker()


class GenerateDatasetRequest(BaseModel):
    name: str
    category: str  # Fintech, Healthcare, Enterprise HR, E-Commerce
    num_records: int = 100


@router.get("", response_model=List[DatasetMeta])
def get_all_datasets():
    """List all available enterprise datasets."""
    return list(state.datasets.values())


@router.get("/{dataset_id}")
def get_dataset_details(dataset_id: str):
    """Get metadata and sample records for a dataset."""
    if dataset_id not in state.datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    meta = state.datasets[dataset_id]
    records = state.raw_records.get(dataset_id, [])
    return {
        "metadata": meta,
        "sample_records": records[:10],
        "total_count": len(records)
    }


@router.post("/generate", response_model=DatasetMeta)
def generate_synthetic_dataset(req: GenerateDatasetRequest):
    """Generate a realistic synthetic dataset for testing."""
    records = []
    category = req.category

    for i in range(req.num_records):
        first_name = fake.first_name()
        last_name = fake.last_name()
        rec_id = f"REC-{category[:3].upper()}-{i+1:04d}"

        if category == "Fintech":
            rec = {
                "_record_id": rec_id,
                "customer_id": f"CUST-99{i+1:03d}",
                "full_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
                "phone": fake.phone_number(),
                "ssn": fake.ssn(),
                "credit_score": fake.random_int(min=590, max=830),
                "account_balance": round(fake.random_number(digits=5) + 0.50, 2),
                "kyc_status": "Verified"
            }
        elif category == "Healthcare":
            rec = {
                "_record_id": rec_id,
                "patient_id": f"MED-PAT-{i+1:04d}",
                "patient_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
                "primary_diagnosis": fake.random_element(["Type 2 Diabetes", "Asthma", "Arrhythmia", "Hypertension"]),
                "treating_physician": f"Dr. {fake.last_name()}, MD",
                "insurance_provider": fake.random_element(["BlueCross", "UnitedHealth", "Aetna"]),
                "treatment_status": "Active Outpatient"
            }
        elif category == "Enterprise HR":
            rec = {
                "_record_id": rec_id,
                "employee_id": f"EMP-10{i+1:03d}",
                "name": f"{first_name} {last_name}",
                "work_email": f"{first_name.lower()}.{last_name.lower()}@enterprise-corp.internal",
                "department": fake.random_element(["Engineering", "Cybersecurity", "Finance", "Legal", "HR"]),
                "role_title": fake.job(),
                "salary_band": f"${fake.random_int(min=80, max=220)}k",
                "clearance_level": fake.random_element(["Confidential", "Secret", "Internal", "Restricted"])
            }
        else:  # E-Commerce
            rec = {
                "_record_id": rec_id,
                "buyer_id": f"BUYER-{i+1:04d}",
                "name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
                "shipping_address": fake.address().replace("\n", ", "),
                "lifetime_spend": round(fake.random_number(digits=4) + 0.99, 2),
                "membership_tier": fake.random_element(["VIP Gold", "Prime", "Standard"])
            }
        records.append(rec)

    new_id = f"DS-{category[:4].upper()}-{uuid.uuid4().hex[:6].upper()}"
    meta = DatasetMeta(
        id=new_id,
        name=req.name,
        category=category,
        description=f"Generated synthetic {category} dataset with {len(records)} realistic records.",
        total_records=len(records),
        columns=list(records[0].keys())
    )
    state.datasets[new_id] = meta
    state.raw_records[new_id] = records
    return meta


@router.post("/upload", response_model=DatasetMeta)
async def upload_dataset_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form("Fintech"),
    description: str = Form("")
):
    """Upload a CSV or JSON dataset."""
    contents = await file.read()
    filename = file.filename or "uploaded.csv"
    records = []

    try:
        if filename.endswith(".json"):
            records = json.loads(contents.decode("utf-8"))
        else:
            decoded = contents.decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded))
            records = [dict(row) for row in reader]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse dataset file: {str(e)}")

    if not records:
        raise HTTPException(status_code=400, detail="Uploaded dataset file contains no records.")

    # Assign IDs if missing
    for idx, rec in enumerate(records):
        if "_record_id" not in rec and "id" not in rec:
            rec["_record_id"] = f"REC-UPL-{idx+1:04d}"

    new_id = f"DS-UPL-{uuid.uuid4().hex[:6].upper()}"
    meta = DatasetMeta(
        id=new_id,
        name=name,
        category=category,
        description=description or f"Custom uploaded dataset ({filename}) with {len(records)} records.",
        total_records=len(records),
        columns=list(records[0].keys())
    )
    state.datasets[new_id] = meta
    state.raw_records[new_id] = records
    return meta
