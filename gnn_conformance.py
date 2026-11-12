"""Conformance checks for the ant colony foraging GNN specification.

The model is specified in ``gnn/ant_colony_foraging.gnn.md`` and validated with
the Generalized Notation Notation (GNN) revision pinned in
``gnn/upstream.json``. The pinned revision is read from the pinned commit (via
``git archive``), never from the GNN checkout's working tree, so in-progress
edits in that repository cannot contaminate a check.

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
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent
PIN_PATH = REPO_ROOT / "gnn" / "upstream.json"
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


@dataclass(frozen=True)
class Pin:
    """The GNN revision this repository's specification is validated against."""

    repository: str
    tag: str
    commit: str


def load_pin(path: Path = PIN_PATH) -> Pin:
    """Read and validate the repository-local GNN pin record."""

    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConformanceError(
            f"{source} is missing; the pinned GNN revision is required to validate "
            "the specification"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ConformanceError(f"{source} is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise ConformanceError(f"{source} must contain a JSON object")
    if data.get("schema") != "gnn-importer-pin/v1":
        raise ConformanceError(f"{source}: schema must be gnn-importer-pin/v1")
    try:
        pin = Pin(
            repository=str(data["repository"]),
            tag=str(data["tag"]),
            commit=str(data["commit"]),
        )
    except KeyError as exc:
        raise ConformanceError(f"{source} is missing the {exc} field") from exc
    if len(pin.commit) != 40 or any(c not in "0123456789abcdef" for c in pin.commit):
        raise ConformanceError(
            f"{source}: commit must be a 40-character lowercase hex SHA"
        )
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


def verify_pin(root: Path, pin: Pin) -> None:
    """Verify the pinned tag and commit resolve to the same object."""

    commit = _git(root, "rev-parse", "--verify", f"{pin.commit}^{{commit}}")
    if commit != pin.commit:
        raise ConformanceError(f"pinned commit resolves to {commit}, not {pin.commit}")
    tag_commit = _git(root, "rev-parse", "--verify", f"{pin.tag}^{{commit}}")
    if tag_commit != pin.commit:
        raise ConformanceError(f"pinned tag {pin.tag} resolves to {tag_commit}, not {pin.commit}")


def pinned_source(root: Path, pin: Pin, destination: Path) -> Path:
    """Extract the pinned ``src/gnn`` tree into ``destination`` and return it."""

    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.Popen(
        ["git", "-C", str(root), "archive", pin.commit, "src/gnn"],
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
    pin = load_pin()
    verify_pin(root, pin)
    python = Path(interpreter) if interpreter else resolve_interpreter(root)
    spec = Path(spec).resolve()
    with tempfile.TemporaryDirectory(prefix="gnn-pinned-") as temporary:
        source = pinned_source(root, pin, Path(temporary))
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

    pin = load_pin()
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
