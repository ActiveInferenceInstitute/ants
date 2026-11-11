# `tests/` — test suite

Pytest suite for the ant-colony foraging simulation. It runs entirely offline:
the structural GNN checks always run, and the pinned-upstream half skips (or
fails when a checkout is explicitly selected) rather than needing the network.

## Running

```sh
uv sync --extra dev
uv run pytest        # full suite with the 90% coverage floor
uv run ruff check .  # lint
```

`pyproject.toml` sets `testpaths = ["tests"]` and
`--cov=ants --cov=config --cov-fail-under=90`. CI runs the same `ruff` and
`pytest` checks on every push and pull request (see
[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml)).

## Files

| File | Covers |
| --- | --- |
| [`test_config.py`](test_config.py) | Grid dimensions, the nine-action map and opposite-action table, and the observation/state/action counts in [`../config.py`](../config.py). |
| [`test_ants.py`](test_ants.py) | Environment initialization and observation reconstruction, `MDP` inference/action selection, `create_ant`, `plot_path`, and the `main()` run path including its `save=False` guards. |
| [`test_figures.py`](test_figures.py) | Regression checks for [`../figure_1.py`](../figure_1.py), [`../figure_2.py`](../figure_2.py), and [`../figure_3.py`](../figure_3.py); imports them in a scratch directory so their `imgs/` side effect never touches the repository. |
| [`test_gnn_conformance.py`](test_gnn_conformance.py) | Pin record and declared dimensions against [`../config.py`](../config.py), plus validation of [`../gnn/ant_colony_foraging.gnn.md`](../gnn/ant_colony_foraging.gnn.md) with the pinned upstream parser when the GNN checkout is available. |

The simulation is stochastic and does not set a random seed, so tests assert
structure and invariants rather than run-to-run numeric equality.

## Conventions

- No mocks: tests exercise the real `Env`, `MDP`, and figure modules.
- A change to `config.py` dimensions or the MDP structure requires updating the
  affected assertions and the GNN conformance checks in the same commit.
- Do not weaken the coverage floor or skip a check to make a change pass.
