"""
SQLAlchemy persistence layer.

Works out-of-the-box against SQLite (zero config) and against PostgreSQL when
DATABASE_URL is set to a postgres DSN — no code changes required, only config.

DatasetRecord stores dataset session/session-management metadata (Section 23).
The actual dataframe (raw + cleaned) is cached on disk as parquet, referenced
by file path, to keep the relational DB lightweight -- this mirrors how real
BI platforms separate metadata (SQL) from bulk analytical data (columnar files).
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class DatasetRecord(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    rows = Column(Integer, default=0)
    columns = Column(Integer, default=0)
    status = Column(String, default="uploaded")  # uploaded | profiled | cleaned | ready | error
    raw_path = Column(String)
    clean_path = Column(String)
    schema_json = Column(Text)          # detected column-role mapping
    profile_json = Column(Text)         # cached profiling result
    is_sample = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
