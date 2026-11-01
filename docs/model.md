# Model overview

This repository implements a small active-inference-inspired MDP simulation of ant-colony foraging. The paper describes the MDP as the decision process of an individual simulated ant; colony-level behavior emerges from many ants interacting through the shared environment and its pheromone field.

## Environment

`Env` in `ants.py` maintains a 40 × 40 grid (`config.py`). Every grid cell has one of ten discrete pheromone observations. The initial observation is level 0 everywhere. Returning ants increase the observation level of each cell on their path; `Env.decay()` probabilistically decreases nonzero levels.

The nest starts at `(20, 30)`. The food region is centered at `(40, 5)` with a nominal size of `(10, 10)`. Movement is constrained to the interior of the grid and checked against the T-maze walls. An ant explores until it reaches the food region and the nest-return transition is sampled; it then follows its stored trajectory backward, depositing pheromone and eventually returning to exploration.

## Ant and MDP

Each `Ant` owns an `MDP` and stores its current position and forward trajectory. The action map has nine one-step actions: the eight neighboring displacements plus staying in place. An ant's local likelihood matrix is rebuilt from the nine cells in its focal area at each forward step.

The `MDP` contains:

- `A`: observation likelihoods for the nine local hidden states;
- `B`: action-conditioned state transitions;
- `C`: preferred observations;
- `sQ`: inferred state beliefs; and
- `uQ`: action probabilities.

`MDP.step()` performs state inference using the previous action and then scores actions using the expected-free-energy calculation implemented in the source. It samples the next action from the resulting softmax distribution. The code also applies priors against staying in place and immediately reversing the previous action.

## GNN specification

`gnn/ant_colony_foraging.gnn.md` states the same model in
[Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
(GNN): the nine hidden states, ten pheromone observation levels and nine actions, the fresh
likelihood `A`, the canonical `(next, previous, action)` transition tensor, the
log-preference `C`, the uniform `D`, and the `E` habit prior that carries the
stay-and-reverse priors. `python scripts/validate_gnn_spec.py` (or
`python -m pytest tests/test_gnn_conformance.py`) re-extracts the specification from the
GNN revision pinned in `gnn/upstream.json` and checks every matrix against `ants.py` and
`config.py`.

## Experiments

The three executable scripts define the experiments used by this repository:

- `figure_1.py` runs one 70-ant, 2,000-step experiment with a food-location switch and writes the primary animation, snapshots, summary, and completed path plots.
- `figure_2.py` repeats five runs for colonies of 10, 30, 50, and 70 ants using a gradual observation preference.
- `figure_3.py` repeats five runs for colonies of 10, 30, 50, and 70 ants using a strict preference that assigns increasing value to pheromone levels 5–9. Its preference vector is transposed to the column shape expected by `MDP`.

Each script uses `save=True` and writes generated artifacts below `imgs/`. The defaults are computational experiments, not a packaged command-line interface.

## Main parameters

`config.py` is the single source for the simulation dimensions and environment constants. Important values include:

| Parameter | Current value | Meaning |
| --- | ---: | --- |
| `GRID` | `[40, 40]` | Environment dimensions |
| `FOCAL_AREA` | `[3, 3]` | Local observation window |
| `NUM_OBSERVATIONS` | `10` | Discrete pheromone levels |
| `NUM_ACTIONS` | `9` | One-step actions |
| `ADD_ANT_EVERY` | `50` | Steps between additions in `main()` |
| `DECAY_FACTOR` | `0.01` | Per-cell probability of one-level decay |
| `NEST_FACTOR` | `0.1` | Probability of switching to return mode after food contact |
| `MAX_LEN` | `500` | Defined trajectory limit (not currently enforced) |

The implementation is stochastic and does not set a random seed. Individual runs therefore need not produce identical outputs.
