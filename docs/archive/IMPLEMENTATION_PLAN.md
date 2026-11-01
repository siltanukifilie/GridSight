# GridSight implementation plan

Historical planning record, not the current setup or feature-status guide.
See the [judge guide](../JUDGES_GUIDE.md) and [current documentation](../README.md).

Prepared 30 October 2026. Requirements expanded 31 October 2026 with the user's 13-item product-success checklist. The synthetic prototype has automated verification; browser QA, real-data validation and commercial validation remain separate open gates.

Build a working mini-grid demand planning prototype using synthetic data. The user's latest instruction authorizes completing the product in this session while retaining the numbered plan and evidence. Demo recording, pitch deck, one-page summary, and final disclosure are deferred. The team has three members.

## Current extension — interactive dashboard redesign (v1.10)

1. **Visual system:** local navy/coral dashboard inspired by the user's reference; consistent inputs, navigation, tables, charts and evidence panels. No map or external font/image service.
2. **Linked exploration:** low/expected/high, forecast Year 1–3 and daily/weekly/monthly/yearly energy display filters. Use existing Python scenario output; never mutate project inputs or change report semantics.
3. **Monthly drill-down:** 36-month curve, keyboard-selectable points, month slider, cash/debt/supply details and accessible monthly table. Financial cards retain monthly units regardless of energy-period filter.
4. **Less repetition:** consolidate overview cards, keep fixed Year-1 profile and contribution shares explicitly labelled, move detailed source explanations into an expandable section. Existing specialised pages stay available.
5. **Verification:** 22 new interface checks plus regression suite; desktop and narrow-screen browser checks. No actual Microsoft Power BI embedding, cloud publication, model rebuilding or evidence-validation claim.

## Historical extension — financial credibility and real-data maintenance (v1.9)

1. **Source-aware finance — implemented:** dated regional reference catalogue, explicit applicability limits, survey/quotation collection pack, exact-input evidence records and reporting. No automatic tariff, FX or local-runtime inference.
2. **Productive-use risk — implemented:** no uptake / half use / assumed use comparisons and a prospective impact study protocol. No claim that unused capacity equals demonstrated savings.
3. **Controlled update pipeline — implemented:** freeze protocol and code, ingest permissioned real-data snapshots, recalibrate aggregate growth/uncertainty, test independent sites and record data/code/model versions.
4. **Regression and drift gates — implemented:** error, bias, coverage, width, country/age groups, sample counts, prior-cohort/input-mix shifts, and failed/undefined metric handling. Thresholds require predeclaration; none are invented as lender standards.
5. **Review lifecycle — implemented:** private immutable local registry, explicit separate review, selection and rollback; test-site reuse guard and integrity checks. No automatic serving-model mutation, scheduler or hosted data store.
6. **Verification — passed with limits:** 690 automated checks and focused desktop browser interactions. Full mobile, keyboard and file workflow browser coverage remains incomplete.
7. **Empirical/production gates — OPEN:** actual site quotes, business/runtime surveys, independent capital-impact evidence, genuine update cohorts, and production-calibrated deployment. A tested workflow is not a completed real-data retraining run.

## Historical extension — confidence and observed early growth (v1.8)

1. **Input uncertainty — implemented:** coherent triangular input draws through the current engineering equation; editable widths, bounds, reproducible seeds, standard-month and annual path totals. Clearly labelled input-assumption bands, not confidence.
2. **Observed growth — implemented:** fixed piecewise-log residual correction fit only on dedicated sites; 24-month default / 36-month option; no forced monotonic growth or unsupported extrapolation. Aggregate growth, not identification of connection/appliance/business mechanisms.
3. **Forecast-error calibration — implemented:** maximum normalized exceedance per calibration site, exact finite-sample conformal order statistic, expansion of the input band. No pooled-month independence shortcut.
4. **Untouched testing — implemented:** site-path and monthly coverage, exact site-level coverage interval, widths, original/fitted errors, early-stage/country/site diagnostics and annual growth.
5. **UI and downloads — implemented:** Feasibility input simulation; Evidence three-file study with frozen split/settings, blank templates, report/CSV, chart and explicit evidence gaps. Does not silently change forecasts, finance or reports.
6. **Software verification — passed:** 474 Python + 107 interface-logic tests (581). No new dependencies or synthetic model/data regeneration. Browser visual QA unavailable.
7. **Empirical gates — OPEN:** no genuine paired histories imported; no real calibrated range or learned East African growth result. See CONFIDENCE_AND_GROWTH.md for counts, data requirements, assumptions and limitations.

## Historical extension — measured-site validation (v1.7)

1. **Public-source review — recorded:** Kenya/Tanzania/Uganda candidates; access, units, input timing and licence limitations remain. No genuine paired observations imported.
2. **Current calculation — implemented:** evaluate the detailed engineering model, not the frozen reference model. Pre-connection inputs and whole-site holdouts required; no retraining/tuning.
3. **Data quality — implemented:** strict two-file contract; historical monthly customer-side kWh; coverage/availability/quality checks; no missing defaults or zero imputation; explicit exclusion ledger.
4. **Comparison — implemented:** calendar-day adjustment, MAE/RMSE/WAPE/bias, per-site/country/service-year groups, 36-month coverage and growth only across complete adjacent years.
5. **UI/reproduction — implemented:** Evidence workflow with starter pack, expected/actual chart/table, source review, JSON/CSV downloads and input/model hashes. Separate batch, not selected-project certification.
6. **Software tests — passed:** 414 Python + 93 interface-logic checks. Original model/dataset hashes unchanged. Visual checks unverified because the browser security check was unavailable.
7. **Field-validation gate — OPEN:** obtain permissioned measured records with matching frozen inputs, verify source/independence, then run and review the study. No automatic pass or fabricated results.

