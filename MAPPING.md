# MAPPING — adapter-http-smoke

## Tool

Python stdlib `urllib.request`. No dependencies.

## Behavior

- Constructs `<target_url>/<path>` and requests it with the configured method.
- Measures wall-clock latency around the request.
- Captures HTTPError status codes (4xx/5xx) — those don't raise from
  the adapter's perspective; they're observations.
- Network errors (URLError, TimeoutError, ConnectionError) yield
  observed_status=0 and exit_code=1; the adapter ran but the probe failed.

## Evidence

`http-status:<N>`, `latency-ms:<N>`, `observed-response:<N>-on-<method>-<path>`,
`exit-code:0`.

## Exit code

0 — probe ran (regardless of observed status); 1 — network failure;
2 — missing target_url input.

The adapter doesn't decide pass/fail; the run validator's expected_status
evaluator does.
