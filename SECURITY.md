# Security policy

`proxybench` is intentionally local-only. It performs no network I/O, telemetry, crawling, provider login, proxy authentication, or credential storage.

## Public input boundary

The benchmark event schema is deliberately small. It accepts only:

- `usable`
- `latency_ms`
- `cost_units`
- `rotated`
- `outcome`

Unknown fields are rejected. This is a data-minimization boundary: target URLs, proxy endpoints, IP addresses, provider names, headers, cookies, credentials, payloads, customer identifiers, and infrastructure details are not required.

## Never publish sensitive material

Do not place any of the following in issues, pull requests, examples, fixtures, screenshots, benchmark artifacts, or CI logs:

- API keys, access tokens, passwords, or private keys;
- proxy credentials or credential-bearing proxy URLs;
- session cookies, authorization headers, or authenticated request dumps;
- private endpoint URLs, IP addresses, internal hostnames, or infrastructure topology;
- production HAR/PCAP captures or raw production logs;
- customer data, personal data, or private datasets;
- non-public commercial implementation details.

Use synthetic fixtures and aggregate counts instead.

## Error behavior

Input-validation errors do not intentionally echo raw JSON lines, unsupported values, or local input paths. This reduces the chance that CI output becomes a secondary disclosure path.

## Statistical safety

The Wilson interval reported for usable success rate is descriptive. `proxybench` does not claim that request events are independent, randomized, or causal. Operator-defined gates are policy checks, not scientific proof.

## Repository hygiene gate

CI runs `scripts/public_hygiene_check.py`, which searches public text files for common secret/token shapes, credential-bearing URLs, IPv4/IPv6 literals, internal-hostname shapes, sensitive filenames, and email addresses.

Detected values are never printed; only the rule class and file path are reported.

This is defense-in-depth, not a replacement for review or dedicated secret scanning.

## Reporting security issues

Do not open a public issue containing sensitive reproduction material. Reduce the problem to a synthetic reproducer or sanitized aggregate description before sharing.
