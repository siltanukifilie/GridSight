# GridSight synthetic data card

Scope: the original fictional dataset only. For current public context and
measured experiments, see the [data catalogue](../data/README.md). Historical
version notes below do not describe the full current app.

Dataset version 1.0.0. Seed 20261030. All 500 sites and all 18,000 monthly observations are generated. No real customer records or operator consumption data were used.

## v1.5 connection inputs (not new measurements)

The connection month, initial connection/appliance/non-household fractions and maturity month are user-editable planning assumptions. Default fractions are 0.35 / 0.60 / 0.50 and maturity is 24 months; these are not observed Rwanda adoption rates. No new training examples or real consumption were collected for this feature. The synthetic-trained estimate is interpreted as an assumed mature reference, then scaled through the unvalidated adoption path. The original generated dataset remains unchanged.

The evidence screen distinguishes all five deliverables and explicitly marks held-out genuine-meter validation pending. The existing CSV diagnostic compares annual averages with the frozen reference; future curve validation needs an independently designed monthly post-connection dataset. The sharing proposal describes operator-side aggregation and governance, not an implemented hosted transfer service.

## Rwanda context

District labels are Kirehe, Nyamasheke, Gicumbi, Muhanga, Bugesera, and Ngoma. They are geographic context, not actual sampled villages or operator sites. The default interface uses Rwandan francs and local-time daily charts; v1.2 also offers an explicitly experimental Uganda/UGX context without retraining. No national tariff, district-level consumption estimate, actual solar yield, or claimed national demand distribution is embedded in the model.

