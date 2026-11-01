# GridSight decision log

## 1 November 2026 — prepared evidence integration (local review)

- Keep the deployed green/light app, roles, eight-country location hierarchy and
  20-input engineering calculation. This integration is local only: no training,
  commit, push or Render redeployment.
- Attach Bugesera sector context after forecasting, not as replacement service-area
  inputs. Use explicit district/sector hierarchy and mark manually typed names
  unverified. Missing labels and inventories remain unavailable, not zero.
- Display the KIT three-site kW benchmark separately from monthly-model validation.
  Include both baseline models, poor-transfer errors, coverage, faults, attribution
  and Haiti's non-East-African scope. Never attach KIT outcomes to Bugesera rows.
- Show hourly-data preparation as completed, real-data prediction-model training
  as not run, and current-model monthly/growth/confidence validation as pending.
- Export reviewed compact summaries and source dictionaries only, with mixed rights
  retained. Preserve all public meter-upload guards. See PREPARED_EVIDENCE.md.

These entries preserve the current working choices. User instructions override proposed defaults. Record later changes with their reason and affected steps.

| ID | Date | Decision | Basis |
|---|---|---|---|
| D01 | 30 October 2026 | Use GridSight and the tagline “See demand before you build.” | Continuation of the earlier naming discussion; “AI” was removed from the name. |
| D02 | 30 October 2026 | Plan first, then implement one numbered step at a time. | Explicit user instruction. |
| D03 | 30 October 2026 | Use synthetic data for the first MVP. | Explicit user instruction, interpreting “Sentitic data” as synthetic data. |
| D04 | 30 October 2026 | Keep a Rwanda demonstration context with fictional communities. | Earlier geographic focus; avoids presenting generated values as actual village observations. |
| D05 | 30 October 2026 | Start with 500 simulated sites, 36 months, and three separately configured demo communities. | Proposed development scale; adjustable during data design if runtime warrants. |
| D06 | 30 October 2026 | Use Python, Streamlit, pandas, NumPy, scikit-learn, and Plotly. | Proposed continuation of the earlier Streamlit approach; local operation and a compact architecture. |
| D07 | 30 October 2026 | Build a baseline before a trained model; compare results honestly. | A useful estimate needs a transparent reference and measured evaluation. |
| D08 | 30 October 2026 | Keep site records together across train, validation, and test partitions. | Avoid leaking one site's history into evaluation on that same site. |
| D09 | 30 October 2026 | Use a nominal 80% quantile prediction interval and report measured synthetic coverage. | Proposed uncertainty method; no guarantee of real-world coverage. |
| D10 | 30 October 2026 | Treat Year 1–3 growth and financial projections as conditional scenarios. | Generated data cannot establish actual demand growth or financial viability. |
| D11 | 30 October 2026 | Use first-year average monthly customer energy as the main target; keep kWh and kW distinct. | Consistent interpretation across data, forecasts, charts, and finance. |
| D12 | 30 October 2026 | RAMP may inform the generator; direct integration is optional. | User allows other mini-grid systems; a dependency should improve the result enough to justify the work. |
| D13 | 30 October 2026 | Preserve the requested finishing order exactly. | Feature freeze, polish, demo, deck, one-page summary, disclosure, final package. |
| D14 | 30 October 2026 | Record tool, data, and prior-work details throughout implementation. | Final disclosure should reflect actual work and timing. |
| D15 | 30 October 2026 | Keep all project writes in `gridsight/`; preserve synced references. | Workspace instructions. |
| D16 | 30 October 2026 | Track prototype completion separately from real-site validation and actual submission. | Avoid overstating readiness or evidence. |

## Claims to preserve

- All demonstration communities are fictional.
- All generated consumption values and simulated outcomes are synthetic.
- Evaluation results must be computed by the implemented pipeline before they are quoted.
- Real metered-site validation remains an open requirement from the earlier discussion.
- Cost, tariff, growth, and adoption inputs are assumptions unless supported by a recorded source.
- A playable video, public link, or completed submission must exist before it is marked done.

## Future change record

Implementation updates on 30 October 2026:

