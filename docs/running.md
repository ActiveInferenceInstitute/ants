# Running the simulations

## Requirements

Use Python 3.11 or later and install the project (plus the development extras for tests and linting) from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

With [uv](https://docs.astral.sh/uv/): `uv sync --extra dev`.

The runtime dependencies (numpy, matplotlib, imageio) are declared in `pyproject.toml`; the exact resolved versions are pinned in `uv.lock`. No command-line entry point is provided — the scripts are run directly from the repository root so their relative `imgs/` output paths resolve correctly.

## Reproduce the default experiments

```sh
.venv/bin/python figure_1.py
.venv/bin/python figure_2.py
.venv/bin/python figure_3.py
```

The scripts create `imgs/` automatically. The default settings use 2,000 simulation steps and can take substantially longer than a smoke test, especially for the repeated experiments in `figure_2.py` and `figure_3.py`.

Generated files include:

- PNG environment snapshots and path plots;
- GIF animations;
- `.npy` arrays for ant locations and round trips;
- the single-run `.txt` summary from `figure_1.py`; and
- append-only JSONL summaries for the repeated experiments in `figure_2.py` and `figure_3.py`.

`imgs*` is excluded by `.gitignore`, so generated artifacts are not tracked.

Repeated experiments use one batch identity, a condition, and a one-based repetition:
`imgs/<condition>_<batch>_r<repetition>/<condition>_<batch>_r<repetition>`.
Each run exclusively creates its directory; reusing an identity refuses rather than
overwriting even a partial run. `imgs/<condition>_<batch>.jsonl` receives a record
only after that run succeeds, including its settings, preference values, results,
and artifact prefix. Failed runs retain any partial artifacts without a success record.

## Small API smoke test

The simulation can be exercised without writing output files by calling `main()` with `save=False`:

```sh
.venv/bin/python - <<'PY'
import numpy as np
import config as cf
from ants import main

preferences = np.arange(cf.NUM_OBSERVATIONS, dtype=float).reshape(-1, 1)
round_trips, paths, distance = main(
    num_steps=100,
    init_ants=3,
    max_ants=3,
    C=preferences,
    save=False,
)
print(round_trips, len(paths), distance)
PY
```

`main()` returns `(completed_trips, paths, distance)`. The run is stochastic, so the numeric values vary. `save=False` suppresses output and does not allocate, append, or convert the output-only frame, location, and round-trip histories; completed trajectories and returned results remain available. Positive saved runs capture GIF frames independently of the PNG snapshot cadence, including short runs and ant-only animations.

## Custom runs

Import `main` and pass a preference matrix `C` with shape `(NUM_OBSERVATIONS, 1)`. The figure scripts provide examples of gradual and strict preference vectors. `init_ants` controls the initial colony size; `max_ants` is the upper bound used when ants are added every `ADD_ANT_EVERY` steps. With `switch=True`, the run-local food location changes exactly once at the positive step `num_steps // 2`; zero- and one-step runs do not switch. Each `Env` copies the configured location, so one run cannot change the next run's starting location.

The implementation is not a stable public API: parameter validation is minimal, and the scripts are the authoritative examples of how this research code is currently used.
