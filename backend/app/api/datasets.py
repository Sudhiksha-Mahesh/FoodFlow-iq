import io
import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import json

from app.models.db import get_session
from app.services import dataset_store
from app.utils.schema_detection import detect_roles, compatibility_report, module_availability
from app.etl.profiling import profile_dataset
from app.schemas.requests import CleanOptions
from app.config import settings

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

# Sample dataset is located via env var (set explicitly in docker-compose) with
# sensible local-development fallbacks so `uvicorn app.main:app` works whether
# run from the backend/ directory or the repo root.
def _resolve_sample_path() -> str:
    env_path = os.getenv("SAMPLE_CSV_PATH")
    candidates = [
        env_path,
        os.path.join(os.getcwd(), "data", "sample_food_delivery_orders.csv"),
        os.path.join(os.getcwd(), "..", "data", "sample_food_delivery_orders.csv"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "sample_food_delivery_orders.csv"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return candidates[-1]

SAMPLE_CSV_PATH = _resolve_sample_path()


def _validate_and_read(content: bytes, filename: str) -> pd.DataFrame:
    if not filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only .csv files are supported.")
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(400, f"File too large ({size_mb:.1f}MB). Maximum allowed is {settings.MAX_UPLOAD_MB}MB.")
    try:
        df = pd.read_csv(io.BytesIO(content), encoding="utf-8", on_bad_lines="skip")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(io.BytesIO(content), encoding="latin-1", on_bad_lines="skip")
        except Exception as e:
            raise HTTPException(400, f"Could not decode CSV file: {e}")
    except Exception as e:
        raise HTTPException(400, f"Corrupt or unreadable CSV file: {e}")

    if df.empty or len(df.columns) == 0:
        raise HTTPException(400, "The uploaded dataset is empty.")

    # duplicate column name check
    if len(df.columns) != len(set(df.columns)):
        dupes = [c for c in df.columns if list(df.columns).count(c) > 1]
        raise HTTPException(400, f"Dataset contains duplicate column names: {set(dupes)}. Please fix and re-upload.")

    role_map = detect_roles(df)
    if "order_date" not in role_map and "subtotal" not in role_map:
        raise HTTPException(
            400,
            "Dataset cannot be analysed. Reason: No date column and no numeric revenue/amount column were "
            "detected. Please upload a transactional dataset containing at least: Date, Transaction/Order "
            "information, and a numeric amount/revenue field."
        )

    return df


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_session)):
    content = await file.read()
    df = _validate_and_read(content, file.filename)
    record = dataset_store.create_dataset(db, name=file.filename, df=df)
    profile = dataset_store.run_profile(db, record)
    role_map = dataset_store.get_role_map(record)

    return {
        "dataset_id": record.id,
        "name": record.name,
        "rows": record.rows,
        "columns": record.columns,
        "profile": profile,
        "compatibility": compatibility_report(role_map),
        "module_availability": module_availability(role_map, n_customers=(df[role_map["customer_id"]].nunique() if "customer_id" in role_map else None)),
    }


@router.post("/load-sample")
def load_sample_dataset(db: Session = Depends(get_session)):
    if not os.path.exists(SAMPLE_CSV_PATH):
        raise HTTPException(404, "Sample dataset not found on server.")
    with open(SAMPLE_CSV_PATH, "rb") as f:
        content = f.read()
    df = _validate_and_read(content, "sample_food_delivery_orders.csv")
    record = dataset_store.create_dataset(db, name="sample_food_delivery_orders.csv", df=df, is_sample=True)
    profile = dataset_store.run_profile(db, record)
    role_map = dataset_store.get_role_map(record)
    return {
        "dataset_id": record.id,
        "name": record.name,
        "rows": record.rows,
        "columns": record.columns,
        "profile": profile,
        "compatibility": compatibility_report(role_map),
        "module_availability": module_availability(role_map, n_customers=(df[role_map["customer_id"]].nunique() if "customer_id" in role_map else None)),
    }


@router.get("")
def list_datasets(db: Session = Depends(get_session)):
    records = dataset_store.list_datasets(db)
    return [{
        "dataset_id": r.id, "name": r.name, "uploaded_at": r.uploaded_at.isoformat(),
        "rows": r.rows, "columns": r.columns, "status": r.status, "is_sample": r.is_sample,
    } for r in records]


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str, db: Session = Depends(get_session)):
    record = dataset_store.get_dataset(db, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found.")
    role_map = dataset_store.get_role_map(record)
    df = dataset_store.load_raw_df(record)
    return {
        "dataset_id": record.id, "name": record.name, "rows": record.rows, "columns": record.columns,
        "status": record.status, "uploaded_at": record.uploaded_at.isoformat(),
        "compatibility": compatibility_report(role_map),
        "module_availability": module_availability(role_map, n_customers=(df[role_map["customer_id"]].nunique() if "customer_id" in role_map else None)),
        "detected_roles": role_map,
    }


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_session)):
    ok = dataset_store.delete_dataset(db, dataset_id)
    if not ok:
        raise HTTPException(404, "Dataset not found.")
    return {"deleted": True}


@router.get("/{dataset_id}/profile")
def get_profile(dataset_id: str, db: Session = Depends(get_session)):
    record = dataset_store.get_dataset(db, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found.")
    if record.profile_json:
        profile = json.loads(record.profile_json)
    else:
        df = dataset_store.load_raw_df(record)
        profile = profile_dataset(df)
    return profile


@router.post("/{dataset_id}/clean")
def clean_dataset_endpoint(dataset_id: str, options: CleanOptions, db: Session = Depends(get_session)):
    record = dataset_store.get_dataset(db, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found.")
    result = dataset_store.run_clean_and_transform(db, record, options.dict())
    return result
