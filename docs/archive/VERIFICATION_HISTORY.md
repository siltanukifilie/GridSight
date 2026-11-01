# GridSight verification history

Historical test runs and browser limitations, preserved without upgrading their
claims. Current release checks are in [verification](../TEST_REPORT.md).

## Bugesera ranking and operator pilot — local checks, 1 November 2026

- Full suite: **653 Python tests pass; all 12 JavaScript test files pass.**
  JavaScript tests use logic/DOM doubles, not a real browser. Changed scripts
  parse and `git diff --check` passes.
- Ranking tests reproduce the existing order and weighted component totals,
  preserve missing counts, require exact country/district/sector matching, and
  reject changed scores, ranks, values, duplicates, NaN and stale equipment data.
  Missing ranking files do not break project calculations; downloads return 503.
- Checked forged client-side ranking/partner claims are ignored, project demand
  and finance are unchanged, dirty/busy navigation is blocked, and the cell
  shortcut fills real hierarchy selectors without creating a project or cell.
- Checked both export routes include ranking/source metadata, assessment weights,
  operator request/approval gates, and blank monthly templates. Public-demo meter
  uploads remain blocked. Operator approval and retention fields remain blank.
- Initial full-suite failure was the older exact export inventory. Updated that
  expectation for the deliberately added growth/scenario/assessment files and
  separately tested evidence folders; the subsequent full suite passed.
- Generated and integrity-checked an 85-entry offline deliverables ZIP plus
  standalone ranking/operator downloads. The example demand is explicitly
  synthetic. No browser visual/mobile/print acceptance, live deployment,
  operator contact or empirical validation was performed in this change.

## v1.11 prepublication checks — real hourly data and comparisons

- **625 Python tests pass; all ten JavaScript test files pass.** These include
  the earlier Bugesera/context integration and twelve new backend checks plus
  four new interface checks for the completed model comparison. Dependencies
  have no broken requirements; changed JavaScript parses; diff whitespace passes.
- Checks cover real snapshot scores (including Random Forest/Gradient Boosting),
  1,540 actual target rows, 4,216 prediction rows, UTC preview alignment, missing
  versus zero, fixed validation choices, hash linkage, CSV/ZIP/report provenance,
  source attribution, corrupted/missing snapshots and HTTP 503 download behavior.
- Both roles retain identical planning forecasts/finance when hourly evidence
  is removed. Current monthly-model validation stays pending and public meter
  uploads remain blocked. The synthetic model and original datasets are unchanged.
- One initial full-suite failure was an outdated export-file inventory expectation;
  it now accounts for the deliberately added operational_models folder, with its
  own explicit content/integrity checks. The subsequent full suite passed.
- Browser preview at localhost could not run because the admin-enforced browser
  security-check service was unavailable. No browser protection was bypassed.
  Current visual/mobile/download-click acceptance is not claimed. API, template
  and interface-logic checks do not establish those visual results.
- The user explicitly authorized publishing after tests. These are prepublication
  checks; hosted verification must be recorded after deployment.

Updated 1 November 2026 for the local prepared-evidence integration. Earlier sections retain historical verification details.

## Current local verification — prepared public evidence (not deployed)

- **613 Python tests pass; all ten JavaScript test files pass.** Final full runs used the low-memory path and the existing dependencies. `git diff --check` passes. These are software checks, not field-validation evidence.
- Backend checks include all 15 actual Bugesera GeoNames sector joins, a sector/cell hierarchy, wrong-area/country rejection, manual-location warnings, null preservation, kW/kWh separation, actual benchmark scores, preparation splits, forged evidence rejection, unchanged forecasts and finances for both roles, HTML/JSON/CSV/ZIP provenance, public upload restrictions, and unavailable/tampered snapshots.
- Desktop Chrome on temporary localhost port 8053 in public-demo mode: Rwanda → Bugesera District → Gashora → Biryogo; both developer and investor/lender workspaces; Project/Community sector context; Evidence benchmark and preparation sections. Biryogo's 56 assumed service-area households remained separate from Gashora's 8,393 census households. Existing green/light styling retained.
- The generated feasibility report was inspected in the browser, including the whole-sector evidence section, units, source limitations and pending-model-validation notice. This is screen QA, not printed-PDF verification. The separate deliverables report is covered by automated rendering checks, not an additional browser review.
- The compact evidence download endpoint and ZIP contents pass API tests. Chrome blocked the direct download with `ERR_BLOCKED_BY_CLIENT`; no browser-generated file was verified and no protection was bypassed. Manual browser download acceptance remains pending.
- All 15 source-file hashes and all 15 bundled snapshot hashes match the inventory (30 checks). The frozen model and both original synthetic datasets retain their previous SHA-256 hashes. No model was trained, no source original was edited, and no commit, push or Render deployment occurred.
- No multi-year consumption labels, current-model validation scores or calibrated confidence bounds were created. Comprehensive mobile, assistive-technology, real-upload, download and print acceptance remain open. The temporary preview server was used only for local review; the existing user server and hosted application were not replaced.

