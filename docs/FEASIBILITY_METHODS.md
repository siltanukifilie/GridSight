# Feasibility engine v1.6

## Detailed engineering method (default for new projects)

Detailed mode takes precedence over legacy model/adoption calculations. It is not a model trained on the 20 features. Let m be the service month (elapsed completed months + forecast month), N service-area households, u starting connection share and n expected new connections/year.

- Connected households C(m) = min(N, N × u + n × (m−1)/12). Fractional expected connections are allowed.
- Household daily energy per connection H(m) = sum(appliance units × power W × effective hours/day / 1000) × (1 + appliance adoption rate)^((m−1)/12).
- Household monthly energy = C(m) × H(m) × 365/12.
- Businesses and productive equipment use count × kW/unit × effective hours/day × 365/12, compounded with the business-growth rate. School/clinic loads use their entered counts and unit rates without business-growth scaling.
- Only mills and pumps receive the entered repeating service-month agricultural multiplier. Defaults are 1; no observed crop/weather seasonality is asserted.
- Additional productive equipment begins once in its selected service year. It is not delayed again when the forecast window starts later.
- Expected total is the component sum. Low/high multiply that whole monthly total with the editable scenario factors. They are not confidence or prediction bounds.
- Forecast Year 1 is the next twelve months, not necessarily the first year since connection. Period cards and the typical-day profile use that year's monthly mean. The 36-month curve and financial cases use each monthly value and supply cap.
- Income and tariff calculate average household bill / gross income. Connection fee / gross monthly income expresses a one-time burden. Unknown/zero income has no ratio. These fields do not infer elasticity, willingness to pay, collection probability or credit eligibility. Connection fees are excluded from recurring cash.
- Old household-growth %, appliance index and S-curve fractions are not applied in this mode. This avoids counting adoption twice.
- Hourly sector shapes remain illustrative RAMP timing. User-entered operating hours determine energy, not actual start/stop times or simultaneous motor loads.

The API `feature_inventory` maps all 20 requested features to their exact fields and uses. `detailed` stores the applied appliance/equipment matrices and 12 seasonal factors. Eight country selectors do not imply eight calibrated models. Local currency labels do not convert money or import tariffs. RAMP's appliance-based approach provides methodological context ([RAMP](https://rampdemand.org/)); no new household-use, price or adoption coefficients were inferred from it.

## Legacy connection-based method

This section supersedes the older normalized annual path **only when connection.enabled is true and detailed.enabled is false**. Legacy saves/API calls without this option retain the previous calculations. No training data or model weights changed.

Let R be the frozen model estimate, w the household share of the transparent baseline, m service month (1–36), and T the maturity month (1–60). For each initial adoption fraction s, use t = clamp((m−1)/(T−1), 0, 1) and ramp(s,m) = s + (1−s)(3t²−2t³). T=1 gives immediate full adoption.

Household factor H(m) = (1+g_household)^((m−1)/12) × connection_ramp × appliance_ramp. Non-household factor B(m) = (1+g_business)^((m−1)/12) × existing_use_ramp.

Expected monthly energy = R × [wH(m)+(1−w)B(m)] + separately scheduled productive additions. Reference lower/upper bounds receive the same scaling and additions. This is conditional arithmetic, not a trained or field-validated adoption model. The original estimate describes a synthetic first-year monthly target; treating it as a mature reference is an explicit additional assumption that requires calibration.

Community counts, uptake and appliance index define the mature target. Starting connected households = households × target uptake × connection ramp, additionally scaled by underlying household expansion. Defaults (35% initial connection fraction, 60% initial appliance use, 50% initial non-household use, 24-month maturity) are illustrative only. A fraction of zero is valid; the internal effective appliance index can be below the model's input domain because it scales a reference, not a new model inference.

Year 1 monthly estimate is the mean of service Months 1–12. Daily and weekly values are average equivalents based on 365 days/year. No normalization forces Year 1 back to R. Calendar labels may be supplied as YYYY-MM; they locate fixed 365/12-day energy equivalents, not actual month-length billing totals. No seasonal weather, reliability or tariff elasticity is modeled.

Existing-use ramps do not delay new equipment twice. New equipment begins once at the start of service Year 2 or 3 at assumed full unit use, then compounds with business growth. Household/business growth is underlying expansion on top of adoption; users must avoid entering adoption growth twice. Negative expansion is allowed and can outweigh increasing adoption.

The typical daily profile uses average Year 1 sector weights. Sizing uses each monthly sector mix and its illustrative peak. Dashboard finance averages monthly capped cash results; Year 1 scenario totals therefore match dashboard monthly cash times 12. Peak fields in finance use the maximum monthly typical-day peak, not the average profile or observed annual maximum. Productive-use options remain static one-unit comparisons at average Year 1 load, not staged option cash forecasts.

The low/expected/high paths (editable demand multipliers) are **what-if scenarios**, not probabilities. Propagated reference bounds have no new 80% coverage claim and omit uncertain adoption, growth and proxy inputs. Synthetic evaluation and annual meter uploads evaluate the frozen reference model, not this curve.

The app/report also includes a five-deliverable status table, plain-language lender explanation and a safe-sharing proposal. No authentic operator data or secure hosted transfer portal is supplied. The proposed curve-validation study requires independent monthly post-connection records and site-level holdouts.

## Retained v1.2 method (connection growth off)

This completes the requested decision-support features in a synthetic MVP. It does not establish real-site engineering feasibility, project bankability or credit approval. The model and source dataset remain v1.0.0; the additional logic is deterministic scenario analysis.

