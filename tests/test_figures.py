"""Regression tests for the experiment scripts (figure_1/2/3.py)."""

import hashlib
import importlib
import json
import sys
from pathlib import Path

import imageio
import numpy as np
import pytest

import ants as implementation
import config as cf
from ants import MDP

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def preserve_random_state():
    state = np.random.get_state()
    try:
        yield
    finally:
        np.random.set_state(state)


def _artifact_hashes(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*") if path.is_file()
    }


def _observe_real_simulation(monkeypatch):
    environments = []
    actual_environment = implementation.Env
    actual_factory = implementation.create_ant

    class ObservedEnv(actual_environment):
        def __init__(self):
            super().__init__()
            self.initial_food = list(self.food_location)
            self.food_history = []
            self.preference_inputs = []
            environments.append(self)

        def decay(self):
            self.food_history.append(list(self.food_location))
            return super().decay()

    def observed_factory(init_x, init_y, preferences):
        environments[-1].preference_inputs.append(np.asarray(preferences).ravel().tolist())
        return actual_factory(init_x, init_y, preferences)

    monkeypatch.setattr(implementation, "Env", ObservedEnv)
    monkeypatch.setattr(implementation, "create_ant", observed_factory)
    return environments


def _assert_saved_run(record):
    prefix = Path(record["artifact_prefix"])
    frames = imageio.mimread(str(prefix) + ".gif")
    assert frames
    assert all(frame.ndim == 3 and frame.shape[2] in (3, 4) for frame in frames)
    assert all(frame.shape[0] > 0 and frame.shape[1] > 0 for frame in frames)
    for step in range(record["num_steps"]):
        snapshot = imageio.imread(str(prefix) + f"_{step}.png")
        assert snapshot.shape[0] > 0 and snapshot.shape[1] > 0
    locations = np.load(str(prefix) + "_locations.npy", allow_pickle=True)
    round_trips = np.load(str(prefix) + "_round_trips.npy")
    assert len(locations) == record["num_steps"]
    assert all(len(row) == record["init_ants"] for row in locations)
    assert round_trips.shape == (record["num_steps"],)
    assert round_trips[-1] == record["num_round_trips"] / record["max_ants"]
    assert np.isfinite(record["coeff"]) and record["coeff"] >= 0


def _import_figure(name, monkeypatch, tmp_path):
    """Import a figure module from a scratch directory so its ``imgs/``
    mkdir side effect never touches the repository."""
    monkeypatch.chdir(tmp_path)
    sys.path.insert(0, str(REPO_ROOT))
    try:
        return importlib.import_module(name)
    finally:
        sys.path.remove(str(REPO_ROOT))


def test_figure_1_constants(monkeypatch, tmp_path):
    fig = _import_figure("figure_1", monkeypatch, tmp_path)
    assert fig.NAME == "main"
    assert fig.NUM_STEPS == 2000
    assert fig.INIT_ANTS == fig.MAX_ANTS == 70


def test_figure_2_constants(monkeypatch, tmp_path):
    fig = _import_figure("figure_2", monkeypatch, tmp_path)
    assert fig.NAME == "compare"
    assert fig.NUM_AVERAGE == 5
    assert fig.INIT_ANTS == fig.MAX_ANTS == 200


def test_figure_3_strict_prior_is_column_vector(monkeypatch, tmp_path):
    """The strict-preference vector must be a (NUM_OBSERVATIONS, 1) column;
    as a row vector it normalizes to a uniform (flat) preference."""
    fig = _import_figure("figure_3", monkeypatch, tmp_path)
    assert fig.C.shape == (cf.NUM_OBSERVATIONS, 1)
    normalized = MDP.normdist(fig.C + np.exp(-16))
    assert not np.isnan(normalized).any()
    assert normalized.min() < 1e-6
    assert normalized.max() > 0.3
    # low pheromone levels (0-4) get no preference
    assert np.all(normalized[:5] < 1e-6)
    assert np.all(normalized[5:] > normalized[4])