## Historical v1.10 verification — five-deliverable review and pack

- **735 automated checks pass:** 582 Python + 153 interface logic. Added 16 packaging/status checks and 7 interface checks; all existing suites still pass. Stylesheet parses. Frozen model and both original synthetic-data SHA-256 values are unchanged.
- Backend coverage: both roles; detailed Months 1–36 and 19–54; enabled legacy connection curve and disabled adoption; period/annual conservation; exact monthly scenario reuse; null unavailable empirical scores; no role-dependent input fingerprint; forged evidence ignored; invalid inputs; escaped names; intact ZIP; blank meter templates and permission worksheet; original analysis-export file list preserved.
- UI coverage: five direct actions, explicit evidence limits, legacy-result fallback, unique explanation anchors, applied-input export, separate batch studies omitted, dirty/busy guards and unchanged ordinary-export behavior.
- Desktop Chrome: the overview shortcut opens the new Evidence hub; both developer and lender can review all five items; the meter-data link reaches the current-model workflow. Green branding retained.
- The browser created `gridsight-deliverables.zip` in the local Downloads folder (synthetic Market centre demo). Download-event observation timed out, but the matching server response, timestamped file and ZIP integrity verified completion. No repeated download was needed.
- Extracted the actual download into an isolated temporary directory and previewed its `START_HERE.html` on loopback. Header/status review and 36-month SVG render correctly; all five sections and blank-data/evidence warnings are present. This was screen QA, not a printed-PDF layout check.
- The user's active Mubuga tab was not reloaded or overwritten. No real data or empirically calibrated uncertainty was produced. Comprehensive mobile, assistive-technology, upload and print acceptance remain open.

## Current v1.10 verification — dashboard redesign

- **712 automated checks:** 566 Python + 146 interface logic (124 prior + 20 analytics + 2 full-workspace integration). All original model and synthetic-data SHA256 hashes unchanged.
- New coverage: three scenarios × three years × four energy periods, annual-total conservation, invalid/prototype-like filters, year/month alignment, zero demand and missing debt, negative cash, connected-grid warnings, service-age labels, escaping, accessible chart targets, focus restoration and dirty-state preservation.
- Desktop Chrome: both roles, scenario/year/period linked totals, clicking Month 18, keyboard to Month 19, reset, feasibility forms and model-maintenance evidence. No browser error logs during these checks.
- Responsive checks: actual measured CSS widths 300 and 394 pixels (host browser scaling differs from requested viewport size). Found and fixed narrow sidebar overflow; document width then equalled viewport width at both sizes. Growth chart scrolls within its card. Month slider keyboard interaction, mobile Community controls and unapplied-input navigation protection verified. Temporary viewport override removed.
- Visual refresh retains the existing Python API and report/export paths. The new display module performs no network calls. Profile and contribution charts are explicitly fixed to Expected / Year 1 rather than falsely responding to the filters above.
- Not Microsoft Power BI embedding. No real consumption data, financial source, calibration release or measured savings were fabricated. No automated scheduling or hosted publication.
- Remaining release QA: complete assistive-technology audit, every mobile specialist form, real-file upload/download interactions and print/PDF visual review. Feature freeze remains open.

## Historical v1.9 verification — financial evidence and real-data updates

