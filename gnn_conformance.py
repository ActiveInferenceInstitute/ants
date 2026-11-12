"""Conformance checks for the ant colony foraging GNN specification.

The model is specified in ``gnn/ant_colony_foraging.gnn.md`` and validated with
the Generalized Notation Notation (GNN) revision pinned in
``gnn/upstream.json``. The pin itself is read by ``gnn.importers``, the reader
shipped in that revision; this module carries no pin shape of its own. The
pinned revision is read from the pinned commit (via ``git archive``), never from
the GNN checkout's working tree, so in-progress edits in that repository cannot
contaminate a check.

Two entry points share this module:

- ``tests/test_gnn_conformance.py`` — pytest checks (skip cleanly when the GNN
  checkout or its interpreter is unavailable);
- ``scripts/validate_gnn_spec.py`` — the strict local gate (fails, never
  skips).

Requires numpy and the GNN checkout; nothing else.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from gnn.importers import ImporterPin

REPO_ROOT = Path(__file__).resolve().parent
SPEC_PATH = REPO_ROOT / "gnn" / "ant_colony_foraging.gnn.md"
DEFAULT_GNN_ROOT = REPO_ROOT.parent / "Generalized_Notation_Notation"

# The headless extractor contract consumed here: gnn.extract returns the
# POMDPStateSpace mapping described by this schema version. Major version 1 is
# required; minor versions may append keys.
REQUIRED_EXTRACT_SCHEMA_MAJOR = "1"


class ConformanceError(RuntimeError):
    """The specification does not conform to the pinned GNN revision or the code."""


class GnnUnavailable(ConformanceError):
    """The pinned GNN checkout or a suitable interpreter is not available."""


def _importer_source(root: Path | str | None = None) -> Path:
    """Return the ``src`` tree whose ``gnn`` package is the pinned revision.

    ``scripts/gate.py`` exports ``GNN_SOURCE`` — ``src/gnn`` extracted from the
    pinned commit — so the reader is the pinned revision even when a sibling
    checkout sits at a different one. A standalone run falls back to the
    checkout that carries the pin.
    """

    explicit = os.environ.get("GNN_SOURCE")
    source = Path(explicit).expanduser().resolve() if explicit else resolve_gnn_root(root) / "src"
    if not (source / "gnn" / "importers.py").is_file():
        raise ConformanceError(
            f"{source} carries no gnn/importers.py; the pin must name a GNN release "
            "that ships the shared reader (v5.1.0 or later)"
        )
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    return source


def _importer_reader(root: Path | str | None = None):
    """Return ``gnn.importers``, the pin reader shipped in the pinned revision."""

    _importer_source(root)
    return import_module("gnn.importers")


def pinned_pin(root: Path | str | None = None) -> ImporterPin:
    """Read this repository's pin with the reader shipped in the pinned revision.

    The reader normalizes the pin shape and reports a pin it cannot read; this
    function only requires the two facts the extraction below is pinned to: a
    release tag and a commit.
    """

    importers = _importer_reader(root)
    path = importers.find_pin(REPO_ROOT)
    if path is None:
        raise ConformanceError(
            "no GNN pin file found; gnn/upstream.json records the revision this "
            "specification is validated against"
        )
    try:
        pin = importers.read_pin(path)
    except importers.PinError as exc:
        raise ConformanceError(str(exc)) from exc
    if not pin.tag:
        raise ConformanceError(f"{path.name} records no release tag")
    return pin


def resolve_gnn_root(explicit: Path | str | None = None) -> Path:
    """Return the GNN checkout path (``--gnn-root``, ``GNN_ROOT``, then sibling)."""

    candidates = [explicit, os.environ.get("GNN_ROOT"), DEFAULT_GNN_ROOT]
    for candidate in candidates:
        if not candidate:
            continue
        root = Path(candidate).expanduser().resolve()
        if (root / "src" / "gnn" / "__init__.py").is_file():
            return root
    raise GnnUnavailable(
        "no GNN checkout found; set GNN_ROOT or clone "
        "ActiveInferenceInstitute/Generalized_Notation_Notation next to this "
        f"repository ({DEFAULT_GNN_ROOT})"
    )


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ConformanceError(f"git {' '.join(args)} failed in {root}: {result.stderr.strip()}")
    return result.stdout.strip()


def verify_pin(root: Path, tag: str, commit: str) -> None:
    """Verify the pinned tag and commit resolve to the same object."""

    resolved = _git(root, "rev-parse", "--verify", f"{commit}^{{commit}}")
    if resolved != commit:
        raise ConformanceError(f"pinned commit resolves to {resolved}, not {commit}")
    tag_commit = _git(root, "rev-parse", "--verify", f"{tag}^{{commit}}")
    if tag_commit != commit:
        raise ConformanceError(f"pinned tag {tag} resolves to {tag_commit}, not {commit}")


def pinned_source(root: Path, commit: str, destination: Path) -> Path:
    """Extract the pinned ``src/gnn`` tree into ``destination`` and return it."""

    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.Popen(
        ["git", "-C", str(root), "archive", commit, "src/gnn"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    extract = subprocess.run(
        ["tar", "-x", "-C", str(destination)],
        stdin=archive.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    assert archive.stdout is not None
    archive.stdout.close()
    archive_stderr = archive.stderr.read().decode() if archive.stderr else ""
    archive.wait()
    if archive.returncode != 0 or extract.returncode != 0:
        raise ConformanceError(
            f"could not extract pinned GNN source: {archive_stderr.strip()} "
            f"{extract.stderr.strip()}"
        )
    source = destination / "src"
    if not (source / "gnn" / "__init__.py").is_file():
        raise ConformanceError(f"pinned GNN extraction is incomplete at {source}")
    return source


def resolve_interpreter(root: Path) -> Path:
    """Return the Python used to run the pinned extractor.

    ``GNN_PYTHON`` wins; otherwise the GNN checkout's own virtualenv; otherwise
    the interpreter running this module. The headless ``gnn.extract`` path is
    standard-library only for discrete POMDP models, so the fallback is valid
    for this repository's model.
    """

    explicit = os.environ.get("GNN_PYTHON")
    if explicit:
        interpreter = Path(explicit).expanduser()
        if not interpreter.is_file():
            raise GnnUnavailable(f"GNN_PYTHON does not exist: {interpreter}")
        return interpreter
    venv_python = root / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return venv_python
    return Path(sys.executable)


def extract_spec(
    spec: Path = SPEC_PATH,
    gnn_root: Path | str | None = None,
    interpreter: Path | str | None = None,
) -> dict:
    """Parse ``spec`` with the pinned GNN extractor and return the mapping."""

    root = resolve_gnn_root(gnn_root)
    pin = pinned_pin(root)
    verify_pin(root, pin.tag, pin.commit)
    python = Path(interpreter) if interpreter else resolve_interpreter(root)
    spec = Path(spec).resolve()
    with tempfile.TemporaryDirectory(prefix="gnn-pinned-") as temporary:
        source = pinned_source(root, pin.commit, Path(temporary))
        environment = dict(os.environ)
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = f"{source}{os.pathsep}{existing}" if existing else str(source)
        result = subprocess.run(
            [str(python), "-m", "gnn.extract", str(spec)],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
    if result.returncode != 0:
        raise ConformanceError(
            f"pinned GNN extractor failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    model = json.loads(result.stdout)
    if isinstance(model, dict) and model.get("status") == "error":
        raise ConformanceError(f"pinned GNN extractor rejected {spec}: {model['error']}")
    schema = str(model.get("extraction_schema_version", ""))
    if schema.split(".")[0] != REQUIRED_EXTRACT_SCHEMA_MAJOR:
        raise ConformanceError(
            f"unexpected extraction schema version {schema!r}; "
            f"this repository consumes major version {REQUIRED_EXTRACT_SCHEMA_MAJOR}"
        )
    return model


def spec_sha256(spec: Path = SPEC_PATH) -> str:
    """Return the SHA-256 of the specification bytes."""

    return hashlib.sha256(Path(spec).read_bytes()).hexdigest()


def receipt(model: dict, checks: list[str], spec: Path = SPEC_PATH) -> dict:
    """Build a JSON-serializable receipt for the validation run."""

    pin = pinned_pin()
    return {
        "spec": str(Path(spec).resolve().relative_to(REPO_ROOT)),
        "spec_sha256": spec_sha256(spec),
        "pin": {"repository": pin.repository, "tag": pin.tag, "commit": pin.commit},
        "extraction_schema_version": model.get("extraction_schema_version"),
        "model_kind": model.get("model_kind"),
        "dimensions": {
            "num_states": model.get("num_states"),
            "num_observations": model.get("num_observations"),
            "num_actions": model.get("num_actions"),
        },
        "checks": checks,
    }


# --------------------------------------------------------------------------
# Model checks: the specification against the implementation in ants.py.
# --------------------------------------------------------------------------


def _import_implementation():
    """Import the repository's simulation modules (numpy + matplotlib)."""

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    import config as cf
    from ants import MDP, Env, create_ant

    return cf, Env, MDP, create_ant


