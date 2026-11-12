# Contributing

This repository contains research code accompanying the Active Inferants paper. Keep changes focused, reproducible, and consistent with the existing small Python codebase.

## Development workflow

1. Create a virtual environment and install the project with development extras:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -e ".[dev]"
   ```

   or, with uv: `uv sync --extra dev`.

2. Run the gate before pushing. `fast` is the default arm; `all` includes the
   full suite and the pinned GNN conformance check:

   ```sh
   .venv/bin/python scripts/gate.py fast
   .venv/bin/python scripts/gate.py all
   ```

   `all` runs `lint`, `docs`, `test`, and `gnn`. The arm table, measured
   timings, and the CI job mapping are in [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md).

3. For simulation changes, add or extend tests in `tests/` (the suite is fast and deterministic — no full 2,000-step experiments required for coverage).
4. Do not commit generated `imgs/` output or coverage artifacts.

Continuous integration (`.github/workflows/ci.yml`) runs the same `scripts/gate.py` arms on every push to `main` and on pull requests, using the locked dependencies in `uv.lock`. When you change dependencies, regenerate the lockfile with `uv lock`.

## Scope

Pull requests should explain the motivation, identify affected experiment scripts, and distinguish behavioral changes from documentation or maintenance changes. Avoid adding heavyweight dependencies for small documentation or maintenance improvements.
