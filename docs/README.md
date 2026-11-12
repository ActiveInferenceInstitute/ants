# `docs/` — documentation hub

Purpose-built documentation for the ant-colony foraging model
(companion code to Friedman et al., 2021, *Front. Behav. Neurosci.* 15:647732).
This is a small, hand-written tree: one short page per topic, plus one generated
page of gate measurements. The source of truth for parameters is
[`../config.py`](../config.py); the executable experiment definitions are
[`../figure_1.py`](../figure_1.py), [`../figure_2.py`](../figure_2.py), and
[`../figure_3.py`](../figure_3.py).

Start with [`documentation-index.md`](documentation-index.md) for the flat list
of every long-lived document in the repository.

## Documents

| Document | Purpose |
| --- | --- |
| [`documentation-index.md`](documentation-index.md) | Flat index of long-lived documents, including the root-level ones. |
| [`RUN_GUIDE.md`](RUN_GUIDE.md) | The gate entry point (`scripts/gate.py`), its arms, the CI job mapping, and where measured timings live. |
| [`running.md`](running.md) | Installation, commands, outputs, and runtime notes, including the in-memory API smoke test. |
| [`model.md`](model.md) | Environment, observations, MDP components, parameters, and the GNN specification. |
| [`index.md`](index.md) | Pointer kept for old links; it forwards to this hub and the flat index. |

## Generated pages

[`_generated/gate-metrics.md`](_generated/gate-metrics.md) and its JSON source
[`_generated/gate-metrics.json`](_generated/gate-metrics.json) hold the measured
per-arm wall times: the pre-gate baseline and the latest `scripts/gate.py` run.
Do not hand-edit them. Refresh with
`uv run python scripts/gate.py metrics`; the `docs` gate arm fails when the page
and the JSON diverge, so stale or typed-in numbers cannot land.

## Repository-level documents

- [Repository overview](../README.md) — quick start and model summary.
- [Agent guidance](../AGENTS.md) — layout, contract, and commands for agents.
- [Contributing](../CONTRIBUTING.md) — scope, tests, and development guidance.
- [Security](../SECURITY.md) — private vulnerability reporting.
- [Review TODO](../TO-DO.md) — documentation review findings and status.
- [Review log](../REVIEW_LOG_2026-08-02.md) — the docs-deep review record.
- [Citation metadata](../CITATION.cff) — machine-readable citation.

## Editing

Every file here except `_generated/` is hand-written. Keep the topic-per-file
split, keep relative links resolvable (checked by the `docs` arm:
`uv run python scripts/gate.py docs`), and update this table plus
[`documentation-index.md`](documentation-index.md) when you add a page. When
`config.py` changes a dimension or the MDP structure, update
[`model.md`](model.md) and [`../gnn/ant_colony_foraging.gnn.md`](../gnn/ant_colony_foraging.gnn.md)
in the same change (see [`../AGENTS.md`](../AGENTS.md)).