## Scenarios versus uncertainty

Low / Expected / High multiply the expected demand path by editable factors, defaulting to 0.8 / 1.0 / 1.3. They are separately labeled what-if cases, not probabilities or the calibrated prediction bounds. The original demand −40%, −20%, base and +30% average-month financial stress table is retained.

Each scenario includes 36 monthly calculations and three annual summaries. Revenue uses the lesser of modeled demand and entered customer-side deliverable monthly energy. Annual financial totals sum monthly results; a capacity constraint can make them differ from twelve times the earlier average-month screen. Annual debt coverage divides total operating surplus by twelve stated monthly debt payments. Zero debt gives no debt-coverage ratio. Cash-gap months are also shown so annual positive cash does not conceal monthly shortfalls.

## Monthly growth with conserved annual energy

The target remains first-year average monthly customer energy, not Month 1 demand. Household and non-household growth use the corresponding existing annual assumptions. For each sector growth rate g, month weights are `(1+g)^(m/12)` for m=0…11, divided by their twelve-month mean. Applying these weights to each annual component preserves the original three annual average estimates and all Year 1 central-estimate cards.

New mills, pumps and cold rooms start once in the first month of the selected adoption year (2 or 3). Their energy subsequently follows the business growth assumption. The Yearly chart now shows the first twelve monthly projections; the Feasibility page shows all 36 months. Positive growth can rise, zero growth stays flat, and negative or mixed growth is not artificially forced upward. Weekly/monthly charts remain average equivalents, not dated forecasts. Bounds propagate the initial range under the same assumptions, not independently calibrated future uncertainty.

## Productive-use comparison

Three independent alternatives add one mill (800), irrigation pump (450) or cold room (500 kWh/month), using the existing synthetic baseline assumptions. None is automatically added to the community or combined with the other alternatives. Incremental served energy is capped by existing spare monthly energy capacity. The illustrative total peak is recomputed with the added appliance profile.

Incremental grid contribution = added served energy × (tariff × collection − variable operating cost) − entered extra developer operating cost. Options are ranked by that contribution, not by business profitability or commercial feasibility. Support cost is the developer's connection/support investment; it is not the enterprise's machinery cost. Optional simple payback divides support cost by twelve times positive monthly contribution. Unknown support cost or nonpositive contribution gives no payback claim. A supplied zero is distinct from an unknown cost. Supply-gap payback is explicitly provisional and excludes the unmodeled upgrade cost.

## Capacity risks and capital

For each case/year the screen reports annual energy served and unserved, energy utilization, unused annual energy capacity, maximum illustrative typical-day peak deficit and spare firm power. Unused energy capacity and peak shortfalls can occur together. Capacity is not reduced automatically and the app does not recommend solar/battery equipment sizes.

Optional capacity-linked capital × unused annual energy fraction gives an idle-capital allocation proxy, not recoverable savings or evidence that reserve capacity is unnecessary. This stock must not be summed across years. A stated capacity-linked portion cannot exceed a stated total project budget. Lost-sales exposure is unserved energy × tariff × collection, not lost profit. Technical dispatch may reveal additional shortfalls beyond this monthly screen.

Optional 36-month NPV = discounted end-of-month operating surpluses − stated initial project capital cost. Annual effective discounting uses `(1+r)^(month/12)`. This is before financing/tax and omits terminal value, replacements, expansion capital, reserves and residual asset value. It is not whole-life or equity NPV. Monthly debt payments are shown separately and never subtracted twice. Missing budgets yield no NPV or capital-exposure claim. Zero extra productive-use operating costs are visible assumptions, not verified estimates.

## Interface and exports

Both roles have a Feasibility page. Developer engineering/community editing remains separate; investor planning and financial inputs are shared scenario assumptions, not private underwriting. Unsaved input edits block navigation to other forms, role/community changes and exports until applied; period tab changes update only the chart. New assumptions survive Save/Restore and every report/export route. Old saved scenarios receive the new defaults.

Download report delivers self-contained HTML, printable via the browser's PDF dialog. The ZIP includes that report, full JSON, existing CSVs, nine annual scenario rows, 108 monthly scenario rows, 36 monthly growth rows and three productive-use options. Report sections cover exact assumptions, reasons, findings, all requested analyses and missing real evidence. No separate binary PDF is generated by the backend.

## Context references

- [ESMAP mini-grid handbook](https://www.esmap.org/new_esmap_report_minigrids_for_half_a_billion_people): mini-grid planning context and productive uses.
- [SAM financial-model overview](https://sam.nlr.gov/financial-models): cash-flow-based financial evaluation context. GridSight does not run SAM or reproduce its full lifecycle financial models.

These sources supply context, not this project's demand observations, tariffs, growth assumptions or cost quotations.
## Country denomination and public context

Rwanda/RWF and experimental Uganda/UGX settings use the same underlying demand/finance calculations. The frontend clears monetary and capital/support inputs on country changes; no exchange rate or transferred tariff is implied. Non-Rwanda backend money defaults are zero, with a warning to complete them. Report/CSV monetary denomination comes from project context. Neutral `_amount` keys replace historical `_rwf` keys in v1.2 exports.

Location and World Bank statistics are context-only. They do not change demand, growth, intervals, productive-use priors or financial inputs. Public data has separate provenance. Assumed thin-data fields are disclosed; no new probabilistic coverage claim is made. A measured-consumption comparison is a separate batch diagnostic and is not automatically attached as validation of the selected project.
