# Active Inferants

Code for the computational model in [Active Inferants: An Active Inference Framework for Ant Colony Behavior](https://doi.org/10.3389/fnbeh.2021.647732) by Daniel Ari Friedman, Alec Tschantz, Maxwell J. D. Ramstead, Karl Friston, and Axel Constant.

The simulation models ant-colony foraging in a 40 × 40 T-maze. Individual simulated ants use a Markov decision process (MDP) to infer local pheromone observations, move through the environment, and deposit trail pheromone while returning from food. The repository contains the implementation used for the paper's in-silico experiments.

## Documentation

- [Running the simulations](docs/running.md) — installation, commands, outputs, and runtime notes.
- [Model overview](docs/model.md) — environment, observations, MDP components, and parameters.
- [Contributing](CONTRIBUTING.md) — scope and development guidance.
- [Review TODO](TO-DO.md) — documentation review findings and status.

## Quick start

The project requires Python 3 and the packages listed in `requirements.txt`. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python figure_1.py
```

The figure scripts create an `imgs/` directory containing PNG snapshots, GIFs, NumPy arrays, text summaries, and (for `figure_1.py`) path plots. Generated output is ignored by Git. The default experiments are intentionally larger runs; see [Running the simulations](docs/running.md) for the smaller API smoke test and experiment details.

## Citation

For the published article:

> Friedman DA, Tschantz A, Ramstead MJD, Friston K, Constant A (2021). Active Inferants: An Active Inference Framework for Ant Colony Behavior. *Frontiers in Behavioral Neuroscience*, 15, 647732. https://doi.org/10.3389/fnbeh.2021.647732

The repository's source code is released under the MIT License. See [LICENSE](LICENSE). The article is open access under the license specified by its publisher; consult the publication for the article's reuse terms.
