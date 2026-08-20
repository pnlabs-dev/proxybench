# Public boundary

`proxybench` is intentionally a transparent measurement baseline, not a source dump of PN Labs commercial systems.

## Included publicly

- sanitized benchmark event schema;
- deterministic summary metrics;
- descriptive Wilson interval for usable success rate;
- operator-defined A/B gate engine;
- JSON CLI;
- synthetic example fixtures;
- tests, documentation, and CI;
- public security/hygiene controls.

## Intentionally excluded

This repository does not contain:

- live proxy routing or traffic orchestration;
- provider selection logic or provider-private configuration;
- target × egress historical learning;
- private scoring weights or optimization heuristics;
- promotion/demotion intelligence;
- automatic provider purchasing or account logic;
- production endpoints, IP addresses, credentials, tokens, cookies, or private hostnames;
- infrastructure topology, deployment secrets, operational runbooks, or incident data;
- non-public benchmark datasets, customer data, or private design-partner material.

## Contribution rule

Contributions should improve the public measurement baseline without requiring disclosure of private infrastructure, production traffic, third-party secrets, or commercial decision logic.

If a change needs sensitive evidence, reduce it to a synthetic reproducer or sanitized aggregate result before opening a public issue or pull request.