- **566 Python tests pass:** 474 previous + 65 maintenance + 27 financial/API tests. Missing/nonfinite data, exact field/currency/value matching, stale evidence detachment, no-input mutation, old-source flags, cost conversion, productive shortfalls, escaped reports and ZIP integrity.
- Maintenance tests exercise actual growth/conformal computation and invented-fixture lifecycle tests in temporary directories: frozen policy/code, immutable versions, rejected duplicate test IDs, failed quality gates, explicit review/selection/rollback, previous-cohort drift, file permissions, symlink/root protections, concurrent locks, audit hash chain and CLI failures. Some storage unit tests substitute computed study results to isolate registry behavior. No fixture was registered as real evidence outside tests.
- **124 interface-logic tests pass:** 107 previous + 15 credibility + 2 restore/rollback checks. Full view integration includes new scripts. Evidence escaping, missing values, currency labels, blank-input and upload-size guards, error recovery, dirty-state guards, saved-packet restoration and unapproved candidate wording.
- Live `/health` confirms feature 1.9 / model 1.0.0. Desktop Chrome browser verification opened a labelled synthetic demo, checked the developer Feasibility panel, expanded sources, and performed a clearly fictional FX/connection-count comparison. Blank CAPEX stayed unknown; the comparison did not change the project budget. Switched to the investor/lender Evidence view and verified the manual update workflow and independent-study warnings. No genuine financial/meter evidence uploaded.
- A screenshot identified overly wide source text; the new evidence table now wraps text. A second screenshot after reloading verified the benchmark table fits the desktop panel without the previous horizontal text overflow. Investor Feasibility and developer update-upload controls were also checked; the original developer role was restored. Full mobile, keyboard, real-file upload/download interaction and release-wide visual regression remain unverified.
- No new dependencies; installed dependency check passes. Frozen model and both synthetic dataset SHA256 values match v1.8. No build.py, synthetic rebuild, real-data deployment, production release or scheduled job.
- Priorities 6/7 have stronger software controls. Local evidence, real update performance and causal capital savings remain empirical gates, not passed by these software tests.

## Historical v1.8 verification — confidence and observed growth

- **474 Python checks pass:** previous 414 plus 60 new uncertainty/statistical checks. Reproducible bounded draws, exact nominal arithmetic, joint-path yearly quantiles, zero inputs, required widths, exact conformal ranks at 80/90/95%, worst-month site scores, nonshrinking intervals, downward growth, no horizon extrapolation, no fitting/calibration/test leakage, small-sample coverage intervals, complete-history guards, country transfer flags, export/API and no frozen artifact mutation.
- **107 interface-logic checks pass:** previous 93 plus 14 new checks. Accurate uncertainty wording, width conversion, no silent blank-to-zero fill, applied-project binding, stale result invalidation, preserved settings, study counts/horizon disclosure, HTML escaping, observed/target coverage distinction, growth plots, download binding, three-file submission and error recovery.
- No dependencies added; installed dependency consistency and JS/Python syntax checks pass.
- Live localhost version **1.8** passes both-role input-simulation requests, blank ZIP integrity and a 90% three-part study using an explicitly invented fixture with nonzero input widths. Nine calibration sites and two test sites remain distinct; results retain unverified/field-incomplete flags. No fixture was saved as real evidence.
- Original model and synthetic dataset hashes unchanged. All generated study observations are clearly invented test fixtures; no field evidence or production calibration artifact is created.
- Supported browser inventory fails during initialization. Visual/mobile/keyboard/download-click QA is unverified; no alternate browser-control route.
- Real calibrated confidence and observed East African growth remain pending eligible measured inputs/outcomes and independent evidence review. Passing software tests is not forecast validation.

## Historical v1.7 verification — monthly current-model holdouts

