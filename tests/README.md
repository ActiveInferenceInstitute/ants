# `tests/` — test suite

Pytest suite for the ant-colony foraging simulation. It runs entirely offline:
the structural GNN checks always run, and the pinned-upstream half skips (or
fails when a checkout is explicitly selected) rather than needing the network.

## Running

```sh
uv sync --extra dev
uv run python scripts/gate.py fast   # default arm: slow test excluded, no coverage
uv run python scripts/gate.py test   # full suite with the 90% coverage floor
```

`pyproject.toml` sets `testpaths = ["tests"]` and
`--cov=ants --cov=config --cov-fail-under=90`. The `slow` marker separates
`tests/test_ants.py::test_main_save_true_writes_outputs` (the full-simulation
run that dominates suite time) from the rest; only the `test-fast` arm
deselects it. CI runs the same gate arms on every push and pull request (see
[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) and
[`../docs/RUN_GUIDE.md`](../docs/RUN_GUIDE.md)).

## Files

| File | Covers |
| --- | --- |
| [`test_config.py`](test_config.py) | Grid dimensions, the nine-action map and opposite-action table, and the observation/state/action counts in [`../config.py`](../config.py). |
| [`test_ants.py`](test_ants.py) | Real environment/MDP behavior; origin-complete return paths (including empty, singleton, consecutive, and ragged trajectories); once-only run-local food switching; saved GIF decoding; and no-save output-history/RNG invariants. |
| [`test_figures.py`](test_figures.py) | Real figure modules in scratch directories: batch/condition/repetition isolation, JSONL results, collision/partial-run preservation, and short-run GIF frames in both rendering modes. |
| [`test_gnn_conformance.py`](test_gnn_conformance.py) | Specification sections and declared dimensions against [`../config.py`](../config.py), plus validation of [`../gnn/ant_colony_foraging.gnn.md`](../gnn/ant_colony_foraging.gnn.md) with the pinned upstream reader and parser when the GNN checkout is available. |

The simulation is stochastic and does not set a random seed, so tests assert
structure and invariants rather than run-to-run numeric equality.

The 2026-11-13 governed focused run of `test_ants.py` and `test_figures.py`
passed 48 tests with no skips. A separate exact-pin source-mode proof passed
all 14 GNN conformance tests and the strict validator at v5.0.3
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`), with independently bound
bootstrap/manifest and verified imported parser bytes. Neither run measures
full-suite coverage, runs the default scientific campaigns, or establishes
installed-origin/release qualification. A5/A6 remain owner-facing open items.

## Conventions

- No mocks: tests exercise the real `Env`, `MDP`, and figure modules.
- A change to `config.py` dimensions or the MDP structure requires updating the
  affected assertions and the GNN conformance checks in the same commit.
- Do not weaken the coverage floor or skip a check to make a change pass.
