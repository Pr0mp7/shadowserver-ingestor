# Shadowserver Ingestor

Standalone service that fetches scan reports from the [Shadowserver](https://www.shadowserver.org/) API and writes them to PostgreSQL. Designed to pair with [IRIS Data Explorer](https://github.com/Pr0mp7/iris-data-explorer) for correlation with DFIR-IRIS case data.

## Features

- **HMAC-SHA256 authenticated** API client
- **CSV report download** from `dl.shadowserver.org/{id}`
- **SHA256-based dedup** — no duplicate events on re-ingestion
- **Scheduled ingestion** every 15 minutes (configurable)
- **Auto-backfill** on first start (default: 7 days)
- **Health endpoint** on port 8088 for Docker healthchecks
- **Ingestion audit log** — tracks every run with event counts and errors
- **Per-report error handling** — one failure doesn't stop other reports

## Quick Start

```bash
git clone https://github.com/Pr0mp7/shadowserver-ingestor.git
cd shadowserver-ingestor
cp .env.example .env
# Edit .env with your Shadowserver API key/secret and DB credentials
docker compose up -d
```

## Prerequisites

- PostgreSQL database with a read-write user
- Shadowserver API key and secret ([request access](https://www.shadowserver.org/what-we-do/network-reporting/))

The ingestor auto-creates the database schema (`ss_events`, `ss_reports`, `ss_ingestion_log`) on first start.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SS_API_KEY` | *(required)* | Shadowserver API key |
| `SS_API_SECRET` | *(required)* | Shadowserver API secret |
| `SS_API_URL` | `https://transform.shadowserver.org/api2/` | API base URL |
| `DB_HOST` | `postgres` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `shadowserver_db` | Database name |
| `DB_USER` | `shadowserver_ingestor` | Database user (needs read-write) |
| `DB_PASSWORD` | *(required)* | Database password |
| `INGEST_INTERVAL_MINUTES` | `15` | Scheduled ingestion interval |
| `BACKFILL_DAYS` | `7` | Days to backfill on first start |
| `REQUEST_DELAY_SECONDS` | `1.0` | Delay between API calls |
| `HEALTH_PORT` | `8088` | Health endpoint port |

## CLI Modes

```bash
# Test API connectivity
docker exec shadowserver-ingestor python -m ingestor.main --ping

# Run one ingestion cycle and exit
docker exec shadowserver-ingestor python -m ingestor.main --once

# Backfill specific number of days and exit
docker exec shadowserver-ingestor python -m ingestor.main --backfill 30
```

## Database Schema

### ss_events
All events from all report types. Hybrid schema: indexed common columns + JSONB for complete data.

| Column | Type | Description |
|--------|------|-------------|
| `report_type` | TEXT | e.g., scan_ssl, device_id, scan_http |
| `report_date` | DATE | Report date |
| `ip` | INET | Source/target IP |
| `port` | INTEGER | Port number |
| `asn` | INTEGER | Autonomous System Number |
| `geo` | TEXT | Country code |
| `hostname` | TEXT | Hostname |
| `tag` | TEXT | Shadowserver tags |
| `severity` | TEXT | low, medium, high |
| `raw_data` | JSONB | Complete event as received |
| `event_hash` | TEXT | SHA256 for dedup |

**Dedup**: `UNIQUE(report_type, report_date, event_hash)`

### ss_reports
Tracks which report types have been ingested per date.

### ss_ingestion_log
Audit trail: run start/finish, status, event counts, errors.

## Database Setup

```sql
CREATE DATABASE shadowserver_db;
CREATE USER shadowserver_ingestor WITH PASSWORD 'your-password';
GRANT ALL ON DATABASE shadowserver_db TO shadowserver_ingestor;

-- Optional: read-only user for IRIS Data Explorer
CREATE USER shadowserver_viewer WITH PASSWORD 'your-password';
-- (SELECT grants are applied automatically by schema.py)
```

## Architecture

```
Shadowserver API ──HTTPS/HMAC──► shadowserver-ingestor
  reports/list                        │
  dl.shadowserver.org/{id} (CSV)      │ writes every 15min
                                      ▼
                               PostgreSQL (shadowserver_db)
                                      │
                                      │ reads (optional)
                                      ▼
                               IRIS Data Explorer (port 8087)
```

## License

LGPL-3.0 — see [LICENSE](LICENSE).
