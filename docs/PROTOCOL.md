# Benchmark protocol

Use this protocol when comparing a baseline routing/rotation policy against a candidate policy.

## 1. Freeze the definition of usable

Define `usable=true` before collecting either arm. Examples might include a parsed record, a validated page state, or another workload-specific success criterion.

Do not change that definition between arms.

## 2. Keep workload conditions comparable

Where practical, compare arms over similar target classes, request mixes, time windows, and instrumentation. Record meaningful differences outside the public fixture if they are sensitive.

`proxybench` does not make a causal claim when conditions differ.

## 3. Sanitize before export

Export only the public event schema:

```text
usable
latency_ms
cost_units
rotated
outcome
```

Do not export URLs, IPs, credentials, cookies, headers, payloads, customer identifiers, provider account data, or infrastructure details.

## 4. Preserve missingness

If latency, rotation, or cost was not measured for an event, omit the field or use `null`.

Do not silently fill missing values with zero or `false`. Coverage is part of the benchmark result.

## 5. Compare operator KPIs

Prioritize:

1. usable success rate;
2. requests per usable result;
3. cost per usable result;
4. rotations per usable result;
5. p95 latency.

Proxy count by itself is not an outcome metric.

## 6. Set gates before looking at the result

When possible, choose acceptance thresholds before running the candidate arm. This reduces post-hoc goal shifting.

Example:

```text
minimum usable-success uplift: +2 percentage points
maximum requests/usable regression: +5%
maximum cost/usable regression: +5%
```

## 7. Treat statistical output conservatively

The Wilson interval is descriptive. Requests from the same session, target, account, subnet, or time window may be correlated.

For production decisions, repeat the benchmark over multiple independent runs or periods where feasible and preserve rollback criteria.
