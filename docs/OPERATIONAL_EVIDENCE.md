# Real-data hourly model evidence — v1.11

The user requested adding the completed dataset/model comparison to GridSight
and explicitly approved publication after tests. The existing monthly planning
calculation, synthetic reference model, growth scenarios, green/light interface,
eight EAC selectors, two roles and public-upload guards are preserved.

## Included

Evidence now displays the completed KIT hourly experiment: 1,540 qualified
examples (1,013 train, 267 validation, 260 test), five ML families and three
baselines fitted separately per site. There were 66 candidate ML fits.

| Site | Validation-selected approach | Test hours | MAE kW | WAPE |
|---|---|---:|---:|---:|
| Rwanda ECOS | Ridge | 64 | 0.039517 | 1.2457% |
| Congo Idjwi | Previous-hour persistence | 86 | 0.199835 | 6.6747% |
| Haiti Beaumont | Extra Trees | 110 | 0.040078 | 28.3128% |

The section includes all 24 site/model test metrics, the last eight scored test
hours per selected model, previous-hour input/actual/predicted power in separate
columns, the feature dictionary and methodological/source limitations. The
unchanged preparation snapshots remain a historical stage record, not an assertion
that the subsequent model comparison is still pending.

The standalone download and existing analysis/deliverable ZIPs include all 1,540
hourly feature rows, all 4,216 validation/test prediction rows, 48 score records,
split definitions, selected results, protocol, source notes and checksum inventory.
No raw high-frequency telemetry, confidential data or executable model/pickle is
added. The original full training pack retains the fitting code, matrices and
model artifacts. No app dependency or model artifact changed.

## Meaning and limits

The target is next-hour mean delivered active power (kW), not billing energy,
unconstrained demand or capacity. Known calendar and historical-power predictors
are not the original 20 pre-construction household/equipment inputs. Models use
training-only preprocessing and fits; settings/choices were selected with validation
MAE before scoring test hours. Earlier observed test hours may supply later lags.
No refitting or test-based selection is performed by the app.

These are later-hour tests at already-observed sites, not held-out-site validation.
Campaigns are short, correlated and previously inspected. Equipment faults and
sampling-quality exclusions remain important. Rwanda ECOS is not Bugesera; Haiti
is outside East Africa. The 15-sector Bugesera table stays unlabelled and is never
joined to KIT target values. No empirical monthly demand, growth model or calibrated
uncertainty is claimed. WAPE is error, not 100 minus accuracy.

The earlier whole-site calendar-only transfer benchmark is retained separately.
Its errors cannot be compared directly with these easier same-site lag models
as evidence of improved transfer. The app's monthly validation deliverable remains
pending; its fields and forecast/finance values are unaffected by this evidence.

## Reproduction and serving

`scripts/import_operational_evidence.py --source <original-training-pack>` checks
the original inventory before copying 13 unmodified allowlisted snapshots into
`data/operational/`. Source originals are never modified. The app verifies these
hashes and validates schemas, counts, site/model identity, validation choices,
protocol/selection linkage and preview alignment. Missing/changed/invalid data
returns unavailable, not plausible substitute scores. A dedicated unavailable
download returns HTTP 503. Hashes detect drift, not cryptographic authenticity.

`GET /api/operational-models` serves the summary and previews.
`GET /api/operational-models/download` serves the public CSV/provenance ZIP.
Neither endpoint performs model inference, accepts new measurements or retrains.
The data is also attached under `prepared_evidence.operational_models` in analysis
JSON and reports; downloads use a separate `operational_models/` folder.

Attribution: Luh et al., KIT / RADAR4KIT,
https://doi.org/10.35097/1305, CC BY 4.0. Accessed 1 November 2026.
Features/results are GridSight transformations, not author-endorsed products.
See TEST_REPORT.md for executed checks and publication status.