## Historical extension — East Africa, no map, twenty features (v1.6)

1. **Scope and sources — implemented:** use the eight previously selected EAC countries. Cascading administrative selectors, real Rwanda cells and source-supported equivalents; explicitly missing levels can be entered as unverified names. No guessed coordinates, map or device-position UI.
2. **Input design — implemented:** compact dark collapsible rail, number steppers, units/help, month slider; preserve light results, branding and developer/lender roles. No new hosted product.
3. **Detailed calculation — implemented:** household ceiling × starting connection share plus capped new connections; per-type appliance units × watts × daily hours; counted businesses/equipment/services × kW × hours; annual appliance/business growth and repeating agricultural factors.
4. **Affordability — implemented:** monthly gross income and connection fee remain optional/unknown until entered. Tariff drives bill/revenue. Fee is a one-time customer burden, excluded from recurring operating cash. No unvalidated income/price elasticity.
5. **Consistency — verified:** the forecast window starts after entered elapsed months. First-year cards, profile, 36 months, yearly summaries, scenarios, monthly caps/finances and exact-input exports agree. Old household-growth/appliance-index/S-ramp do not also apply.
6. **Evidence — explicit:** this is engineering scenario arithmetic, not a 20-feature retrained model. Low/high are user-defined multipliers, not calibrated probability. Legacy model and training data remain frozen.
7. **Tests — automated/live complete:** 361 Python + 84 interface-logic checks; both-role live analysis/report/ZIP passes. Source and dependency checks pass. Supported browser initialization fails; visual/real-click acceptance is still open.
8. **Handoff — local only:** select location → review all inputs → Update dashboard → inspect Overview/Scenarios/Feasibility → export. Next gate is browser QA and independent real-site evidence; demo, pitch and one-page remain deferred.

## Historical extension — connection growth and deliverable checklist (v1.5)

1. **Connection model — implemented:** preserve the frozen model, add explicit adoption fractions/maturity/date, allow zero starts and declines in underlying growth, disclose reference reinterpretation and standard-month time basis.
2. **Consistency — verified:** Year 1 averages, period cards, profile, 36 monthly rows, annual summaries, monthly-cap finances and reports all use the same path.
3. **Dashboard — implemented:** overview curve for both roles; developer controls in Feasibility; lender-readable assumptions; save/restore/export and joint form submission.
4. **Five deliverables — surfaced:** Rwanda location estimate/range, curve, pending genuine meter validation, lender explanation and downloadable safe-sharing proposal.
5. **Meter study — pending:** the existing annual frozen-reference diagnostic is not a growth-curve backtest. Obtain authorized independent site-month records before designing/calibrating/testing the adoption model. Do not invent measurements or security guarantees.
6. **Verification — 387 automated checks pass:** 306 Python + 81 interface-logic tests. Live local API/report/download checks pass. Browser tool initialization remains blocked; visual QA is not complete.
7. **Handoff:** refresh the local app; choose a location, edit connection assumptions, compare scenarios, then review Evidence. Keep demo/pitch/one-page work deferred.

## Previous extension — Rwanda public-data dashboard (v1.4)

Latest user instruction supersedes the eight-country active release: Rwanda now, East Africa later. [Exact data pipeline](../RWANDA_DATA_PIPELINE.md).

1. **Scope — complete:** Rwanda-only visible selector; preserve future-country architecture and two roles.
2. **Collect — partial, explicitly recorded:** import 4,251,978 Google building detections, 2,232 OSM facility/shop objects and 236 MININFRA historical records. Preserve dates/checksums/licences. VIIRS, GridFinder, EAE, MTF, cost benchmark extraction and metered labels remain uncollected; GEP download requires login.
3. **Prepare — complete for collected layers:** confidence threshold 0.738; Rwanda ADM0 clip; numerical spatial index; no ambiguous government household count used.
4. **Connect — complete:** selecting a Rwanda place builds 500 m public proxies plus explicit placeholders and immediately opens the shared demand/finance engine. No previous project data is reused.
5. **Explain — complete:** source status, starting vs current inputs, unknown grid status, historical sector warning, illustrative-finance notice and profile export/report.
6. **Verify — automated complete, visual open:** 264 Python + 71 logic tests. No model retraining or synthetic-data regeneration. Browser initialization remains unavailable.
7. **Next:** field-survey one candidate, confirm current utility coverage, replace illustrative costs and compare with permissioned real consumption. Obtain access to the remaining data layers; do not call them collected.

## Historical extension — East Africa location-first redesign (v1.3, superseded)

User confirmed **all eight EAC countries**, superseding the Rwanda/Uganda-only geographic scope. Keep the two roles and every existing analysis/report capability. Sites skill guided a local-only, task-first redesign; no publication or separate project was created.

