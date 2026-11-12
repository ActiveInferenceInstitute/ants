"""Conformance tests for the ant colony foraging GNN specification.

The specification is validated with the pinned GNN revision when the GNN
checkout is available; the structural checks (specification sections and
declared dimensions against config.py) always run so CI still guards the
specification. The pin itself is read by the ``gnn.importers`` reader shipped
in the pinned revision — this repository carries no pin shape of its own, and
the ``gnn`` arm runs that reader directly. When ``GNN_ROOT`` selects a checkout
explicitly (as CI does after provisioning the pinned revision), an unusable
checkout is a failure, never a skip.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

import config as cf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gnn_conformance import (
    SPEC_PATH,
    GnnUnavailable,
    check_conformance,
    extract_spec,
    pinned_pin,
)

REQUIRED_SECTIONS = (
    "GNNSection",
    "GNNVersionAndFlags",
    "ModelName",
    "StateSpaceBlock",
    "Connections",
    "InitialParameterization",
    "Equations",
    "Time",
    "ActInfOntologyAnnotation",
    "ModelParameters",
    "Footer",
    "Signature",
)


@pytest.fixture(scope="module")
def extracted_model() -> dict:
    try:
        return extract_spec()
    except GnnUnavailable as exc:
        if os.environ.get("GNN_ROOT"):
            pytest.fail(f"GNN_ROOT selects a checkout, but the pinned parser is unavailable: {exc}")
        pytest.skip(f"pinned GNN checkout unavailable: {exc}")


def test_pin_is_read_by_the_shipped_reader() -> None:
    try:
        pin = pinned_pin()
    except GnnUnavailable as exc:
        if os.environ.get("GNN_ROOT"):
            pytest.fail(f"GNN_ROOT selects a checkout, but the shipped reader is unavailable: {exc}")
        pytest.skip(f"pinned GNN checkout unavailable: {exc}")
    assert pin.path.name == "upstream.json"
    assert pin.schema == "gnn-importer-pin/v1"


def test_spec_declares_every_section() -> None:
    text = SPEC_PATH.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" in text, f"missing section {section}"


def declared_dimensions() -> dict[str, tuple[int, ...]]:
    text = SPEC_PATH.read_text(encoding="utf-8")
    dimensions: dict[str, tuple[int, ...]] = {}
    for line in text.splitlines():
        match = re.match(
            r"^([A-Za-z_][A-Za-z0-9_]*)\[([0-9]+(?:\s*,\s*[0-9]+)*)\s*,type=",
            line.strip(),
        )
        if match:
            dimensions[match.group(1)] = tuple(int(part) for part in match.group(2).split(","))
    return dimensions


def test_declared_dimensions_match_config() -> None:
    dimensions = declared_dimensions()
    assert dimensions["A"] == (cf.NUM_OBSERVATIONS, cf.NUM_STATES)
    assert dimensions["B"] == (cf.NUM_STATES, cf.NUM_STATES, cf.NUM_ACTIONS)
    assert dimensions["C"] == (cf.NUM_OBSERVATIONS,)
    assert dimensions["D"] == (cf.NUM_STATES,)
    assert dimensions["E"] == (cf.NUM_ACTIONS,)
    assert dimensions["s"] == (cf.NUM_STATES, 1)
    assert dimensions["o"] == (cf.NUM_OBSERVATIONS, 1)


def test_extraction_uses_schema_major_one(extracted_model: dict) -> None:
    assert extracted_model["extraction_schema_version"].startswith("1.")


def test_spec_conforms_to_implementation(extracted_model: dict) -> None:
    checks = check_conformance(extracted_model)
    assert len(checks) == 6
