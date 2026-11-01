# East Africa: current-model validation

## Status and steps

1. **Implemented:** monthly comparison of the exact current 20-input engineering calculation, separate from the old annual reference-model tool.
2. **Implemented:** strict paired input/observation checks, whole-site holdouts, calendar alignment, errors and annual growth comparisons.
3. **Pending:** obtain genuinely measured customer-side site totals AND documented pre-connection inputs with suitable reuse permission. Public-source findings are in `data/validation/source_catalog.json`.
4. **Pending:** external review of provenance, alias-free independent sites, representativeness and forecast accuracy. The software never assigns an automatic validation pass.

This does not retrain the old model. No real dataset is supplied with this release, and no real-site accuracy score has been calculated. Automated test fixtures are invented software checks and are not field evidence.

## In the app

Open **Evidence → Test the current forecast**. Download the starter pack, complete its site manifest and monthly CSV, then upload both. Results are a separate batch comparison, not certification of the selected dashboard location. Download the JSON report and predicted-versus-actual CSV. Uploads and results are not saved to the server or local storage, and are not sent to external providers.

The starter pack has **blank fields, not invented measurements**. Do not use proxy/default dashboard values as though they were independently observed inputs.

## Site manifest

Use schema `gridsight-monthly-holdout-v1`. Give a source name, retrievable reference/version, licence or written permission reference, and every real site used in development/calibration. An empty development list means no real sites were used; the software cannot verify that declaration. Hold out whole mini-grids, not customer rows or different months from the same site. Use one stable anonymous ID per physical mini-grid. All sites in this file are test sites.

For each site:

- Country code RW, UG, KE, TZ, BI, SS, SO or CD; no inferred country transfer accuracy.
- Connection month YYYY-MM; inputs_as_of YYYY-MM-DD strictly before that month. For mid-month commissioning, omit the incomplete first month's observation; do not shift the connection month to hide it.
- Input evidence reference: the dated pre-connection survey, equipment register and frozen planning assumptions. Inputs must not be reverse-engineered from consumption. This is retrospective testing of today's model, not a historical forecast made before commissioning.
- Complete community counts, initial connection rate, appliance ownership/watts/hours, equipment kW/hours, twelve service-month agricultural multipliers, annual new connections/adoption/business growth and planned additions. Fill a known absence with zero. Never fill unknown demand inputs with guessed zeros.
- Detailed mode true and elapsed connection months zero. All detailed fields and appliance/equipment types must be present; no hidden default fill. Household income and connection fee may be null because they do not drive physical energy. Tariff must be documented; it affects revenue, not energy. The old appliance index and household-growth slider are not used.
- All attestations true only after source authority, privacy/disclosure, customer-side units, pre-connection timing and independence have actually been checked.

No personal names, phones, account numbers, precise household coordinates or household-level records. Site aggregates can still disclose small groups; review before uploading/exporting. This local app is not a secure hosted operator portal.

## Monthly CSV

Exact header:

`site_id,month,actual_kwh,coverage_fraction,availability_fraction,quality`

One row per anonymous site and complete historical local calendar month. `actual_kwh` is the sum of customer-side meter energy (not generation, amperes, power, cumulative counter readings or loss-inclusive energy). Aggregate raw interval/counter data upstream with operator-approved rules for counter resets, duplicates, time zones and gaps; this importer does not infer those rules.

`coverage_fraction` is the observed fraction of expected customer-meter time across all relevant meters. `availability_fraction` is the fraction of calendar service time without outages, rationing or binding supply constraints. Both must be documented, not automatically set to one. `quality` is measured or estimated.

Incomplete coverage, availability below one, estimated records and months outside service months 1–36 are retained in the exclusion report and never scored. No missing-month imputation. Missing rows are displayed as missing/excluded service months. The strict complete-service sample may be unrepresentative of real reliability: report this selection limitation.

Limits: 30 sites, 1,080 rows, CSV 90 KB, entire JSON request 256 KiB. Historical months only. Duplicate site/month pairs, unknown fields, unsupported countries, bad dates, negative/non-finite values and declared development/test overlap are rejected.

## Predictions and errors

Calls `detailed_months`, the same calculation used by the dashboard, without any training or recalibration. Dashboard energy uses 365/12 days per month; for comparison multiply by actual calendar days / (365/12), including leap years. This assumes a constant mean daily rate within each service month. Do not compare an average daily archetype with a monthly total.

- MAE: mean absolute monthly kWh error.
- RMSE: square root of mean squared monthly kWh error.
- WAPE: sum absolute errors / sum actual kWh × 100; undefined (null) when actual total is zero.
- Bias: predicted minus actual, in mean kWh/month and as a percentage of total actual energy; positive means overprediction.
- Groups: each site, country and service year. Overall errors pool site-months, which are not independent sites; site count is reported separately.
- Growth: annual totals and year-on-year growth only for adjacent service years each containing 12 eligible months. Zero base-year energy gives undefined percentage growth. Three-year evaluation requires all 36 months.

No confidence level is assigned to low/high assumptions. No hourly peak, willingness-to-pay, financial or lender-approval claim follows from this energy check.

The report retains the submitted manifest, CSV hash, model/module/config hashes, exclusions and limitations. Hashes support reproduction and change detection, not verification that inputs predate targets. Keep the original CSV under approved retention rules if reproducibility is needed. Current app results never overwrite global evidence or mark a location validated.

## Public-source review

Reviewed 1 November 2026:

- [Renewvia](https://github.com/Renewvia-Energy/minigrid-dataset): Kenya subset is relevant, but actual records require a DTUA and authorized access. No agreement was signed or request sent.
- [Hartvigsson & Ahlgren](https://data.mendeley.com/datasets/bbtn9wxhzm/1): measured Tanzanian current, not directly monthly kWh; CC BY-NC 3.0. Not incorporated into the commercial product.
- [Scott & Coley](https://doi.org/10.3390/en14144207): useful published Tanzanian meter study; raw paired files not obtained and the later survey cannot establish pre-connection inputs.
- [Uganda integrated-energy study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12799770/): source records identified as proprietary.

These findings do not prove that no suitable public data exists. They document the candidates checked and why no valid comparison can yet be reported.