1. **Country scope — implemented.** RW/RWF, UG/UGX, KE/KES, TZ/TZS, BI/BIF, SS/SSP, SO/SOS and CD/CDF; local source-supported administrative labels, coordinate bounds, time-zone context and explicit transfer warnings.
2. **Public geography — implemented.** Import attributed GeoNames country dumps; retain source hashes/dates and canonical IDs. Country → administrative area → local subdivision → settlement; search/manual-coordinate fallback when links are absent. No invented administrative coverage.
3. **Rural-first discovery — implemented.** Exclude source capitals/seats, known large settlements and urban-labelled areas/descendants. Mark access as unknown by default. User-reported access needs source/date; connected/planned claims visibly change the next action. No grid-access verification is inferred from geography.
4. **Fresh site setup — implemented.** Blank customer inputs, household anchor, reviewable suggestions, explicit acceptance, no inherited money/capacity or public snapshot. Country/parent changes clear dependent choices. A failed analysis restores the prior valid project.
5. **Two-role dashboard — implemented.** New location-first home, site banner, simpler disclosures, map/provenance/grid checks. Preserve demand horizons, cases, growth, productive uses, explanations, finance, real-consumption comparison and reports.
6. **Verification — automated complete; browser open.** 246 Python + 68 logic tests, source/launcher checks, dependency consistency and local HTTP smoke checks. No model retraining or synthetic-data regeneration. Visually verify desktop/mobile/manual inputs/maps/downloads/print when supported browser access returns.
7. **Evidence gates — remain open.** Current authoritative grid and administrative maps, real customer surveys, measured demand validation and country-specific calibration, engineering/site permissions and a paid pilot.

Current next action: open the v1.6 location-first home and run Rwanda district/sector/cell through detailed inputs and a reviewed forecast; repeat a country with incomplete subdivisions using the unverified-name fallback. The supported browser tool currently cannot initialize.

## Product definition

| Item | Working decision |
|---|---|
| Name | GridSight |
| Tagline | See demand before you build. |
| Problem | Developers need to estimate community electricity demand before building a mini-grid. |
| Primary user | Mini-grid developer assessing expected demand, peak demand, future demand, uncertainty, productive-use potential and financial risk. |
| Secondary user | Investor / lender reviewing forecast credibility, financial viability limits, lower/faster demand and repayment capacity. |
| Geographic scope | Rwanda active; all eight EAC countries retained as future architecture. Rural-first public-location discovery is not proof of no grid. |
| Track | Digital Solutions and AI, inherited from the earlier project discussion. |
| Data for this version | Synthetic training/consumption; public building/facility proxies; editable planning assumptions; historical electricity context and public geography. |
| Main output | A transparent demand estimate with a range, growth scenarios, demand drivers, and revenue sensitivity. |

The user selects a Rwanda place (or surveyed point), immediately sees a preliminary forecast, reviews the public proxies and planning assumptions, changes growth/supply/financial inputs and exports a report. Public places are not verified mini-grid opportunities. Fictional demos remain explicitly separate.

## Two-role product workflow

The user explicitly requested two roles on 30 October 2026: developers are the primary users; investors and lenders share the secondary workspace. Each has a dedicated workflow.

| Step | Mini-grid developer | Investor / lender |
|---|---|---|
| 1 — Understand the project | Demand, uncertainty, daily peak and growth overview. | Revenue, cash after debt, debt coverage and downside overview. |
| 2 — Inspect inputs | Edit community counts, uptake, appliances and equipment. | Read-only community and technical profile; inspect provenance. |
| 3 — Test scenarios | Edit growth, added equipment, energy/power limits and operating economics. | Edit tariff, collection, operating costs and debt payment; retain technical inputs. |
| 4 — Review evidence | Check forecast limitations and prepare a transparent planning analysis. | Check model evidence, missing diligence documents and investment-screening report. |

Implemented acceptance checks: exactly two role options; same scenario and calculations across roles; no loss of unapplied inputs on a role switch; role-specific report headings and investor snapshot; investor finance edits preserve technical assumptions; clear synthetic and access-control disclosures. Automated API and logic checks pass; browser interaction checks remain pending.

This MVP uses an audience switch, not authenticated accounts or authorization. Both views share one working scenario in the browser. Financial edits are not private investor overrides. Before a multi-user release, implement verified accounts, server-side project ownership and reviewer permissions, separate investor scenarios, an audit trail, and cross-user access tests. These are explicitly outside the current local prototype.

Investor outputs are early screening only: no IRR, whole-life valuation, credit rating, loan approval, or verified due-diligence status is claimed. The 31 October completion adds optional user-entered capital budgets and a clearly bounded 36-month pre-financing/pre-tax NPV screen; see `FEASIBILITY_METHODS.md` and `COMPLETION_PLAN.md` for the completed scenario, productive-use, sizing and report extensions.

### Requirements mapped to the product

