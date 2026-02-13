"""Shadowserver API client with HMAC-SHA256 authentication.

reports/list — lists available reports (metadata).
Reports are downloaded as CSV from https://dl.shadowserver.org/{id}.
"""

import csv
import hashlib
import hmac
import io
import json
import logging
import time

import requests

from .config import Config

log = logging.getLogger(__name__)

DOWNLOAD_BASE = "https://dl.shadowserver.org/"


class ShadowserverClient:
    def __init__(self):
        self.api_url = Config.SS_API_URL.rstrip("/")
        self.api_key = Config.SS_API_KEY
        self.api_secret = Config.SS_API_SECRET
        self.request_delay = Config.REQUEST_DELAY_SECONDS

    def _sign(self, data):
        return hmac.new(
            self.api_secret.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _call(self, method, params=None):
        url = f"{self.api_url}/{method}"
        body = params or {}
        body["apikey"] = self.api_key

        body_json = json.dumps(body, sort_keys=True)
        signature = self._sign(body_json)

        resp = requests.post(
            url,
            data=body_json,
            headers={"Content-Type": "application/json", "HMAC2": signature},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def ping(self):
        """Test API connectivity."""
        return self._call("test/ping")

    def list_reports(self, date_str):
        """List available reports for a date (YYYY-MM-DD).

        Returns list of report dicts with 'id', 'type', 'file', 'report', 'timestamp', 'url'.
        """
        result = self._call("reports/list", {"date": date_str})
        return result if isinstance(result, list) else []

    def download_report(self, report):
        """Download a report CSV and parse it into a list of dicts.

        report: dict from list_reports() with at least 'id' and 'file' keys.
        Returns list of event dicts (one per CSV row).
        """
        report_id = report["id"]
        url = DOWNLOAD_BASE + report_id
        log.info("  Downloading %s ...", report.get("file", report_id))

        resp = requests.get(url, timeout=300)
        resp.raise_for_status()

        # Parse CSV content
        text = resp.text
        if not text.strip():
            return []

        reader = csv.DictReader(io.StringIO(text))
        return list(reader)

    def fetch_all_reports(self, date_str):
        """Fetch all report files for a date.

        Yields (report_meta, events_list) tuples.
        """
        reports = self.list_reports(date_str)
        if not reports:
            log.info("No reports for %s", date_str)
            return

        log.info("Found %d report files for %s", len(reports), date_str)
        for report in reports:
            try:
                events = self.download_report(report)
                yield report, events
            except Exception as e:
                log.error("  Error downloading %s: %s", report.get("file", "?"), e)
                continue
            time.sleep(self.request_delay)