The Rwanda Energy Group mini-grid page provides background context, including examples of mini-grid installations. It is not a source of training labels or the assumed consumption rates. [REG mini-grids](https://www.reg.rw/what-we-do/offgrid-solutions/mini-grids/)

## Files and units

| File | Grain and purpose |
|---|---|
| `data/synthetic_sites.csv` | 500 site profiles, each with a synthetic first-year average monthly target. |
| `data/synthetic_monthly.csv` | 36 months per site, with sector energy and total customer energy in kWh. |
| `data/metadata.json` | Seed, version, counts, partitions, and provenance. |
| `data/load_shapes.json` | RAMP-generated normalized hourly energy shares for seven sectors, plus appliance definitions. |
| `reports/test_predictions.csv` | Forecasts and intervals for 100 held-out synthetic sites. |

## Input dictionary

| Field | Unit | Main generator range | Accepted application range |
|---|---|---|---|
| households | household count | 50–800 | 0–1,500 |
| shops | count | Derived from 2.5–12% of household count, rounded | 0–150 |
| schools | count | 0–3 | 0–10 |
| clinics | count | 0–2 | 0–5 |
| mills | equipment count | 0–3, archetype-dependent | 0–10 |
| pumps | equipment count | 0–4, agricultural archetype | 0–15 |
| cold_rooms | equipment count | 0–3, trading archetype | 0–10 |
| uptake | connected-household fraction | 0.50–0.98 | 0–1 |
| appliance_index | dimensionless multiplier | 0.60–1.80 | 0.5–2 |

The application warns when an input exceeds the realized training partition's minimum or maximum, not just these nominal ranges. Business and facility counts describe connected customer groups; uptake applies to households. Separately listed productive equipment must not be included again in shop assumptions.

The target is average monthly customer energy over months 1–12. It is unconstrained by a proposed system's capacity. Financial calculations separately cap served customer energy at an entered delivery limit.

## Generator assumptions

The baseline monthly rates are 15 kWh per connected household at appliance index 1, 100 per shop, 130 per school, 600 per clinic, 800 per mill, 450 per pump, and 500 per cold room. These are editable development assumptions, not empirical Rwanda estimates.

The generator introduces site-level lognormal variation, sector variation, an appliance and uptake correction, seasonal effects, monthly noise, and latent adoption growth. Generator-only variables are excluded from model inputs. Each site's first 12 simulated months determine its target. Counts, sector totals, and units are checked in tests.

The dataset partitions contain 300 training, 100 calibration, and 100 test sites. Every month belonging to a site carries the same partition. An internal 60-site holdout within the training partition selects between the baseline and learned point model; the chosen learned estimator is refitted on the 300 training sites. The 100 calibration sites widen the interval; the final 100 evaluate it.

## RAMP integration

`build_profiles.py` uses the actual `rampdemand==0.5.0` Python package. Seven original appliance configurations produce seven days of minute-level simulated load, using 12 representative users per sector. Outputs are averaged to 24 hourly values and normalized to sum to one. The application scales those shapes to its daily demand estimate, using baseline sector shares.

RAMP determines timing here. It does not supply the monthly training labels or validate the Rwanda assumptions. The profiles and energy estimates are synthetic. NumPy 2.3.5 and pandas 2.3.3 are pinned because RAMP 0.5 uses array scalar conversions and time aliases removed in later releases. Upstream package source has not been modified.

RAMP source and license: [RAMP introduction and EUPL notice](https://rampdemand.readthedocs.io/en/latest/intro.html). The source is available at [RAMP-project/RAMP](https://github.com/RAMP-project/RAMP). The cited research is Lombardi et al., 2019, “Generating high-resolution multi-energy load profiles for remote areas with an open-source stochastic model,” [DOI](https://doi.org/10.1016/j.energy.2019.04.097).

## Appropriate interpretation

Use this dataset to test the software, demonstrate a planning workflow, and explore explicit assumptions. Do not use it to establish field accuracy, actual village demand, affordability, investment viability, or coverage of a real district. Household and business behavior after electrification must be calibrated using permissioned local evidence.

Synthetic-to-real transfer is an open research and validation task. A separate stress experiment increases test outcomes by 25% while leaving inputs unchanged; its deterioration in performance is displayed in the app.
## Separate public and user-supplied layers (v1.2)

The original files above remain synthetic and unchanged. The app separately retrieves GeoNames place coordinates through Open-Meteo and World Bank national population/electricity-access indicators. Neither source supplies training labels or changes local demand forecasts. Sources, licences, geography, observation year, retrieval time and transformations are attached to optional public-data snapshots. See `THIRD_PARTY_NOTICES.md`.

Custom community inputs are labeled user-entered planning assumptions, not measured consumption. The thin-data guide marks explicitly accepted placeholder fields; the model’s prediction range does not include uncertainty in these guessed inputs. Household count is mandatory; zero remains an observed/entered choice rather than an automatically interpreted missing value.

The optional consumption comparison accepts anonymous independent-site aggregates with complete 12-month historical windows. Annual customer energy is normalized by actual days observed to a 365/12-day monthly basis. Uploaded data is processed locally in memory, not stored on disk, sent to external services or used to retrain. Source authenticity and measurement completeness remain user attestations. Automated test fixtures are not real observations and do not change the zero-real-sites status of the trained model.

## Public EAC location index (v1.3)

Eight attributed GeoNames extracts were fetched on 31 October 2026 into `data/locations/`: RW 12,808; UG 12,946; KE 6,716; TZ 11,540; BI 9,697; SS 5,336; SO 4,584; CD 37,515 retained records (101,142 total). These counts combine ADM1–4 administrative records and PPL/PPLL populated places; they are not numbers of verified off-grid sites.

Importer: `scripts/import_locations.py`. Keep names, canonical IDs, coordinates, administrative codes, population where supplied, time zone and record modification date. Store source URL, CC BY 4.0 attribution, fetch timestamp and original ZIP SHA-256. Do not retain alternate names or extract untrusted ZIP paths. Invalid/nonfinite coordinates and other-country records are excluded. A zero source population becomes unknown, not zero residents; no population reference year is supplied, so population is not converted into households.

Serving additionally filters capitals/admin seats (excluded during import), urban-labelled areas and descendants, Kigali's source region and reported settlement population ≥20,000. Unknown population stays searchable. These are conservative search choices, not rural/off-grid certification; potentially suitable peri-urban sites may be omitted and served small places may remain.

Administrative code links are used directly, not guessed by coordinate proximity. Missing links yield explicit empty states, broader search, an attributed administrative reference point or a manually surveyed point. Burundi and some other source divisions may be old; no current authoritative boundary coverage is asserted. Coordinates identify a place/reference point, not the mini-grid service-area boundary.

The index never enters model training, demand features or accuracy evaluation. Source/point provenance and user-reported grid evidence are preserved in analysis/report exports. No customer data is sent to GeoNames. Site selection does not fetch a map or infer utility coverage.

## v1.4 public input evidence, separate from synthetic training

Active scope is Rwanda. 4,251,978 Google building detections, 2,232 OSM facility/shop objects and 236 historical Bugesera electricity records were actually imported. See [Rwanda data pipeline](RWANDA_DATA_PIPELINE.md) for filters, country clip, licences, missing layers, assumptions and source hashes. These sources initialize 500 m-radius screening proxies. They do not replace synthetic consumption labels, retrain the model or establish real performance. Original suggestions stay separate from subsequent user edits. Government household-energy values are excluded because their definition is unclear. The former eight-country active UI is superseded; other country configurations are future architecture.