| User need | Product response | Evidence limit |
|---|---|---|
| Developer: expected demand | Central estimates in kWh/day, kWh/week, kWh/month and kWh/year. | Year 1 average equivalents (365 days/year, 12 months/year, 7 days/week), not date-specific forecasts or real-site measurements. |
| Developer: peak demand | RAMP-based typical-day peak and firm-power shortfall. | Not an annual extreme or engineering design value. |
| Developer: future demand | Year 1–3 growth and productive-equipment adoption scenarios. | Assumption-based growth, not independently validated. |
| Developer: uncertainty | Nominal 80% prediction range and observed held-out coverage. | A prediction interval, not a confidence interval for a population mean; real-site coverage unknown. |
| Developer: productive-use potential | Mills, pumps, cold rooms and shops; baseline contributions and input sensitivities. | Entered opportunities, not verified local commercial demand. |
| Developer: financial risk | Costs, collection, debt, break-even and capacity-limited stress cases. | Operating screen, not full investment appraisal. |
| Investor: Is the forecast credible? | Baseline comparison, site-separated test metrics, uncertainty method, shifted-data stress and provenance. | Credibility outside the simulator requires independent real-site validation. |
| Investor: Is the project financially viable? | Revenue, operating surplus, cash after debt and break-even assumptions. | Viability cannot be established without capital costs, financing terms, lifecycle costs and real evidence. |
| Investor: What if demand is lower? | −20% and −40% demand cases, cash and debt coverage. | Stress factors are illustrative, not probabilities. |
| Investor: What if demand grows faster? | +30% stress with served/unserved energy and peak shortfall; separate three-year growth view. | Growth rate is not inferred from the +30% stress case; supply expansion costs are not modeled. |
| Investor: Can financing be repaid? | Base and downside operating surplus / stated monthly debt payment. | No full amortization, lender covenant or credit decision; no payment gives “Not applicable.” |

## Product success checklist — 31 October 2026

The user's comparison table is the target, not proof that every row is already achieved. The earlier description of a completed MVP referred to synthetic scenario features, not a real-data or commercially validated product. No competitor has been assessed; keep the Other Team column unknown until evidence is supplied.

| ID | Question / requirement | Current evidence-backed status | Completion criterion / remaining work |
|---|---|---|---|
| R01 | Can it predict demand? | Implemented for synthetic planning: baseline plus trained estimate, daily/week/month/year energy and illustrative peak. | Preserve tested units, zero-demand behavior, reproducible results and model version. Field accuracy depends on R07. |
| R02 | Uses real/public data? | Implemented as a separate context layer: eight-country offline GeoNames hierarchy (101,142 source records), opt-in World Bank national context and a legacy geocoder. Eight-country local geographic endpoints and earlier Rwanda/Uganda public-statistic responses verified. All training/consumption labels remain synthetic. | Source URL, licence, geography, year, retrieval time, transformation and snapshot identity retained. Do not describe national context as village consumption or model training. |
| R03 | Predicts demand growth? | Implemented as conditional 36-month / three-year growth, not learned real-world growth accuracy. | Preserve monthly/annual conservation, adoption timing and positive/zero/negative growth tests. Independently observed future consumption is needed before claiming growth validation. |
| R04 | Gives uncertainty range? | Implemented: calibrated nominal 80% interval with synthetic test coverage; separate Low / expected / high scenario range. | Keep probabilistic prediction bounds separate from editable scenario factors. Report real-data coverage and width when R07 is available. Never relabel scenario factors as calibrated confidence. |
| R05 | Includes businesses/productive use? | Implemented: shops, mills, irrigation, cold rooms, added-equipment scenarios and developer contribution/payback comparisons. | Preserve supply caps and cost disclosures; establish local business demand and ability to pay before claiming commercial uptake or enterprise profit. |
| R06 | Explains predictions? | Implemented: baseline components, local model sensitivities, exact assumptions and provenance. | Explain known/assumed inputs and dominant sensitivities in the report. Do not present baseline shares as exact model attribution or sensitivities as causes. |
| R07 | Validated against real consumption? | Actual validation remains open. Added a permissioned-aggregate CSV comparison workflow with frozen-model hash, baseline/model error, bias, interval coverage, country breakdown and downloadable results. | Supply genuinely measured, compatible independent sites. The app enforces 12 historical complete months and input validity, but authenticity/independence remain user attestations. No automatic pass or lending claim. |
| R08 | Shows financial consequences? | Implemented: capacity-limited revenue, cash, debt coverage, stress cases, capital exposure and optional bounded NPV/payback. | Keep inputs transparent, missing costs unknown, and forecast/finance/export consistency tested. No bankability or lending approval claim. |
| R09 | Works with thin data? | Implemented as guided planning: household count required, other unknown inputs explicitly proposed and reviewed before application. Known zero is preserved; assumed fields are retained in reports. | Software missing-input checks pass. Accuracy under missingness is not established; synthetic interval coverage does not cover uncertainty in guessed inputs. Verify local priors and actual outcomes before relying on this path. |
| R10 | Works beyond Rwanda? | All eight EAC country configurations, currency-labelled UI/reports, hierarchical public geography and transfer warnings implemented. New projects require fresh inputs and clear money/capacity. | Same synthetic model and energy priors in all eight contexts. No automatic FX conversion; cost entries are user-supplied. Held-out-country measurements are still needed for transfer accuracy. |
| R11 | Has a paying customer? | Unconfirmed. Mini-grid developer is the intended primary buyer; no verified payment/customer record has been supplied. Clarification requested. | Confirm an actual paying organization and paid transaction, with permission to disclose any identity. A prospect, interview, free pilot or letter of intent is not a paying customer. Do not contact prospects or create commitments without a separate request. |
| R12 | Clear business model? | Proposed per-project developer assessment, recurring portfolio subscription and lender review licence now visible in the app and report. Prices and customer status are explicitly unconfirmed. | Validate buyer budget, pilot scope, willingness to pay, cost to serve, repeat use and actual transactions through authorized commercial work. No billing or outreach implemented. |
| R13 | Generates decision/report? | Implemented: scenario-based findings, next actions, HTML report, browser print/PDF and CSV/JSON package. | Preserve exact inputs, evidence limits and reproducibility across both roles. Browser print/layout checks remain open; output is decision support, not automated investment approval. |

