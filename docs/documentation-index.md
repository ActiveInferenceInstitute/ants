# Documentation index

Flat list of this repository's long-lived documents. The hub is
[`docs/README.md`](README.md); start there unless you already know the page.

## Repository-level

| Document | Purpose |
| --- | --- |
| [`../README.md`](../README.md) | Project overview, quick start, citation. |
| [`../AGENTS.md`](../AGENTS.md) | Layout, contract, and commands for agents. |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Scope and development workflow. |
| [`../SECURITY.md`](../SECURITY.md) | Private vulnerability reporting. |
| [`../TO-DO.md`](../TO-DO.md) | Documentation review findings and open/deferred items. |
| [`../REVIEW_LOG_2026-08-02.md`](../REVIEW_LOG_2026-08-02.md) | Point-in-time docs review record. |
| [`../CITATION.cff`](../CITATION.cff) | Machine-readable citation metadata. |

## `docs/`

| Document | Purpose |
| --- | --- |
| [`README.md`](README.md) | Documentation hub: what this folder is for and how it is maintained. |
| [`index.md`](index.md) | Pointer to the hub and this index. |
| [`RUN_GUIDE.md`](RUN_GUIDE.md) | The gate entry point, its arms, measured timings, and the CI job mapping. |
| [`running.md`](running.md) | Installation, experiment commands, outputs, and the API smoke test. |
| [`model.md`](model.md) | Environment, observations, MDP components, parameters, GNN specification. |

## Generated

| Document | Producer |
| --- | --- |
| [`_generated/gate-metrics.json`](_generated/gate-metrics.json) | `uv run python scripts/gate.py metrics` (folds `.gate-cache/latest.json` receipts). |
| [`_generated/gate-metrics.md`](_generated/gate-metrics.md) | Rendered from the JSON above by `scripts/check_docs.py`; never hand-edited. |

## GNN

| Document | Purpose |
| --- | --- |
| [`../.github/GNN.md`](../.github/GNN.md) | What the pinned conformance job parses and where the pin lives. |
| [`../gnn/upstream.json`](../gnn/upstream.json) | Canonical pin record, schema `gnn-importer-pin/v1`. |
| [`../gnn/ant_colony_foraging.gnn.md`](../gnn/ant_colony_foraging.gnn.md) | The model specification in Generalized Notation Notation. |

## Tests and CI

| Document | Purpose |
| --- | --- |
| [`../tests/README.md`](../tests/README.md) | Suite layout, coverage floor, and file reference. |
| [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) | The two CI jobs and the gate arms they run. |
