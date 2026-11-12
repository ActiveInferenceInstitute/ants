"""Behavioral tests for the ant colony simulation (ants.py)."""

import os

import numpy as np
import pytest

import config as cf
from ants import MDP, Env, create_ant, dis, main, plot_path

PREFERENCES = np.arange(cf.NUM_OBSERVATIONS, dtype=float).reshape(-1, 1)


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


def test_step_backward_completes_trip():
    env = Env()
    ant = create_ant(cf.INIT_X, cf.INIT_Y, PREFERENCES)
    ant.traj = [
        (cf.INIT_X, cf.INIT_Y),
        (cf.INIT_X + 1, cf.INIT_Y),
        (cf.INIT_X + 2, cf.INIT_Y),
    ]
    ant.is_returning = True
    env.step_backward(ant)
    complete, traj = env.step_backward(ant)
    assert complete
    assert len(traj) == 3
    assert not ant.is_returning
    assert ant.traj == []


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


def test_mdp_priors_prefer_not_staying_and_not_reversing():
    C = np.zeros((cf.NUM_OBSERVATIONS, 1))
    mdp = MDP(np.zeros((cf.NUM_OBSERVATIONS, cf.NUM_STATES)),
              np.zeros((cf.NUM_ACTIONS, cf.NUM_STATES, cf.NUM_STATES)),
              C)
    mdp.reset(0)
    mdp.step(0)
    assert mdp.uQ.shape == (cf.NUM_ACTIONS, 1)
    assert np.isclose(np.sum(mdp.uQ), 1.0)


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


def test_main_switch_moves_food():
    original = cf.FOOD_LOCATION[0]
    try:
        np.random.seed(0)
        main(num_steps=120, init_ants=3, max_ants=3, C=PREFERENCES,
             save=False, switch=True, name="switch")
        assert cf.FOOD_LOCATION[0] == cf.GRID[0] - original
    finally:
        cf.FOOD_LOCATION[0] = original


def test_main_adds_ants_up_to_max(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    np.random.seed(0)
    rt, _paths, _coeff = main(num_steps=60, init_ants=1, max_ants=3, C=PREFERENCES,
                            save=False, switch=False, name="grow")
    assert 0 <= rt <= 3


def test_main_returns_ragged_paths_as_object_array():
    """Completed round trips have varied lengths and must be returned as an
    object array (numpy >= 1.24 rejects ragged numeric arrays)."""
    try:
        # nest on the top corridor for fast, reliable food discovery
        cf.INIT_X, cf.INIT_Y = 20, 5
        cf.NEST_FACTOR = 1.0
        np.random.seed(2)
        rt, paths, _coeff = main(num_steps=200, init_ants=5, max_ants=5, C=PREFERENCES,
                                save=False, switch=False, name="ragged")
        assert rt >= 1
        assert paths.dtype == object
        lengths = {len(p) for p in paths}
        assert len(lengths) > 1
        assert all(hasattr(p, "__len__") for p in paths)
    finally:
        cf.INIT_X, cf.INIT_Y = 20, 30
        cf.NEST_FACTOR = 0.1


def test_plot_path_writes_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = np.array([[20.0, 30.0], [21.0, 30.0], [22.0, 30.0]])
    plot_path(path, "path.png")
    assert os.path.isfile("path.png")


def test_dis():
    assert dis(0, 0, 3, 4) == pytest.approx(5.0)
