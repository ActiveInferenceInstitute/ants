# Active Inferants

[![CI](https://github.com/ActiveInferenceInstitute/ants/actions/workflows/ci.yml/badge.svg)](https://github.com/ActiveInferenceInstitute/ants/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Code for the computational model in [Active Inferants: An Active Inference Framework for Ant Colony Behavior](https://doi.org/10.3389/fnbeh.2021.647732) by Daniel Ari Friedman, Alec Tschantz, Maxwell J. D. Ramstead, Karl Friston, and Axel Constant.

The simulation models ant-colony foraging in a 40 × 40 T-maze. Individual simulated ants use a Markov decision process (MDP) to infer local pheromone observations, move through the environment, and deposit trail pheromone while returning from food. The repository contains the implementation used for the paper's in-silico experiments.

## Documentation

- [Running the simulations](docs/running.md) — installation, commands, outputs, and runtime notes.
- [Model overview](docs/model.md) — environment, observations, MDP components, and parameters.
- [Contributing](CONTRIBUTING.md) — scope, tests, and development guidance.
- [Review TODO](TO-DO.md) — documentation review findings and status.

## Quick start

The project requires Python 3.10 or later. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python figure_1.py
```

With [uv](https://docs.astral.sh/uv/), the same setup is `uv sync --extra dev` followed by `uv run figure_1.py`.

The figure scripts create an `imgs/` directory containing PNG snapshots, GIFs, NumPy arrays, text summaries, and (for `figure_1.py`) path plots. Generated output is ignored by Git. The default experiments are intentionally larger runs; see [Running the simulations](docs/running.md) for the smaller API smoke test and experiment details.

## Tests

The test suite lives in `tests/` and runs under pytest with a 90% coverage floor:

```sh
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest        # full suite, ~99% coverage (90% floor)
.venv/bin/ruff check .            # lint
```

Continuous integration runs the same checks on every push and pull request (see `.github/workflows/ci.yml`).

## Model specification (GNN)

The ant-colony foraging MDP is specified in
[`gnn/ant_colony_foraging.gnn.md`](gnn/ant_colony_foraging.gnn.md) in
[Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
(GNN): the 9 focal-cell states, 10 pheromone-level observations, 9 actions, the
environment-driven likelihood, the deterministic transition tensor, the log-preference
vector, and the habit prior.

The specification is validated against the GNN revision pinned in
[`gnn/upstream.json`](gnn/upstream.json), read from that pinned commit rather than from
the GNN checkout's working tree:

```sh
uv run python scripts/validate_gnn_spec.py   # strict gate (needs the GNN checkout)
uv run pytest tests/test_gnn_conformance.py  # structural + pinned-parser checks
```

The gate parses the specification with the pinned GNN extractor and checks the extracted
matrices against `ants.py`; the test module runs the same checks under pytest and skips
only the pinned-parser half when the GNN checkout is unavailable. When editing the
specification, start from GNN's [Start Here](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/v5.0.3/docs/START_HERE.md),
[framework integration guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/v5.0.3/docs/gnn/integration/framework_integration_guide.md),
and [syntax reference](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/v5.0.3/docs/gnn/reference/gnn_syntax.md).
For the wider picture (the adoption patterns sibling repositories use, pin discipline, and
the drift guard these checks implement), see GNN's
[downstream adoption guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md),
linked on GNN's default branch because it landed after the v5.0.3 pin.

### Related repositories

- [Active_InferAnts](https://github.com/ActiveInferenceInstitute/Active_InferAnts) — the
  multi-language Active Inference framework that grew out of this model. Its framework
  agent is specified separately, in that repository's `gnn/` directory.
- [Active_Skillference](https://github.com/ActiveInferenceInstitute/Active_Skillference) —
  the Active Inference / Free Energy Principle micro-learning platform; its discrete
  active-inference agent kernel is specified in that repository's `gnn/` directory.

Each concept has one canonical home: this repository owns the 2021 ant-colony foraging
MDP; the other two specify their own models.

## Citation

For the published article:

> Friedman DA, Tschantz A, Ramstead MJD, Friston K, Constant A (2021). Active Inferants: An Active Inference Framework for Ant Colony Behavior. *Frontiers in Behavioral Neuroscience*, 15, 647732. https://doi.org/10.3389/fnbeh.2021.647732

Machine-readable citation metadata is provided in [CITATION.cff](CITATION.cff). The repository's source code is released under the MIT License. See [LICENSE](LICENSE). The article is open access under the license specified by its publisher; consult the publication for the article's reuse terms.

## InstituteOS sidecar

This repository carries a committed [`.aii/`](.aii/README.md) sidecar with curated
InstituteOS metadata (`aii-sidecar/v1`): category, maturity, ecosystem relations,
key artifacts, provenance, and portable tasks. It is read by
[InstituteOS](https://github.com/ActiveInferenceInstitute/InstituteOS) tooling and
does not affect the project's build or runtime.
