# Data and review utilities

The app runs from committed snapshots. **None of these collection, training or
rebuild commands is needed for judge review or normal deployment.** Rebuilds can
overwrite results; preserve the current release before a deliberate refresh.

Run commands from the repository root using the project's Python environment.

| Utility | Purpose | Requirements / side effects |
| --- | --- | --- |
| `scripts/build_bugesera_site_features.py` | Prepare the canonical 15-sector table | Pinned Bugesera snapshot; writes CSV and metadata in `data/processed/` |
| `scripts/build_bugesera_site_ranking.py` | Reproduce sector ranking | Canonical table; writes ranking; no measured labels |
| `scripts/import_operational_evidence.py --source /path/to/original-pack` | Import reviewed KIT results | Separate original pack and inventory; checks and copies allowed snapshots; no training |
| `scripts/build_transfer_uncertainty.py --source /path/to/qualified-panels` | Rebuild operational transfer study | Separate qualified Parquet inputs and DuckDB 2.0.0 (not a web dependency); writes study artifacts |
| `scripts/import_locations.py` | Refresh GeoNames extracts | Network; replaces dated country snapshots |
| `scripts/collect_rwanda.py` | Refresh selected geographic sources | Network, potentially large downloads; rights differ by source |
| `scripts/update_real_data.py --help` | Private evaluation/review workflow | Permissioned data and private registry, not a public upload service |
| `scripts/export_planning_review.py` | Generate fictional planning review | Writes ignored `reports/planning_review/` |
| `scripts/export_screening_review.py` | Generate fictional screening/operator review | Writes ignored `reports/screening_review/` |

Root utilities remain for compatibility:

- `build.py` regenerates **synthetic** data and trains the legacy reference model.
- `build_profiles.py` regenerates simulated RAMP hourly shapes.
- `export_examples.py` writes fictional reports to ignored `reports/examples/`.
  Frozen regression fixtures are separate in `tests/fixtures/`.
- `export_data_bundle.py` exports the explicitly labelled **historical v1.5**
  bundle. For current data use the app downloads or [catalogue](../data/README.md).

Optional synthetic/RAMP rebuild dependencies are in `requirements.txt`, with
the historical environment in `requirements-lock.txt`. The deployed app uses
`requirements-web.txt`. The complete original hourly fitting pipeline and raw
campaigns are not bundled: inspection and verification of results are supported,
but independently rerunning every upstream experiment requires its source pack.

Never fabricate missing demand labels or refresh a checksum without reviewing
the underlying data change and its source rights.