| ID | Updated decision | Reason and affected steps |
|---|---|---|
| D17 | Complete the product in this session; defer presentation deliverables. | Latest user direction supersedes pausing after each numbered step in D02. |
| D18 | Use Flask and a custom responsive frontend, retaining Python calculations. | Supersedes D06's Streamlit UI proposal for dashboard layout control. |
| D19 | Team has three members; names can wait. | User clarification; no team feature needed for the MVP. |
| D20 | Use RAMP directly for seven normalized daily sector shapes. | Supersedes D12's optional reference. Monthly training data remains generated separately. |
| D21 | 300 training, 100 calibration, 100 test sites; select model within training. | Separates point selection, interval calibration and evaluation. |
| D22 | Pin NumPy 2.3.5 and pandas 2.3.3 for RAMP 0.5.0. | Newer versions removed APIs RAMP uses. No upstream source edits. |
| D23 | Keep browser QA open while admin-policy verification is unavailable. | No browser-control workaround; API, calculation and export tests continue. |
| D24 | Provide exactly two first-class workspaces: Mini-grid developer and Investor / lender. | Explicit user clarification. Separate navigation, overview, project-input treatment, financial editing and report emphasis; use one calculation engine. |
| D25 | The local role selector is an audience view, not access control. | Accounts remain deferred. Shared scenario edits are disclosed; investor views do not expose community/technical editing controls. Production ownership, permissions, private review scenarios and audit history require a separate implementation stage. |
| D26 | Investor screening must expose missing evidence, not imply investment approval. | All site data is synthetic. No capital budget or full investment model is supplied; do not invent bankability scores, IRR, NPV or verified diligence. |
| D27 | Adopt the user's exact 12-step product sequence, with developer primary and investor/lender secondary. | Latest clarification. Product tracking uses P01–P12 and finishing gates D01–D07; historical records are retained. All requested user questions map to features and evidence limits in the plan. |
| D28 | Explain faster-demand risk as well as downside risk. | The existing +30% stress case now explicitly displays cash, unserved energy and peak shortfall. It is not a growth-rate forecast; three-year growth remains a separate conditional scenario. |
| D29 | Show central customer demand per day, week, month and year in both role overviews and exports. | User request. Convert the first-year monthly estimate using 365 days/year, 12 months/year and 7 days/week. These are average equivalents, not independent date-specific forecasts. Keep financial calculations and calibrated uncertainty on their existing monthly basis. |
| D30 | Keep dashboard copy brief and direct; move extended methods into native disclosure sections. | User asked for simpler, catchier text. Removed duplicate hero blocks and shortened navigation, while retaining synthetic/risk notices, units, all calculations and detailed exports. |
| D31 | Add four chart horizons using the existing forecast; do not invent temporal variation. | 31 October 2026: user requested weekly, monthly and yearly charts. Daily retains hourly kW; week/month show uniform kWh/day, and year shows uniform first-year kWh/month. The average month includes an explicit partial final day so weighted totals match D29. Bands scale the monthly range, not separately calibrated horizon uncertainty. Both roles share the chart, and tab changes leave form drafts untouched. |

When changing a decision, retain its original meaning here and add a dated entry with the replacement, reason, and affected steps. If a change invalidates a completed check, reopen the corresponding tracker item and rerun the relevant check.

## Feasibility completion — 31 October 2026

- D32: User authorized completing all previously partial features. Add a fifth Feasibility area to both role workspaces, with explicit Low / Expected / High factors separate from the model prediction range.
- D33: Supersede D31's flat yearly chart with a normalized monthly growth path. Each year's monthly mean equals the existing annual projection; Year 1 cards retain their totals. Negative growth is allowed. Add cold-room adoption alongside mills/pumps.
- D34: Compare productive uses as independent one-unit opportunities, ranked by added grid operating contribution. Optional support payback is developer-side, not enterprise ROI. Supply-constrained results remain provisional.
- D35: Quantify unused capacity and shortfalls together. Capacity-linked budget × unused energy share is an exposure proxy, not wasted or recoverable cost. Do not infer installed solar/battery sizes or reliability.
- D36: Extend D26 with optional user-entered capital/support budgets and a clearly bounded 36-month, pre-financing/pre-tax NPV. Blank is unknown, not zero. No verified quotation, whole-life investment valuation or approval is claimed.
- D37: Deliver standalone downloadable HTML plus browser print/PDF and an expanded CSV/JSON ZIP. All outputs and Save/Restore carry the exact planning assumptions. Guard unsaved forms from cross-page/community changes rather than silently discarding inputs. Browser QA remains open after supported discovery failed; no workaround was used.
- D38: Use the user's exact heading “Low / expected / high range” in both overview summaries, the Feasibility chart and downloaded report. This is a wording-only change; preserve case factors, forecasts and the distinction between scenario ranges and prediction intervals.
- D39: Adopt all 13 items in the user's product comparison as explicit acceptance criteria (R01–R13). Preserve the distinction between implemented synthetic features, real/public data integration, measured consumption validation, thin-data capability, country transfer and commercial traction. The previous feature-completion statement does not establish these additional outcomes.
- D40: Treat “Developer” as the intended buyer until the user clarifies whether a developer has actually paid. Record per-project assessment and recurring portfolio access as a proposed commercial model only; no verified customer, price, revenue or competitor capability is inferred.
## Public context and remaining software — 31 October 2026

