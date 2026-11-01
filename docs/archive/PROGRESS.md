# GridSight progress tracker

Historical development log. Deployment and verification statements below are
dated milestones, not current status. See [verification](../TEST_REPORT.md).

## v1.12 publication requested — 1 November 2026

The user requested running the updated app on the existing Render service.
This supersedes the local-only release decision below. Publication includes
Bugesera ranking, operator pilot, rubric checklist, measured operational-error
evidence and growth/productive-use/affordability scenarios. Keep public meter
uploads disabled and the existing free service settings unchanged. Exclude local
review bundles, private layers and credentials. Deployment and live checks must
be verified separately from the prior local tests.

## Latest local changes — Bugesera ranking and operator pilot, 1 November 2026

1. Connected the existing 15-sector ranking to the initial location finder,
   Locations, an Overview shortcut, analysis JSON and both export packages.
   Source-checked score reproduction fails closed on stale or missing files.
   Cell-selection shortcuts preserve the active project's demand/finance inputs.
2. Preserved the existing ranking, explicitly disclosing shorter historical-grid
   distance as a positive score and neutral equipment assumptions. Missing mills
   and generators remain unavailable counts, not observed zeros. Sector totals
   are not service-area customers and scores are not demand or investment advice.
3. Added an operator-reviewable pilot proposal, draft request (not sent), approval
   gates, blank handover and compatible monthly templates. Evidence includes a
   dedicated download and printable proposal; ordinary exports include the pack.
4. Added the Brief 03 five-criterion checklist with exact rubric weights,
   available evidence and remaining gaps. No judge score, partner approval,
   Rwanda accuracy or realized savings are fabricated.
5. Verification: 653 Python tests pass, all 12 JavaScript test files pass, changed
   JavaScript parses and diff whitespace passes. Browser visual acceptance remains
   open due to the previously observed browser security-check service failure.

Offline artifacts: `reports/screening_review/`. The review uses explicitly
synthetic demand inputs and separate real public-sector context. These changes
are local only: no push, hosted deployment or operator outreach was performed.
Next action: review the new screens in an authorized browser, then decide on
publication. The main data gate remains operator-approved pre-connection inputs
paired with independent-site monthly observations.

## v1.11 release candidate — real hourly data and model comparisons

The user approved publication after tests on 1 November 2026. This entry
supersedes the earlier preparation-only/local-review status below.

- Added 1,540 measured hourly feature rows, 4,216 saved prediction rows and all
  eight approaches' results for each of three separately fitted sites.
- Evidence and reports show validation-selected Ridge (Rwanda ECOS), persistence
  (Congo Idjwi) and Extra Trees (Haiti Beaumont), with errors and scope limitations.
- Dedicated public data/results download plus existing project ZIP integration.
  No executable model deployment or change to monthly calculations/growth scenarios.
- Local verification: 625 Python checks and all ten JavaScript test files pass.
  Dependencies, JavaScript syntax, source hashes and unchanged frozen-model inputs
  checked. Current browser preview is blocked by a security-check service failure;
  no visual acceptance or bypass is claimed. See TEST_REPORT.md.
- Publication is explicitly authorized. GitHub/Render release verification follows
  the local checks; this entry alone is not proof of a completed hosted deployment.

## Latest local integration — 1 November 2026

Prepared Bugesera context and KIT measured-power evidence are integrated locally.
**Not pushed or deployed; the live Render demo remains unchanged.** This current
entry supersedes older deployment/status wording in the historical log below.

- Completed: inspectable 15-sector context, exact district/sector joins, null
  preservation, source/date/unit/scope labels and separation from service inputs.
- Completed: separate published KIT three-site power benchmark (both baselines,
  actual errors, exclusions and faults), hourly preparation counts and original
  20-input coverage. No new model trained; no Bugesera/KIT label joins.
- Completed: integration into Locations, Community/Project, Evidence and
  JSON/CSV/ZIP/HTML exports. Public meter uploads remain blocked.
- Pending: matched monthly kWh labels for the current pre-construction model,
  real first-years histories, calibrated confidence coverage and release review.
- Source originals are unchanged; only reviewed compact summaries are bundled.
  See PREPARED_EVIDENCE.md and the latest TEST_REPORT.md entry for actual checks.

