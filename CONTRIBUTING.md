# Contributing

This repository contains research code accompanying the Active Inferants paper. Keep changes focused, reproducible, and consistent with the existing small Python codebase.

## Development workflow

1. Create a virtual environment and install the project with development extras:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -e ".[dev]"
   ```

   or, with uv: `uv sync --extra dev`.

2. Run the test suite (pytest with a 90% coverage floor) and the linter:

   ```sh
   .venv/bin/python -m pytest
   .venv/bin/ruff check .
   ```

3. For simulation changes, add or extend tests in `tests/` (the suite is fast and deterministic — no full 2,000-step experiments required for coverage).
4. Do not commit generated `imgs/` output or coverage artifacts.

Continuous integration (`.github/workflows/ci.yml`) runs ruff and the full pytest suite on every push to `main` and on pull requests, using the locked dependencies in `uv.lock`. When you change dependencies, regenerate the lockfile with `uv lock`.

## Scope

Pull requests should explain the motivation, identify affected experiment scripts, and distinguish behavioral changes from documentation or maintenance changes. Avoid adding heavyweight dependencies for small documentation or maintenance improvements.