- D41: Implement the user’s remaining software requirements locally, including live locations. Continue the Sites local-only workflow; no cloud account, publishing, customer outreach or commercial commitments.
- D42: “Live locations” means on-demand place lookup and a user-selected planning map, not live mini-grid telemetry or tracking. Keep fictional demand distinct from real coordinates. Device position is optional, one-shot, rounded and draft-only until applied; map loading is separately opt-in.
- D43: Integrate public World Bank national statistics and Open-Meteo/GeoNames places with attribution, source year, retrieval time and cache/provenance. These are context only and never silently become local demand features, training labels or evidence of accuracy. Review hosted-provider terms before commercial use.
- D44: Missing inputs require a household anchor plus explicit review of proposed planning placeholders. Known zero remains distinct from unknown. Persist assumed-field flags and state that model intervals do not cover uncertainty in guessed inputs.
- D45: Add Uganda/UGX as a second configured demonstration. Preserve shared energy priors and synthetic model with transfer warnings. Country changes clear money values, capital/support budgets and location; never silently convert or relabel existing amounts.
- D46: Provide a frozen-model diagnostic for permission-attested, anonymized site aggregates over 12 complete historical months. Validate input shape and periods; report hashes and metrics without retraining or a pass/approval label. Authenticity, independence, outages and sample representativeness still need real evidence.
- D47: Monetary feasibility fields use neutral `_amount` keys and exported monetary rows include a currency code. This changes v1.2 export field names, not calculation mathematics. Source-version and input provenance remain explicit.
- D48: Expose the proposed developer-paid assessment, portfolio subscription and lender review offer. Keep prices, willingness to pay and paying-customer status unconfirmed until supported.

## East Africa redesign — 31 October 2026

- D49: User explicitly selected **all eight EAC countries**: RW, UG, KE, TZ, BI, SS, SO and CD. This supersedes D45's two-country scope, not its no-FX/no-unvalidated-accuracy rule.
- D50: Default to location discovery, not a fictional dashboard. Keep synthetic examples available only through an explicit demo action. Reuse the local Flask app and Sites local-only workflow; do not publish.
- D51: Use attributed GeoNames country snapshots for offline administrative/settlement browsing. Store canonical IDs, source hashes, retrieval dates, record modification dates and licence. Use local equivalents and clearly label older/incomplete mappings; never invent sectors or current boundary coverage.
- D52: Rural-first is a search heuristic: capitals/seats, known ≥20,000-person settlements and explicitly urban-labelled administrative areas/descendants are excluded. Unknown population stays unknown. Missing utility data is never proof of no grid; geography cannot establish eligibility.
- D53: Grid-access claims are user-reported with source/date, not independently verified. Connected sites are visibly outside the unserved-site focus; planned expansion triggers grid-arrival review. Correcting coordinates clears stale grid evidence.
- D54: A new project must not silently inherit counts, finances, capacity, budgets, grid claims or public context. Require a household anchor and review of any proposed missing inputs. Restore the previous valid project on failure.
- D55: Retain the same synthetic Rwanda-context model/energy priors with country-specific transfer warnings. Support local currency entry without exchange-rate conversion. Widen generic per-kWh numeric entry ceilings to accommodate currencies; ceilings are software bounds, not tariff recommendations.
- D56: Financial zero placeholders are not evidence of viability. New-site supply/money starts at zero and the dashboard requires completing these assumptions before interpretation. Keep all forecast horizons, scenario/uncertainty distinctions and existing report logic.
- D57: Browser access failed again at supported discovery. Proceed with source, handler, API, offline-data and live-local-service tests; do not bypass the browser tool or claim visual QA. Leave acceptance and real-site validation explicitly open.

