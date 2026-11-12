# TO-DO — documentation review and improvements

Last reviewed: 2026-11-12 (estate pass; supersedes the 2026-08-02 docs-deep pass
recorded in REVIEW_LOG_2026-08-02.md).

Scoping definitions:

- **Minor** — typo, broken link, formatting, small stale detail.
- **Medium** — stale section rewrite, doc restructure, added missing guide.
- **Major** — large doc-system overhaul, cross-cutting refactors, new tooling.

Implemented in commits `247de94` (code fixes), `a4bc393` (documentation), `8f2b054` (sidecar/gitignore); see REVIEW_LOG_2026-08-02.md. Work that landed after that pass carries the merged pull request that proves it.

## Minor

- [x] README: fix heading/link text and add canonical DOI link to the published article — `README.md` (✓ a4bc393)
- [x] README: broken-link and license-badge check (MIT badge matches `LICENSE`) — `README.md`
- [x] `.gitignore`: remove duplicated `.ipynb_checkpoints` entry, add `.venv/` — `.gitignore` (✓ 8f2b054)
- [x] Figure scripts: remove trailing whitespace on `from pathlib import Path` lines — `figure_1.py`, `figure_2.py`, `figure_3.py` (✓ 247de94)
- [x] Figure scripts: replace manual `open()`/`close()` file writes with context managers — `figure_1.py`, `figure_2.py`, `figure_3.py` (✓ 247de94)
- [x] `figure_3.py`: unused `import config as cf` removed (ruff F401) (✓ 247de94)
- [x] `ants.py`: dead commented-out code blocks removed (trajectory-limit and distance-coefficient leftovers) (✓ 247de94)
- [x] `ants.py`: class and `main()` docstrings added; module docstring with paper reference (✓ 247de94)
- [x] `.gitignore`: ignore the gate cache (`.gate-cache/`) alongside `.pytest_cache/`, coverage files, and `*.egg-info/` — `.gitignore` (✓ #13)
- [x] Python floor raised to `>=3.11` (`requires-python`, ruff `target-version`) with `pillow>=13.0.0` carried as a uv constraint, clearing the pillow advisories — `pyproject.toml`, `uv.lock` (✓ #2, #9)
- [x] uv pinned to `0.13.7` in CI and guarded by `[tool.uv] required-version` — `.github/workflows/ci.yml`, `pyproject.toml` (✓ #8)
- [x] CI actions pinned to release SHAs, and Dependabot moved to the uv ecosystem — `.github/workflows/ci.yml`, `.github/dependabot.yml` (✓ #4, #5)
- [x] `Env.plot()` returning-ant branch covered (blue markers on the backward trip) — `tests/test_ants.py::test_plot_renders_returning_ants_as_blue_markers` (✓ #10)

## Medium

- [x] README: full rewrite — overview grounded in the actual code, quick start, repo layout, citation, license — `README.md`
- [x] Add `docs/` with index and two guides (running the simulations; model overview with configuration reference) — `docs/index.md`, `docs/running.md`, `docs/model.md`
- [x] Add `CITATION.cff` with validated YAML and preferred-citation for the published article (DOI 10.3389/fnbeh.2021.647732)
- [x] Add `CONTRIBUTING.md` grounded in the repo's actual workflow (gate command, test expectations, `imgs/` hygiene) — `CONTRIBUTING.md` (✓ a4bc393; rewritten for the single gate in #13)
- [x] Add `SECURITY.md` with private vulnerability reporting guidance
- [x] `.aii/config.yaml`: complete truncated description, add new doc artifacts, canonical citation text, refresh date
- [x] `ants.py`: fix `Env.plot()` frame capture for matplotlib ≥ 3.11 (`tostring_rgb` removed → `buffer_rgba`) — figure scripts crashed on modern matplotlib
- [x] `ants.py`: `main(save=False)` no longer writes `imgs/*.npy` (previously always wrote, crashing when `imgs/` did not exist); progress/snapshot cadence guards for `num_steps < 100`
- [x] `ants.py`: return `paths` as an object array (`np.array(paths, dtype=object)`) — ragged forward trajectories raised `ValueError` on numpy ≥ 1.24 at the end of a real run (reproduced with 26 completed trips)
- [x] `figure_3.py`: transpose the strict-preference vector to the column shape expected by `MDP` (the row vector normalized to a uniform preference, silently disabling the "strict" condition and mis-broadcasting the utility term) — verified numerically
- [x] `figure_1.py`: write each completed path instead of `np.random.choice(paths)` (which raised for empty or same-length path lists)
- [x] `ants.py`: `plot_path()` axis limits fixed — single-scalar `set_xlim/ylim` rendered inverted axes (verified visually); now explicit `0..GRID` ranges
- [x] Ruff clean (`ruff check .` passes; now the `lint` arm of `scripts/gate.py`) — verified again 2026-11-12 (✓ 247de94, #13)
- [x] Add folder guides for the `docs/` and `tests/` directories (purpose, document list, and test-file reference) — `docs/README.md`, `tests/README.md` (✓ 32b5305)
- [x] Add the gate run guide — entry point, arm table, `slow` marker, GNN arm resolution, and the CI job mapping — `docs/RUN_GUIDE.md` (✓ #13)
- [x] Add a flat documentation index and the generated metrics page (`docs/_generated/gate-metrics.json` plus its rendered `.md`) — `docs/documentation-index.md`, `docs/_generated/` (✓ #13)
- [x] Record what the pinned conformance job parses and where the pin lives — `.github/GNN.md` (✓ #6, #12)
- [x] Sidecar and readiness passes: `.aii/config.yaml` artifacts/tasks/docs lists, `.aii/docs/INTEGRATION.md`, `.aii/readiness.json`; `aii_platform.aii_sidecar validate` reports `OK` (re-run 2026-11-12) (✓ 117ddf2, 3a0d700, 32b5305)

## Major

- [x] Add a test suite — `tests/` (config sanity, Env/MDP behavior, `main()` outputs and guards, figure-script regression, GNN conformance); pytest with a 90% coverage floor; measured 2026-11-12: 32 passed, 3 skipped for the absent pinned GNN checkout, 100.00% coverage on `ants.py`+`config.py` (✓ 984a192; conformance tests #1, #10)
- [x] Add automated CI — `.github/workflows/ci.yml`: two jobs (`lint and tests`, `gnn conformance (pinned)`) that call the same gate arms on every push and pull request, uv `0.13.7`, Python 3.13, locked dependencies (✓ dfcd9f5; consolidated into one gate in #13)
- [x] Pin dependencies / lockfile — `pyproject.toml` declares runtime and dev dependencies; `uv.lock` pins exact resolutions; `requirements.txt` removed (single source of truth) (✓ aefbc04)
- [x] One composable gate — `scripts/gate.py` with the arms `lint`, `test-fast`, `test`, `docs`, `gnn`, `metrics` and the `fast`/`all` aliases; CI, `CONTRIBUTING.md`, and `AGENTS.md` call the same arms, and each arm writes a receipt that is folded into the checked-in metrics page (✓ #13, #14)
- [x] Add the `docs` arm — `scripts/check_docs.py` checks every relative link in tracked Markdown and that the generated metrics page still matches its JSON source (✓ #13)
- [x] Specify the ant-colony foraging MDP in GNN and validate it against the pinned upstream revision — `gnn/ant_colony_foraging.gnn.md`, `gnn_conformance.py`, `tests/test_gnn_conformance.py` (✓ #1)
- [x] Adopt the canonical importer pin schema `gnn-importer-pin/v1` in `gnn/upstream.json` and validate the pin's shape in the conformance checks (✓ #11, #16)
- [x] GNN–FEP importer cutover — pin advanced to `v5.1.0` (`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`, the newest upstream tag); the local pin reader is gone and the `gnn` arm runs `python -m gnn.importers check --repo .` from the pinned environment, then the strict validator and the conformance tests (✓ #15; arm re-run green 2026-11-12)

## Open / deferred

- `figure_2.py` and `figure_3.py` have still never been run end-to-end in a recorded pass: each is `NUM_AVERAGE = 5` repetitions of four colony sizes (10, 30, 50, 70) at 2,000 steps with `switch=True`, and `tests/test_figures.py` only asserts their module constants plus the strict-prior column shape. End-to-end evidence for the shared `main()` path is `figure_1.py`'s run together with the suite. Blocked on workstation CPU time, not on code — it cannot move into CI while hosted Actions is locked. Owner: a maintainer running it locally, then recording the run in a dated review log.
- mypy: not added — numpy-heavy untyped research code with no existing mypy config; out of proportion for this repository. `docs/RUN_GUIDE.md` records the absent `types` arm as deliberate. Owner: whoever adds the annotations first; a `types` arm without a configured checker would prove nothing.
- Generated metrics carry the measuring host's absolute paths: `docs/_generated/gate-metrics.json` stores `python /Users/friedman/.../scripts/check_docs.py` at `/latest/arms/docs/commands/0` and the same shape for `validate_gnn_spec.py` at `/latest/arms/gnn/commands/1`, and `gate-metrics.md` renders them verbatim. Cause: those arms build their script arguments with `str(SCRIPTS / ...)` and `run_arm` only rewrites the interpreter to `python`, although every command already runs with `cwd=REPO_ROOT`. Effect: re-measuring on another checkout rewrites two checked-in lines and publishes a maintainer's home path, while the `docs` arm stays green because it only compares the page against the JSON. Owner: whoever next edits `scripts/gate.py`.
- Hosted CI cannot produce evidence here: the last CI run that executed a step was green on `c267a40` (2026-11-05), and every run since `7ce7fdb` (2026-11-07) — including `43258631147` on the current `main` head `f0102e8` — fails both jobs before any step with "The job was not started because your account is locked due to a billing issue". The README badge therefore reflects a run that never started, and the local `uv run python scripts/gate.py all` is the only gate, as `docs/RUN_GUIDE.md` already states. Blocked on organization billing; owner: Active Inference Institute organization admins, since nothing in this repository can unblock it.
