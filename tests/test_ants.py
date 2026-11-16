"""Behavioral tests for the ant colony simulation (ants.py)."""

import os
import sys
from pathlib import Path

import imageio
import numpy as np
import pytest

import config as cf
import ants as implementation
from ants import MDP, Env, create_ant, dis, main, plot_path

PREFERENCES = np.arange(cf.NUM_OBSERVATIONS, dtype=float).reshape(-1, 1)


@pytest.fixture(autouse=True)
def preserve_random_state():
    state = np.random.get_state()
    try:
        yield
    finally:
        np.random.set_state(state)


def _returning_trip_fixture(monkeypatch):
    origin = (cf.INIT_X, cf.INIT_Y)
    paths = [
        [origin, (origin[0] + 1, origin[1])],
        [origin, (origin[0], origin[1] - 1), (origin[0], origin[1] - 2)],
    ]
    pending = iter(paths)

    def factory(init_x, init_y, preferences):
        ant = create_ant(init_x, init_y, preferences)
        ant.traj = list(next(pending))
        ant.x_pos, ant.y_pos = ant.traj[-1]
        ant.is_returning = True
        return ant

    monkeypatch.setattr(implementation, "create_ant", factory)
    return paths


def _path_coordinates(paths):
    return [[tuple(position) for position in path] for path in paths]


# ---------------------------------------------------------------- Env


def test_env_initial_state():
    env = Env()
    assert env.obs_matrix.shape == (cf.NUM_OBSERVATIONS, cf.GRID[0], cf.GRID[1])
    # every cell starts at pheromone level 0
    assert np.all(env.obs_matrix[0] == 1.0)
    assert np.all(env.obs_matrix[1:] == 0.0)


def test_env_get_obs_and_A():
    env = Env()
    ant = create_ant(cf.INIT_X, cf.INIT_Y, PREFERENCES)
    assert env.get_obs(ant) == 0
    A = env.get_A(ant)
    assert A.shape == (cf.NUM_OBSERVATIONS, cf.NUM_STATES)


def test_check_food_inside_and_outside():
    env = Env()
    inside = (cf.FOOD_LOCATION[0] - 1, cf.FOOD_LOCATION[1] + 1)
    assert env.check_food(*inside)
    assert not env.check_food(0, 0)
    assert not env.check_food(cf.INIT_X, cf.INIT_Y)


def test_food_geometry_is_owned_by_each_environment():
    original = list(cf.FOOD_LOCATION)
    first, second = Env(), Env()
    first.food_location[0] = cf.GRID[0] - first.food_location[0]
    assert first.check_food(1, original[1] + 1)
    assert not second.check_food(1, original[1] + 1)
    assert second.check_food(original[0] - 1, original[1] + 1)
    assert not first.check_food(original[0] - 1, original[1] + 1)
    assert second.food_location == original
    assert cf.FOOD_LOCATION == original


def test_check_walls():
    env = Env()
    # moving left into the wall from inside the corridor is blocked
    assert not env.check_walls(cf.WALL_LEFT + 1, cf.WALL_TOP + 1, cf.WALL_LEFT, cf.WALL_TOP + 1)
    # moving right into the wall is blocked
    assert not env.check_walls(cf.WALL_RIGHT - 1, cf.WALL_TOP + 1, cf.WALL_RIGHT, cf.WALL_TOP + 1)
    # open moves stay valid
    assert env.check_walls(cf.INIT_X, cf.INIT_Y, cf.INIT_X + 1, cf.INIT_Y)
    # descending outside the corridor through the top is blocked
    assert not env.check_walls(cf.WALL_RIGHT + 1, cf.WALL_TOP, cf.WALL_RIGHT + 1, cf.WALL_TOP + 1)


