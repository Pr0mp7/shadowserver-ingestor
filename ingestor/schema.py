"""Auto-create Shadowserver database tables on startup."""

import logging

import psycopg2

from .config import Config

log = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ss_events (
    id              BIGSERIAL PRIMARY KEY,
    report_type     TEXT NOT NULL,
    report_date     DATE NOT NULL,
    ip              INET,
    port            INTEGER,
    asn             INTEGER,
    geo             TEXT,
    hostname        TEXT,
    tag             TEXT,
    severity        TEXT,
    raw_data        JSONB NOT NULL,
    event_hash      TEXT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (report_type, report_date, event_hash)
);

CREATE INDEX IF NOT EXISTS idx_ss_events_ip ON ss_events (ip);
CREATE INDEX IF NOT EXISTS idx_ss_events_asn ON ss_events (asn);
CREATE INDEX IF NOT EXISTS idx_ss_events_geo ON ss_events (geo);
CREATE INDEX IF NOT EXISTS idx_ss_events_tag ON ss_events (tag);
CREATE INDEX IF NOT EXISTS idx_ss_events_severity ON ss_events (severity);
CREATE INDEX IF NOT EXISTS idx_ss_events_report_date ON ss_events (report_date);
CREATE INDEX IF NOT EXISTS idx_ss_events_report_type ON ss_events (report_type);
CREATE INDEX IF NOT EXISTS idx_ss_events_raw_data ON ss_events USING GIN (raw_data);

CREATE TABLE IF NOT EXISTS ss_reports (
    report_id       BIGSERIAL PRIMARY KEY,
    report_type     TEXT NOT NULL,
    report_date     DATE NOT NULL,
    event_count     INTEGER NOT NULL DEFAULT 0,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (report_type, report_date)
);

CREATE TABLE IF NOT EXISTS ss_ingestion_log (
    id              BIGSERIAL PRIMARY KEY,
    run_started     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_finished    TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running',
    reports_found   INTEGER DEFAULT 0,
    events_ingested INTEGER DEFAULT 0,
    events_skipped  INTEGER DEFAULT 0,
    error_message   TEXT
);
"""


def ensure_schema():
    """Create tables and indexes if they don't exist."""
    log.info("Ensuring Shadowserver database schema...")
    conn = psycopg2.connect(
        host=Config.DB_HOST, port=Config.DB_PORT, dbname=Config.DB_NAME,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
    )
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        log.info("Shadowserver schema ready.")
    finally:
        conn.close()
