"""Sanity checks for the simulation parameters in config.py."""

import numpy as np

import config as cf


def test_grid_dimensions():
    assert cf.GRID[0] == cf.GRID[1] == 40
    assert cf.GRID_SIZE == np.prod(cf.GRID)


def test_action_map():
    assert len(cf.ACTION_MAP) == 9
    assert cf.ACTION_MAP[4] == (0, 0)
    # eight neighbors around the center
    assert len(set(cf.ACTION_MAP)) == 9


def test_opposite_actions():
    assert cf.OPPOSITE_ACTIONS == list(reversed(range(len(cf.ACTION_MAP))))


def test_observation_and_state_counts():
    assert cf.NUM_OBSERVATIONS == cf.NUM_PHEROMONE_LEVELS == 10
    assert cf.NUM_STATES == cf.FOCAL_SIZE == 9
    assert cf.NUM_ACTIONS == cf.FOCAL_SIZE


def test_positive_parameters():
    for value in (
        cf.DECAY_FACTOR,
        cf.NEST_FACTOR,
        cf.ADD_ANT_EVERY,
        cf.MAX_LEN,
    ):
        assert value > 0