def test_step_forward_and_wall_block():
    env = Env()
    ant = create_ant(cf.INIT_X, cf.INIT_Y, PREFERENCES)
    assert ant.traj == [(cf.INIT_X, cf.INIT_Y)]
    env.step_forward(ant, 4)  # stay
    assert len(ant.traj) == 2  # the executed stay-move is recorded
    # a wall-blocked move must not mark the ant as returning
    ant.x_pos, ant.y_pos = cf.WALL_LEFT + 1, cf.WALL_TOP + 1
    ant.traj = [(ant.x_pos, ant.y_pos)]
    env.step_forward(ant, 0)  # (-1, -1) -> would cross into the wall
    assert not ant.is_returning
    assert len(ant.traj) == 1  # blocked moves are not recorded


def test_step_backward_deposits_pheromone():
    env = Env()
    ant = create_ant(cf.INIT_X, cf.INIT_Y, PREFERENCES)
    ant.traj = [
        (cf.INIT_X, cf.INIT_Y),
        (cf.INIT_X + 1, cf.INIT_Y),
        (cf.INIT_X + 2, cf.INIT_Y),
    ]
    ant.is_returning = True
    complete, traj = env.step_backward(ant)
    assert not complete
    assert traj is None
    # pheromone level of the retraced cell increased from 0 to 1
    assert env.obs_matrix[1, cf.INIT_X + 2, cf.INIT_Y] == 1.0


def test_step_backward_completes_trip_at_origin_and_preserves_consecutive_paths():
    env = Env()
    origin = (20, 30)
    expected = [origin, (21, 30), (22, 30)]
    ant = create_ant(*origin, PREFERENCES)
    ant.traj = list(expected)
    ant.x_pos, ant.y_pos = expected[-1]
    ant.is_returning = True
    completions = 0
    first_path = None
    for index, position in enumerate(reversed(expected)):
        complete, path = env.step_backward(ant)
        assert (ant.x_pos, ant.y_pos) == position
        assert env.visit_matrix[position] == 1
        assert env.obs_matrix[(1, *position)] == 1.0
        assert complete == (index == len(expected) - 1)
        completions += int(complete)
        if complete:
            first_path = path
        else:
            assert path is None
    assert first_path == expected
    assert ant.traj == [origin]
    assert first_path is not ant.traj
    assert ant.backward_step == 0
    assert not ant.is_returning

    ant.update_forward(21, 30)
    ant.update_forward(22, 30)
    ant.is_returning = True
    for index, position in enumerate(reversed(expected)):
        complete, path = env.step_backward(ant)
        assert (ant.x_pos, ant.y_pos) == position
        assert complete == (index == len(expected) - 1)
        completions += int(complete)
        if complete:
            assert path == expected
            assert path is not first_path
    assert completions == 2
    assert first_path == expected
    assert ant.traj == [origin]
    assert all(env.visit_matrix[position] == 2 for position in expected)


def test_step_backward_single_position_completes_without_aliasing_next_trip():
    env = Env()
    ant = create_ant(20, 30, PREFERENCES)
    ant.is_returning = True
    complete, path = env.step_backward(ant)
    assert complete
    assert path == [(20, 30)]
    assert (ant.x_pos, ant.y_pos) == (20, 30)
    assert env.visit_matrix[20, 30] == 1
    ant.update_forward(21, 30)
    assert path == [(20, 30)]
    assert ant.traj == [(20, 30), (21, 30)]


def test_step_backward_empty_trajectory_guard():
    """An ant flagged as returning with no trajectory must not crash."""
    env = Env()
    ant = create_ant(cf.INIT_X, cf.INIT_Y, PREFERENCES)
    ant.traj = []
    ant.is_returning = True
    complete, traj = env.step_backward(ant)
    assert complete is False
    assert traj is None
    assert ant.is_returning is False


def test_decay():
    env = Env()
    env.obs_matrix[0, 3, 3] = 0.0
    env.obs_matrix[1, 3, 3] = 1.0
    np.random.seed(0)
    env.decay()
    # level-0 cells stay level 0; the level-1 cell may decay to 0
    assert env.obs_matrix[0, 0, 0] == 1.0
    assert env.obs_matrix[1, 3, 3] in (0.0, 1.0)


