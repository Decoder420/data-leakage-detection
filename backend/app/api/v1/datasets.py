"""Datasets API — Ingestion, Synthesis & Schema Inspection."""

import io
import csv
import json
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from faker import Faker

from backend.app.core.database import get_db
from backend.app.core.security import get_current_auth
from backend.app.models.dataset import Dataset, DatasetRecord
from backend.app.schemas.dataset import DatasetResponse, DatasetDetailResponse, DatasetGenerateRequest

router = APIRouter(prefix="/datasets", tags=["Datasets Vault"])
fake = Faker()
Faker.seed(42)


@router.get("", response_model=List[DatasetResponse], summary="List All Monitored Datasets")
def list_datasets(db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.get("/{dataset_id}", response_model=DatasetDetailResponse, summary="Get Dataset Details & Sample Records")
def get_dataset(dataset_id: str, db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    sample_records = [
        r.data for r in db.query(DatasetRecord).filter(DatasetRecord.dataset_id == dataset_id).limit(10).all()
    ]
    
    return DatasetDetailResponse(
        id=ds.id,
        name=ds.name,
        category=ds.category,
        description=ds.description,
        total_records=ds.total_records,
        columns=ds.columns or [],
        created_at=ds.created_at,
        sample_records=sample_records
    )


@router.post("/generate", response_model=DatasetResponse, summary="Generate Realistic Synthetic Dataset")
def generate_synthetic_dataset(
    req: DatasetGenerateRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    dataset_id = f"DS-{req.category[:4].upper()}-{uuid.uuid4().hex[:6].upper()}"
    records = []
    
    for i in range(req.num_records):
        first_name = fake.first_name()
        last_name = fake.last_name()
        r_id = f"REC-{req.category[:3].upper()}-{i+1:05d}"
        
        if req.category == "Fintech":
            rec = {
                "id": r_id,
                "customer_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
                "ssn": fake.ssn(),
                "credit_score": fake.random_int(min=580, max=830),
                "account_balance": round(fake.random_number(digits=5) + 0.50, 2),
                "account_tier": fake.random_element(["Platinum", "Gold", "Preferred"])
            }
        elif req.category == "Healthcare":
            rec = {
                "id": r_id,
                "patient_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}",
                "diagnosis": fake.random_element(["Type 2 Diabetes", "Asthma", "Hypertension", "Arrhythmia"]),
                "treating_physician": f"Dr. {fake.last_name()}, MD",
                "insurance_provider": fake.random_element(["BlueCross", "UnitedHealth", "Aetna"])
            }
        else:
            rec = {
                "id": r_id,
                "employee_name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}@corp.internal",
                "department": fake.random_element(["Cybersecurity", "Engineering", "Finance", "Legal"]),
                "clearance": fake.random_element(["Secret", "Confidential", "Internal"])
            }
        records.append(rec)

    new_dataset = Dataset(
        id=dataset_id,
        name=req.name,
        category=req.category,
        description=f"Generated synthetic {req.category} dataset with {len(records)} realistic records.",
        total_records=len(records),
        columns=list(records[0].keys())
    )
    db.add(new_dataset)
    db.flush()

    for rec in records:
        r_hash = str(rec.get("id"))
        dr = DatasetRecord(
            id=f"dr_{uuid.uuid4().hex[:12]}",
            dataset_id=dataset_id,
            record_hash=r_hash,
            data=rec,
            is_canary=False
        )
        db.add(dr)

    db.commit()
    db.refresh(new_dataset)
    return new_dataset


@router.post("/upload", response_model=DatasetResponse, summary="Upload CSV or JSON Dataset")
async def upload_dataset_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form("Fintech"),
    description: str = Form(""),
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
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
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    if not records:
        raise HTTPException(status_code=400, detail="Uploaded dataset contains no rows.")

    dataset_id = f"DS-UPL-{uuid.uuid4().hex[:6].upper()}"
    new_dataset = Dataset(
        id=dataset_id,
        name=name,
        category=category,
        description=description or f"Uploaded dataset ({filename}) with {len(records)} rows.",
        total_records=len(records),
        columns=list(records[0].keys())
    )
    db.add(new_dataset)
    db.flush()

    for idx, rec in enumerate(records):
        r_hash = rec.get("id") or rec.get("_record_id") or f"REC-{idx+1:05d}"
        rec["id"] = str(r_hash)
        dr = DatasetRecord(
            id=f"dr_{uuid.uuid4().hex[:12]}",
            dataset_id=dataset_id,
            record_hash=str(r_hash),
            data=rec,
            is_canary=False
        )
        db.add(dr)

    db.commit()
    db.refresh(new_dataset)
    return new_dataset
