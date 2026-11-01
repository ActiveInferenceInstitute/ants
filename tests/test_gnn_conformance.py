"""Conformance tests for the ant colony foraging GNN specification.

The specification is validated with the pinned GNN revision when the GNN
checkout is available; the structural checks (pin record, sections, declared
dimensions against config.py) always run so CI still guards the specification.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

import config as cf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gnn_conformance import (
    SPEC_PATH,
    ConformanceError,
    GnnUnavailable,
    check_conformance,
    extract_spec,
    load_pin,
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

CANONICAL_PIN = {
    "repository": "ActiveInferenceInstitute/Generalized_Notation_Notation",
    "tag": "v5.0.3",
    "commit": "8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1",
}


@pytest.fixture(scope="module")
def extracted_model() -> dict:
    try:
        return extract_spec()
    except GnnUnavailable as exc:
        pytest.skip(f"pinned GNN checkout unavailable: {exc}")


def test_pin_record_is_canonical() -> None:
    pin = load_pin()
    assert pin.repository == CANONICAL_PIN["repository"]
    assert pin.tag == CANONICAL_PIN["tag"]
    assert pin.commit == CANONICAL_PIN["commit"]


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


def test_missing_pin_file_is_rejected(tmp_path) -> None:
    with pytest.raises(ConformanceError, match="is missing"):
        load_pin(tmp_path / "upstream.json")


def test_incomplete_pin_record_is_rejected(tmp_path) -> None:
    pin = tmp_path / "upstream.json"
    pin.write_text('{"repository": "x", "tag": "v1"}', encoding="utf-8")
    with pytest.raises(ConformanceError, match="missing the 'commit' field"):
        load_pin(pin)


def test_malformed_pin_file_is_rejected(tmp_path) -> None:
    pin = tmp_path / "upstream.json"
    pin.write_text("not json", encoding="utf-8")
    with pytest.raises(ConformanceError, match="is unreadable"):
        load_pin(pin)