def test_plot_savefig_and_gif_frame(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env = Env()
    ants = [create_ant(cf.INIT_X, cf.INIT_Y, PREFERENCES) for _ in range(3)]
    frame = env.plot(ants)
    assert frame.ndim == 3 and frame.shape[2] == 3
    env.plot(ants, savefig=True, name="snap.png")
    assert os.path.exists("snap.png")
    env.plot(ants, ant_only_gif=True)
    env.plot(ants, ant_only_gif=True, savefig=True, name="snap_ants.png")
    assert os.path.exists("snap_ants.png")


def _blue_pixels(frame):
    """Count blue-dominant pixels: the colour Env.plot uses for returning ants."""
    red = frame[:, :, 0].astype(int)
    blue = frame[:, :, 2].astype(int)
    return int(((blue > 200) & (red < 50)).sum())


def test_plot_renders_returning_ants_as_blue_markers(tmp_path, monkeypatch):
    """The backward-ant branch must place returning ants on the frame as the
    blue scatter, separately from the red forward-ant scatter."""
    monkeypatch.chdir(tmp_path)
    env = Env()
    forward = create_ant(cf.INIT_X, cf.INIT_Y, PREFERENCES)
    returning = create_ant(cf.INIT_X - 5, cf.INIT_Y - 5, PREFERENCES)
    baseline = env.plot([forward])
    assert _blue_pixels(baseline) == 0
    returning.is_returning = True
    marked = env.plot([forward, returning])
    assert _blue_pixels(marked) > 0


# ---------------------------------------------------------------- MDP


def test_softmax_and_normdist():
    x = np.array([[1.0, 2.0, 3.0]])
    sm = MDP.softmax(x)
    assert np.isclose(np.sum(sm), 1.0)
    col = np.array([[1.0], [2.0], [3.0]])
    nd = MDP.normdist(col)
    assert np.isclose(np.sum(nd), 1.0)


def test_mdp_step_returns_valid_action():
    C = np.arange(cf.NUM_OBSERVATIONS, dtype=float).reshape(-1, 1)
    mdp = MDP(np.zeros((cf.NUM_OBSERVATIONS, cf.NUM_STATES)),
              np.zeros((cf.NUM_ACTIONS, cf.NUM_STATES, cf.NUM_STATES)),
              C)
    mdp.reset(0)
    assert mdp.sQ.shape == (cf.NUM_STATES, 1)
    for _ in range(5):
        action = mdp.step(0)
        assert 0 <= action < cf.NUM_ACTIONS


@pytest.mark.parametrize("previous_action", [0, 8])
def test_mdp_priors_prefer_not_staying_and_not_reversing(previous_action):
    mdp = create_ant(cf.INIT_X, cf.INIT_Y, PREFERENCES).mdp
    # Identical observation columns give equal risk for every action; the real
    # posterior therefore exposes stay/reversal penalties independently.
    mdp.set_A(np.full((cf.NUM_OBSERVATIONS, cf.NUM_STATES), 1.0 / cf.NUM_OBSERVATIONS))
    mdp.reset(0)
    mdp.prev_action = previous_action
    mdp.step(0)
    posterior = mdp.uQ.ravel()
    opposite = cf.OPPOSITE_ACTIONS[previous_action]
    unpenalized = [action for action in range(cf.NUM_ACTIONS) if action not in (4, opposite)]
    np.testing.assert_allclose(posterior[unpenalized], posterior[previous_action])
    assert posterior[opposite] < posterior[previous_action]
    assert posterior[4] < posterior[previous_action]
    assert posterior[opposite] / posterior[previous_action] == pytest.approx(np.exp(-20))
    assert posterior[4] / posterior[previous_action] == pytest.approx(np.exp(-20))
    assert np.sum(posterior) == pytest.approx(1.0)


def test_strict_prior_vector_shape():
    """figure_3.py's strict prior must be a (10, 1) column (regression)."""
    strict = np.array([[0, 0, 0, 0, 0, 1, 2, 3, 4, 5]]).T
    assert strict.shape == (cf.NUM_OBSERVATIONS, 1)
    normalized = MDP.normdist(strict + np.exp(-16))
    assert not np.isnan(normalized).any()
    # gradient: ~0 preference for low levels, increasing for high levels
    assert normalized.min() < 1e-6
    assert normalized.max() > 0.3


# ---------------------------------------------------------------- main()


def test_main_save_false_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    np.random.seed(0)
    rt, _paths, coeff = main(num_steps=60, init_ants=3, max_ants=3, C=PREFERENCES,
                            save=False, switch=False, name="nosave")
    assert isinstance(rt, int)
    assert float(coeff) >= 0
    assert not os.path.isdir("imgs")
    assert not [f for f in os.listdir(".") if f.endswith(".npy")]


@pytest.mark.slow
def test_main_save_true_writes_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    np.random.seed(0)
    main(num_steps=120, init_ants=3, max_ants=3, C=PREFERENCES,
         save=True, switch=False, name="save")
    assert os.path.isfile("imgs/save.gif")
    assert os.path.isfile("imgs/save_locations.npy")
    assert os.path.isfile("imgs/save_round_trips.npy")
    pngs = [f for f in os.listdir("imgs") if f.endswith(".png")]
    assert len(pngs) == 20  # one snapshot every 5% of the run


@pytest.mark.parametrize("num_steps", [0, 1, 3, 5, 7, 6])
@pytest.mark.parametrize("switch", [False, True])
def test_main_switch_is_once_and_run_local(num_steps, switch, monkeypatch):
    original = tuple(cf.FOOD_LOCATION)
    mirrored = (cf.GRID[0] - original[0], original[1])
    instances = []

    class ObservedEnv(Env):
        def __init__(self):
            super().__init__()
            self.initial_food = tuple(self.food_location)
            self.food_history = []
            instances.append(self)

        def decay(self):
            self.food_history.append(tuple(self.food_location))
            return super().decay()

    monkeypatch.setattr(implementation, "Env", ObservedEnv)
    for _ in range(2):
        main(num_steps=num_steps, init_ants=1, max_ants=1, C=PREFERENCES,
             save=False, switch=switch)
        assert tuple(cf.FOOD_LOCATION) == original
    middle = num_steps // 2
    expected = [
        mirrored if switch and middle > 0 and step >= middle else original
        for step in range(num_steps)
    ]
    for env in instances:
        assert env.initial_food == original
        assert env.food_history == expected
        transitions = sum(
            before != after
            for before, after in zip([original] + env.food_history, env.food_history)
        )
        assert transitions == int(switch and middle > 0)


def test_main_adds_ants_up_to_max(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    np.random.seed(0)
    rt, _paths, _coeff = main(num_steps=60, init_ants=1, max_ants=3, C=PREFERENCES,
                            save=False, switch=False, name="grow")
    assert 0 <= rt <= 3


def test_main_returns_ragged_paths_as_object_array(monkeypatch):
    expected = _returning_trip_fixture(monkeypatch)
    completed, paths, _distance = main(
        num_steps=3, init_ants=2, max_ants=2, C=PREFERENCES, save=False,
    )
    assert completed == 2
    assert paths.dtype == object
    assert _path_coordinates(paths) == expected
    assert {len(path) for path in paths} == {2, 3}


def test_plot_path_writes_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = np.array([[20.0, 30.0], [21.0, 30.0], [22.0, 30.0]])
    plot_path(path, "path.png")
    assert os.path.isfile("path.png")


def test_dis():
    assert dis(0, 0, 3, 4) == pytest.approx(5.0)


@pytest.mark.parametrize("num_steps", [1, 5])
@pytest.mark.parametrize("ant_only_gif", [False, True])
def test_small_saved_runs_have_decodable_animation_and_histories(
    tmp_path, monkeypatch, num_steps, ant_only_gif,
):
    monkeypatch.chdir(tmp_path)
    completed, _paths, _distance = main(
        num_steps=num_steps, init_ants=1, max_ants=1, C=PREFERENCES,
        save=True, name="short", ant_only_gif=ant_only_gif,
    )
    frames = imageio.mimread("imgs/short.gif")
    assert frames
    for frame in frames:
        assert frame.ndim == 3 and frame.shape[2] in (3, 4)
        assert frame.shape[0] > 0 and frame.shape[1] > 0
        assert frame.max() > 0
    assert sorted(path.name for path in Path("imgs").glob("short_*.png")) == [
        f"short_{step}.png" for step in range(num_steps)
    ]
    locations = np.load("imgs/short_locations.npy", allow_pickle=True)
    round_trips = np.load("imgs/short_round_trips.npy")
    assert len(locations) == num_steps
    assert all(len(row) == 1 for row in locations)
    assert round_trips.shape == (num_steps,)
    assert np.isfinite(round_trips).all()
    assert round_trips[-1] == completed


def test_main_no_save_preserves_results_and_rng_without_output_history_work(
    tmp_path, monkeypatch,
):
    saved_directory = tmp_path / "saved"
    unsaved_directory = tmp_path / "unsaved"
    saved_directory.mkdir()
    unsaved_directory.mkdir()
    initial_state = np.random.RandomState(23).get_state()
    np.random.set_state(initial_state)
    with monkeypatch.context() as selected:
        selected.chdir(saved_directory)
        expected = _returning_trip_fixture(selected)
        saved = main(num_steps=3, init_ants=2, max_ants=2, C=PREFERENCES,
                     save=True, name="paired")
        saved_rng = np.random.get_state()

    def output_reached(*_args, **_kwargs):
        pytest.fail("save=False reached output generation")

    original_array = np.array

    def reject_output_history(values):
        if isinstance(values, list) and values:
            if isinstance(values[0], (float, np.floating)):
                pytest.fail("save=False retained or converted the output-only round-trip history")
            if (isinstance(values[0], list) and values[0]
                    and isinstance(values[0][0], list)):
                pytest.fail("save=False retained or converted the output-only location history")

    def without_output_histories(values, *args, **kwargs):
        reject_output_history(values)
        return original_array(values, *args, **kwargs)

    observed_path_appends = []

    def observe_collection(frame, event, method):
        if event != "c_return" or frame.f_code is not main.__code__:
            return
        if getattr(method, "__name__", None) != "append":
            return
        values = getattr(method, "__self__", None)
        reject_output_history(values)
        if (isinstance(values, list) and values and isinstance(values[0], list)
                and values[0] and isinstance(values[0][0], tuple)):
            observed_path_appends.append([tuple(position) for position in values[-1]])

    np.random.set_state(initial_state)
    with monkeypatch.context() as selected:
        selected.chdir(unsaved_directory)
        _returning_trip_fixture(selected)
        selected.setattr(Env, "plot", output_reached)
        selected.setattr(implementation, "save_gif", output_reached)
        selected.setattr(np, "save", output_reached)
        selected.setattr(np, "array", without_output_histories)
        previous_profile = sys.getprofile()
        try:
            sys.setprofile(observe_collection)
            unsaved = main(num_steps=3, init_ants=2, max_ants=2, C=PREFERENCES, save=False)
        finally:
            sys.setprofile(previous_profile)
        unsaved_rng = np.random.get_state()
    assert saved[0] == unsaved[0] == 2
    assert saved[1].dtype == unsaved[1].dtype == object
    assert _path_coordinates(saved[1]) == _path_coordinates(unsaved[1]) == expected
    assert observed_path_appends == expected
    assert saved[2] == unsaved[2]
    assert saved_rng[0] == unsaved_rng[0]
    np.testing.assert_array_equal(saved_rng[1], unsaved_rng[1])
    assert saved_rng[2:] == unsaved_rng[2:]
    assert list(unsaved_directory.iterdir()) == []
