# AGENTS.md — ants

Guidance for agents working in this repository: companion code for Friedman et al.
(2021), "Active Inferants: An Active Inference Framework for Ant Colony Behavior"
(Front. Behav. Neurosci. 15:647732).

## Layout

- `ants.py` — `Env` (grid, pheromone field, food, walls), `Ant`, `MDP` (state
  inference and one-step action selection), `create_ant`, `main`.
- `config.py` — the single source for dimensions and environment constants.
- `figure_1.py` / `figure_2.py` / `figure_3.py` — the paper's experiments
  (heavy runs; generated artifacts go under the ignored `imgs/`).
- `gnn/ant_colony_foraging.gnn.md` — the Generalized Notation Notation (GNN)
  specification of the MDP; `gnn/upstream.json` — the pinned GNN revision.
- `gnn_conformance.py` — pinned-parser extraction and specification-vs-code checks.
- `scripts/validate_gnn_spec.py` — the strict local GNN gate.
- `tests/` — pytest suite with a 90% coverage floor.

## Contract

- `config.py` is the single source for dimensions and environment constants; the GNN
  specification must stay consistent with it.
- `gnn/ant_colony_foraging.gnn.md` is the model specification. It is validated against
  the GNN revision pinned in `gnn/upstream.json`, read from the pinned commit (via
  `git archive`), never from the GNN checkout's working tree.
- The simulation is stochastic and does not set a random seed; tests assert structure
  and invariants, not run-to-run numeric equality.

## Commands

```sh
uv sync --extra dev
uv run ruff check .
uv run pytest
uv run python scripts/validate_gnn_spec.py   # needs GNN_ROOT (or the sibling checkout) and GNN_PYTHON
```

CI runs the strict validator and `tests/test_gnn_conformance.py` in the
`gnn conformance (pinned v5.0.3)` job, which fetches the pinned revision from the
public upstream repository and provisions its interpreter, so the pin is
re-checked on every push and pull request.

## Editing the model

- Changing `config.py` dimensions or the `create_ant` / `MDP` structure requires updating
  the GNN specification and the checks in `gnn_conformance.py` in the same change.
- Keep the pin at the newest GNN release; when bumping it, update `gnn/upstream.json`
  and the canonical values asserted in `tests/test_gnn_conformance.py`.
- GNN's [downstream adoption
  guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md)
  documents the adoption patterns, pin discipline, and drift-guard checks used here.
