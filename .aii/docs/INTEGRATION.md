# InstituteOS integration — ants

## Identity

| Field | Value |
| --- | --- |
| Repository | `ActiveInferenceInstitute/ants` |
| Affiliation | `institute` |
| Category | `research-software` |
| Status | `active` |
| Maturity | `wip` |
| Steward | Active Inference Institute |
| Default branch | `main` |
| Current release | — |
| License | `MIT` |
| Citation | Friedman DA, Tschantz A, Ramstead MJD, Friston K, Constant A (2021). Active Inferants: An Active Inference Framework for Ant Colony Behavior. Front. Behav. Neurosci. 15:647732. doi:10.3389/fnbeh.2021.647732 |

## Federation

| Setting | Value |
| --- | --- |
| Dashboard mode | `repos` |
| Analytics | `true` |
| Dashboard | `true` |
| Sync policy | `pull` |
| Registries | — |
| Tags | ants, inferants, basis, simulation, python |

## Ecosystem relations

| Repository | Relation | Note |
| --- | --- | --- |
| `ActiveInferenceInstitute/InstituteOS` | `referenced-by` | Federated via the InstituteOS .aii manifest. |
| `ActiveInferenceInstitute/Active_Inference_Ontology` | `references` | Uses Active Inference Ontology terms. |
| `ActiveInferenceInstitute/Generalized_Notation_Notation` | `references` | Uses Generalized Notation Notation (GNN) for model specifications. |

## Key artifacts

| Path | Kind | Description |
| --- | --- | --- |
| `README.md` | `doc` | Repository overview and quick start. |
| `docs/README.md` | `doc` | Documentation folder guide and index. |
| `docs/running.md` | `doc` | Installation, commands, outputs, and runtime notes. |
| `docs/model.md` | `doc` | Model and environment overview with configuration reference. |
| `CONTRIBUTING.md` | `doc` | Contribution guidance. |
| `CITATION.cff` | `doc` | Citation metadata for the software and companion paper. |
| `LICENSE` | `doc` | License (MIT). |
| `AGENTS.md` | `doc` | Agent guidance. |
| `gnn` | `doc` | GNN model specification and pinned upstream revision. |
| `pyproject.toml` | `code` | Python package configuration. |
| `tests` | `test` | Test suite. |
| `docs` | `doc` | Documentation tree. |

## Portable tasks

| Task | Command | Working directory | Description |
| --- | --- | --- | --- |
| `inventory` | `git ls-files` | `.` | List tracked files. |
| `test` | `uv run pytest tests/ -q` | `.` | Run the test suite. |

## Validation

```bash
python -m aii_platform.aii_sidecar.validate <repo> --completeness
python -m aii_platform.aii_sidecar docs <repo> --overwrite
python -m aii_platform.aii_sidecar.run <repo> --list
```

The sidecar is valid when `validate` prints `OK` and reports no missing artifact,
manifest, link, or declared-doc path. Completeness is a curation target, not a
runtime requirement.

## Data boundary

This sidecar carries metadata only. It does not grant execution permission, does not
replace the repository's own documentation, and must not be used to move private
content into a public repository. Task execution is limited to trusted checkouts.
