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

## Citation

For the published article:

> Friedman DA, Tschantz A, Ramstead MJD, Friston K, Constant A (2021). Active Inferants: An Active Inference Framework for Ant Colony Behavior. *Frontiers in Behavioral Neuroscience*, 15, 647732. https://doi.org/10.3389/fnbeh.2021.647732

Machine-readable citation metadata is provided in [CITATION.cff](CITATION.cff). The repository's source code is released under the MIT License. See [LICENSE](LICENSE). The article is open access under the license specified by its publisher; consult the publication for the article's reuse terms.
