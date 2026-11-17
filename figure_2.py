import json
from pathlib import Path
from uuid import uuid4

import numpy as np

import config as cf
from ants import main

Path("imgs").mkdir(parents=True, exist_ok=True)


NUM_AVERAGE = 5
NAME = "compare"
NUM_STEPS = 2000
INIT_ANTS = 200
MAX_ANTS = 200

# standard prior
PRIOR_TICK = 1
C = np.zeros((cf.NUM_OBSERVATIONS, 1))
prior = 0
for o in range(cf.NUM_OBSERVATIONS):
    C[o] = prior
    prior += PRIOR_TICK


def run(*, batch_id=None, repetition=1):
    batch_id = uuid4().hex if batch_id is None else batch_id
    condition = NAME
    run_id = f"{condition}_{batch_id}_r{repetition}"
    output_directory = Path("imgs") / run_id
    # An existing identity, including a partial run, must never be overwritten.
    output_directory.mkdir(parents=True)
    artifact_prefix = output_directory / run_id
    initial_food = list(cf.FOOD_LOCATION)
    preferences = C.ravel().tolist()
    settings = {"num_steps": NUM_STEPS, "init_ants": INIT_ANTS, "max_ants": MAX_ANTS}
    num_round_trips, _paths, coeff = main(
        **settings, C=C, save=True, switch=True, name=f"{run_id}/{run_id}",
    )
    print(f"num_round_trips_{settings['max_ants']} {num_round_trips} / coeff {coeff}")
    summary_path = Path("imgs") / f"{condition}_{batch_id}.jsonl"
    record = {
        "run_id": run_id, "batch_id": batch_id, "condition": condition,
        "repetition": repetition, **settings,
        "initial_food_location": initial_food, "switch": True,
        "preference": "gradual", "preference_values": preferences,
        "num_round_trips": int(num_round_trips), "coeff": float(coeff),
        "artifact_prefix": str(artifact_prefix), "summary_path": str(summary_path),
    }
    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


if __name__ == "__main__":

    batch_id = uuid4().hex
    for repetition in range(1, NUM_AVERAGE + 1):
        NAME = "compare_10"
        INIT_ANTS = 10
        MAX_ANTS = 10
        run(batch_id=batch_id, repetition=repetition)

        NAME = "compare_30"
        INIT_ANTS = 30
        MAX_ANTS = 30
        run(batch_id=batch_id, repetition=repetition)

        NAME = "compare_50"
        INIT_ANTS = 50
        MAX_ANTS = 50
        run(batch_id=batch_id, repetition=repetition)
        
        NAME = "compare_70"
        INIT_ANTS = 70
        MAX_ANTS = 70
        run(batch_id=batch_id, repetition=repetition)