- **414 Python tests pass**, including 53 new tests for exact-model agreement, hand-calculated kWh, error arithmetic, leap months, full-year growth, country scope, site overlap/case-normalized IDs, strict inputs, outage/coverage/quality exclusions, zero targets, bounded imports, templates, hashes and unchanged global evidence.
- **93 interface-logic tests pass**: previous 84 plus 9 monthly-validation checks. Both-role integration, escaping, source-link safety, gap-aware charts, expected/actual tables, null metrics, growth gates, paired upload, stale-result clearing and failure recovery.
- Live localhost service restarted at **feature 1.7 / model 1.0.0**. New routes covered by HTTP/API checks and test client. No new dependencies.
- Frozen model and synthetic site/monthly dataset hashes match the prior release. No training or regeneration.
- **Visual/browser QA unverified:** browser selection succeeded, but localhost navigation was denied because the admin-enforced security check was unavailable. No alternate browser/security bypass. Logic/API checks are not browser proof.
- **No genuine field-validation metrics:** all test observations are invented fixtures under tests/. Source-candidate research is not evaluated data. Pending-real-validation status preserved.

## Historical v1.6 verification — administrative input panel and 20 features

- **361 Python tests pass**, including 55 new detailed arithmetic/validation/persistence/geography checks. Cases cover all 20 feature uses, per-appliance and per-equipment factors, connection ceilings, elapsed time, seasonal isolation, annual/monthly/profile conservation, zero load/income, optional values, finance invariants, both roles and report/ZIP preservation.
- **84 interface-logic tests pass**: workspaces 13, demand charts 14, feasibility/detailed inputs 41, administrative discovery 16. Obsolete map/survey handler expectations were replaced with the requested no-map/cell/name-only behavior. Detailed tests cover fractional inputs, steppers, slider sync, nested-value round trips, investor read-only views, legacy opt-in, dirty-state protection and applied-input export/rollback.
- All nine frontend scripts pass syntax checks; Python compilation, launcher syntax and dependency consistency pass. No dependencies changed.
- Live localhost service reports feature **1.6**, model **1.0.0**. Eight country administrative endpoints pass. Rwanda → Kirehe District → Gahara → Butezi resolves an actual ADM4 cell; both-role analysis, HTML reports and ZIP integrity/input-retention pass with service Months 19–54 and edited low/high factors. Landing page and new JS/CSS return HTTP 200. This is a diagnostic scenario, not a proposed operating project.
- Original model/site/monthly dataset SHA-256 values remain unchanged. No public-data snapshot or synthetic model regeneration occurred.
- **Browser QA remains unverified:** supported inventory returns no browsers and app-server initialization failure. No alternative browser control, visual/mobile screenshot, real click-download or print-preview pass is claimed.
- **Real-site validation remains pending:** engineering arithmetic and frozen synthetic-model tests are not measured forecasting accuracy; annual CSV comparison does not validate the new detailed path.

### Current manual acceptance sequence (when browser access returns)

1. Fresh load → choose among the eight EAC countries; no map/latitude/longitude controls.
2. Rwanda district → sector → actual cell; other countries show local equivalents or source gaps. Missing records allow three unverified names, never substitute coordinates.
3. Confirm dark collapsible input rail, accessible +/- buttons, decimal ratings/hours, exact units and synchronized month slider at desktop/mobile widths.
4. Edit each of the 20 features, including zero and blank optional income/fee. Apply once and check next-36-month labels, low/expected/high, all four time-period cards and affordability.
5. Inspect both roles; lender demand inputs read-only, shared financial edits preserved. Check supplies/cash/cases and reports.
6. Save/restore, switch locations/countries and exercise source failures. No draft leakage, inherited customer/cost data, stale descendants or invented source coverage.
7. Inspect real download and browser print layout. Feature freeze is still gated on this acceptance.

## Historical v1.5 verification — connection curve and deliverables

- Full Python suite: **306 passed**, including 42 new tests for invalid fields/types/dates, zero starts, immediate maturity, long ramps, calendar rollover, negative growth, annual conservation, one-time productive additions, monthly caps, cash consistency, both roles, report/ZIP contents and the proposal download.
- Interface logic: **81 passed** (workspaces 13; demand charts 14; feasibility 31; discovery 23). Ten new checks cover both-role curve rendering, five-deliverable status, explicit zero/blank date handling, saved/exported inputs, restore/rollback, role invariance, joint form updates and invalid/busy submission.
- Running local service: health reports feature 1.5; a public Rwanda location initializes the enabled curve. Both-role analyze/report/ZIP checks and the sharing-proposal download pass. Daily/weekly/monthly/yearly totals share the first-year path.
- Python compilation and connection JavaScript syntax pass. Original model/site/monthly dataset SHA-256 checksums remain unchanged.
- **Not completed:** supported browser inventory fails with “codex app-server exited before returning initialize.” No visual, responsive screenshot or real-browser interaction claims.
- **Not completed:** held-out authentic meter validation or post-connection calibration. Synthetic tests and annual-upload support cannot substitute for independent operator evidence. The safe-sharing proposal is not implemented hosted security.

