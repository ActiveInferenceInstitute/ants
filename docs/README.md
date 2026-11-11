# `docs/` — documentation folder guide

Purpose-built documentation for the ant-colony foraging model
(companion code to Friedman et al., 2021, *Front. Behav. Neurosci.* 15:647732).
This is a small, hand-written tree: one short page per topic. The source of
truth for parameters is [`../config.py`](../config.py); the executable
experiment definitions are [`../figure_1.py`](../figure_1.py),
[`../figure_2.py`](../figure_2.py), and [`../figure_3.py`](../figure_3.py).

## Documents

| Document | Purpose |
| --- | --- |
| [`index.md`](index.md) | Compact topic index for this folder. |
| [`running.md`](running.md) | Installation, commands, outputs, and runtime notes, including the in-memory API smoke test. |
| [`model.md`](model.md) | Environment, observations, MDP components, parameters, and the GNN specification. |

## Repository-level documents

- [Repository overview](../README.md) — quick start and model summary.
- [Agent guidance](../AGENTS.md) — layout, contract, and commands for agents.
- [Contributing](../CONTRIBUTING.md) — scope, tests, and development guidance.
- [Security](../SECURITY.md) — private vulnerability reporting.
- [Review TODO](../TO-DO.md) — documentation review findings and status.
- [Review log](../REVIEW_LOG_2026-08-02.md) — the docs-deep review record.
- [Citation metadata](../CITATION.cff) — machine-readable citation.

## Editing

Every file here is hand-written; none is generated. Keep the topic-per-file
split, keep relative links resolvable, and update this table when you add a
page. When `config.py` changes a dimension or the MDP structure, update
[`model.md`](model.md) and [`../gnn/ant_colony_foraging.gnn.md`](../gnn/ant_colony_foraging.gnn.md)
in the same change (see [`../AGENTS.md`](../AGENTS.md)).