## Rwanda data-driven selection — 31 October 2026

- D58: Latest request supersedes D49: active country Rwanda only; East Africa remains future architecture. No external deployment.
- D59: Supersede the review gate in D44/D54: selecting a place may initialize a clearly labelled preliminary screen automatically. Never imply user review occurred; manual survey fallback remains. New-site failure restores the prior project.
- D60: Import actual Google Open Buildings v3 points (confidence >= 0.738), clip to geoBoundaries Rwanda ADM0, and query a 500 m radius. A 70% residential fraction and one household/building are editable planning assumptions, not measurements. Cap at model input limits and disclose caps. No detections/unavailable coverage uses a labelled 150-household placeholder, not inferred local demand.
- D61: OSM amenity/shop objects are incomplete proxies, not verified operating customers; absent objects remain unknown with explicit defaults. MININFRA 2022 Bugesera records provide sector-level historical context only. Ambiguous household-energy counts are excluded; no current grid status is inferred.
- D62: Supersede D56 for automatic screens: use explicitly illustrative Rwanda supply/financial defaults so all scenario panels work immediately. These are not public cost benchmarks, quotations, current tariffs or viability evidence. Optional capital budgets remain unknown. No previous project values are carried over.
- D63: Source manifest marks collected, missing, partner-needed and login-gated layers separately. Do not count metadata/reference links or old synthetic templates as actual observations. Preserve licences/checksums/dates and avoid raw government redistribution while terms remain unspecified.
- D64: Original synthetic training data/model remain unchanged. Collected data initializes inputs, not labels or real-site validation. Profile evidence is generated server-side and included in analysis/report exports. Source uncertainty is outside the nominal model range.
## Connection growth and five deliverables — 31 October 2026

- D65: Add optional connection-growth inputs; enable for new location projects and explicit demos, preserve old saved/API calculations by default. Keep the existing frozen model and data unchanged.
- D66: Use the model estimate as an assumed mature reference, disclosed as an unvalidated reinterpretation. Smooth connection, appliance and non-household ramps are scenario assumptions, not fitted Rwanda rates; no measured growth claim.
- D67: Compute first-year energy and cash from the monthly path, including monthly supply caps. Preserve 365/12-day energy months; date labels are service-period anchors, not exact billing-month totals. Apply existing annual growth only as additional underlying expansion.
- D68: Separate propagated reference bounds from low/expected/high demand multipliers. Neither the adoption curve nor its bounds inherit synthetic model-validation claims.
- D69: Show the five deliverables in Evidence and reports. Held-out authentic meter validation remains pending. The annual CSV diagnostic evaluates the frozen reference, not the adoption curve; future curve study needs independent site-month records.
- D70: Provide a downloadable sharing proposal grounded in operator-side aggregation, disclosure-risk review and independent holdouts. Clearly distinguish proposed transfer/security/retention controls from the local in-memory MVP; do not claim compliance or anonymity guarantees.
- D71: Keep both roles on one scenario; developer controls adoption, investor reviews it. Apply both same-page forms together so edits cannot be lost. Persist exact applied inputs in save/restore and all reports.
- D72: Sites local workflow preserves the existing task-first layout and app. Automated/live checks pass; supported browser initialization still fails. Do not bypass it or mark visual QA complete.


## Twenty-feature East Africa interface — 31 October 2026

