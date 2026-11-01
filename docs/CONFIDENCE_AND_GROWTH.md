# Forecast confidence and early growth — v1.8

## What is and is not finished

The application now implements input-uncertainty propagation, an observed-history growth fitting method, separate site-block conformal calibration and untouched-site coverage testing. **No eligible genuine paired dataset has been imported. Therefore no real calibrated range, learned East African growth curve, or field accuracy is claimed.** Invented automated fixtures test software only.

The original low / expected / high planning scenarios stay visible and are not renamed confidence intervals. The synthetic reference model's coverage cannot validate this detailed model. New results are explicit, separate studies; they never silently overwrite site forecasts, financial screens or feasibility reports.

## 1. Explore uncertain inputs now

In **Feasibility → How uncertain are the inputs?**, review the uncertainty widths and run the simulation. All widths are user assumptions. Default widths are illustrative, not survey estimates. The output is an **input-assumption band**, NOT a calibrated prediction interval.

The current engineering energy calculation is evaluated for 256 reproducible input draws by default. The seed and draw count are included in the downloadable JSON. Advanced settings allow 64–1,024 draws. Symmetric triangular distributions have their mode at the entered value. Relative widths multiply counts, ownership, watts, hours, new connections and seasonal factors. Connection-rate and annual-growth widths are absolute percentage points. Rounding/clipping preserves count and physical limits.

Within a draw, each group shares its perturbation across appliance/equipment types and the entire monthly path. Different groups are assumed independent. This retains time dependence but is not a learned correlation structure. Household and non-household counts, connection share, appliance ownership/power/hours, equipment power/hours, new connections, appliance adoption, business growth and agricultural multipliers are covered. Income, tariff and connection fees do not drive energy in this model. Planned equipment additions and their timing remain fixed. A zero multiplicative input cannot invent an unlisted customer or appliance.

Central remains the original engineering estimate. Monthly bounds use equal-tail simulation quantiles and are widened to include that nominal estimate. The chosen 80/90/95% simulation mass is **not an observed coverage rate**. Annual bounds use quantiles of each draw's summed path, not sums of marginal quantiles. Units are 365/12-day monthly energy equivalents. Simulations omit unobserved forecast error until separately calibrated.

## 2. Supply histories and freeze the study

In **Evidence → Calibrate confidence & growth**, download the starter pack. It contains:

- site_inputs.json: blank strict current-model input manifest.
- monthly_meter_totals.csv: blank customer-side monthly meter schema.
- study_plan.json: separate whole-site fit, calibration and test IDs, horizon, uncertainty settings and protocol reference.

Follow MONTHLY_DATA_CONTRACT.md. Only actual measured customer-side kWh with documented pre-connection inputs and appropriate authority is eligible. Source/permission, disclosure review, timing and independence are user attestations, not authenticated by the app. The pre-existing development-site exclusion list applies to all imported sites; the study plan then allocates fresh sites between fitting, calibration and testing.

Fix all settings and site roles **before inspecting outcomes**. Record a protocol reference. Same physical mini-grid aliases must not appear across groups, even if their text IDs differ. Site identifiers are case-normalized and textual overlaps/duplicates are rejected. Prefer independent operators and document country/population comparability; the program cannot detect shared-operator dependence.

Use either the first **24 months** (default, focused on early uptake) or **36 months**. Every site must have every eligible month from Month 1 through the horizon. Missing months, incomplete coverage, outages and estimated readings are not filled or relabelled. They prevent that site's inclusion in a complete-path study; the error explains the missing months. Reviewed exclusions and all later records remain in the separate monthly-validation report. The maximum is 30 sites / 1,080 rows and 256 KiB per study request. This is a local, in-memory retrospective tool, not a secure hosted data portal.

Minimum sample counts:

| Target | Growth-fit sites | Calibration sites | Untouched test sites | Minimum total |
|---|---:|---:|---:|---:|
| 80% | 3 | 4 | 2 | 9 |
| 90% | 3 | 9 | 2 | 14 |
| 95% | 3 | 19 | 2 | 24 |

These are computational guards, **not adequacy or representativeness claims**. More independent, comparable sites are needed for convincing validation. The app rejects an impossible finite conformal quantile rather than silently weakening the coverage target.

