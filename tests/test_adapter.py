"""Unit tests for adapter-http-smoke.

Drives a real http.server in a thread; probes against it. No mocks needed
for the happy path. Network-error paths use a connection-refused address.
"""

from __future__ import annotations

import http.server
import threading
from contextlib import contextmanager

from aieos_adapter_http_smoke import HttpSmokeAdapter


class _Handler(http.server.BaseHTTPRequestHandler):
    """Configurable handler — class-level state set per test."""

    response_code: int = 200
    response_body: bytes = b'{"status": "ok"}'

    def do_GET(self):
        self.send_response(self.response_code)
        self.send_header("Content-Length", str(len(self.response_body)))
        self.end_headers()
        self.wfile.write(self.response_body)

    def log_message(self, format, *args):
        return  # silence access logs


@contextmanager
def _server(response_code: int = 200):
    _Handler.response_code = response_code
    httpd = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_smoke_against_200_target():
    with _server(200) as url:
        result = HttpSmokeAdapter().execute(
            {
                "target_url": url,
                "check_configuration": {
                    "method": "GET",
                    "path": "/healthz",
                    "expected_status": 200,
                },
            }
        )
    assert result.exit_code == 0
    assert result.findings["observed_status"] == 200
    assert any("http-status:200" in e for e in result.evidence)


def test_smoke_records_404_without_marking_failure():
    """The adapter records the observed status; the run validator decides if
    it matches expected. 404 -> still exit_code 0 (the probe ran)."""
    with _server(404) as url:
        result = HttpSmokeAdapter().execute(
            {
                "target_url": url,
                "check_configuration": {
                    "method": "GET",
                    "path": "/missing",
                    "expected_status": 200,
                },
            }
        )
    assert result.exit_code == 0
    assert result.findings["observed_status"] == 404


def test_smoke_connection_refused():
    """Unreachable target -> exit_code 1, observed_status 0."""
    result = HttpSmokeAdapter(timeout_seconds=0.5).execute(
        {
            "target_url": "http://127.0.0.1:1",  # nothing listens on port 1
            "check_configuration": {"method": "GET", "path": "/", "expected_status": 200},
        }
    )
    assert result.exit_code == 1
    assert result.findings["observed_status"] == 0
    assert any("http-status:0" in e for e in result.evidence)


def test_smoke_missing_target_url():
    result = HttpSmokeAdapter().execute({"target_url": "", "check_configuration": {}})
    assert result.exit_code == 2


def test_smoke_default_check_configuration():
    """Empty check_configuration -> defaults (GET / expected 200)."""
    with _server(200) as url:
        result = HttpSmokeAdapter().execute({"target_url": url})
    assert result.exit_code == 0
    assert result.findings["observed_status"] == 200


def test_smoke_records_latency_field():
    with _server(200) as url:
        result = HttpSmokeAdapter().execute(
            {"target_url": url, "check_configuration": {"path": "/"}}
        )
    assert "latency_ms" in result.findings
    assert result.findings["latency_ms"] >= 0
    assert any("latency-ms:" in e for e in result.evidence)
