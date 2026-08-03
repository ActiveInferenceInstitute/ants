# TO-DO — documentation review and improvements

Last reviewed: 2026-08-02 (docs-deep pass; see REVIEW_LOG_2026-08-02.md).

Scoping definitions:

- **Minor** — typo, broken link, formatting, small stale detail.
- **Medium** — stale section rewrite, doc restructure, added missing guide.
- **Major** — large doc-system overhaul, cross-cutting refactors, new tooling.

Implemented in commits `247de94` (code fixes), `a4bc393` (documentation), `8f2b054` (sidecar/gitignore); see REVIEW_LOG_2026-08-02.md.

## Minor

- [x] README: fix heading/link text and add canonical DOI link to the published article — `README.md` (✓ a4bc393)
- [x] README: broken-link and license-badge check (MIT badge matches `LICENSE`) — `README.md`
- [x] `.gitignore`: remove duplicated `.ipynb_checkpoints` entry, add `.venv/` — `.gitignore` (✓ 8f2b054)
- [x] Figure scripts: remove trailing whitespace on `from pathlib import Path` lines — `figure_1.py`, `figure_2.py`, `figure_3.py` (✓ 247de94)
- [x] Figure scripts: replace manual `open()`/`close()` file writes with context managers — `figure_1.py`, `figure_2.py`, `figure_3.py` (✓ 247de94)
- [x] `figure_3.py`: unused `import config as cf` removed (ruff F401) (✓ 247de94)
- [x] `ants.py`: dead commented-out code blocks removed (trajectory-limit and distance-coefficient leftovers) (✓ 247de94)
- [x] `ants.py`: class and `main()` docstrings added; module docstring with paper reference (✓ 247de94)

## Medium

- [x] README: full rewrite — overview grounded in the actual code, quick start, repo layout, citation, license — `README.md`
- [x] Add `docs/` with index and two guides (running the simulations; model overview with configuration reference) — `docs/index.md`, `docs/running.md`, `docs/model.md`
- [x] Add `requirements.txt` (numpy, matplotlib, imageio) matching the actual imports
- [x] Add `CITATION.cff` with validated YAML and preferred-citation for the published article (DOI 10.3389/fnbeh.2021.647732)
- [x] Add `CONTRIBUTING.md` grounded in the repo's actual workflow (no test suite; ruff/py_compile checks; imgs/ hygiene)
- [x] Add `SECURITY.md` with private vulnerability reporting guidance
- [x] `.aii/config.yaml`: complete truncated description, add new doc artifacts, canonical citation text, refresh date
- [x] `ants.py`: fix `Env.plot()` frame capture for matplotlib ≥ 3.11 (`tostring_rgb` removed → `buffer_rgba`) — figure scripts crashed on modern matplotlib
- [x] `ants.py`: `main(save=False)` no longer writes `imgs/*.npy` (previously always wrote, crashing when `imgs/` did not exist); progress/snapshot cadence guards for `num_steps < 100`
- [x] `ants.py`: return `paths` as an object array (`np.array(paths, dtype=object)`) — ragged forward trajectories raised `ValueError` on numpy ≥ 1.24 at the end of a real run (reproduced with 26 completed trips)
- [x] `figure_3.py`: transpose the strict-preference vector to the column shape expected by `MDP` (the row vector normalized to a uniform preference, silently disabling the "strict" condition and mis-broadcasting the utility term) — verified numerically
- [x] `figure_1.py`: write each completed path instead of `np.random.choice(paths)` (which raised for empty or same-length path lists)
- [x] `ants.py`: `plot_path()` axis limits fixed — single-scalar `set_xlim/ylim` rendered inverted axes (verified visually); now explicit `0..GRID` ranges
- [x] Ruff clean (`ruff check .` passes) and `py_compile` clean on all Python files

## Major

- [ ] Add automated CI (e.g. GitHub Actions: ruff + py_compile) — deferred: no existing CI convention in the repo; single small script set; low value without a test suite.
- [ ] Add a test suite — deferred: research code with no tests; out of scope for a documentation pass.
- [ ] Pin dependencies or add a lockfile — deferred: no packaging convention in this repo; `requirements.txt` lists the three direct dependencies.

## Open / deferred

- `figure_2.py` and `figure_3.py` full runs were not executed in this pass (5 × 4 repetitions of 2,000-step, up-to-200-ant experiments; heavy). `figure_1.py` was run end-to-end and its outputs verified.
- No CI, no tests, no lockfile (see Major above).