def standard_preference() -> np.ndarray:
    """The standard prior used by figure_1.py and figure_2.py."""

    cf, _, _, _ = _import_implementation()
    return np.arange(cf.NUM_OBSERVATIONS, dtype=float).reshape(-1, 1)


def _softmax(values: np.ndarray) -> np.ndarray:
    shifted = np.asarray(values, dtype=float) - float(np.max(values))
    exponentiated = np.exp(shifted)
    return exponentiated / exponentiated.sum()


def _normalize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    return values / values.sum()


def check_conformance(model: dict) -> list[str]:
    """Check the extracted specification against the implementation.

    Returns the list of passed check names; raises :class:`ConformanceError` on
    the first mismatch.
    """

    cf, Env, MDP, create_ant = _import_implementation()
    passed: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ConformanceError(message)

    require(model.get("model_kind") == "discrete", "model kind must be discrete")
    require(
        int(model["num_states"]) == cf.NUM_STATES == 9,
        f"hidden states: spec {model['num_states']} vs config {cf.NUM_STATES}",
    )
    require(
        int(model["num_observations"]) == cf.NUM_OBSERVATIONS == 10,
        f"observations: spec {model['num_observations']} vs config {cf.NUM_OBSERVATIONS}",
    )
    require(
        int(model["num_actions"]) == cf.NUM_ACTIONS == 9,
        f"actions: spec {model['num_actions']} vs config {cf.NUM_ACTIONS}",
    )
    parameters = model.get("model_parameters") or {}
    require(
        parameters.get("num_hidden_states") == cf.NUM_STATES
        and parameters.get("num_obs") == cf.NUM_OBSERVATIONS
        and parameters.get("num_actions") == cf.NUM_ACTIONS,
        f"ModelParameters disagree with config.py: {parameters}",
    )
    passed.append("dimensions match config.py (9 states, 10 observations, 9 actions)")

    env = Env()
    ant = create_ant(cf.INIT_X, cf.INIT_Y, standard_preference())
    initial_likelihood = env.get_A(ant)
    require(
        np.allclose(np.asarray(model["A_matrix"], dtype=float), initial_likelihood),
        "A does not match the fresh-environment likelihood from Env.get_A",
    )
    require(
        np.allclose(initial_likelihood.sum(axis=0), 1.0),
        "the implementation's initial likelihood columns must be stochastic",
    )
    passed.append("A equals the fresh-environment likelihood (Env.get_A)")

    # The implementation stores B as [action][next_state][previous_state]
    # (MDP.step computes B[a] @ sQ); GNN stores it as
    # [next_state][previous_state][action].
    raw_transitions = np.zeros((cf.NUM_ACTIONS, cf.NUM_STATES, cf.NUM_STATES))
    for action in range(cf.NUM_ACTIONS):
        raw_transitions[action, action, :] = 1.0
    mdp = MDP(initial_likelihood, raw_transitions, standard_preference())
    canonical_transitions = np.transpose(mdp.B, (1, 2, 0))
    require(
        np.allclose(np.asarray(model["B_matrix"], dtype=float), canonical_transitions, atol=1e-5),
        "B does not match the deterministic create_ant transition tensor",
    )
    passed.append("B matches the deterministic action-index transitions (create_ant)")

    log_preferences = np.log(_normalize(standard_preference().ravel() + mdp.p0))
    require(
        np.allclose(_softmax(model["C_vector"]), np.exp(log_preferences), atol=1e-6),
        "softmax(C) does not recover normalize(C_raw + p0) for the standard prior",
    )
    passed.append("C decodes to the standard-prior preference distribution")

    require(
        np.allclose(model["D_vector"], np.full(cf.NUM_STATES, 1.0 / cf.NUM_STATES)),
        "D must be the uniform prior over focal cells",
    )
    passed.append("D is uniform over the nine focal cells")

    habit = np.zeros(cf.NUM_ACTIONS)
    habit[4] = -20.0
    expected_habit = _softmax(habit)
    require(
        np.allclose(model["E_vector"], expected_habit, atol=1e-12),
        "E must encode the implementation's -20 stay-avoidance log-prior",
    )
    require(
        int(np.argmin(model["E_vector"])) == 4,
        "E must assign the smallest habit weight to staying in place (action 4)",
    )
    passed.append("E encodes the -20 stay-avoidance habit prior")

    return passed
