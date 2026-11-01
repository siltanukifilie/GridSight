# Prepared public evidence integration — 1 November 2026

**Follow-up:** v1.11 also integrates the completed hourly training experiment.
See OPERATIONAL_EVIDENCE.md. The preparation-only and not-published statements
below describe the earlier integration stage; the original preparation snapshots
remain unchanged. Current publication/verification status is in TEST_REPORT.md.

## Release scope

Implemented locally in the existing GridSight application. No model was trained,
no source dataset was rebuilt, and no commit, push or Render redeployment was
performed for this integration. The hosted application remains on its prior
release until a separate publication review. Green/light branding, the two
audience workspaces, eight-country selection, original calculations and public
meter-upload guards are preserved.

## What the app now exposes

- Locations and the selected Project/Community show Bugesera **whole-sector**
  context. Matching uses the Rwanda + Bugesera district + sector hierarchy, not
  a cell name alone. GeoNames' `Bugesera District` and `Bugesera` are explicit
  district aliases. User-entered names are labelled geographically unverified.
- All 15 sectors have the original 58 fields, 12 engineered features and label
  status. The 71-field inspection retains units, dates, evidence type, missingness,
  derivation and source limitations. Source totals never become project inputs.
- Evidence separates census/sensor observations, map proxies, derived features,
  assumptions, synthetic demos and unavailable inputs. KIT benchmark results and
  preparation status are distinct from the five current-model deliverables.
- Existing project JSON, CSV/ZIP and both HTML reports include evidence scope and
  provenance. `prepared_evidence/selected_sector_features.csv` is long-format
  with units/date/source per value; it is header-only when no sector matches.
- `/api/prepared-evidence` supplies the inspectable summary;
  `/api/prepared-evidence/download` supplies the compact public summary pack.
  Original training matrices, raw telemetry, survey microdata, noncommercial
  Tanzania data and restricted layers are not bundled.

## Scientific boundaries

Bugesera rows have **no matched monthly kWh or measured peak kW labels**. They
cannot train or validate a pre-construction estimator. Census counts are from
2022; boundaries represent 2012; building detections are the 2023 release. OSM
coverage is incomplete. GridFinder is historical, not current utility evidence.
Nightlights are indirect GEP inputs with exact VIIRS year unresolved. Estimates
of phone/TV-owning households are not device counts. Not-grid-connected does not
mean unelectrified. Missing remains JSON null / blank CSV, never a fabricated zero.

The KIT benchmark targets hourly arithmetic sample-mean **delivered active power
in kW**, not monthly billing kWh, annual demand growth or unconstrained demand.
It uses Rwanda ECOS (not Bugesera), DR Congo Idjwi and Haiti Beaumont (outside
East Africa). Of 2,035 calendar hours, 1,620 pass the fixed sampling-quality rules.
Both fixed equal-site baselines are retained. Local-hour MAE is 1.243 kW Rwanda,
2.047 kW Congo and 3.192 kW Haiti. WAPE is 40.3%, 58.3% and 2503.9%, respectively.
These are poor-transfer exploratory results, not an accuracy percentage or
validation of GridSight's current monthly model. Campaigns last about 18–36 days,
include faults/gaps, and are not a blinded or chronological deployment backtest.

Preparation produced 1,540 eligible operational examples, with separate per-site
chronological splits: RW 280/64/64; CD 215/90/86; HT 518/113/110 train/validation/test.
There are 20 candidate calendar/past-power predictors, not the original 20
pre-construction inputs. Rwanda/Haiti retain 20 plus 15 missingness flags; Congo
retains 16 plus 11, dropping four all-missing 24-hour rolling features. Medians and
scalers were fit to training rows only. No target imputation, new model training,
pooled backtest, calibrated intervals or multi-year growth observations occurred.

Monthly demand, low/expected/high and the 36-month curve remain the existing
engineering/scenario workflow. Its real-world validation still needs permissioned,
matched pre-connection inputs and complete longitudinal monthly consumption.

## Implementation and integrity

`src/prepared_evidence.py` loads allowlisted, SHA-256-pinned local snapshots after
the existing forecast/finance computation. It does not access external services,
change input values or read a model registry. Missing/changed source sections
return explicit unavailable states, without substituting example scores. This
detects accidental snapshot drift; it is not a signed authenticity guarantee.

`data/prepared/inventory.json` records original paths relative to the supplied
packs, original hashes, bundled hashes and transformations. Originals in the
project's `outputs/01a190dc-cde9-7621-b62c-9d51c038cd44/` remain read-only. The source
manifest is restricted to nine relevant source records; other copied summaries
only normalise line endings/final newline. Metadata paths refer to upstream packs.

Attribution: Luh et al., KIT / RADAR4KIT,
https://doi.org/10.35097/1305, CC BY 4.0; no author endorsement. Bugesera uses mixed
rights, including ODbL for OSM and limited factual NISR extracts without a confirmed
general reuse licence. Preserve the bundled README and source manifest; review
rights before wider redistribution. No blanket open licence is asserted.

## Verification

Backend tests cover all 15 sector joins, a real GeoNames sector/cell hierarchy,
wrong-country/district/nonmatches, null versus zero, observed kW versus missing
kWh labels, unchanged forecasts/finance for both roles, scenario-growth labels,
JSON/CSV/ZIP/HTML provenance, public upload guards and absent/tampered snapshots.
Interface tests cover both roles, escaped content, missing states, benchmark
units/errors, preparation status and existing page/report wiring. See the latest
entry in `TEST_REPORT.md` for actual test and browser results.

## Changed-file inventory

Paths below are relative to the existing repository; there is no replacement app.

- Backend: `app.py`, `src/analysis.py`, `src/prepared_evidence.py` (new),
  `src/rwanda_data.py`, `src/deliverables.py`.
- Interface: `static/prepared-evidence.js` (new), `static/app.js`,
  `static/context.js`, `static/workspaces.js`, `static/maintenance.js`,
  `static/statistical.js`. No stylesheet or branding assets changed.
- Reports/templates: `templates/prepared_evidence_sections.html` (new),
  `templates/index.html`, `templates/report.html`,
  `templates/deliverables_report.html`.
- Tests: `tests/test_prepared_evidence.py` and `tests/prepared-evidence.test.cjs`
  (new); `tests/test_api.py`, `tests/test_rwanda_data.py`,
  `tests/statistical.test.cjs` (updated expectations).
- Data: 15 compact snapshots enumerated in `data/prepared/inventory.json`,
  plus that inventory and `data/prepared/README.txt` (17 new files total).
- Documentation: `README.md`, `THIRD_PARTY_NOTICES.md`, `docs/PROGRESS.md`,
  `docs/DECISIONS.md`, `docs/MODEL_CARD.md`, `docs/MONTHLY_VALIDATION.md`,
  `docs/REAL_DATA_UPDATES.md`, `docs/TEST_REPORT.md`, and this new document.

Final review: 613 Python checks and all ten JavaScript test files pass. Both
desktop role views and the generated feasibility report were inspected. Native
browser download acceptance remains pending because Chrome blocked the download;
API/ZIP integrity checks passed. No live publication or model training occurred.
