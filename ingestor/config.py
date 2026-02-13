import os


class Config:
    # Shadowserver API
    SS_API_URL = os.environ.get("SS_API_URL", "https://transform.shadowserver.org/api2/")
    SS_API_KEY = os.environ.get("SS_API_KEY", "")
    SS_API_SECRET = os.environ.get("SS_API_SECRET", "")

    # PostgreSQL
    DB_HOST = os.environ.get("DB_HOST", "postgres")
    DB_PORT = int(os.environ.get("DB_PORT", "5432"))
    DB_NAME = os.environ.get("DB_NAME", "shadowserver_db")
    DB_USER = os.environ.get("DB_USER", "shadowserver_ingestor")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

    # Ingestion
    INGEST_INTERVAL_MINUTES = int(os.environ.get("INGEST_INTERVAL_MINUTES", "15"))
    BACKFILL_DAYS = int(os.environ.get("BACKFILL_DAYS", "7"))
    REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", "1.0"))
    PAGE_SIZE = int(os.environ.get("PAGE_SIZE", "1000"))

    # Health endpoint
    HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8088"))
