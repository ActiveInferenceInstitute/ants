# GNN conformance

`gnn conformance (pinned)` is defined in `.github/workflows/ci.yml` under the
job key `gnn-conformance` and reads `gnn/upstream.json`, a
`gnn-importer-pin/v1` record pinning
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.1.0`
(`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`).

The job calls the `gnn` arm of `scripts/gate.py`, which reuses an explicit
`GNN_ROOT` or a sibling checkout carrying the pinned revision. Otherwise, the
gate provisions the checkout in `.gate-cache/gnn`, installs `numpy` and
`defusedxml` into `.gate-cache/gnn-venv`, and extracts `src/gnn` at the pinned
commit into `.gate-cache/gnn-src`. From that environment the arm runs
`python -m gnn.importers check --repo .` — the reader shipped in the pinned
revision, which reads this pin and validates the specification with the pinned
parser. The arm then runs `scripts/validate_gnn_spec.py` and
`tests/test_gnn_conformance.py`: the script parses `gnn/ant_colony_foraging.gnn.md`
with the pinned extractor and checks the extracted dimensions plus the A, B, C,
D and E matrices against `config.py` and `ants.py`, and the test asserts the
required GNN sections and the dimensions each one declares. It does not scan the
rest of the repository for `*.gnn.md`; only that one specification is in scope.