The public Render demo exists. The local real-data update registry still does
not deploy models. Historical P05 completion below refers only to the synthetic
reference model, never the prepared operational features or current 20-input model.

Last updated: 1 November 2026.

Current stage: v1.10 deliverables follow-up adds a prominent five-item Evidence review and a single offline deliverables ZIP. **582 Python + 153 interface-logic checks pass (735 total).** Desktop checks cover both roles, the validation link, an actual ZIP download and exported HTML/growth-chart layout. Genuine operator histories remain unavailable; no authentic validation, calibrated real-data coverage/growth or real-data release is claimed. Forecast calculations and frozen model/data remain unchanged.

The Python application, synthetic dataset, trained model, RAMP profiles, analysis exports, and documentation exist. Published to [GitHub](https://github.com/siltanukifilie/GridSight) and the full planning app runs on [Render Free](https://gridsight-0al3.onrender.com/). Demo recording, pitch deck, one-page summary and final disclosure remain deferred. The team has three members.

Live release verified on 1 November 2026: health, both roles' detailed forecasts,
36-month growth, 27-file deliverables ZIP integrity, public source status and
all four public meter-upload guards passed. GitHub checks passed for app commit
`b47a54f`; the first CI run exposed an unsupported newest runner image, fixed
by pinning Ubuntu 24.04. No model or original synthetic dataset was rebuilt.

## Public release — 1 November 2026

- Added a free Render Blueprint, pinned web runtime, production server, health
  check and GitHub test workflow. No synthetic rebuild during deployment.
- Public mode preserves planning and reports but blocks four meter-data
  processing endpoints; operator uploads need a secure deployment.
- Excluded local exports, private-data folders and the government layer whose
  redistribution terms are unspecified. Missing-layer behavior is tested.
- Added a bounded-memory geographic lookup using the same spherical-distance
  calculation. A representative query retained 173 detections while peak
  process memory dropped from about 498 MiB to 238 MiB.
- 593 Python tests and all nine interface suites pass both in the existing
  environment and a clean publication checkout with a fresh web-only runtime
  and no government extract. Dependency and production-server configuration
  checks pass; the production preview health endpoint returns OK.
  Live checks are recorded above. See DEPLOYMENT.md.

## Step checklist — current user sequence

P01–P12 follow the user's latest product workflow. Historical implementation-stage numbers in the evidence table below are retained for continuity; the current plan supersedes them.

- [x] P01 — Select geographic scope: eight EAC countries, superseding the Rwanda-only active release. Country/district/sector/cell and visible local-equivalent coverage gaps; no map. Three fictional Rwanda examples remain separate demo cases.
- [ ] P02 — Collect Data: public buildings, mapped facilities, historical Bugesera electricity and geography collected. Remaining pack layers, calibrated cost/survey priors and operator consumption remain open. See RWANDA_DATA_PIPELINE.md.
- [x] P03 — Clean & Prepare Data: synthetic feature/unit preparation, bounds, completeness, unique site-months and partition checks pass. Public responses are validated and normalized without inventing missing values; real consumption cleaning depends on a supplied dataset.
- [x] P04 — Build Baseline: transparent demand calculation and RAMP profiles.
- [x] P05 — Train ML Model: trained artifact and baseline comparison.
- [ ] P06 — Validate Model: software/synthetic tests pass; current detailed-model monthly comparison is implemented, but genuine independent metered-site validation remains open.
- [ ] P07 — Calibrated uncertainty: scenario bands and input simulations work; site-block conformal calibration/testing is implemented. Genuine measured calibration and observed coverage remain pending.
- [ ] P08 — Credible growth: assumption-based 36 months and separate observed-history fitting/testing work. Genuine first-two-year histories and driver-specific customer/appliance/business panels remain missing.
- [x] P09 — Add Explainability: baseline contributions, local sensitivities and assumptions.
- [x] P10 — Add Financial Analysis: downside/upside cash, debt coverage, break-even and supply limits.
- [x] P11 — Build Dashboard: primary developer and secondary investor/lender workspaces, role-specific exports.
- [ ] P12 — Test Prototype: 712 automated checks pass; focused desktop/mobile and chart-keyboard checks pass. Full file-workflow, assistive-technology and release-wide visual regression checks remain open.
- [ ] D01 — Feature Freeze: awaits P12 browser checks.
- [ ] D02 — Polish Product: responsive styles implemented; final visual verification pending.
- [ ] D03 — Record Demo: deferred by user.
- [ ] D04 — Prepare Pitch Deck: deferred.
- [ ] D05 — Prepare One-Page Summary: deferred.
- [ ] D06 — Prepare Disclosure: final document deferred; source/dependency records maintained.
- [ ] D07 — Check Final Package: deferred.

## Current step — dashboard redesign (v1.10)

Deliverables follow-up:

1. Added direct Overview → Five deliverables navigation; Evidence starts with the five requirements, status, scope and next action.
2. Added `/api/deliverables-pack`: offline `START_HERE.html`, four-period scenario range CSV, 36-month growth CSV, lender text, safe-sharing proposal, blank operator handover and blank validation templates/protocols, alongside the original reproducible analysis/finance files.
3. Used final backend scenario outputs; no second forecast implementation. Service age, uncalibrated ranges, missing actuals and separate batch studies stay explicit. Current input fingerprints do not certify evidence.
4. Added 16 Python and 7 interface tests. All 735 checks pass; model and original synthetic dataset hashes are unchanged. Browser download was independently confirmed on disk and passed ZIP integrity; the browser download-event observer timed out, so its event alone was not treated as success.
5. Preserved the user's active Mubuga project tab and tested in a separate synthetic preview. No hosted publication, operator upload, submission, demo video or deck.

Next action: obtain approved, paired pre-connection inputs and measured monthly histories, run the existing independent holdout/confidence workflows, and review evidence before closing the validation requirement. The download includes the exact blank data contracts; no substitute measurements were generated.

Colour-only follow-up: the user preferred the earlier green/light palette. Restored the original cream background, white cards, green sidebar/actions and green chart palette, while retaining the new interactive layout and filters. No calculation or dataset changes.

1. Implemented navy/coral visual system across both roles, location selection, inputs, feasibility and evidence. Power BI–style interaction inside the existing app, not Microsoft Power BI integration.
2. Implemented linked scenario/year/energy-period cards and an interactive 36-month curve with monthly financial/supply drill-down. Display filters do not save inputs, refit the model or change exports.
3. Kept assumptions and unvalidated status visible; verified calendar/service-age labels, scenarios versus confidence, and monthly versus annual units. Existing forecasts and frozen data are unchanged.
4. Added 20 analytics checks and 2 full-workspace integration checks (566 Python + 146 interface checks = 712). Desktop role switching, click/keyboard/slider interaction, narrow-screen wrapping and dirty-input protection tested in Chrome.
5. Existing user project tab was not reloaded or overwritten; a separate local preview uses an explicitly synthetic demo. No cloud deployment or deferred pitch/demo artifacts.

## Historical step — financial credibility and maintainability (v1.9)

1. Financial source register: AMDA Eastern/Southern regional cost averages, Rwanda CLASP field-study context, Kenya milling methodology and REG utility-tariff applicability caution. None is auto-applied as local data.
2. Exact-project evidence attachments: units, values, source reference/date, sample size, permission/privacy confirmations, age flag and changed-input detachment. Save/restore and report/export integration.
3. User-sourced FX/connection-count comparison keeps unknown CAPEX unknown and avoids adding OPEX twice. No-uptake/half-use/full-use productive alternatives retain support costs.
4. Added a prospective impact-evaluation protocol; measured savings stay null. Priority 6's empirical local-survey and demonstrated-impact gaps remain open.
5. Versioned update specification, frozen splits/gates/code, real-history recalibration, country/age/performance/drift checks and redacted candidate artifacts. No synthetic fallback.
6. Explicit private CLI registry: immutable events, integrity checking, fresh-test-ID guards, review, local selection and rollback. Browser checks are exploratory and never write or promote a registry.
7. Manual monthly review/quarterly recalibration guidance, no scheduler created. Registry promotion does not deploy into the live dashboard. Priority 7's workflow is implemented/tested; first genuine run and production deployment/monitoring remain pending.
8. See FINANCIAL_EVIDENCE.md, REAL_DATA_UPDATES.md and TEST_REPORT.md. Deferred delivery materials are unchanged.

## Historical step — confidence and growth (v1.8)

1. Feasibility → How uncertain are the inputs?: coherent simulated paths, editable input widths and separate download. Uncalibrated status is explicit.
2. Evidence → Calibrate confidence & growth: fresh whole-site fit, calibration and test partitions, complete early histories and frozen settings.
3. Fit only aggregate growth correction on fitting sites; preserve assumptions as the benchmark and permit real declines.
4. Calibrate input bands with worst-month residuals per site; reject too few sites rather than reducing the target.
5. Report untouched test coverage/width/error, exact coverage confidence interval, country transfer cautions, early stages and annual growth.
6. Preserve metadata, hashes, seed, fitted coefficients and score ranks in downloads. No automatic selected-project or financial changes.
7. 581 automated checks pass. Browser inventory still cannot initialize; visual tests not passed.
8. **Priorities 2 and 3 are software-ready, not empirically complete.** Need eligible real histories; aggregate energy alone cannot identify each adoption mechanism. See CONFIDENCE_AND_GROWTH.md.

## Historical step — metered validation (v1.7)

1. Public-source research: Kenya/Tanzania/Uganda candidates reviewed; none yet supplies an eligible paired input/outcome bundle. No agreement, outreach, raw-data import or fake accuracy result.
2. Exact current detailed calculation: implemented, without training/tuning or older-model substitution.
3. Whole-site holdout checks, full dated inputs and provenance: implemented; declarations still need independent review.
4. Monthly calendar alignment, MAE/RMSE/WAPE/bias, country/site/year groups and exclusions: implemented.
5. Growth: complete consecutive service years required; full three-year coverage reported separately.
6. Evidence dashboard: blank starter pack, expected/actual chart and table, source register, JSON/CSV results. No server persistence.
7. Verification: 507 automated checks; live version 1.7. Browser security-policy verification prevented visual testing; no bypass attempted.
8. **Priority 1 is partially addressed, not complete.** Remaining: obtain genuine paired metered records and independent evidence review. See MONTHLY_VALIDATION.md.

## Historical step — twenty-feature interface (v1.6)

- [x] S01: eight-country administrative selectors, actual Rwanda cells, manual names for source gaps, no map/device-position UI.
- [x] S02: reference-inspired dark collapsible numeric controls, +/- buttons, fractional ratings/hours, elapsed-month slider.
- [x] S03: all 20 input paths drive engineering energy, growth, revenue or affordability; no false model-retraining claim.
- [x] S04: both roles, day/week/month/year cards, scenarios, 36-month curve, finances, save/restore and reports share applied values.
- [x] S05: 445 automated checks and live local API/report/archive checks pass. Original model/data hashes unchanged.
- [ ] S06: browser visual/keyboard/mobile/print acceptance; browser app-server cannot initialize. Do not mark feature freeze complete.
- [ ] S07: independent metered-site validation, country-specific priors, current grid checks and missing public-data layers.

Next: refresh the local app, select Rwanda → Kirehe → Gahara → Butezi (example administrative flow, not a development recommendation), review inputs, then inspect both roles. Repeat a missing-cell case using names only. No cloud deployment or pitch artifacts were created.

## Historical post-connection growth and five deliverables (v1.5)

New Rwanda projects and explicit demos enable a 36-service-month connection curve. In **Feasibility → Start from connection**, set an optional connection month, initial connection/appliance/non-household fractions and the month adoption reaches its target. The default 35% / 60% / 50% initial fractions and Month 24 maturity are editable design assumptions, not measured Rwanda rates. A one-month ramp means immediate full use. Old saved projects retain the previous calculation until this feature is enabled.

The frozen synthetic-trained estimate is used as an **assumed mature reference**, not an observed mature load. The connection ramp determines Year 1 energy, all four period cards, daily profile, annual projections, monthly-cap cash flow and reports. First-year totals are not normalized back to the reference. Annual expansion applies in addition to adoption; avoid double counting. Calendar labels locate standard 365/12-day energy months, not exact calendar billing totals.

**Evidence** now contains all five requested deliverables: Rwanda location estimate/range; first-years curve; held-out meter comparison **pending authentic operator data**; plain-language lender explanation; and a downloadable safe meter-sharing proposal. The annual CSV tool compares the frozen reference model; it does **not** validate the connection ramp. A monthly independent holdout study is still needed. Proposed hosted security/transfer controls are not implemented.

Both roles share the same results. Developers edit connection assumptions; lenders review them. Either Feasibility update button applies both connection and financial-planning forms, avoiding lost edits. Saved scenarios, report, print view and ZIP retain the applied connection inputs.

## Completed work and evidence

| Date | Step | Work completed | Evidence |
|---|---|---|---|
| 30 October 2026 | 01 | Retrieved prior decisions and reviewed kickoff rules and deliverable screenshots. | Source descriptions in the implementation plan. |
| 30 October 2026 | 01 | Defined synthetic data design, product scope, modeling approach, checks, and delivery stages. | `IMPLEMENTATION_PLAN.md` and `DECISIONS.md`. |
| 30 October 2026 | 01 | Created a persistent continuation process. | This tracker and the project `README.md`. |
| 30 October 2026 | 02–04 | Built the Python environment, generator, baseline, and seven RAMP sector shapes. | `config/`, `src/domain.py`, `src/synthetic.py`, `build_profiles.py`, `data/`. |
| 30 October 2026 | 05 | Trained gradient boosting and interval models with separate calibration and test sites. | `models/forecast.joblib`, `reports/evaluation.json`, `reports/test_predictions.csv`. |
| 30 October 2026 | 06–09 | Built dashboard, growth, finance, explanation, export and report functionality. | `app.py`, `static/`, `templates/`, `src/analysis.py`, `reports/examples/`. |
| 30 October 2026 | 10 partial (historical) | Original 50 tests passed; JavaScript and launcher syntax passed; no dependency conflicts. | `tests/`, `docs/TEST_REPORT.md`. |
| 30 October 2026 | P10–P12 | Added two audience workspaces, shared-result tests, investor financial-only editing, role-specific exports and missing-evidence checklist. Made downside repayment and faster-demand capacity risk explicit. | `static/workspaces.js`, `src/workspaces.py`, `tests/test_workspaces.py`, `tests/workspaces.test.cjs`. |
| 30 October 2026 | P03 / P12 | Verified prepared synthetic data quality and independent downside/upside financial cases. Final result: 81 Python + 9 logic tests pass; local service restarted and health checked. | `tests/test_engine.py`, `docs/TEST_REPORT.md`. |
| 30 October 2026 | P11–P12 | Added central demand per day/week/month/year to both role overviews, JSON/CSV and printable reports. Refreshed example exports; conversion, profile consistency, unchanged finance and report matching checks pass. Final check: 96 Python + 11 logic tests. | `src/domain.py`, `tests/test_demand_periods.py`, `reports/examples/`. |
| 30 October 2026 | P11–P12 | Simplified both workspaces: shorter headings/navigation, no duplicate hero, concise financial notes and native expandable explanations. Kept units, four time periods, synthetic/risk notices and detailed exports. 96 Python + 13 logic tests pass. | `static/`, `templates/index.html`, `tests/workspaces.test.cjs`. |
| 31 October 2026 | P11–P12 | Added Daily / Weekly / Monthly / Yearly chart tabs to both overviews, with period totals, explicit average-based longer views and keyboard controls. Tests verify conservation, all three demos, zero demand, markup and draft preservation. 97 Python + 27 logic tests pass. | `static/demand-charts.js`, `tests/demand_charts.test.cjs`. |
| 31 October 2026 | P08–P12 | Completed separate demand cases, normalized 36-month growth, productive-use comparisons, over-/under-sizing screens and downloadable feasibility report. Added optional budget/payback/limited NPV calculations, a fifth workspace area, draft guards and exact-input exports. Refreshed all example reports. 150 Python + 38 logic tests pass. | `src/feasibility.py`, `static/feasibility.js`, `templates/feasibility_sections.html`, `tests/test_feasibility.py`, `tests/feasibility.test.cjs`, `FEASIBILITY_METHODS.md`. |

Synthetic test results: MAE 1,294.73 kWh/month; WAPE 10.55%; interval coverage 91% against a nominal 80% target. Baseline MAE 2,236.26 kWh/month. A 25% shifted-outcome stress case yields 22.49% WAPE and 36% coverage. These are simulation results, not real-site validation.

## Exact next action

Open http://127.0.0.1:8050/. In Feasibility, review and run the input-uncertainty simulation. In Evidence, download the confidence/growth starter pack and review its independent fit/calibration/test plan. A 90% whole-path study needs at least 3 fitting, 9 calibration and 2 test sites with complete first-24/36-month histories and pre-connection inputs; these are computational minimums, not proof of representativeness. Do not substitute illustrative defaults for measured evidence. Complete browser acceptance when available.

R02 public-context integration, R09 guided thin-data handling, and R10 eight-country configuration are implemented. R07 actual real-site validation still needs genuine permissioned data; its comparison tool alone does not close the gate. R11 paid customer and R12 pricing remain unconfirmed. No customer was contacted, no payment was taken and no public deployment was made.

31 October live checks: health reports feature v1.2/model v1.0.0; Rwanda Kirehe lookup returned 8 matches and Uganda Jinja 7. World Bank returned population (2025) and electricity access (2024) for both countries. A public-context analysis, standalone HTML attachment and ZIP all returned HTTP 200; location and national context did not alter the forecast. Provider responses may change.

Preserve “Low / expected / high range” and all existing forecast/finance assumptions. The original synthetic training set and model were not regenerated. Example reports were refreshed for the new context/currency schema.

## Open items

| Item | Effect | Planned handling |
|---|---|---|
| Browser tool could not verify admin-enforced policy | Visual and interaction QA not complete. | Resume browser checks when available; do not bypass the policy. |
| Browser selection works but localhost navigation failed its security check | No visual or interaction acceptance in v1.7. | Keep visual, mobile, download-click and print checks pending; no alternate browser-control route. |
| Brief 03 reviewed in prior audit | Remaining requirements recorded; final package still deferred. | Preserve the five deliverables and evidence boundaries in the implementation plan. |
| No eligible paired metered-site dataset | Cannot claim field accuracy or completed real-site validation. | Use the monthly current-model workflow with permissioned observations and pre-connection inputs; do not treat research summaries or test fixtures as observations. |
| Paying developer not confirmed | Target-buyer identification does not establish traction. | R11: await clarification and evidence; distinguish prospect/pilot/payment. |
| Commercial offer and prices untested | A proposed business model is not validated revenue. | R12: define paid deliverable and validate willingness to pay through authorized pilot work. |
| Current submission portal not verified | Final submission fields and latest deadline need checking. | Recheck during delivery; kickoff screenshot says 1 November 2026, 19:00 Kigali. |
| Three-person team; member details and prior work not supplied | Final team slide and disclosure need accurate information. | Gather missing facts during later submission preparation. |
| Recording and hosting route not selected | Video file and share links are future deliverables. | Check capabilities at D03 and destination at D07. |

The two-role local product and automated checks are implemented. The selector is not authentication or authorization; both roles share one scenario. Production accounts and private reviewer scenarios remain outside this local MVP. Browser QA and real-data validation are separate open items; they must not be marked passed based on API tests alone.

## Session closing procedure

Dataset export requested and completed: `exports/gridsight-dataset-v1.0.0.zip` contains the original 500-site and 18,000-monthly-record CSVs, load shapes, assumptions, metadata, data/model cards and evaluation files. ZIP integrity passed; SHA-256 checks confirmed both main CSVs are byte-identical to the application inputs. No data was regenerated or changed. All records remain synthetic.

For each stage, record artifacts created, checks actually performed, and unresolved issues. Update the checklist only when the completion check passes. Set a single exact next action. Record scope changes in `DECISIONS.md`. Never replace measured results with planned or illustrative values.

## Delivery status

| Item | Status |
|---|---|
| Local MVP | Two-role prototype implemented and running locally |
| Automated checks | 264 Python + 71 interface-logic tests passed |
| Browser QA | Pending due to tool access restriction |
| Synthetic evaluation | Complete, recorded and reproducible |
| Real-site validation | No data available |
| Demo video | Deferred by user |
| Pitch PDF | Deferred by user |
| One-page PDF | Deferred by user |
| Disclosure | Requirements recorded; final statement not started |
| Build package | Not started |
| Public links | Not created |
| Submission | Not performed |
## v1.2 completion record

- Added `src/context.py`, `src/public_data.py`, `src/validation.py`, country configuration and a sixth interface area. Kept all changes inside the existing local app; no synced project sources were edited.
- Added source/licence/year/provenance handling, manual and device-coordinate drafts, country-safe amount resets and documented provider limits.
- Added missing-input proposal/review/accept flow with persistent assumed-field warnings. No automatic imputation in the core analysis API.
- Added permission-attested CSV comparison of 12 complete historical months per independent site, model/input hashes, baseline/model metrics and downloadable diagnostics. No retraining, persistent upload storage or external transmission.
- Added explicit proposed commercial offer and unconfirmed customer/pricing status in app/reports.
- Verified 211 Python + 48 interface-logic tests, syntax/dependency checks and read-only live endpoints. Browser/mobile/map permission/download-click/print QA is still open.

## v1.3 completion record — East Africa

- Confirmed RW, UG, KE, TZ, BI, SS, SO and CD. Public GeoNames snapshots contain 101,142 administrative/place records, with attribution, fetch dates and ZIP hashes. Synthetic training inputs are unchanged.
- Built hierarchical browsing, filtered-settlement search, source-backed administrative reference points and manual surveyed-coordinate fallback. Country-specific coverage warnings explicitly acknowledge older/incomplete records; no official current administrative completeness claim.
- Replaced automatic demo analysis with **Find your next mini-grid → add customers → build dashboard**. New sites start with blank counts, explicit reviewed suggestions, cleared money/budgets/capacity and no prior public snapshot. Existing project remains intact until replacement analysis succeeds.
- Added unknown/reported-unserved/planned/connected grid evidence, source/date validation, connected-site exclusion messaging, planned-grid risk, source provenance in reports, and visible incomplete-supply/finance status.
- Sites skill influenced the task-first home and responsive hierarchy while retaining the existing local Flask app and brand. No external publication or account was created.
- Automated verification: 246 Python + 68 JavaScript logic checks passed; syntax/dependency checks passed. Example reports refreshed. Browser initialization still fails; no visual or end-to-end browser verification.
- Local feature v1.3 service restarted at the same address. Next work is browser acceptance, authoritative local utility/admin evidence and measured-site validation—not the deferred deck/video/one-page summary.

## v1.4 completion record — Rwanda public evidence

- Active picker narrowed to Rwanda; future-country configuration retained. Site selection immediately prepares fresh public proxies/placeholders and opens the dashboard in either role. Source gap and assumption labels are explicit.
- Imported 4,251,978 country-clipped Google building detections, 2,232 OSM facility/shop objects and 236 historical Bugesera electricity records. Public source/metadata hashes and boundaries retained. Original synthetic data/model hashes remain unchanged.
- Added reproducible importer, local spatial indexes, source-status API, automatic-project endpoint, evidence summaries, source/building downloads and report/ZIP location profiles. Government raw records are not redistributed in the public pack.
- Live v1.4 HTTP smoke passed for Kirehe → Gahara → Butanga and Kirehe → Gatore → Curazo. Nearby building counts differed (82 vs 292); initialized inputs and forecasts differed accordingly. Both roles’ standalone reports and ZIPs returned successfully, ZIP integrity passed, source pack and 57,837,002-byte building download verified. These are software checks, not evidence of actual electricity use.
- 264 Python + 71 JavaScript checks passed. Dependency checks passed. Supported browser control still fails during app-server initialization; visual acceptance remains open.
- Sites guidance shaped the place-first, immediate-dashboard flow; data-handling guidance kept raw observations, derived proxies, assumptions and missing values separate. No hosted site or new accounts were created.
- Remaining data gates: VIIRS/GridFinder/EAE/MTF integrations, public cost-table calibration, GEP download access and permissioned meter data. Not all source-list items are collected. Current utility coverage and financial viability remain unverified.
