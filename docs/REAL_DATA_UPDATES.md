# Real-data updates and version review (v1.9)

## Scope and status

The update workflow recalibrates the current detailed engineering model's aggregate post-connection growth correction and whole-site uncertainty band using `src.statistical.confidence_study`. It does **not** retrain a new 20-input ML estimator, rebuild synthetic data, replace the frozen reference model, or automatically change live estimates/finance. No genuine operator data or real-data release is bundled. Candidate metrics are not authenticated field validation.

The Evidence page offers an **exploratory in-memory check** and downloadable diagnostics. It cannot approve or deploy a release. Repeatedly exploring the same test outcomes invalidates their independence; do not later present those sites as untouched tests.

## 1. Agree the protocol before outcomes are examined

Obtain permissioned, anonymised monthly customer-side kWh and dated pre-connection inputs. Use the existing monthly data contract and confidence/growth study protocol. Select whole-site fit, calibration and test groups; keep customers/months from one site together. Default horizon is the complete first 24 months; a 36-month claim requires 36 months for all sites. No imputation or synthetic fallback.

Fill `release_spec.json` from the update starter ZIP: release metadata, study plan and all policy thresholds. Version IDs are unique, 3–60 letters/digits/underscores/hyphens. `prepared_by` is an anonymous role ID, not a person's name or authentication. `data_kind` is `operator_metered` only for genuine data; software test fixtures use `invented_test_fixture` and can never be approved.

All quality thresholds start blank deliberately. A reviewer must set them for the declared population/use before outcomes are seen: WAPE, absolute bias, mean interval width, minimum test-site counts, site-path coverage (at least the study target), allowable regression against the engineering baseline/prior cohort, and input/country-mix change limits. No universal lender tolerance is implied. Null/undefined error metrics fail closed. Overall, country and early/late service-age performance are checked; country transfers without matching fitting/calibration evidence fail the release gates.

## 2. Freeze, then evaluate

Use the app's Python environment, from the GridSight directory. Paths below are placeholders for your approved private files; keep them out of synced `sources/`, version control and public exports.

```text
.venv/bin/python scripts/update_real_data.py prepare --registry /absolute/private/gridsight-registry --spec /absolute/private/release_spec.json
.venv/bin/python scripts/update_real_data.py update --registry /absolute/private/gridsight-registry --request /absolute/private/update_request.json
```

The parent of the registry must already exist. The tool creates only an explicit owner-only (0700) registry; it refuses broad roots, symlinks, protected source/model directories and nonempty unrelated directories. It never overwrites prior events. The update request contains exactly `manifest`, `csv` (CSV text), `plan`, `release`, `policy`. Its last three objects must match the prepared specification. The UI's starter supplies an empty request shell as well as the specification.

Preparation freezes release metadata, protocol, thresholds, code/runtime hashes and site assignments before evaluation. Updates retain dataset, manifest, CSV, plan, policy and code hashes, coefficients, interval calibration, aggregate diagnostics and package versions. Keep the exact authorised input snapshot in the operator's secure data store to reproduce the run; the registry intentionally does not retain raw meter rows or the source manifest.

Each prepared version permits one evaluation attempt. Failed studies are recorded; do not change gates and rerun the same test. Sites used in any earlier prepared split cannot become fresh test sites in this registry. Renamed sites, external prior use or a different registry cannot be detected: governance must maintain stable site IDs and a cross-project exclusion register. Local timestamps/attestations do not prove that outcomes were unseen.

## 3. Review, approve and select locally

```text
.venv/bin/python scripts/update_real_data.py status --registry /absolute/private/gridsight-registry
.venv/bin/python scripts/update_real_data.py review --registry /absolute/private/gridsight-registry --version release-001 --reviewer review-role --decision approve --reason "Reviewed permission, cohort and declared quality gates"
.venv/bin/python scripts/update_real_data.py promote --registry /absolute/private/gridsight-registry --version release-001 --actor release-role --reason "Approved local candidate for subsequent integration review"
```

Review and selection are separate explicit steps. The reviewer role must differ from the preparer; this is not identity verification or two-factor access control. A failed/unfrozen/fixture candidate cannot be approved. Code/runtime and baseline changes block promotion. File permissions, an append-only hash chain and integrity checking detect common accidental changes; the file owner can rewrite the entire registry, so this is not tamper-proof or signed evidence.

**Promotion selects a candidate in the registry only; it does not deploy to the dashboard.** Deployment of a calibrated model needs a separately reviewed integration and population/horizon restrictions. Avoid silently mixing calibration-study outputs into financial decisions.

To return to a previously selected and approved local version:

```text
.venv/bin/python scripts/update_real_data.py rollback --registry /absolute/private/gridsight-registry --version release-001 --actor release-role --reason "Investigation of a later cohort performance issue"
```

Rollback is audited and does not overwrite files or reverse running code. Exit code 0 is success; 2 means invalid/blocked operation; 3 means an update was recorded but is not review-eligible.

## 4. Check performance after each update

Each candidate reports original-versus-recalibrated errors, exact site-coverage uncertainty, interval widths and breakdowns by country and service age. Compare new untouched cohorts to the previously selected candidate's cohort. Report differences in country mix and input means; a zero-to-nonzero feature makes the relative-shift metric undefined and blocks the gate rather than hiding drift. Cohort differences are descriptive, not proof that a model improved. Investigate failed gates and sampling shifts; never relax thresholds to obtain a pass.

Recommended manual cadence (not a created scheduler): check data quality, missing months, outages and source permissions monthly; consider a new version quarterly only when enough newly eligible histories exist. For first-two-year studies, recently connected sites cannot be validated until complete histories mature. Revisit local quotes/FX and business surveys when prices or operations change. Review later observed demand, cash collections and service outcomes separately; model errors do not validate financial assumptions.

## Privacy, retention and limits

The browser check holds data in process memory only and never writes a registry. Downloaded diagnostics omit raw monthly observations and per-site results but small-cohort aggregates and hashed IDs can remain sensitive; review disclosure. Registry files are private local artifacts, not a secure multi-user service. Use your organisation's approved encrypted storage, backups, role controls and retention policy for real data. This prototype does not supply authentication, consent management, automated ingestion, production monitoring or unattended retraining.

Tests use clearly invented fixtures in temporary test directories. Passing those tests verifies mechanics, not field accuracy or proven capital savings.
