from pathlib import Path

import numpy as np

import config as cf
from ants import main, plot_path

NAME = "main"
NUM_STEPS = 2000
INIT_ANTS = 70
MAX_ANTS = 70

Path("imgs").mkdir(parents=True, exist_ok=True)

# standard prior
PRIOR_TICK = 1
C = np.zeros((cf.NUM_OBSERVATIONS, 1))
prior = 0
for o in range(cf.NUM_OBSERVATIONS):
    C[o] = prior
    prior += PRIOR_TICK

if __name__ == "__main__":
    num_round_trips, paths, coeff = main(
        num_steps=NUM_STEPS,
        init_ants=INIT_ANTS,
        max_ants=MAX_ANTS,
        C=C,
        save=True,
        switch=True,
        name=NAME,
        ant_only_gif=False,
    )
    print(f"num_round_trips {num_round_trips} / coeff {coeff / MAX_ANTS}")
    with open(f"imgs/{NAME}.txt", "w") as f:
        f.write(f"num_round_trips {num_round_trips} / coeff {coeff / MAX_ANTS}")

    for i, path in enumerate(paths):
        plot_path(path, f"imgs/path_{i}.png")
