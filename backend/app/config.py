import os

class Settings:
    APP_NAME: str = "FoodFlow IQ"
    # Defaults to a local SQLite file so the app works with zero configuration.
    # Set DATABASE_URL to a Postgres DSN (e.g. postgresql://user:pass@localhost:5432/foodflow)
    # for persistent, production-grade storage.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./foodflow.db")
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "50"))
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
