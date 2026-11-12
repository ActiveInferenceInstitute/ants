#!/usr/bin/env python3
"""Composable local gate: one entry point, one command per arm.

Run every arm through this script locally and in CI so a command is defined
exactly once:

    uv run python scripts/gate.py fast        # lint + docs + fast tests
    uv run python scripts/gate.py test-fast   # tests selected as "not slow"
    uv run python scripts/gate.py test        # full suite, 90% coverage floor
    uv run python scripts/gate.py gnn         # pinned-upstream GNN conformance
    uv run python scripts/gate.py docs        # relative links + generated metrics
    uv run python scripts/gate.py lint
    uv run python scripts/gate.py all         # every arm, failing fast

Each arm records a receipt (wall time, exit code, parsed pytest/ruff facts)
under ``.gate-cache/``; ``metrics`` folds the receipts into the checked-in
``docs/_generated/gate-metrics.json`` and regenerates ``gate-metrics.md``.

There is no ``types`` arm: this repository has no type checker configured
(see docs/RUN_GUIDE.md).

Exit codes: 0 every requested arm passed, 1 an arm failed or was interrupted.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
CACHE = REPO_ROOT / ".gate-cache"
RECEIPTS = CACHE / "latest.json"
GNN_PIN = REPO_ROOT / "gnn" / "upstream.json"
METRICS_JSON = REPO_ROOT / "docs" / "_generated" / "gate-metrics.json"

# Summary facts parsed from arm output; they land in the receipt and the
# generated metrics page instead of being copied into prose by hand.
FACT_PATTERNS = (
    ("tests_passed", re.compile(r"(\d+) passed")),
    ("tests_failed", re.compile(r"(\d+) failed")),
    ("tests_skipped", re.compile(r"(\d+) skipped")),
    ("coverage_percent", re.compile(r"Total coverage: ([\d.]+)%")),
    ("ruff", re.compile(r"All checks passed!")),
)


@dataclass(frozen=True)
class Arm:
    name: str
    summary: str
    commands: tuple[tuple[str, ...], ...]
    needs_gnn: bool = False


def arms() -> dict[str, Arm]:
    """Build the arm table around the interpreter running this script."""

    python = sys.executable
    return {
        "lint": Arm(
            "lint",
            "ruff over the whole tree",
            ((python, "-m", "ruff", "check", "."),),
        ),
        "test-fast": Arm(
            "test-fast",
            "default test arm: slow-marked test excluded, no coverage instrumentation",
            ((python, "-m", "pytest", "-q", "--no-cov", "-m", "not slow"),),
        ),
        "test": Arm(
            "test",
            "full suite with the 90% coverage floor",
            ((python, "-m", "pytest"),),
        ),
        "docs": Arm(
            "docs",
            "relative-link check and generated-metrics freshness",
            ((python, str(SCRIPTS / "check_docs.py"),),),
        ),
        "gnn": Arm(
            "gnn",
            "pinned-upstream GNN conformance: strict validator plus conformance tests",
            (
                (python, str(SCRIPTS / "validate_gnn_spec.py")),
                (python, "-m", "pytest", "tests/test_gnn_conformance.py", "-q", "--no-cov"),
            ),
            needs_gnn=True,
        ),
    }


ALIASES = {
    "fast": ("lint", "docs", "test-fast"),
    "all": ("lint", "docs", "test", "gnn"),
}


def _run_streaming(command: tuple[str, ...], env: dict[str, str]) -> tuple[int, str]:
    """Run ``command``, echoing its combined output, and return (exit, output)."""

    print(f"$ {' '.join(command)}", flush=True)
    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    chunks: list[str] = []
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        chunks.append(line)
    return process.wait(), "".join(chunks)


def _must(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"provisioning failed: {' '.join(command)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def _read_pin() -> dict[str, str]:
    return json.loads(GNN_PIN.read_text(encoding="utf-8"))


def _fetch_pinned(pin: dict[str, str]) -> Path:
    """Fetch the pinned GNN revision into the ignored gate cache."""

    root = CACHE / "gnn"
    if not (root / ".git").is_dir():
        root.mkdir(parents=True, exist_ok=True)
        _must(["git", "init", "--quiet", str(root)])
    origin = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    url = f"https://github.com/{pin['repository']}.git"
    if origin.returncode != 0:
        _must(["git", "-C", str(root), "remote", "add", "origin", url])
    elif origin.stdout.strip() != url:
        _must(["git", "-C", str(root), "remote", "set-url", "origin", url])

    have = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "-q", f"{pin['commit']}^{{commit}}"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    if have.returncode != 0:
        # A pin that no longer resolves upstream fails here rather than skipping.
        _must(
            [
                "git",
                "-C",
                str(root),
                "fetch",
                "--depth",
                "1",
                "origin",
                pin["commit"],
                f"refs/tags/{pin['tag']}:refs/tags/{pin['tag']}",
            ]
        )
    checkout = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "-q", "HEAD"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    checked_out = (root / "src" / "gnn" / "__init__.py").is_file()
    if checkout.stdout.strip() != pin["commit"] or not checked_out:
        _must(["git", "-C", str(root), "checkout", "--quiet", "--detach", pin["commit"]])
    return root


def _gnn_venv(root: Path) -> Path:
    """Return the pinned-extractor interpreter, provisioning it once."""

    venv = CACHE / "gnn-venv"
    interpreter = venv / "bin" / "python"
    if interpreter.is_file():
        return interpreter
    _must(["uv", "venv", "--python", sys.executable, "--no-project", str(venv)])
    _must(["uv", "pip", "install", "--python", str(interpreter), "numpy", "defusedxml"])
    return interpreter


def provision_gnn() -> dict[str, str]:
    """Resolve a verified pinned checkout and export GNN_ROOT/GNN_PYTHON.

    An explicit ``GNN_ROOT`` (CI or a caller-supplied checkout) wins. Otherwise
    the module's own default checkout next to this repository is used when it
    carries the pinned tag and commit, and the pinned revision is fetched into
    ``.gate-cache/gnn`` when it is not.
    """

    env = dict(os.environ)
    if env.get("GNN_ROOT"):
        print(f"==> gnn: using GNN_ROOT={env['GNN_ROOT']}", flush=True)
        return env

    pin = _read_pin()
    sys.path.insert(0, str(REPO_ROOT))
    from gnn_conformance import ConformanceError, Pin, resolve_gnn_root, verify_pin

    record = Pin(repository=pin["repository"], tag=pin["tag"], commit=pin["commit"])
    root: Path | None = None
    try:
        candidate = resolve_gnn_root(None)
        verify_pin(candidate, record)
        root = candidate
    except ConformanceError as exc:
        print(f"==> gnn: default checkout unusable ({exc}); fetching the pin", flush=True)

    if root is None:
        root = _fetch_pinned(pin)
        verify_pin(root, record)
        env["GNN_PYTHON"] = str(_gnn_venv(root))
    elif not env.get("GNN_PYTHON") and (root / ".venv" / "bin" / "python").is_file():
        env["GNN_PYTHON"] = str(root / ".venv" / "bin" / "python")

    env["GNN_ROOT"] = str(root)
    print(
        f"==> gnn: pin {pin['tag']} ({pin['commit']}) at {root}, "
        f"interpreter {env.get('GNN_PYTHON', 'project python')}",
        flush=True,
    )
    return env


def _facts(output: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    for name, pattern in FACT_PATTERNS:
        match = pattern.search(output)
        if match:
            facts[name] = match.group(1) if match.groups() else "true"
    return facts


def _merge_receipt(name: str, entry: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    data = {"schema": "ants-gate-receipts/v1", "arms": {}}
    if RECEIPTS.is_file():
        try:
            data = json.loads(RECEIPTS.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    data.setdefault("arms", {})[name] = entry
    handle, temp = tempfile.mkstemp(dir=CACHE, prefix=".latest.", suffix=".json", text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temp, RECEIPTS)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def run_arm(arm: Arm) -> dict:
    env = provision_gnn() if arm.needs_gnn else dict(os.environ)
    print(f"\n=== {arm.name}: {arm.summary} ===", flush=True)
    started = time.perf_counter()
    output = ""
    status = 0
    for command in arm.commands:
        status, chunk = _run_streaming(command, env)
        output += chunk
        if status != 0:
            break
    elapsed = round(time.perf_counter() - started, 2)
    entry = {
        "arm": arm.name,
        "commands": [
            " ".join(command).replace(sys.executable, "python") for command in arm.commands
        ],
        "exit_code": status,
        "seconds": elapsed,
        "facts": _facts(output),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": platform.python_version(),
        "platform": f"{platform.system().lower()}-{platform.machine()}",
    }
    _merge_receipt(arm.name, entry)
    print(f"=== {arm.name}: {'pass' if status == 0 else 'FAIL'} in {elapsed}s ===", flush=True)
    return entry


def _step_summary(entries: list[dict]) -> None:
    destination = os.environ.get("GITHUB_STEP_SUMMARY")
    if not destination:
        return
    lines = ["### gate", "", "| Arm | Result | Wall time (s) | Facts |", "| --- | --- | ---: | --- |"]
    for entry in entries:
        facts = ", ".join(f"{key}={value}" for key, value in entry["facts"].items())
        lines.append(
            f"| `{entry['arm']}` | {'pass' if entry['exit_code'] == 0 else 'fail'} "
            f"| {entry['seconds']} | {facts} |"
        )
    lines.append("")
    with open(destination, "a", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "selections",
        nargs="*",
        metavar="ARM",
        help="arms to run: lint, test-fast, test, docs, gnn; aliases fast (default) and all",
    )
    parser.add_argument("--list", action="store_true", help="list the arms and exit")
    args = parser.parse_args(argv)

    table = arms()
    if args.list:
        for name, arm in table.items():
            print(f"{name:10} {arm.summary}")
        print(f"{'fast':10} alias: lint docs test-fast (the default)")
        print(f"{'all':10} alias: lint docs test gnn")
        print(f"{'metrics':10} refresh docs/_generated/gate-metrics.json and .md")
        return 0

    selections = args.selections or ["fast"]
    requested: list[str] = []
    for selection in selections:
        if selection == "metrics":
            requested.append("metrics")
        elif selection in ALIASES:
            requested.extend(ALIASES[selection])
        elif selection in table:
            requested.append(selection)
        else:
            parser.error(f"unknown arm: {selection}")

    entries: list[dict] = []
    failed = False
    for name in dict.fromkeys(requested):
        if name == "metrics":
            status, _ = _run_streaming(
                (sys.executable, str(SCRIPTS / "check_docs.py"), "--write-metrics"),
                dict(os.environ),
            )
            if status != 0:
                failed = True
                break
            continue
        entry = run_arm(table[name])
        entries.append(entry)
        if entry["exit_code"] != 0:
            failed = True
            break

    _step_summary(entries)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
