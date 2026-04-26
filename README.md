# adapter-http-smoke

AIEOS adapter: `verify.smoke` via stdlib HTTP probe. Single-shot request to
a target URL; records observed status + latency for the run validator's
`expected_status` criterion.

```bash
pip install -e '.[dev]' && pytest
```

MIT.