### Commercial model — explicit hypothesis, not traction

- Primary buyer: mini-grid developers screening candidate projects before committing to construction.
- Proposed initial paid deliverable: a per-project demand and feasibility-screening assessment, with documented inputs, uncertainty and scenario report. Scope and price must be agreed before any paid pilot.
- Proposed recurring offer: a portfolio subscription for developers repeatedly comparing and updating projects. Secondary opportunity: an investor/lender review license for evaluating developer submissions.
- Value proposition to test: less manual analysis and clearer identification of demand, capacity and repayment risks. No quantified savings or revenue claims until measured.
- Commercial evidence to collect: who owns the budget, whether the output affects a real decision, willingness to pay, support/data costs, repeat use, and actual paid transactions.
- Pricing amounts, named customers, revenue, conversion and retention are currently unknown. No contract, payment integration, outreach or purchase is authorized by this checklist.

### Remaining implementation and evidence gates

1. Browser QA of all six views, location search/results, opt-in map/device permission, country reset, missing-input review, consumption upload and report/print flows.
2. Obtain eligible permissioned measured aggregates and comparable features. Use the frozen comparison tool, document collection/outages and freeze holdouts before any later tuning. Public context cannot close R07.
3. Validate all seven transfer-country configurations and any country-specific priors against independent observations; current support is an architectural demonstration.
4. Confirm whether a developer has paid and validate pricing through an authorized pilot. Do not infer payment from a target buyer.
5. Feature freeze and polish after checks, followed by the user-deferred demo, deck, one-page summary, disclosure and final package.

### Live-location addition — completed software scope

A sixth Locations area supports user-triggered place-name search, explicit match selection, manual coordinates and an optional one-shot, permission-gated device-coordinate draft. OpenStreetMap is loaded only on click, with visible attribution and coordinate-sharing notice. These are planning places, not a live fleet of operating mini-grids. Approximate country bounding boxes check obvious mistakes; they are not surveyed borders.

National observations are fetched only on request, cached for 24 hours and attached to reports through server-owned snapshot IDs. Source failure never replaces missing data with invented values. Neither coordinates nor national indicators change forecasts, training labels or financial assumptions. No private community/financial inputs are sent to these providers.

## Scope of the first working version

| Capability | What the user will receive |
|---|---|
| Community input | Three prepared demonstration communities and an editable community form. |
| Demand estimate | Central customer demand per day, week, month and year, derived consistently from the first-year average monthly estimate. |
| Uncertainty | Lower, central, and upper estimates with a stated method and synthetic evaluation coverage. |
| Daily load pattern | An illustrative 24-hour profile and typical-day peak in kW, with its shape assumptions visible. |
| Growth | Conditional demand scenarios for Years 1, 2, and 3. |
| Productive use | Visible contributions from shops, milling, pumping, and refrigeration assumptions. |
| Explanations | A baseline demand breakdown and sensitivity to selected inputs. |
| Financial scenarios | Revenue, operating surplus or shortfall, and break-even demand under stated cost assumptions. |
| Evidence and export | Synthetic evaluation metrics, assumptions, a downloadable results table, and a printable report. |

Defer accounts, payments, live meter connections, satellite ingestion, full solar and battery optimization, multiple-country calibration, and a production database. These can enter the later roadmap. A professional layout, understandable labels, and reproducible calculations are part of the MVP.

## Demonstration communities

These are proposed fictional inputs, not measured communities. The counts below are design assumptions; energy values will come from implemented calculations.

| Scenario | Households | Shops | Schools | Clinics | Additional productive uses | Demonstration purpose |
|---|---:|---:|---:|---:|---|---|
| Demo A, small residential community | 120 | 8 | 1 | 0 | None initially | Show household demand and an evening load shape. |
| Demo B, trading community | 300 | 25 | 2 | 1 | One mill and two refrigeration units | Show the effect of daytime commercial demand. |
| Demo C, growing farming community | 450 | 18 | 2 | 1 | One mill and two irrigation pumps | Show seasonal assumptions and growth sensitivity. |

Shops exclude separately listed productive-use equipment. Each appliance or customer group must be counted once. Use labels such as “Demo B — fictional community” everywhere; do not attach simulated consumption to a real operator or village.

## Technical approach

