# Gate and CI run guide

One entry point, separately runnable arms, one command per arm. CI runs the
same `scripts/gate.py` arms described here; there is no second copy of a command
in `.github/workflows/ci.yml`.

```sh
uv sync --extra dev                        # once per checkout
uv run python scripts/gate.py --list       # show the arms
uv run python scripts/gate.py fast         # default: lint + docs + test-fast
uv run python scripts/gate.py all          # every arm, stopping at the first failure
```

`fast` is the default so the ordinary edit loop skips the full-simulation test;
`all` is the pre-PR check.

## Arms

| Arm | Command (as run by `scripts/gate.py`) | What it proves |
| --- | --- | --- |
| `lint` | `python -m ruff check .` | Style and import hygiene across the tree. |
| `test-fast` | `python -m pytest -q --no-cov -m "not slow"` | The suite minus the `slow`-marked full simulation; coverage instrumentation is off, so the 90% floor does not apply. |
| `test` | `python -m pytest` | Full suite with the `--cov-fail-under=90` floor from `pyproject.toml`. |
| `docs` | `python scripts/check_docs.py` | Every relative link in tracked Markdown resolves, and the generated metrics page matches its JSON source. |
| `gnn` | `python scripts/validate_gnn_spec.py` then `python -m pytest tests/test_gnn_conformance.py -q --no-cov` | The GNN specification conforms to the pinned upstream parser and to `ants.py`/`config.py`. |

There is no `types` arm: this repository has no type checker configured
(`pyproject.toml` declares none, and `TO-DO.md` records mypy as deliberately not
added for this numpy-heavy research code). Adding an arm without a configured
checker would prove nothing.

Each arm writes a receipt (exit code, wall time, parsed pytest/ruff facts) to
the ignored `.gate-cache/latest.json`; the `metrics` command folds the receipts
into the checked-in [`_generated/gate-metrics.json`](_generated/gate-metrics.json)
and regenerates [`_generated/gate-metrics.md`](_generated/gate-metrics.md).
Measured per-arm wall times, including the pre-gate baseline, live on that
generated page — read it there, never from prose.

## `slow` marker

`pyproject.toml` registers the `slow` marker. Exactly one test carries it:
`tests/test_ants.py::test_main_save_true_writes_outputs`, which runs the full
`main()` path with GIF/PNG/NumPy output (the dominant cost of the suite).
The `test` arm still runs it; only `test-fast` deselects it. Coverage stays
enforced on the arm that measures it.

## GNN conformance arm

- Canonical pin: [`../gnn/upstream.json`](../gnn/upstream.json), schema
  `gnn-importer-pin/v1`, pinning
  `ActiveInferenceInstitute/Generalized_Notation_Notation` at tag `v5.0.3`
  (commit `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).
- [`.github/GNN.md`](../.github/GNN.md) records what the conformance job parses:
  the pinned extractor reads `gnn/ant_colony_foraging.gnn.md` and the checks
  compare the extracted dimensions and the A, B, C, D and E matrices against
  `config.py` and `ants.py`; no other specification is in scope.
- CI job key `gnn-conformance`, display name `gnn conformance (pinned)`.
- Local resolution: an explicit `GNN_ROOT` wins; otherwise a sibling
  `../Generalized_Notation_Notation` checkout is used after `verify_pin` confirms
  the pinned tag and commit. If neither exists, the arm fetches the pinned commit
  into `.gate-cache/gnn` and provisions `.gate-cache/gnn-venv` with `numpy` and
  `defusedxml` — the same provisioning CI relies on, defined once in
  `scripts/gate.py`.

## CI mapping

`.github/workflows/ci.yml` keeps two jobs so the GNN arm runs in parallel with
the suite:

| Job key | Display name | Commands |
| --- | --- | --- |
| `test` | `lint and tests` | `uv sync --extra dev` once, then `uv run python scripts/gate.py lint docs test` |
| `gnn-conformance` | `gnn conformance (pinned)` | `uv sync --extra dev` once, then `uv run python scripts/gate.py gnn` |

Both jobs pin `astral-sh/setup-uv` at
`68559e99cc807c1eb7e9238fd43a15bba460eec2` (v10.3.3) with uv `0.13.7` and
Python `3.13`, and share the repository's single `uv.lock`. The workflow does not
use the organization composite action
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv`; it invokes
`astral-sh/setup-uv` directly. The earlier inline GNN fetch, venv creation,
version-reporting step and per-job Python-version split are gone: provisioning
lives in the `gnn` arm and `scripts/gate.py` appends the arm table to
`$GITHUB_STEP_SUMMARY`.

GitHub Actions is billing-locked for this organization, so the local arms are
the only executable gate; a green local `uv run python scripts/gate.py all` is
the evidence recorded in pull requests.