## Historical v1.3 verification

## Automated checks

`python -m pytest -q` completed with **211 passed** after the public-context and validation-tool completion. The suite covers independent baseline and financial examples, energy conservation, growth anchoring, single equipment additions, served-energy caps, nonpositive break-even margins, zero demand, invalid inputs, synthetic reproducibility, component totals, site separation, recomputed metrics, RAMP shape normalization, all three analysis workflows, API routes (including the new chart script), exports, report escaping, and request limits. New checks cover exactly two audience roles, identical calculations across both roles, default compatibility, invalid role values on all analysis/report/export routes, and role-specific exports including zero-debt handling. Additional tests verify prepared-data completeness, bounds and unique site-months, a downside repayment shortfall, and a +30% demand case with capped revenue, unserved energy and peak-power shortfall.

`node tests/workspaces.test.cjs` completed with **13 passed**. These logic-only tests check navigation definitions, stored-role fallback, preservation of technical assumptions during financial editing, blocked switches while busy/dirty/loading, scenario identity across real switch-handler calls, remembered role, and unavailable browser storage. Two additional presentation tests verify the four-period card order, units, values, basis text and zero demand. They do not launch a browser and do not count as browser interaction QA.

`node tests/demand_charts.test.cjs` completed with **14 passed**, covering the chart component (legacy average fallback and conserved totals). Checks cover four horizons, fallback handling, units and interval scaling, partial-month weighting, energy conservation, zero/fractional demand, all three stored demo analyses, tab markup, keyboard handler behavior and preserved scenario/dirty state. These use lightweight test doubles, not a live browser.

`node --check` passed for app.js, workspaces.js, demand-charts.js, feasibility.js and context.js; `bash -n run.sh` passed. `python -m pip check` passed again; dependencies are unchanged. The RAMP integration previously ran after the documented compatibility pins. Rebuilding the monthly generator and model in that earlier step reproduced the recorded evaluation values; no model rebuild was performed for v1.2.

The export test compares saved forecasts, finance and assumptions to the analysis response exactly, and opens the generated ZIP to verify its contents and synthetic provenance. All three prepared examples are also exported to `reports/examples/` for review.

## Feasibility completion checks

`node tests/feasibility.test.cjs` now passes **21 tests**, bringing interface-logic checks to **48** (259 automated tests overall). Real view functions render both roles against prepared examples using DOM test doubles. Tests cover optional cost handling, all report inputs, saved/legacy settings, dirty-form navigation and download guards, monthly growth, clearly separated case cards, country currency/reset behavior, context provenance, opt-in map/device handlers, failure recovery and reviewed thin-data inputs. They do not verify browser layout or downloads.

The expanded Python suite independently verifies scenario multipliers, ten growth/adoption combinations, monthly compounding with positive/zero/negative rates, conservation of every annual estimate, cold-room adoption, capped revenues, simultaneous spare energy and peak shortfalls, idle-capital exposure, discounted NPV without double-counting debt, productive option cash/payback, missing budgets, invalid inputs, two-role equality and full exports. Both report routes render all requested sections. CSV rows (9 annual cases, 108 monthly cases, 36 growth months, 3 productive options) match JSON; HTML escapes user text.

All three prepared example HTML/JSON/ZIP packages were refreshed after the final calculation changes. No model retraining, synthetic dataset regeneration, dependency change or public deployment was performed.

## Copy simplification