@pytest.mark.parametrize(
    ("module_name", "preference"), [("figure_2", "gradual"), ("figure_3", "strict")],
)
def test_figure_replicates_preserve_separate_artifacts(
    monkeypatch, tmp_path, module_name, preference,
):
    figure = _import_figure(module_name, monkeypatch, tmp_path)
    monkeypatch.setattr(figure, "NUM_STEPS", 5)
    monkeypatch.setattr(figure, "INIT_ANTS", 2)
    monkeypatch.setattr(figure, "MAX_ANTS", 2)
    original_food = list(cf.FOOD_LOCATION)
    environments = _observe_real_simulation(monkeypatch)
    legacy = Path("imgs") / f"{figure.NAME}.txt"
    legacy.parent.mkdir(exist_ok=True)
    legacy.write_text("retained historical summary\n", encoding="utf-8")

    first = figure.run(batch_id="batch-one", repetition=1)
    _assert_saved_run(first)
    first_directory = Path(first["artifact_prefix"]).parent
    first_hashes = _artifact_hashes(first_directory)
    second = figure.run(batch_id="batch-one", repetition=2)
    _assert_saved_run(second)
    assert first["run_id"] != second["run_id"]
    assert first["artifact_prefix"] != second["artifact_prefix"]
    assert _artifact_hashes(first_directory) == first_hashes
    assert first["summary_path"] == second["summary_path"]

    rows = [
        json.loads(line)
        for line in Path(first["summary_path"]).read_text(encoding="utf-8").splitlines()
    ]
    assert rows == [first, second]
    for record, env, repetition in zip(rows, environments, (1, 2)):
        assert record["batch_id"] == "batch-one"
        assert record["condition"] == figure.NAME
        assert record["repetition"] == repetition
        assert record["num_steps"] == 5
        assert record["init_ants"] == record["max_ants"] == 2
        assert record["initial_food_location"] == env.initial_food == original_food
        assert record["switch"] is True
        assert record["preference"] == preference
        assert env.preference_inputs
        assert all(values == record["preference_values"] for values in env.preference_inputs)
        assert record["preference_values"] == figure.C.ravel().tolist()
        mirrored = [cf.GRID[0] - original_food[0], original_food[1]]
        assert env.food_history == [original_food, original_food, mirrored, mirrored, mirrored]
        _assert_saved_run(record)
    assert cf.FOOD_LOCATION == original_food

    third = figure.run(batch_id="batch-two", repetition=1)
    _assert_saved_run(third)
    assert third["batch_id"] != first["batch_id"]
    assert third["artifact_prefix"] not in (first["artifact_prefix"], second["artifact_prefix"])
    assert third["summary_path"] != first["summary_path"]
    assert _artifact_hashes(first_directory) == first_hashes
    assert legacy.read_text(encoding="utf-8") == "retained historical summary\n"

    before_collision = _artifact_hashes(Path("imgs"))
    rng_before = np.random.get_state()
    with pytest.raises(FileExistsError):
        figure.run(batch_id="batch-one", repetition=1)
    rng_after = np.random.get_state()
    assert _artifact_hashes(Path("imgs")) == before_collision
    assert rng_before[0] == rng_after[0]
    np.testing.assert_array_equal(rng_before[1], rng_after[1])
    assert rng_before[2:] == rng_after[2:]


@pytest.mark.parametrize("module_name", ["figure_2", "figure_3"])
def test_figure_invocations_generate_new_batch_identity(monkeypatch, tmp_path, module_name):
    figure = _import_figure(module_name, monkeypatch, tmp_path)
    monkeypatch.setattr(figure, "NUM_STEPS", 1)
    monkeypatch.setattr(figure, "INIT_ANTS", 1)
    monkeypatch.setattr(figure, "MAX_ANTS", 1)
    first = figure.run()
    first_directory = Path(first["artifact_prefix"]).parent
    first_hashes = _artifact_hashes(first_directory)
    second = figure.run()
    assert first["batch_id"] != second["batch_id"]
    assert first["run_id"] != second["run_id"]
    assert first["artifact_prefix"] != second["artifact_prefix"]
    _assert_saved_run(first)
    _assert_saved_run(second)
    assert _artifact_hashes(first_directory) == first_hashes