The implemented app uses Flask with a custom responsive HTML/CSS/JavaScript dashboard and SVG charts. Python handles forecasting and financial calculations, using pandas, NumPy, and scikit-learn. Data, forecasting, growth, finance, and reporting functions are separate from the interface. This supersedes the initial Streamlit proposal to provide closer control over dashboard layout. [Flask documentation](https://flask.palletsprojects.com/en/stable/)

The processing sequence will be:

```text
Community characteristics and documented assumptions
                        |
             Input and unit validation
                        |
           Baseline and trained forecast
                        |
         Estimate, range, and daily profile
                        |
       Growth scenarios and financial scenarios
                        |
          Dashboard and downloadable report
```

Local files are sufficient for this prototype. Dataset and model versions travel with the application. The prepared demonstration should work without a live data service after dependencies are installed.

Planned project organization, created as the relevant stages begin:

```text
gridsight/
  README.md
  app.py
  requirements.txt
  config/              assumptions, feature schema, scenario definitions
  src/                 synthetic data, forecasting, growth, finance, reports
  data/                generated synthetic inputs and outcomes
  models/              trained models and metadata
  tests/               calculation, leakage, and workflow checks
  reports/             measured evaluation results and exported examples
  docs/                implementation plan, progress, decisions, data card
  submission/          demo, deck, one-page summary, disclosure, build package
```

RAMP is integrated directly through its Python package. Seven original appliance templates generate cached hourly shares from seven-day minute-level simulations. These supply daily shapes; a separate custom generator supplies monthly training outcomes. No upstream source was modified. Version and attribution details are recorded in the data card and notices. [RAMP project](https://rampdemand.org/)

## Synthetic data design

Start with 500 synthetic sites, 36 monthly observations per site, and three independently configured demonstration cases. The 500-site count is a manageable development target, not evidence that the simulation represents Rwanda.

| Data object | Grain | Essential content |
|---|---|---|
| Site profile | One record per site | Anonymous synthetic ID, archetype, household and business counts, facilities, expected connection uptake, and pre-construction appliance assumptions. |
| Simulated outcomes | One site and one month | Month since connection, customer energy demand, sector components, and simulated seasonal and adoption variation. |
| Model target | One record per site | Average monthly customer demand across the first 12 months. |
| Daily shape | One archetype and hour | Normalized hourly shares used to illustrate the distribution of daily energy. |
| Scenario configuration | One scenario | Growth, tariff, costs, collection rate, and optional supply-capacity assumptions. |
| Dataset metadata | One dataset version | Generator version, random seed, input ranges, units, synthetic origin, and assumptions. |

The generator will combine appliance power, use duration, ownership or adoption, and customer counts. It will include household differences, uncertain connection uptake, business mix, seasonality, and noise. Save the seed so the same configuration reproduces the same dataset. Design correlated quantities coherently; do not independently randomize values that should agree.

Give all synthetic records a clear provenance marker. Record assumed ranges and their rationale in a data card. Mark any later empirical inputs separately with their actual source. Do not describe assumed parameters as local measurements.

Use only information plausibly available before construction as forecast inputs. Site IDs, simulated outcomes, realized future growth, and hidden generator parameters are excluded from features. Unknown inputs need an explicit assumption or a request for completion; missing values must not silently become zero.

Keep all observations belonging to a site in the same dataset partition. Implemented split: 300 training sites, 100 calibration sites, and 100 final test sites. An internal 60-site holdout within the training partition selects the point estimator, then the chosen learned estimator is refitted on 300 sites. Calibration only widens the interval. All monthly records inherit their site's partition. [scikit-learn group splitting](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html)

## Forecasting and evaluation

1. Build a transparent baseline: connected customer counts multiplied by documented sector demand assumptions.
2. Train one modest gradient-boosting model on synthetic pre-construction features and the first-year monthly target. Compare its point predictions with the baseline.
3. Fit lower and upper quantile models for a nominal 80% prediction interval, using the 10th and 90th percentiles. Widen with nonnegative normalized split-conformal scores from the separate calibration sites. Label the point value as the central estimate.
4. Check interval ordering and the position of the central estimate. Evaluate the same interval correction, if any, that is used in the app; disclose the correction.
5. Report MAE, RMSE, WAPE when total observed demand is positive, empirical interval coverage, and average interval width on the untouched synthetic test sites. Show sample size and dataset version.
6. Report subgroup behavior across the community archetypes and stress cases with shifted adoption or consumption assumptions.

Quantile regression is supported by scikit-learn, including an example that evaluates prediction intervals. A nominal interval level is a target, not a guaranteed coverage result. [scikit-learn prediction interval example](https://scikit-learn.org/stable/auto_examples/ensemble/plot_gradient_boosting_quantile.html)

There is no preselected accuracy claim. If the trained point model does not outperform the baseline on validation data, retain the stronger point estimator and explain the comparison. If uncertainty estimates perform poorly, show the measured limitation and label fallback scenario bands as assumption-based. Do not present arbitrary percentage bands as a calibrated confidence interval.

Testing a model on data from its own simulator measures consistency with that simulator. Include at least one shifted-assumption stress case, and carry the real-data validation gap into the demo and pitch. The prior discussion describes validation against held-out metered sites as a challenge requirement; synthetic evaluation does not fulfill that requirement. Keep it open until the original brief and an acceptable evidence path are confirmed.

## Growth, explanations, and financial calculations

Growth will initially be scenario-based. Use the Year 1 estimate as the base, then compute Years 2 and 3 from displayed household, business, and productive-use assumptions. Do not label these scenarios as an independently validated growth forecast. Additional equipment is added once, with a stated adoption year.

The daily profile must conserve energy: hourly kW multiplied by interval duration must sum to daily kWh. The maximum hourly value is an illustrative typical-day peak, not a measured annual maximum. Distribution losses, if included, convert customer energy into required supply energy; they must not also be subtracted from that same customer energy before calculating revenue.

Explain the baseline's sector contributions directly. For the trained model, show how predictions change when selected input values change, holding other inputs fixed. Call this sensitivity, not proof of causation. Do not pass a baseline breakdown off as an exact decomposition of the machine-learning prediction.

Use the following transparent monthly scenario calculations, with one consistent declared currency:

- `collected revenue = served customer kWh × tariff per kWh × collection rate`
- `variable operating cost = served customer kWh × variable cost per kWh`
- `operating surplus = collected revenue − variable operating cost − fixed operating cost`
- `cash after stated financing payment = operating surplus − monthly financing payment`
- `break-even served kWh = (fixed operating cost + monthly financing payment) / (tariff × collection rate − variable cost per kWh)`, only when the denominator is positive.

Compare demand factors 0.6, 0.8, 1.0, and 1.3. Tariff and cost inputs are editable simulation assumptions, not verified Rwanda tariffs or investment recommendations. Keep demand fixed when adjusting tariff unless a separately disclosed elasticity assumption is implemented.

If users enter a monthly deliverable-energy limit, cap served energy at that limit and show the unserved remainder. An optional firm available-power input can flag a typical-day peak shortfall; do not equate installed solar nameplate kW with firm available power. These are screening scenarios, not an hourly solar and battery dispatch model. Report an operating surplus or shortfall rather than declaring a project financially viable; the MVP omits a full investment appraisal.

Check zero demand, zero collection, zero tariff, nonpositive break-even margins, missing inputs, negative counts, extreme growth, and insufficient supply. These cases must produce understandable outputs without crashes or invented values.

## Sequential implementation steps

This is the user's 12-step product sequence. Product steps use P01–P12; delivery gates use D01–D07. Earlier progress entries retain their original stage numbers as historical records.

| Step | Work | Implemented output / status | Completion check |
|---|---|---|---|
| P01 | Select Rwanda Case | Three fictional Rwanda-context communities: residential, trading and agricultural. | Explicit synthetic labels; no claim of a surveyed or pilot site. |
| P02 | Collect Data | 500 generated communities and 18,000 monthly records; real operator collection remains open. | Reproducible seed, provenance and clear separation from empirical evidence. |
| P03 | Clean & Prepare Data | Typed features, input validation, monthly-to-first-year targets and site-grouped partitions. | Finite values, bounded features, integer counts, unique site-months, complete 36-month series, units and no site leakage. Real-source cleaning remains future work. |
| P04 | Build Baseline | Transparent sector-demand calculation plus RAMP daily shapes. | Hand-worked examples and daily energy conservation pass. |
| P05 | Train ML Model | Baseline comparison and gradient-boosting models trained on synthetic pre-construction features. | Model selection within training; saved reproducible model artifact. |
| P06 | Validate Model | 100 untouched synthetic test sites, baseline comparison, subgroup and shifted-outcome metrics. | Recomputed reported metrics; real metered-site validation remains open. |
| P07 | Generate Confidence Range | Nominal 80% **prediction** range with separate calibration and observed test coverage. | Ordered bounds, finite nonnegative outputs and honest coverage. Not a guarantee or a confidence interval for a mean. |
| P08 | Forecast Demand Growth | Years 1–3 with household/business growth and productive-equipment adoption. | Year 1 anchored; additions occur once; assumptions and limitations displayed. |
| P09 | Add Explainability | Baseline sector contributions and one-input-at-a-time model sensitivities. | Units, input increments, attribution limits and noncausal interpretation visible. |
| P10 | Add Financial Analysis | −40%, −20%, base and +30% demand; revenue, cash, debt coverage, break-even and supply shortfalls. | Independent formula tests; downside repayment and faster-demand capacity risks explicit. No unsupported viability verdict. |
| P11 | Build Dashboard | Primary developer and secondary investor/lender workspaces, scenario persistence and role-specific exports. | Shared results and role behavior pass API/logic tests; visual interaction checks are still open. |
| P12 | Test Prototype | Automated data, model, finance, API and role tests; documented remaining browser checklist. | Browser walkthrough, responsive layout, save/restore and actual downloads must pass before freeze. |

For statistical integrity, interval fitting/calibration happens **before** the untouched test-set evaluation even though the user-facing walkthrough discusses validation before presenting the range. Test outcomes must never tune the interval. Product steps P06/P07 are complete only for synthetic evidence; this does not close the real-data gap.

| Delivery gate | Work | Completion check |
|---|---|---|
| D01 | Feature Freeze | Required prototype features pass the browser checklist; freeze a release snapshot. |
| D02 | Polish Product | Verify readable laptop/mobile layout and focused regression checks. |
| D03 | Record Demo | Playable, readable 3–5 minute video; state synthetic-data limits. Deferred by user. |
| D04 | Prepare Pitch Deck | Editable deck and at-most-five-slide PDF matching the frozen evidence. Deferred. |
| D05 | Prepare One-Page Summary | Required fields fit a readable single-page PDF. Deferred. |
| D06 | Prepare Disclosure | Accurate prior/sprint work, tools, code, licenses, data and validation limits. Final document deferred. |
| D07 | Check Final Package | Files open, required links work and current submission requirements are verified. Submission itself needs confirmation. |

The finishing order remains **Feature Freeze → Polish Product → Record Demo → Prepare Pitch Deck → Prepare One-Page Summary → Prepare Disclosure → Check Final Package**.

## Screen plan

| Area | Main contents |
|---|---|
| Community | Fictional site selector, editable customer groups and facilities, input assumptions. |
| Demand | Monthly and daily estimate, prediction range, typical-day profile, baseline comparison. |
| Growth and scenarios | Years 1–3, productive-use changes, revenue and cost sensitivities, supply screening. |
| Evidence and report | Data origin, evaluation metrics, drivers, limitations, download and print actions. |

A persistent synthetic-data label should be visible without opening the evidence area. Prioritize readable charts and a complete story on the demonstration laptop; check a narrower layout during polish.

## Safe meter-data sharing proposal

Prepare a short future-integration proposal during the dashboard and evidence stage (P11). It should cover operator permission, a common schema, removing direct identifiers, aggregating to appropriate site and time levels, suppressing small identifiable groups, controlled access, retention limits, and a data-quality review. Removing names alone does not establish anonymity. The MVP itself uses no personal meter data.

Describe how a future operator dataset will replace the synthetic input adapter while preserving site-separated evaluation. The public demonstration dataset must remain separate from restricted operator data.

## Demo and submission content

The kickoff screenshots supplied in “Review energy hackathon streams” specify a required 3–5 minute demo link, a pitch PDF of up to five slides, a one-page PDF summary, and a disclosure. A separate pitch video and build files are optional. Our plan includes build files for reproducibility.

### Demo video

Aim for four minutes, leaving room within the stated limit:

| Time | Story |
|---|---|
| 0:00–0:30 | Explain the developer's planning problem and the synthetic demonstration. |
| 0:30–1:10 | Select Demo B and inspect community inputs. |
| 1:10–2:00 | Generate demand, inspect the range and daily load pattern. |
| 2:00–2:50 | Change growth or productive-use assumptions, then show lower-demand revenue risk. |
| 2:50–3:30 | Explain drivers, show measured synthetic evaluation, and export results. |
| 3:30–4:00 | State the real-data validation gap and the next pilot milestone. |

At the Record Demo gate (D03), check available recording tools. If direct recording or narration is unavailable, complete the script, screenshots, and rehearsal package, then identify the exact recording action still needed. Mark the video complete only when a playable file exists. Hosted links require a suitable publishing destination.

### Pitch deck

1. Problem and users: decisions developers make before construction.
2. Solution: GridSight's workflow and a screenshot from the built product.
3. Evidence: synthetic dataset, baseline comparison, measured metrics, uncertainty behavior, and the real-data gap.
4. Cost and sustainability: prototype operating assumptions, proposed business model, and a budget for the next validation phase.
5. Scale, impact, and team: what must be locally calibrated, the intended benefit, next milestones, and actual team members.

Use screenshots and numbers from the frozen build. Potential impact is a hypothesis until measured. Do not invent deployment partners, customer adoption, financial savings, model accuracy, or team credentials.

### One-page summary

Include problem, users, solution, cost estimate, a 6–18 month roadmap, track, and setting. Suggested roadmap: months 0–6 obtain permissioned data and validate; months 6–12 run a small operator pilot; months 12–18 test transfer to another context and evaluate a service offering. Label this as the proposed next phase.

### Disclosure

Keep a running record while building, then finalize it after the one-page summary. Include what existed before the sprint, what was actually completed during it, AI assistance, libraries and versions, any reused code and licenses, synthetic generation assumptions, actual datasets used, and validation limitations. Do not infer that all work occurred within the sprint simply because it is in this project folder.

## Timing and priorities

The supplied kickoff slide gives Sunday 1 November 2026 at 12:00 PM US Eastern as the deadline, which converts to 19:00 in Kigali on that date. Confirm the current submission portal when preparing the package; its live page could not be retrieved during this planning session. This plan does not reset the original 48-hour sprint clock.

Protect roughly the final third of the remaining work window for feature freeze, polish, recording, documents, and packaging. If time becomes tight, simplify the estimator or optional daily-profile detail before dropping uncertainty, validation transparency, or required submission materials. Keep the three prepared scenarios available locally for the demonstration.

During each step, provide: what was completed, the concrete artifact or preview, what was checked, any unresolved limitation, and the next step number. Record progress immediately in `PROGRESS.md`.

## Completion conditions

The local MVP is complete when a new user can select or enter a community, generate coherent estimates and ranges, explore growth and financial scenarios, understand key assumptions, and export matching results. The prepared demonstration must run after a clean restart using documented setup instructions.

The submission package is complete when the playable demo, deck PDF, one-page PDF, disclosure, and build package have been checked. “Package complete,” “public links ready,” and “submitted” are distinct statuses; record only what has actually happened.

Real-world forecasting validation remains open while only synthetic consumption is available. That gap does not prevent building the demonstration, but it limits the claims and may affect challenge compliance.

## Sources and evidence status

- User direction in this task: synthetic data, plan first, build one step at a time, and retain progress.
- Earlier conversation: “Review energy hackathon streams,” reviewed 30 October 2026. It supplies the GridSight name, mini-grid demand focus, Rwanda context, and earlier project plan.
- User-provided kickoff screenshots: “Play Fair, Build Bold” and “What to Submit,” visually inspected 30 October 2026. These support the stated rules, formats, and screenshot deadline.
- Earlier discussion of Problem Brief 03: carries requirements for demand, growth, uncertainty, explanations, metered-site validation, and safe sharing. The original brief itself was not available in the retrieved attachments, so exact brief wording and scoring must be checked before making a full compliance claim.
- [Flask documentation](https://flask.palletsprojects.com/en/stable/): implemented local web application approach.
- [RAMP project](https://rampdemand.org/): installed dependency used to generate daily load shapes.
- [scikit-learn group splitting](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html): grouping observations by site.
- [scikit-learn prediction intervals](https://scikit-learn.org/stable/auto_examples/ensemble/plot_gradient_boosting_quantile.html): quantile-based interval approach.