Shortened both workspace headings, navigation and explanations, removed duplicate hero blocks, and added closed native disclosure sections for methods and missing evidence. Important synthetic-data and financial-screening notices remain visible. The calculation engine and exported report content are unchanged. Two new logic tests cover concise labels and native disclosure markup. Follow-up browser discovery returned no controllable tabs, so visual and click-through QA remains open.

## Central demand periods

The same first-year monthly point estimate is converted to daily (`monthly × 12 / 365`), weekly (`daily × 7`), monthly (unchanged) and annual (`monthly × 12`) customer energy. Tests cover zero/fractional inputs, invalid values, agreement with the daily profile, unchanged monthly finance, both roles, all three communities, JSON/CSV exports and report values. The range remains explicitly monthly; no separate daily/weekly prediction intervals are claimed. Refreshed all three prepared HTML/JSON/ZIP examples.

## Demand chart horizons

Daily keeps the existing illustrative hourly power profile. Weekly/monthly show average daily energy and an explicit partial final day for the average month. Yearly now uses normalized monthly growth for Year 1, with the same annual total as the cards. Positive, zero and negative growth are tested; no seasonality is invented. Feasibility shows 36 expected monthly values and a separate low/high scenario envelope. Model prediction bounds remain distinct from these cases. Chart-only rendering does not reset inputs.

## Local service

The local server was restarted at `http://127.0.0.1:8050/`. Health returned `ok`, model_version 1.0.0 and feature_version 1.2. Live analysis returned all three cases, 36 months and three productive options; the Market centre example rises from 9,843.1 kWh in M1 to 10,754.4 kWh in M12. Unknown-budget NPV is null. The live standalone report returned HTTP 200 with an attachment filename and 23,334-byte HTML content. An initial smoke request mistakenly sent the full large analysis artifact and correctly received HTTP 413; the normal compact inputs succeeded.

The server is bound to localhost and has not been publicly deployed. It is a development server, not a production hosting arrangement.

## Browser verification limit

Earlier browser access failed policy verification. The latest supported discovery returned no browsers and reported that the app-server exited before initialization. No usable page state or screenshot was obtained. No alternate browser-control route was used. Opening the preview through the app returned queued, not verified UI completion.

Browser interaction and visual checks remain open: desktop/mobile layout, form interaction, chart rendering, browser save/restore, browser-triggered downloads, and print preview. Static JavaScript validation and API tests are not substitutes. Responsive styling and accessible labels are implemented, but visual QA is not claimed as passed.

## Browser checklist when access is available

1. Open the default Market centre dashboard.
2. Switch among all three communities and verify charts and figures update.
3. Edit households, run the analysis, and confirm the custom-community label.
4. Set tariff to zero and verify the no-break-even message.
5. Reduce energy capacity and verify served energy is capped.
6. Add a mill in Year 2 and verify one addition carried into Year 3.
7. Save and restore a scenario in the browser.
8. Export and open the HTML and CSV analysis files.
9. Check evidence metrics, synthetic labels, and dataset downloads.
10. Review laptop and narrow mobile layouts for clipping and usability.
11. Switch between developer and investor/lender roles; verify role-specific headings/navigation and identical scenario numbers.
12. Verify investor Project profile is read-only and financial edits leave community, growth and capacity unchanged.
13. Change a form input, then try switching roles; verify the switch is blocked and the draft input remains.
14. Export in each role and verify planning versus investment headings and investor evidence gaps. Refresh and confirm the role is remembered.
15. Confirm the role selector remains usable on narrow screens and missing evidence/access-control disclosures remain visible.
16. In the investor view, check the faster-demand panel against the +30% row, including unserved energy and peak shortfall; test a base-case payment covered while the downside has a shortfall.
17. Verify both roles show the central estimate in day/week/month/year order, with units and the Year 1 average-equivalent note. Compare the values with `central_demand_estimates.csv` and the printable report; check mobile card layout.
18. Confirm the simplified headings and navigation in both roles. Open and close “How it works,” “Growth assumptions,” and “Missing evidence,” including with the keyboard; ensure essential warnings remain visible when closed.
19. In both roles, switch all four chart tabs using click, arrows, Home and End. Confirm heading, units, total, selected state and focus; compare totals against the cards. Check the partial-day note in Monthly and all 12 months in Yearly, including narrow layouts.
20. Select a chart period, then change community or role; verify the same period updates to the current analysis. Input edits now block leaving that form or changing community until applied, protecting all new settings. Verify the draft remains visible and exports are blocked. Check zero demand and visible assumption/uncertainty disclosures.

