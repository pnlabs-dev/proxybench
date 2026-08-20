# proxybench

**Measure usable results, not proxy count.**

`proxybench` is a local, deterministic benchmark utility for proxy and web-retrieval workloads. It compares sanitized request outcomes using metrics that matter to operators: usable success rate, requests per usable result, rotations per usable result, latency, and cost per usable result.

Built by **PN Labs**.

## Why this exists

Adding more proxies or rotating more often does not guarantee better retrieval outcomes. A benchmark should answer a narrower question:

```text
baseline policy
      vs
candidate policy
       ↓
usable success rate
requests / usable result
rotations / usable result
latency distribution
cost / usable result
```

`proxybench` deliberately does **not** perform crawling, make network requests, accept proxy credentials, or select providers. It measures evidence you already collected from an authorized workload.

## Relationship to proxy-outcome

[`proxy-outcome`](https://github.com/pnlabs-dev/proxy-outcome) answers:

> What observation do we actually have, and how strong is the proxy-layer evidence?

`proxybench` answers:

> Did policy A or policy B produce better usable outcomes and efficiency?

Classification and benchmarking stay separate.

## Install

```bash
python -m pip install .
```

Runtime dependencies: **none**.

## Input format

Input is JSON Lines (`.jsonl`). Every line is one sanitized retrieval event.

Allowed fields only:

```json
{"usable": true, "latency_ms": 420, "cost_units": 0.0021, "rotated": false, "outcome": "SUCCESS"}
```

- `usable` — required boolean. Whether the result was usable for the workload.
- `latency_ms` — optional non-negative number.
- `cost_units` — optional non-negative number in any consistent cost unit.
- `rotated` — optional boolean.
- `outcome` — optional uppercase categorical token such as `HTTP_RATE_LIMIT`.

Unknown fields are rejected. URLs, IP addresses, proxy identifiers, provider credentials, cookies, headers, payloads, customer identifiers, and other production context are neither required nor part of the schema.

## Summarize one arm

```bash
proxybench summarize examples/baseline.jsonl
```

Output includes:

- request count;
- usable result count;
- usable success rate + descriptive Wilson interval;
- requests per usable result;
- rotation coverage and rotations per usable result;
- latency coverage, p50, and p95;
- cost coverage and cost per usable result;
- categorical outcome counts.

## Compare A/B arms

```bash
proxybench compare examples/baseline.jsonl examples/candidate.jsonl
```

The comparison reports directional deltas without pretending that request events are necessarily independent or causal.

Optional operator-defined gates:

```bash
proxybench compare examples/baseline.jsonl examples/candidate.jsonl \
  --min-requests 20 \
  --min-success-uplift-pp 2 \
  --max-rpu-regression-pct 5 \
  --max-cost-regression-pct 5
```

Gate verdicts are `PASS`, `FAIL`, `INCONCLUSIVE`, or `NO_GATES_CONFIGURED`.

## Design principles

- **Usable-result first** — HTTP success alone is not the buyer KPI.
- **Data minimization** — no URLs, IPs, credentials, raw headers, or production payloads are required.
- **Local only** — no network I/O or telemetry.
- **Evidence before claims** — descriptive intervals are not presented as causal proof.
- **Explicit coverage** — cost/latency/rotation metrics report how much of the input actually contained that field.
- **Zero runtime dependencies** — easy to embed in CI and benchmark harnesses.

## Public / commercial boundary

This repository contains the transparent measurement baseline only. It does not contain PN Labs' private routing/scoring implementation, provider selection logic, target × egress learning, promotion/demotion intelligence, private benchmark datasets, production infrastructure, or cost-optimization control plane.

See [`docs/PUBLIC-BOUNDARY.md`](docs/PUBLIC-BOUNDARY.md).

## Validation

```bash
python -m pip install .
python -m unittest discover -s tests -v
python scripts/public_hygiene_check.py
```

CI installs the package before testing, smoke-tests the installed CLI, and runs a non-echoing vendor-neutral public repository hygiene gate.

## Security

See [`SECURITY.md`](SECURITY.md). Do not put production logs, credentials, private endpoint information, personal/customer data, or private infrastructure details into public benchmark fixtures or issues.

## Responsible use

Use `proxybench` only with workloads you are authorized to run. Respect applicable target policies, rate limits, robots directives where relevant, and law.

## License

MIT.
