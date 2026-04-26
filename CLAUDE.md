# AIEOS Adapter — verify.smoke via HTTP

Claims: `verify.smoke` at 1.0.0. Stdlib only — no third-party deps.

Inputs: target_url + check_configuration {method, path, expected_status}.
Output: findings.observed_status + http-status:<N> evidence.
Run validator's expected_status criterion does the threshold comparison.
