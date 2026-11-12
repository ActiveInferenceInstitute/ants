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
- `gnn_conformance.py` — pinned-parser extraction and specification-vs-code checks. It
  reads the pin with `gnn.importers`, the reader shipped in the pinned revision.
- `scripts/validate_gnn_spec.py` — the strict local GNN gate (one step of the `gnn` arm).
- `scripts/gate.py` — the single gate entry point: `fast` (default), `all`, `lint`,
  `test-fast`, `test`, `docs`, `gnn`, `metrics`.
- `scripts/check_docs.py` — relative-link check plus the generated gate-metrics page.
- `tests/` — pytest suite with a 90% coverage floor.

## Contract

- `config.py` is the single source for dimensions and environment constants; the GNN
  specification must stay consistent with it.
- `gnn/ant_colony_foraging.gnn.md` is the model specification. It is validated against
  the GNN revision pinned in `gnn/upstream.json`, read from the pinned commit (via
  `git archive`), never from the GNN checkout's working tree. The pin is read by
  `gnn.importers`, the reader shipped in that revision; no local pin reader exists.
- The simulation is stochastic and does not set a random seed; tests assert structure
  and invariants, not run-to-run numeric equality.

## Commands

```sh
uv sync --extra dev
uv run python scripts/gate.py fast   # default arm: lint + docs + test-fast
uv run python scripts/gate.py all    # lint + docs + full tests + GNN conformance
uv run python scripts/gate.py gnn    # GNN arm alone; provisions the pin if needed
```

`scripts/gate.py` is the single gate entry point and holds each command once;
CI calls the same arms. The arm table and measured timings are in
`docs/RUN_GUIDE.md` and generated into `docs/_generated/gate-metrics.md`.

CI runs `python -m gnn.importers check --repo .` from the pinned environment, the
strict validator, and `tests/test_gnn_conformance.py` in the
`gnn conformance (pinned)` job (key `gnn-conformance`), which fetches the pinned
revision from the public upstream repository and provisions its interpreter, so
the pin is re-checked on every push and pull request.

## Editing the model

- Changing `config.py` dimensions or the `create_ant` / `MDP` structure requires updating
  the GNN specification and the checks in `gnn_conformance.py` in the same change.
- Keep the pin at the newest GNN release; when bumping it, update `gnn/upstream.json`
  only. The reader shipped in the pinned revision re-checks the pin, so there are no
  canonical values to repeat in the tests.
- GNN's [downstream adoption
  guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md)
  documents the adoption patterns, pin discipline, and drift-guard checks used here.