Additional browser checks:

21. Open Feasibility in both roles. Check all six navigation items on mobile, table scrolling, form labels, empty optional budgets and short method disclosures.
22. Enter low/high factors, capital budgets and productive support costs. Update, Save/Restore, switch roles, and verify values persist. Reject capacity-linked cost above total cost and invalid/missing required values.
23. Check positive, zero and negative monthly growth. Verify Year 1 totals match the cards and Year 2/3 equipment is added once. Check cold-room adoption.
24. Test insufficient energy, insufficient firm power, spare energy with insufficient power, and a large-capacity case. Check cost exposure is labeled as a proxy, not savings.
25. Download the standalone HTML report and the ZIP. Compare inputs and values, open the report, and inspect browser print/PDF output. Check tables and page breaks visually.

## Evidence boundary

Passing software tests establishes consistency of this implementation and synthetic workflow. No real metered-site accuracy or suitability for financing an actual project has been established.
## v1.2 verification extension

Final automated total: **211 Python + 48 JavaScript logic checks = 259 checks**. The JavaScript files are executed individually: 13 workspace checks, 14 chart checks and 21 integrated feasibility/context checks. JavaScript and launcher syntax checks and dependency consistency pass. DOM test doubles are not browser QA.

New checks cover explicit missing-versus-zero inputs, no silent analysis-time imputation, proposal/accept/second-submit flow, assumed-field reporting, country-specific defaults/units, no currency conversion, escaped location labels, coordinate bounds, unchanged predictions with public context, malformed/upstream-failure responses, cache/snapshot isolation, offline forecasts, report provenance and monetary export units. Location-map and device tests prove the handlers are opt-in at the logic level only.

Upload tests use clearly named **automated fixtures, not measured evidence**. They check required permission/source attestations, headers, limits, duplicate/demo IDs, complete historical 12-month periods, leap-year normalization, zero-total WAPE, numeric bounds, country groups, baseline/model metrics and unchanged model/evaluation hashes. No real validation sample is claimed.

Live HTTP checks on 31 October: health v1.2, public places for Kirehe (RW) and Jinja (UG), World Bank population/electricity-access data for both countries, unchanged forecast after adding context, and HTTP 200 report/ZIP attachments. Source observation years are displayed separately from fetch time. Browser automation returned `codex app-server exited before returning initialize`; no screenshot or end-to-end browser approval is claimed.

Additional browser checks:

26. Locations: search ambiguous names, select the intended match, verify label/coordinates, and load the map only after choosing. Check OpenStreetMap attribution, narrow layouts and external-map link.
27. Test permission denied/unavailable/accepted device location; confirm it fills rounded drafts without applying or fetching a map automatically. Confirm coordinates are the project, not assumed device identity.
28. Change country with confirmation; verify all money inputs and optional budgets clear, currency changes everywhere, counts persist, and transfer warnings appear. Check both roles and Save/Restore.
29. Fetch/download public country data, check years and source links, and verify forecast invariance. Test offline failures and expired snapshots after restart.
30. Enable missing-input guidance, clear fields, review/accept proposals, edit them and submit. Confirm zero versus unknown, assumed-field notices, saved provenance and report disclosure.
31. Upload authorized test-only aggregates through Evidence; inspect errors, metrics and downloadable JSON. Check no file goes to public providers and no global validation status changes. Use real data only with permission.

## v1.3 verification — current

**246 Python + 68 JavaScript logic checks = 314 passing checks.** JavaScript suites: workspaces 13, demand charts 14, feasibility/context 21, discovery 20. All six JS source files pass syntax checks, launcher syntax passes, and dependency consistency passes. No dependencies or model artifacts were rebuilt.

