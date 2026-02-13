<p align="center">
  <h1 align="center">Shadowserver Ingestor</h1>
  <p align="center">
    Fetches scan reports from the <a href="https://www.shadowserver.org/">Shadowserver</a> API and writes them to PostgreSQL.<br>
    Designed to pair with <a href="https://github.com/Pr0mp7/iris-data-explorer">IRIS Data Explorer</a> for DFIR-IRIS case correlation.
  </p>
</p>

<p align="center">
  <a href="https://github.com/Pr0mp7/shadowserver-ingestor/releases"><img src="https://img.shields.io/github/v/release/Pr0mp7/shadowserver-ingestor?style=flat-square&color=blue" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-LGPL--3.0-blue?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.13-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/docker-ready-blue?style=flat-square&logo=docker&logoColor=white" alt="Docker">
</p>

---

## Features

- **HMAC-SHA256 authenticated** API client
- **CSV report download** from `dl.shadowserver.org/{id}`
- **SHA256-based dedup** — no duplicate events on re-ingestion
- **Scheduled ingestion** every 15 minutes (configurable)
- **Auto-backfill** on first start (default: 7 days)
- **Health endpoint** for Docker healthchecks
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

The ingestor auto-creates the database schema on first start.

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

<details>
<summary><strong>ss_events</strong> — all events from all report types</summary>

Hybrid schema: indexed common columns + JSONB for complete data.

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

</details>

<details>
<summary><strong>ss_reports</strong> — tracks ingested report types per date</summary>

Records which reports have been ingested and when, with event counts.

</details>

<details>
<summary><strong>ss_ingestion_log</strong> — audit trail</summary>

Logs every ingestion run: start/finish timestamps, status, events ingested/skipped, and error messages.

</details>

## Database Setup

```sql
CREATE DATABASE shadowserver_db;
CREATE USER shadowserver_ingestor WITH PASSWORD 'your-password';
GRANT ALL ON DATABASE shadowserver_db TO shadowserver_ingestor;

-- Optional: read-only user for IRIS Data Explorer
CREATE USER shadowserver_viewer WITH PASSWORD 'your-password';
-- (SELECT grants are applied automatically by schema.py)
```

## Related

- **[iris-data-explorer](https://github.com/Pr0mp7/iris-data-explorer)** — interactive case data explorer that reads from this service's database
- **[DFIR-IRIS](https://github.com/dfir-iris/iris-web)** — the incident response platform

## License

[LGPL-3.0](LICENSE)