## 3. Learn total-demand growth from fitting sites only

The method learns an age-dependent correction to the original engineering trajectory using **only growth-fit outcomes**. Actual calendar-month energy and original forecasts are normalized to 365/12 days. The response is:

`log(actual_standard_month_kWh + 1) − log(original_standard_month_kWh + 1)`.

A piecewise-linear basis has fixed service-month knots at 1, 6, 12 and 24 (plus 36 for the longer study). Ridge strength is fixed at 0.1. Log corrections are clipped to ±log(10) when applied. Adjusted energy is nonnegative. No hyperparameter is selected using calibration or test outcomes. Early growth may rise or fall; monotonic increase is not forced. This is an empirical model-design choice, not a published or country-calibrated mini-grid law.

Total meter energy **cannot separately identify** connection uptake, appliance adoption and business growth. To fit those mechanisms credibly, operators must additionally supply dated customer counts/connections, appliance panels and business/equipment activity registers. This release fits the aggregate demand trajectory, not those causal parameters. It reports whether adjustment improves or worsens untouched-site errors.

A 24-month study cannot calibrate or validate Month 25–36. The fitting function explicitly rejects extrapolation outside the declared horizon. The original dashboard's three-year assumption curve remains separate.

## 4. Calibrate input + forecasting-error uncertainty

Run the frozen input simulations through the fitted growth correction. Scale back to actual calendar days for comparison. Let L, U and P be each month's input-only lower, upper and central forecasts. Each calibration site supplies **one** score:

`site_score = max_month max(L − actual, actual − U, 0) / max(P, 1 kWh)`.

For n independent comparable calibration sites and target c, choose the exact sorted score at rank `ceil((n+1)*c)` (one-based). If this rank exceeds n, no finite band is returned. Ties are retained conservatively. Expand each test month to:

`[max(0, L − q*max(P,1)), U + q*max(P,1)]`.

The expansion cannot shrink the input band. This accounts empirically for residual forecast errors, including growth-fitting error, under the calibration population. It is a **whole-path prediction band**, not a confidence interval for a mean. Standard split-conformal logic gives the target marginal coverage of the full declared path only under **exchangeability of whole-site trajectories**, conditional on the frozen fitting process. Months within a site are not independent calibration samples. New-country transfer, shared operators, selection bias and distribution shifts may violate the assumption. The application does not assert these assumptions are true.

The construction adapts the general methods in [Angelopoulos & Bates](https://arxiv.org/abs/2107.07511) and the whole-trajectory framing discussed in [Conformal Time-series Forecasting](https://proceedings.neurips.cc/paper/2021/hash/312f1ba2a72318edaaa995a67835fad5-Abstract.html); it is not a reproduction of that paper's forecasting model.

## 5. Test once on untouched sites

The app reports:

- Full-path test coverage: fraction of test sites whose every eligible month lies inside the calibrated band.
- Descriptive monthly coverage and mean interval width; neither treats months as independent sites.
- A 95% exact binomial interval for full-path coverage, calculated across test sites, not monthly rows. It assumes independent comparable test-site indicators. See [SciPy's Clopper–Pearson implementation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html).
- Original versus fitted MAE, RMSE, WAPE and bias.
- Separate Months 1–6, 7–12 and 13–24 results; Months 25–36 only when supplied.
- Actual, original and fitted year-on-year growth, with undefined growth when base-year energy is zero.
- Per-country/site diagnostics, monthly expected/actual/bounds and coverage flags.

Do not repeatedly tune on the test results. A tiny test sample may yield apparently perfect coverage and a very wide confidence interval. There is no automatic “validated”, “lender-ready” or regional pass. Calibration is not proof of good sharpness or prospective performance. New-site deployment is deliberately not automatic: these outputs stay a reviewed batch study.

## Reproduction and disclosure

Download the JSON study and test-results CSV. JSON retains the exact manifest, split/settings, growth coefficients, site-level calibration scores, finite-sample rank, model/config hashes, input hashes, limits and timestamps. Do not publish small-site results without disclosure review. Keep original input files under agreed retention rules; the server does not retain uploads. Changing settings or site roles requires a new independently designed study, not relabelling the previous test.
