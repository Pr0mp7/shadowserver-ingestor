# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-13

### Added
- Initial release (extracted from iris-data-explorer repo)
- HMAC-SHA256 authenticated Shadowserver API client
- CSV report download from `dl.shadowserver.org/{id}`
- PostgreSQL upsert with SHA256-based dedup
- APScheduler for scheduled ingestion (default: every 15 minutes)
- Auto-backfill on first start (default: 7 days)
- Health endpoint on port 8088
- Ingestion audit log (`ss_ingestion_log` table)
- Auto-create database schema on startup
- CLI modes: `--ping`, `--once`, `--backfill N`
- Per-report error handling
- Docker deployment with healthcheck

[1.0.0]: https://github.com/Pr0mp7/shadowserver-ingestor/releases/tag/v1.0.0
