# GNN conformance

`gnn conformance (pinned)` is defined in `.github/workflows/ci.yml` under the
job key `gnn-conformance` and reads `gnn/upstream.json`, a
`gnn-importer-pin/v1` record pinning
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).

The job calls the `gnn` arm of `scripts/gate.py`, which reuses an explicit
`GNN_ROOT` or a sibling checkout carrying the pinned revision. Otherwise, the
gate provisions the checkout in `.gate-cache/gnn` and installs `numpy` and
`defusedxml` into `.gate-cache/gnn-venv`. It then runs
`scripts/validate_gnn_spec.py` and `tests/test_gnn_conformance.py`. The script
parses `gnn/ant_colony_foraging.gnn.md` with the pinned extractor and checks
the extracted dimensions plus the A, B, C, D and E matrices against
`config.py` and `ants.py`; the test also asserts the pin record, the required
GNN sections and the dimensions each one declares. It does not scan the rest
of the repository for `*.gnn.md`; only that one specification is in scope.