New checks verify all eight country extracts and report currencies; canonical metadata rather than client-supplied provenance; invalid/cross-country parent and place IDs; Rwanda's Kirehe → 12 sectors → linked settlements; incomplete Kenyan subdivisions; urban-parent exclusions; unknown population; pagination/search; offline/manual fallback; grid claim source/date validation and future-date rejection; connected/planned warnings; report/ZIP provenance; no automatic forecast at boot; stale-response protection; fresh money/capacity/budget/customer handling; reviewed suggestions; failed-analysis rollback; dirty-project preservation; and opt-in map handlers.

Public snapshots: GeoNames country ZIPs retrieved 31 October 2026; 101,142 retained administrative/settlement records across eight countries. This is actual downloaded geography, not measured energy evidence or a current grid map. Raw source ZIP SHA-256 is retained per country. Refreshing source data may change exact coverage counts and should be treated as a versioned data change.

Local HTTP checks verify health feature 1.3/model 1.0.0, all eight administrative and filtered-settlement endpoints, landing markup, candidate analysis, standalone HTML attachment, ZIP integrity and exact geographic provenance. Diagnostic customer inputs are test fixtures, not surveyed projects.

Browser discovery again returned no browsers and `codex app-server exited before returning initialize`. No visual, mobile, permission-prompt, click-download or print-preview pass is claimed. The Sites skill's supported-browser restriction was respected.

### Superseding browser acceptance sequence

1. Fresh load must show the site finder without automatically analysing a fictional demo. Both roles should be selectable.
2. Rwanda → Kirehe District → Gahara → a settlement; confirm path/coordinate provenance, blank customer fields and opt-in map.
3. Change country or parent; dependent choices and candidate inputs must clear without modifying the currently analysed project. Back to current project should restore its view.
4. Try each of the eight countries, a missing subdivision, empty search, paginated search and manual surveyed point. Labels must match source coverage; no invented sectors or off-grid labels.
5. Enter households; leave an unknown field blank; request suggestions, review/edit, check the acknowledgement and build. Editing any input must clear that acknowledgement.
6. New project must show zero/unset supply and finances, its own currency, and an incomplete-financial-case message. Set supply/costs, save/restore and export exact inputs.
7. Reported unserved/planned/connected grid states require date/source. Connected must not look like a recommended unserved site. Correcting coordinates clears previous claims.
8. Verify developer/investor views, four chart horizons, scenario cases, three-year growth, productive uses, sizing, cash, validation and report download/print.
9. Check keyboard navigation, focus, dropdown widths, contrast and overflow at desktop and narrow mobile sizes.
10. Explore demo explicitly, then return to Find a site. Keep synthetic labels and preserve current-project data until a new analysis succeeds.

Earlier checklist items that assumed auto-opening the Market centre or retaining counts on country change are superseded.

## v1.4 Rwanda evidence and automatic selection — 31 October 2026

- 264 Python tests passed, including actual imported counts/metadata, spatial radius isolation, missing-layer placeholders, household conversion/caps, active-country scope, invalid and outside-boundary coordinates, historical sector-vs-site grid distinction, report/ZIP source retention and both audience flows.
- 71 JavaScript handler/render tests passed: 13 workspace, 14 chart, 21 feasibility, 23 discovery/data-flow. New tests cover automatic preparation, preserved previous project on failure, survey fallback, Rwanda-only active picker and escaped evidence markup.
- Python compilation, JavaScript syntax and dependency consistency checks passed. Shapely 2.2.0 is pinned for boundary processing. The original model and synthetic training CSVs were not regenerated.
- Imported actual public records: 4,251,978 country-clipped detections from 22,106,220 tile records; 2,232 OSM facility objects; 236 historical government records. No metered consumption was imported.
- Supported CUA browser discovery again returned no controllable browser and an app-server initialization error. Visual, mobile, real-click and print QA remain unperformed, not passed. No alternate browser-control path used.

Live service verification: feature 1.4/model 1.0.0 at http://127.0.0.1:8050/. Two distinct Kirehe settlements produced different local counts and provisional demand inputs. Developer and investor analysis/report/ZIP requests succeeded; all downloaded ZIP integrity checks passed. Source pack contents and building attachment size verified. Original model and both synthetic training CSV SHA-256 values match the pre-change values. This does not substitute for browser QA or real demand validation.
