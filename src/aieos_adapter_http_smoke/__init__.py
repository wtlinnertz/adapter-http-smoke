"""AIEOS adapter: verify.smoke via HTTP probe.

Stdlib-only HTTP probe. Takes a target URL and a check configuration,
makes one request, returns the observed status as findings + evidence.
The run validator's expected_status criterion threshold-checks the result.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

__version__ = "1.0.0"


@dataclass
class AdapterResult:
    findings: dict[str, Any] | None
    evidence: list[str]
    exit_code: int


class HttpSmokeAdapter:
    """Single-shot HTTP probe satisfying the verify.smoke contract."""

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self._timeout = timeout_seconds

    def execute(self, inputs: dict[str, Any]) -> AdapterResult:
        target_url = inputs.get("target_url", "")
        check = inputs.get("check_configuration") or {}
        method = check.get("method", "GET")
        path = check.get("path", "/")
        expected_status = int(check.get("expected_status", 200))

        if not target_url:
            return AdapterResult(findings=None, evidence=["exit-code:2"], exit_code=2)

        url = target_url.rstrip("/") + "/" + path.lstrip("/")
        request = urllib.request.Request(url, method=method.upper())
        observed_status: int = 0
        latency_ms = 0
        error_repr = ""
        try:
            from time import perf_counter

            t0 = perf_counter()
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                observed_status = response.status
            latency_ms = int((perf_counter() - t0) * 1000)
        except urllib.error.HTTPError as exc:
            observed_status = exc.code
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            error_repr = f"{type(exc).__name__}: {exc}"
            return AdapterResult(
                findings={"observed_status": 0, "error": error_repr},
                evidence=[
                    "http-status:0",
                    "exit-code:1",
                ],
                exit_code=1,
            )

        return AdapterResult(
            findings={
                "observed_status": observed_status,
                "expected_status": expected_status,
                "latency_ms": latency_ms,
                "url": url,
                "method": method.upper(),
            },
            evidence=[
                f"http-status:{observed_status}",
                f"latency-ms:{latency_ms}",
                f"observed-response:{observed_status}-on-{method.upper()}-{path}",
                "exit-code:0",
            ],
            exit_code=0,
        )
