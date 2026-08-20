# Metrics

`proxybench` focuses on operator metrics tied to usable outcomes rather than raw proxy inventory.

## Usable success rate

```text
usable results / requests
```

The event producer decides what `usable=true` means for the workload. That definition should be fixed before comparing arms.

A descriptive 95% Wilson interval is reported for the proportion. It is not a causal claim and does not establish request independence.

## Requests per usable result

```text
requests / usable results
```

Lower is generally more efficient. If an arm produces zero usable results, this metric is `null` rather than infinity.

## Rotations per usable result

```text
rotations / usable results
```

This metric is emitted only when `rotated` coverage is 100%. Partial coverage is reported, but no complete-arm ratio is invented.

## Cost per usable result

```text
total cost units / usable results
```

`cost_units` can represent currency, provider credits, bandwidth-equivalent units, or another consistent operator-defined unit.

The ratio is emitted only when cost coverage is 100%. Do not compare arms that use different cost units.

## Latency

`proxybench` reports p50 and p95 over supplied non-negative `latency_ms` values using linear interpolation between ordered samples.

Latency coverage is always reported so partial instrumentation remains visible.

## Outcome counts

The optional `outcome` field is an uppercase categorical token. It is intended for sanitized categories such as `SUCCESS`, `HTTP_RATE_LIMIT`, or `PROXY_PATH_FAILURE`—not target names, URLs, provider endpoints, or private identifiers.

## A/B deltas

Candidate deltas are reported relative to baseline:

- usable success uplift in percentage points;
- usable success relative change in percent;
- requests-per-usable-result percent change;
- rotations-per-usable-result percent change;
- cost-per-usable-result percent change;
- p95 latency percent change.

A negative change is favorable for ratios where lower is better.

## Gate semantics

Gates are operator-defined acceptance criteria. For example:

```text
min success uplift >= 2 percentage points
requests / usable result regression <= 5%
cost / usable result regression <= 5%
```

Possible verdicts:

- `PASS` — all configured gates are evaluable and pass;
- `FAIL` — at least one configured gate fails and none is missing;
- `INCONCLUSIVE` — minimum sample count is not met or a required metric lacks full coverage;
- `NO_GATES_CONFIGURED` — comparison is descriptive only.

These verdicts are operational policy results, not hypothesis-test or causal conclusions.
