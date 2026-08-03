# Contributing

This repository contains research code accompanying the Active Inferants paper. Keep changes focused, reproducible, and consistent with the existing small Python codebase.

## Development workflow

1. Create a virtual environment and install `requirements.txt`.
2. Run the Python syntax check:

   ```sh
   .venv/bin/python -m py_compile ants.py config.py figure_1.py figure_2.py figure_3.py
   ```

3. Run Ruff if available:

   ```sh
   .venv/bin/ruff check .
   ```

4. For simulation changes, run a short `main(..., save=False)` smoke test before attempting a full experiment.
5. Do not commit generated `imgs/` output.

There is currently no automated test suite or CI configuration in this repository. Document any changes to model assumptions or experiment parameters in the relevant source and documentation.

## Scope

Pull requests should explain the motivation, identify affected experiment scripts, and distinguish behavioral changes from documentation or maintenance changes. Avoid adding heavyweight dependencies for small documentation or maintenance improvements.