- D73: Latest request supersedes D58's Rwanda-only UI: restore all eight previously selected EAC countries. Use Country → District → Sector → Cell, with source-supported equivalents and visible gaps. Rwanda cells are ADM4, not settlement records. No map/device-location/coordinate-entry UI.
- D74: Source gaps permit three unverified administrative names. Store no invented coordinates; do not attach local public evidence to name-only locations. Rwanda still has the only imported building/facility pipeline; new countries use explicit defaults and need field surveys.
- D75: Use the supplied dark/collapsible numeric-panel references within the existing local app. Preserve light analysis panels and shared roles. No publishing, new task or cloud accounts.
- D76: Implement all 20 features as a separate transparent engineering path, enabled for new projects/demos. Keep old saved/API behavior when detailed is absent/disabled, with explicit opt-in. Do not retrain the frozen nine-feature model or relabel its metrics as new-model validation.
- D77: Connection rate is the starting service-Month-1 share; yearly new household connections are linear and capped at service-area households. Appliance ownership grows proportionally; business growth applies to shops/productive equipment, not schools/clinics. Elapsed time advances the 36-month window. Do not also apply old household growth, appliance index or S-ramp.
- D78: Agriculture is twelve repeating service-month factors, applied only to mills/pumps. Not calendar-specific weather, crop evidence or guaranteed monotonic growth. Use 365/12-day energy months and illustrative sector timing, not motor-start or hourly-dispatch engineering.
- D79: Income/connection fee support explicit affordability ratios. Tariff affects revenue/bills, not physical energy. Unknown income/fee stays null; zero stays zero; zero income gives no ratio. One-time connection fees are excluded from recurring cash/debt coverage.
- D80: Detailed Low / expected / high uses the same editable scenario multipliers across charts/reports. No confidence-interval or 20-feature ML accuracy claim. Plain-language drivers and feature-use inventory explain calculation limits.
- D81: Save/restore and report/export use applied nested inputs, not drafts. Lender demand profile remains read-only; shared finance may change. Both roles calculate the same scenario.
- D82: 445 automated checks and live local report/archive checks pass; original model/data hashes unchanged. Browser initialization still fails. Report visual QA unverified and leave feature freeze/field-validation gates open.
- D83: User prioritized held-out metered validation in East Africa and has no operator data. Research public sources, but do not substitute synthetic data, literature averages, household surveys or incompatible current measurements for monthly customer-side mini-grid kWh.
- D84: v1.7 uses the exact detailed engineering calculation. Require complete dated pre-connection inputs, whole-site holdouts, attestations and hashes. No fitting or automatic authenticity/accuracy pass.
- D85: Scale 365/12-day energy to actual calendar days. Exclude/report incomplete, estimated and outage-affected months, never impute zero. Score site/country/service year; annual growth needs complete adjacent years. Pooled months are not independent sites.
- D86: Source register records Renewvia's agreement requirement, Tanzania current-data units/non-commercial licence, later survey timing and Uganda proprietary records. No agreements, outreach, commercial reuse or imports occurred. Priority 1 remains partially open.
- D87: Uploads stay in local memory; downloadable anonymous reports require disclosure review. Browser security-check failure is not bypassed. 507 automated checks do not establish genuine metered accuracy.
- D88: v1.8 addresses priorities 2/3 as separate statistical workflows, not relabelling low/high scenarios. Input simulation uses explicit triangular group assumptions and coherent paths. No calibrated probability without empirical error calibration.
- D89: Learn a fixed piecewise-log aggregate growth correction on fit sites only; knots 1/6/12/24/(36), fixed ridge 0.1 and bounded corrections. No forced growth; no 24-to-36-month extrapolation. Meter totals do not identify connection/appliance/business mechanisms individually.
- D90: Separate fresh whole-site fit/calibration/test groups; complete 24/36-month histories and predeclared settings. Calibrate maximum normalized path exceedance per site with rank ceil((n+1)*coverage). Refuse finite bands with insufficient independent calibration sites.
- D91: Report observed full-path coverage plus descriptive monthly coverage, widths, exact site-level coverage interval, stage/country/site errors and original-versus-fitted growth. Exchangeability, source authority and split timing are attestations, not verified facts; country transfer is flagged.
- D92: Statistical results remain local in-memory batch studies or explicit uncertainty downloads, not automatic forecast/finance changes. No genuine real-data fit/calibration run is claimed. 581 automated checks; browser QA remains unavailable.
- D93: v1.9 financial references are historical regional comparators, not local quotations. Keep the AMDA connection denominator explicit; no kWp-to-firm-power substitution, auto-FX, or double-counted OPEX. CLASP/Practical Action/REG context does not supply site runtime or business-uptake coefficients.
- D94: Bind user-declared source records to the exact applied project and field value/unit; detach on change. Date/sample/permission checks do not authenticate evidence. Preserve records in intentional saves/reports, not an undisclosed server database.
- D95: Productive-use downside cases are usage assumptions, not probabilities. Capital-allocation proxies are not demonstrated savings; retain a prospective controlled-impact protocol and null measured-savings status.
- D96: Recalibration versions use the existing current-model growth/conformal study, not synthetic rebuilding or a new 20-input trained estimator. Freeze protocol, thresholds, data IDs and code/runtime before outcomes. Do not invent universal acceptance thresholds.
- D97: Explicit private registry writes use immutable, owner-only, hash-chained events; guard prior test-ID use, failed/undefined metrics, code changes and concurrency. Human review/local promotion/rollback never silently deploys a model. Alias/external reuse and source authenticity remain governance responsibilities.
- D98: Browser evaluations are exploratory and cannot forge registry preparation or approval. No real-data release or automated schedule was created. 690 automated checks pass; focused desktop browser checks now available, with broader release QA still open.
- D99: v1.10 redesign interprets Power BI as an interactive analytical presentation inside the existing local app. No Microsoft account, embedded report, external data transfer or hosted publication. Navy/coral inspiration does not copy hackathon registration or marketing content.
- D100: Display filters select exact Python feasibility scenario/year records; energy-period cards divide annual energy by 365, 365/7, 12 or 1. Cash cards remain monthly averages, annual debt coverage comes from Python, and no display filter mutates saved project inputs or exports. Fixed Year-1 profile/mix panels explicitly disclose their separate scope.
- D101: New 36-month chart supports mouse, keyboard, slider and tabular access. Local responsive checks found/fixed narrow-screen overflow. The user's existing unsaved project tab remains untouched; preview uses a synthetic demo. 712 automated checks, focused browser checks and unchanged model/dataset hashes do not close empirical or full-release QA gates.
- D102: User rejected the navy/coral colouring and requested the previous palette. Restore original green/light colours (including chart categories and browser theme colour), retaining interactive layout/filters and the pre-existing dark input rail. Colour-only follow-up; no model, data or calculation changes.
- D103: Restore the original GridSight arrow mark and wordmark proportions to match the existing arrow favicon and green/light palette. Keep the established name and “See demand before you build” tagline. Interactive features and calculations remain unchanged.
- D104: Match the location and shared project-input panels to GridSight's forest-green sidebar and lime accents. Replace charcoal/red field, action, slider and disclosure colours; retain readable disabled controls and keyboard focus. Styling only: no location logic, inputs, data or calculations change.
- D105: Make the five brief deliverables a first-class Evidence review and a single downloadable pack, retaining the existing local app and green brand. Reuse final applied feasibility scenarios for all new period/month tables; do not change model or forecast calculations.
- D106: Artifact availability is not empirical completion. Metered validation stays blocked; range/growth calibration stays pending; forward months for already-connected sites are not relabelled as first years. Blank templates, protocols and the operator-sharing worksheet contain no invented observations or permission. User-attested batch studies remain separate from project certification.
- D107: Preserve the ordinary export contract and add an explicit deliverables-pack route. Include an offline review and the full existing analysis, exact inputs, finance and provenance. Input fingerprints aid reproduction, not evidence authentication. Browser QA uses a separate synthetic preview, preserving the user's active project.
- D108: Connect the user's existing Bugesera ranking without silently redesigning its objective. Reproduce scores against pinned public features, expose the historical-grid direction and missing-equipment assumptions, and fail closed on stale files. Administrative sectors are screening context only; never use their totals as service-area demand inputs.
- D109: Expand the sharing proposal into an operator pilot request and blank review packet. No partner commitment, data-sharing permission, secure hosted portal or sent outreach is implied. Keep public-demo upload guards. Map Brief 03 weights to available evidence and gaps, not self-awarded scores. This change is local, not a public deployment.
# Real hourly evidence integration — 1 November 2026

Add the completed public-data experiment as evidence and downloadable data, not
as the monthly planning engine. The user requested integration and approved
publication after tests. Keep model selection fixed to validation MAE; show all
test comparisons, actual/predicted columns and the limitations of same-site
hourly testing. Preserve the earlier whole-site benchmark separately. No model
pickle is loaded, no target is invented and no household/monthly/growth accuracy
is inferred from the KIT records. See OPERATIONAL_EVIDENCE.md.
