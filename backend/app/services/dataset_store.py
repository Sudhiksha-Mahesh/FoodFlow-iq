"""
Dataset session management.

Metadata (name, status, row/col counts, detected schema) lives in the SQL
database (SQLite by default, Postgres in production). The actual dataframes
(raw + cleaned + transformed) are cached on disk as parquet files, keyed by
dataset id, so repeated dashboard requests don't re-parse the CSV every time.
"""
import os
import json
import uuid
import shutil
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.models.db import DatasetRecord
from app.utils.schema_detection import detect_roles
from app.etl.profiling import profile_dataset
from app.etl.cleaning import clean_dataset
from app.etl.transform import apply_transformations

RAW_DIR = os.path.join(settings.STORAGE_DIR, "raw")
PROCESSED_DIR = os.path.join(settings.STORAGE_DIR, "processed")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# small in-process cache to avoid re-reading parquet on every request within one server run
_df_cache: Dict[str, pd.DataFrame] = {}


def new_dataset_id() -> str:
    return "ds_" + uuid.uuid4().hex[:12]


def create_dataset(db: Session, name: str, df: pd.DataFrame, is_sample: bool = False) -> DatasetRecord:
    dataset_id = new_dataset_id()
    raw_path = os.path.join(RAW_DIR, f"{dataset_id}.parquet")
    df.to_parquet(raw_path)

    role_map = detect_roles(df)

    record = DatasetRecord(
        id=dataset_id,
        name=name,
        uploaded_at=datetime.utcnow(),
        rows=len(df),
        columns=len(df.columns),
        status="uploaded",
        raw_path=raw_path,
        clean_path=None,
        schema_json=json.dumps(role_map),
        profile_json=None,
        is_sample=is_sample,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    _df_cache[f"{dataset_id}:raw"] = df
    return record


def get_dataset(db: Session, dataset_id: str) -> Optional[DatasetRecord]:
    return db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()


def list_datasets(db: Session):
    return db.query(DatasetRecord).order_by(DatasetRecord.uploaded_at.desc()).all()


def delete_dataset(db: Session, dataset_id: str) -> bool:
    record = get_dataset(db, dataset_id)
    if not record:
        return False
    for path in [record.raw_path, record.clean_path]:
        if path and os.path.exists(path):
            os.remove(path)
    _df_cache.pop(f"{dataset_id}:raw", None)
    _df_cache.pop(f"{dataset_id}:clean", None)
    db.delete(record)
    db.commit()
    return True


def load_raw_df(record: DatasetRecord) -> pd.DataFrame:
    key = f"{record.id}:raw"
    if key not in _df_cache:
        _df_cache[key] = pd.read_parquet(record.raw_path)
    return _df_cache[key]


def load_clean_df(record: DatasetRecord) -> Optional[pd.DataFrame]:
    if not record.clean_path or not os.path.exists(record.clean_path):
        return None
    key = f"{record.id}:clean"
    if key not in _df_cache:
        _df_cache[key] = pd.read_parquet(record.clean_path)
    return _df_cache[key]


def run_profile(db: Session, record: DatasetRecord) -> Dict[str, Any]:
    df = load_raw_df(record)
    profile = profile_dataset(df)
    record.profile_json = json.dumps(profile)
    record.status = "profiled"
    db.commit()
    return profile


def run_clean_and_transform(db: Session, record: DatasetRecord, options: Dict[str, Any]) -> Dict[str, Any]:
    df = load_raw_df(record)
    result = clean_dataset(df, options)
    cleaned = result["dataframe"]

    role_map = json.loads(record.schema_json) if record.schema_json else detect_roles(df)
    transformed = apply_transformations(cleaned, role_map)

    clean_path = os.path.join(PROCESSED_DIR, f"{record.id}_clean.parquet")
    transformed.to_parquet(clean_path)
    record.clean_path = clean_path
    record.status = "ready"
    db.commit()

    _df_cache[f"{record.id}:clean"] = transformed

    return {
        "before": result["before"],
        "after": result["after"],
        "rows_removed": result["rows_removed"],
        "derived_columns": [c for c in transformed.columns if c not in df.columns],
    }


def get_working_df(record: DatasetRecord) -> pd.DataFrame:
    """Returns the cleaned+transformed dataframe if available, else raw."""
    clean = load_clean_df(record)
    if clean is not None:
        return clean
    return load_raw_df(record)


def get_role_map(record: DatasetRecord) -> Dict[str, str]:
    return json.loads(record.schema_json) if record.schema_json else {}
