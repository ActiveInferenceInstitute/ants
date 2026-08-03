"""Regression tests for the experiment scripts (figure_1/2/3.py)."""

import importlib
import sys
from pathlib import Path

import numpy as np

import config as cf
from ants import MDP

REPO_ROOT = Path(__file__).resolve().parents[1]


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
