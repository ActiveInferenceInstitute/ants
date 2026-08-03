# REVIEW_LOG_2026-08-02.md

Docs-deep review pass on `ActiveInferenceInstitute/ants` (public submodule).
Companion scoping file: `TO-DO.md`.

## Phase 0 — Preflight

- Default branch: `origin/main`; checked out `main` @ `c4cba10` (`add .aii sidecar (100% complete) + CC-BY-4.0 LICENSE`); clean tree; `git fetch`/`git pull --ff-only` → already up to date.
- Inventory: `ants.py` (348 lines, simulation core), `config.py` (parameters), `figure_1.py` / `figure_2.py` / `figure_3.py` (experiments), `README.md` (9 lines), `LICENSE` (MIT, © 2020 Alexander Tschantz), `.aii/config.yaml` (InstituteOS sidecar), `.gitignore`. No `docs/`, no CI, no tests, no dependency manifest, no TODO files.

## Phase 1 — Mega-deep docs review: findings

**Minor**
1. README heading/link text used the preprint-style title without punctuation; no DOI link to the published article.
2. `.gitignore` had a duplicated `.ipynb_checkpoints` entry; no `.venv/`.
3. Trailing whitespace in figure scripts; manual `open()`/`close()` file writes; unused `import config as cf` in `figure_3.py`; dead commented-out blocks in `ants.py`; no docstrings.

**Medium**
4. README was a stub: no install, usage, layout, configuration, or citation sections.
5. No `docs/` folder at all; no docs index, no guides (running/model), no `CONTRIBUTING.md`, no `CITATION.cff`, no `SECURITY.md`, no `requirements.txt`.
6. `.aii/config.yaml` description truncated with "by…"; artifacts list incomplete; citation text a stub.
7. **Code–doc drift, verified by execution:**
   - `Env.plot()` used `fig.canvas.tostring_rgb()`, removed in matplotlib 3.11 → `figure_1.py` crashed at step 0 on a modern stack (reproduced).
   - `main(save=False)` still wrote `imgs/*.npy` and crashed with `FileNotFoundError` when `imgs/` did not exist (reproduced).
   - `figure_3.py` strict-prior vector had shape `(1, 10)`; after the MDP's normalization it became **uniform** (all ones), silently disabling the "strict" preference, and the utility term mis-broadcast to shape `(10,)`. Verified numerically; transposed to `(10, 1)` matching figures 1–2 (intended gradient: 0 for levels 0–4, increasing for levels 5–9).
   - `figure_1.py` used `np.random.choice(paths)` on a list of arrays — raises for empty or same-length path lists; replaced with direct iteration.
   - Progress-print / snapshot cadence divided by `num_steps // 100` / `// 20` → `ZeroDivisionError` for `num_steps < 100`; guarded with `max(1, ...)`.
   - `main()` returned `np.array(paths)` on ragged forward trajectories → `ValueError` on numpy ≥ 1.24 at the end of a full run (reproduced: 26 completed trips); fixed with `dtype=object`.
   - `plot_path()` passed a single scalar to `set_xlim`/`set_ylim`, rendering inverted axes on the path plots (verified visually); fixed with explicit `0..GRID` ranges and re-verified.

**Major**
8. No CI, no tests, no dependency pins (deferred — see `TO-DO.md`).

## Phase 3 — Implemented (see `TO-DO.md` for the full checklist)

- Rewrote `README.md`; added `docs/index.md`, `docs/running.md`, `docs/model.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CITATION.cff` (YAML validated, DOI 10.3389/fnbeh.2021.647732), `requirements.txt` (numpy, matplotlib, imageio).
- Fixed the four verified code–doc drift issues above plus lint hygiene; `ruff check .` clean; `py_compile` clean.
- Updated `.aii/config.yaml` (description, artifacts, citation, date).
- Verification runs: `main(..., save=False)` smoke tests (standard and strict priors) pass with no output files; `figure_1.py` run end-to-end (see below).
- Heavy suites not run: `figure_2.py` / `figure_3.py` full experiments (20 runs × 2,000 steps × up to 200 ants). Their `main()` code path is shared with the verified `figure_1.py` run; the strict-prior path was smoke-tested.

## Phase 4 — Final verification

- `git status` contains only intended changes (7 modified, 7 added).
- Pushed to `origin/main`; `git status` shows up to date with `origin/main`.
