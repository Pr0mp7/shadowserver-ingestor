"""PostgreSQL write operations for ingesting Shadowserver events."""

import hashlib
import json
import logging

import psycopg2
import psycopg2.extras

from .config import Config

log = logging.getLogger(__name__)


def _get_conn():
    return psycopg2.connect(
        host=Config.DB_HOST, port=Config.DB_PORT, dbname=Config.DB_NAME,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
    )


def _compute_hash(event):
    """SHA256 hash of the sorted JSON representation for dedup."""
    canonical = json.dumps(event, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _extract_common_fields(event):
    """Extract indexed common fields from a raw event dict."""
    ip_raw = event.get("ip") or event.get("src_ip") or event.get("dst_ip")
    # Validate IP is not empty before passing to INET column
    ip = ip_raw if ip_raw and ip_raw.strip() else None

    port_raw = event.get("port") or event.get("src_port") or event.get("dst_port")
    try:
        port = int(port_raw) if port_raw else None
    except (ValueError, TypeError):
        port = None

    asn_raw = event.get("asn")
    try:
        asn = int(asn_raw) if asn_raw else None
    except (ValueError, TypeError):
        asn = None

    return {
        "ip": ip,
        "port": port,
        "asn": asn,
        "geo": event.get("geo") or event.get("country") or None,
        "hostname": event.get("hostname") or event.get("rdns") or None,
        "tag": event.get("tag") or event.get("type") or None,
        "severity": event.get("severity") or None,
    }


def upsert_events(report_type, report_date, events):
    """Insert events with ON CONFLICT DO NOTHING for dedup.

    Returns (inserted_count, skipped_count).
    """
    if not events:
        return 0, 0

    conn = _get_conn()
    inserted = 0
    skipped = 0
    try:
        with conn.cursor() as cur:
            for event in events:
                fields = _extract_common_fields(event)
                event_hash = _compute_hash(event)
                try:
                    cur.execute(
                        """
                        INSERT INTO ss_events
                            (report_type, report_date, ip, port, asn, geo,
                             hostname, tag, severity, raw_data, event_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (report_type, report_date, event_hash) DO NOTHING
                        """,
                        (
                            report_type, report_date,
                            fields["ip"], fields["port"], fields["asn"],
                            fields["geo"], fields["hostname"], fields["tag"],
                            fields["severity"],
                            json.dumps(event, default=str),
                            event_hash,
                        ),
                    )
                    if cur.rowcount > 0:
                        inserted += 1
                    else:
                        skipped += 1
                except psycopg2.Error as e:
                    log.warning("Event insert error: %s", e)
                    conn.rollback()
                    skipped += 1
                    continue
            conn.commit()
    finally:
        conn.close()

    return inserted, skipped


def upsert_report(report_type, report_date, event_count):
    """Track that a report has been ingested."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ss_reports (report_type, report_date, event_count)
                VALUES (%s, %s, %s)
                ON CONFLICT (report_type, report_date)
                DO UPDATE SET event_count = ss_reports.event_count + EXCLUDED.event_count,
                             ingested_at = NOW()
                """,
                (report_type, report_date, event_count),
            )
        conn.commit()
    finally:
        conn.close()


def start_ingestion_log():
    """Create a new ingestion log entry. Returns the log id."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ss_ingestion_log (status) VALUES ('running') RETURNING id"
            )
            log_id = cur.fetchone()[0]
        conn.commit()
        return log_id
    finally:
        conn.close()


def finish_ingestion_log(log_id, status, reports_found, events_ingested, events_skipped, error_message=None):
    """Update an ingestion log entry with results."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ss_ingestion_log
                SET run_finished = NOW(), status = %s,
                    reports_found = %s, events_ingested = %s,
                    events_skipped = %s, error_message = %s
                WHERE id = %s
                """,
                (status, reports_found, events_ingested, events_skipped, error_message, log_id),
            )
        conn.commit()
    finally:
        conn.close()
