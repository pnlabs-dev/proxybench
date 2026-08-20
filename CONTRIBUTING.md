# Contributing

Thanks for considering a contribution to `proxybench`.

## Scope

Good contributions improve the public measurement baseline without weakening its data-minimization or evidence-first behavior.

Useful changes include:

- additional deterministic summary metrics;
- clearer comparison semantics;
- explicit missing-data coverage;
- regression tests for edge cases;
- CLI usability improvements;
- packaging, CI, security, or documentation improvements.

Private routing/scoring logic, provider selection, credentials, production infrastructure, private benchmark data, and customer/workload identifiers do not belong in this repository.

## Development

```bash
python -m pip install .
python -m unittest discover -s tests -v
python scripts/public_hygiene_check.py
```

Keep runtime dependencies at zero unless there is a strong, documented reason to change that constraint.

## Pull requests

A good pull request should:

1. state the metric or operator problem precisely;
2. include tests for behavior changes;
3. keep input/output semantics deterministic;
4. report missing-data coverage rather than silently imputing values;
5. avoid presenting descriptive comparisons as causal proof;
6. keep fixtures synthetic and non-sensitive;
7. keep CI green across the supported Python matrix.

## Sensitive information

Do not post credentials, private endpoints/IPs, provider account details, production logs, customer data, or private infrastructure details.

See [`SECURITY.md`](SECURITY.md) for the repository security boundary.
