# GridSight

See demand before you build.

**[Open the live GridSight demo](https://gridsight-0al3.onrender.com/)**  
Free Render hosting may need about a minute to wake after inactivity.

## Deploy the full app

GitHub repository: [siltanukifilie/GridSight](https://github.com/siltanukifilie/GridSight).
The included `render.yaml` deploys one **free Render web service**. See
[deployment instructions](docs/DEPLOYMENT.md) for setup, checks and privacy limits.
Forecasts and report downloads run on the server; operator-meter uploads stay
disabled on the public demo until secure access is implemented. Those tools
remain available locally. The government electricity extract is local-only
pending redistribution terms; other permitted public snapshots are included.

GridSight is a local Python web app for **Mini-grid developers** and **Investors / lenders**. **East Africa: the eight EAC countries selected by the user.** Choose Country → District → Sector → Cell (source-supported local equivalents outside Rwanda), with no map or coordinate-entry UI. New projects use a transparent 20-input engineering estimate; Rwanda building/facility proxies can initialize the counts. Other-country and missing-record inputs are labelled assumptions. The legacy nine-feature synthetic-trained model is retained, not retrained on these new inputs.

## Start here

- [Implementation plan](docs/IMPLEMENTATION_PLAN.md): scope, architecture, data approach, numbered steps, and completion checks.
- [Progress tracker](docs/PROGRESS.md): completed work, current step, evidence, blockers, and the next action.
- [Decision log](docs/DECISIONS.md): choices and assumptions to preserve between sessions.

The implementation plan now includes the user's complete **13-item product-success checklist (R01–R13)**. Public-context integration, guided missing-input assumptions and eight country configurations are implemented. Measured-site accuracy, country transfer performance and paying-customer evidence remain open. The commercial model is proposed, not proven traction.

Current milestone: **v1.10 — interactive dashboard redesign.** Original green/light colours restored at the user’s request, simpler overview, linked low/expected/high and Year 1–3 filters, daily/weekly/monthly/yearly energy cards, and a clickable 36-month curve with cash/debt/supply drill-down. Both developer and lender workspaces retain all specialist tools. This is a Power BI–style experience in the existing Python app, not a Microsoft Power BI connection. **566 Python + 146 interface-logic checks pass (712 total)**; focused desktop, mobile and chart-keyboard checks pass. Full release QA remains open. Financial evidence and controlled real-data update workflows from v1.9 remain available. No model/data rebuild or empirical accuracy/savings claim. See [Verification record](docs/TEST_REPORT.md), [Financial evidence](docs/FINANCIAL_EVIDENCE.md) and [Real-data updates](docs/REAL_DATA_UPDATES.md).

## Continue the project

At the beginning of each working session, read the progress tracker and decision log. The latest user instruction is to complete the product now and defer the demo recording, deck, one-page summary and final disclosure. The team has three members. Preserve a numbered record of completed artifacts, checks and remaining work.

Record actual artifacts and checks before marking a step complete. Keep unfinished items and limits visible. Log changes to scope in the decision log. Preserve existing work and treat all files in the parent project's `sources/` folder as read-only reference material.

The application runs locally at **http://127.0.0.1:8050/** while its server is running. Publishing and submission belong to the later delivery stage. No public site exists yet.

## Five deliverables — one review and download

Open **Evidence → Five deliverables** (also linked from Overview). Each requirement has a status, scope, next action and direct route to its tool. **Download deliverables** exports a ZIP; extract it and open **START_HERE.html** for the offline five-part review.

- Demand: low / expected / high for day, week, month and year, conserving forecast-Year-1 scenario energy.
- Growth: all 36 forecast months with actual service-age labels. An older connected site's forward forecast is not relabelled as its first years.
- Validation: the current-model monthly comparison and observed-growth/confidence tools, blank input/meter/study templates and protocols. No measured results are invented or attached.
- Explanation: the applied project's plain-language lender explanation and customer-group energy contributions.
- Safe sharing: the operator aggregation/holdout/retention proposal plus a blank handover worksheet (not authorization or a secure portal).

The pack also preserves the full existing feasibility report, exact applied inputs, financial tables, provenance and an input fingerprint. Separate upload studies must be downloaded and reviewed separately; they never automatically certify the selected project. **Authentic held-out metered-site validation, measured confidence coverage and calibrated growth remain pending.** Latest verification: 582 Python + 153 interface checks (735 total), desktop checks in both roles, real browser ZIP download/integrity check, and screen review of the exported HTML/chart. Print/PDF and full release acceptance remain separate.

## Run the prepared project

The environment, model, dataset and RAMP profiles are already present. From this folder:

```bash
bash run.sh
```

Choose your role, then Country → District → Sector → Cell. The detailed input workspace opens automatically. Review assumptions in its dark collapsible panel and press **Update dashboard**. Review results in Overview; enter capacity, costs and financing in Scenarios. If a source lacks lower-level records, enter the administrative names; no coordinates or local observations are inferred. **Explore demo** remains a separate, labelled synthetic option.

- **Primary — Mini-grid developer:** edit Community, test Scenarios, inspect uncertainty and export a planning analysis.
- **Secondary — Investor / lender:** review the read-only Project view, edit Finance, inspect lower/faster demand and Evidence, and export an investment-screening review.

Switching roles preserves the current analyzed scenario. Run any changed inputs before switching. The role choice is remembered locally; Save keeps one scenario in the browser, restorable from the developer workspace. Exports include exact inputs, JSON, CSV tables and a printable HTML report.

Open **Feasibility** in either role to compare Low / Expected / High cases, 36-month growth, productive-use opportunities, capacity risks and cash. Enter optional capital/support budgets for cost exposure, support payback and a limited three-year NPV screen. Unknown costs stay unknown. Use **Download report** for the standalone HTML feasibility report or **Print / PDF** for browser printing. Apply changed inputs before leaving a form or exporting.

This is a local audience switch, **not secure accounts or permissions**. Both workspaces share one scenario, including financial edits. Investors' adjustments are not private. Multi-user ownership, authentication, reviewer access, audit records and separate review scenarios remain future work.

## Current detailed-input workflow (v1.6)

1. **Choose location:** eight EAC countries only. Rwanda uses actual ADM4 cell records, not settlements relabelled as cells. Other countries display available local equivalents. Source gaps remain visible.
2. **Review the 20 features:** households, connection rate, elapsed service months, income, tariff, fee; appliance ownership/power/hours; businesses, mills, pumps, productive power/hours; schools, clinics; agricultural cycle, new connections, appliance adoption and business growth.
3. **Apply:** counts × power × hours determine energy. New connections are capped by the service-area household count. Growth and a 12-month agricultural cycle shape 36 months from the entered time since connection.
4. **Review both roles:** developers edit the demand inputs; investors/lenders review them and can edit shared financial assumptions. Income/fee show household affordability; tariff sets bills/revenue. No untrained income/price elasticity is assumed.
5. **Save/export:** exact applied inputs appear in browser save/restore, analysis JSON, monthly CSV and both HTML reports. Old saved projects keep legacy math until **Open detailed inputs** is selected.

Low / expected / high are editable scenarios, **not calibrated confidence intervals**. The legacy household-growth percentage, appliance index and S-curve are not double-counted in detailed mode. All defaults, prices and growth rates require field review. Actual hourly operating schedules, motor starts, crop/weather forecasts, country calibration and real meter validation remain outside this screen. See [methods](docs/FEASIBILITY_METHODS.md).

## Historical connection-growth mode (v1.5; retained for legacy saves)

New Rwanda projects and explicit demos enable a 36-service-month connection curve. In **Feasibility → Start from connection**, set an optional connection month, initial connection/appliance/non-household fractions and the month adoption reaches its target. The default 35% / 60% / 50% initial fractions and Month 24 maturity are editable design assumptions, not measured Rwanda rates. A one-month ramp means immediate full use. Old saved projects retain the previous calculation until this feature is enabled.

The frozen synthetic-trained estimate is used as an **assumed mature reference**, not an observed mature load. The connection ramp determines Year 1 energy, all four period cards, daily profile, annual projections, monthly-cap cash flow and reports. First-year totals are not normalized back to the reference. Annual expansion applies in addition to adoption; avoid double counting. Calendar labels locate standard 365/12-day energy months, not exact calendar billing totals.

**Evidence** now contains all five requested deliverables: Rwanda location estimate/range; first-years curve; held-out meter comparison **pending authentic operator data**; plain-language lender explanation; and a downloadable safe meter-sharing proposal. The annual CSV tool compares the frozen reference model; it does **not** validate the connection ramp. A monthly independent holdout study is still needed. Proposed hosted security/transfer controls are not implemented.

Both roles share the same results. Developers edit connection assumptions; lenders review them. Either Feasibility update button applies both connection and financial-planning forms, avoiding lost edits. Saved scenarios, report, print view and ZIP retain the applied connection inputs.

## Rwanda data workflow (v1.4 sources, retained in v1.6)

Read [Data pipeline and coverage](docs/RWANDA_DATA_PIPELINE.md) for the exact source counts, assumptions, licences and missing layers. Imported: 4,251,978 country-clipped Google building detections, 2,232 OSM facility/shop objects and 236 historical Bugesera electricity records. The existing Rwanda gazetteer has 12,808 administrative/place records, of which 9,788 settlements pass the rural-first filter. These are dated public snapshots, not live meter feeds.

1. **Select a Rwanda cell.** Country → District → Sector → Cell. These building/facility sources currently cover Rwanda only, not every EAC country.
2. **Open the dashboard automatically.** Query the local 500 m radius; prepare building/facility proxies plus explicit placeholders. Never inherit the prior project's counts or finances.
3. **Review evidence.** Original suggestions, current inputs, source dates and missing layers stay visible in Locations and the report. Existing grid status starts unknown; historical sector records are not current village coverage.
4. **Refine the project.** Review households, equipment, growth, supply, tariff and financing. The nominal model range does not include proxy-input uncertainty. All money defaults are illustrative, not extracted ESMAP/AMDA benchmarks.
5. **Export.** Reports and analysis ZIP retain the profile; download the compact source pack and the separate numerical building-point dataset in Locations. Metered validation, VIIRS/GridFinder/EAE/MTF layers and cost calibration remain open.

To refresh deliberately: `.venv/bin/python scripts/collect_rwanda.py electricity facilities buildings boundary`, rerun tests, then restart the app. The building tile download is about 576 MB. Preserve old snapshots before a refresh needed for report reproduction. Selection works offline after import.

## Historical location-first workflow (v1.3, superseded by v1.4)

The following records the earlier eight-country/manual-review flow. v1.6 above is the current user scope and default interaction. The following map and coordinate workflows are historical, not available in the current UI.

1. **Find a site.** Browse public place records for all eight countries. Rwanda uses district → sector → settlement; other countries use source-supported local equivalents. Missing or older subdivisions are disclosed, not invented. Country-wide settlement search and surveyed-coordinate entry are fallbacks.
2. **Add customers.** Inputs start blank for each new place. A household estimate is required. Unknowns can be filled with explicitly reviewed planning placeholders; zero is not automatically inferred from missing data.
3. **Check grid access.** Default: unknown. Reported unserved, planned and connected claims require a source note and date and remain user-reported. Connected sites are flagged outside the unserved-site focus. Search excludes capitals/admin seats, urban-labelled administrative areas and their linked descendants, and known large settlements; it does not verify rural character or absence of a grid.
4. **Build the dashboard.** Keep day/week/month/year estimates, Low / expected / high cases, three-year growth, productive uses, explanations, sizing risks, financial stress and downloadable reports. New projects reset all money budgets and supply limits; enter capacity, tariff, costs and financing before interpreting cash. Currency labels never convert amounts.
5. **Review the evidence.** Load the map only by choice; fetch World Bank national context separately. Compare genuinely measured, permissioned annual site aggregates in Evidence. Public geography and national statistics do not calibrate the model or validate village demand.

The default selector runs offline from 101,142 public administrative/place records downloaded on 31 October 2026, stored in `data/locations/{country}.json`. The filtered settlement list is smaller. [GeoNames](https://download.geonames.org/export/dump/readme.txt), CC BY 4.0; source URLs, fetch times, modification dates and source ZIP hashes are preserved. Administrative coverage is uneven, especially lower-level Kenya/South Sudan records and older Burundi divisions. This is a dated gazetteer snapshot, not a current utility map or live meter feed.

To deliberately refresh all eight public extracts, run `.venv/bin/python scripts/import_locations.py`, rerun geography tests, then restart the app. The script sends no project data and validates all downloads before replacing outputs. Do not refresh during report reproduction without retaining the old snapshot.

Historical v1.3 behavior below (maps and device-position controls were removed in v1.6). Public statistics require internet; geography browsing does not. World Bank snapshots are memory-cached up to 24 hours and may need refetching after a restart. Save keeps one project in this browser; reports include its coordinates and provenance. Device location is optional, one-shot, rounded and draft-only under **Correct this project’s coordinates**; it is never assumed to be the project site. Correcting coordinates clears previous grid-access claims. Use **Find another site** for a different project; no counts or costs are silently copied.

## Reproduce on another machine

Tested on Linux with Python 3.14.4. The lock file records the full tested dependency set.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python build.py
.venv/bin/python build_profiles.py
.venv/bin/python -m pytest -q
node tests/workspaces.test.cjs
node tests/demand_charts.test.cjs
node tests/feasibility.test.cjs
node tests/discovery.test.cjs
bash run.sh
```

RAMP 0.5 requires the pinned NumPy 2.3.5 and pandas 2.3.3 versions. Keep those pins unless its integration is upgraded and retested. Set `GRIDSIGHT_PORT` to change the default port. The Flask development server binds to localhost; public hosting would require a production server and appropriate access controls.

Generate local example analysis reports with `.venv/bin/python export_examples.py`.

## Implemented capabilities

- Short dashboard copy and expandable “How it works” explanations; detailed exported reports remain unchanged.
- Two role-specific dashboards with six areas each, a shared forecast, and role-specific exports.
- Central demand estimates per day, week, month and year in both overviews and exports. These are Year 1 average equivalents using 365 days/year, 12 months/year and 7 days/week; seasonal patterns and future growth are not applied to these conversions. Financial calculations remain monthly.
- Daily / Weekly / Monthly / Yearly chart tabs in both overviews. Daily shows illustrative hourly power; week/month show average daily energy. Yearly displays the next 12 monthly estimates and preserves their annual total. The average-month view explicitly weights its partial final day. Keyboard navigation is supported.
- 500 synthetic communities and 18,000 monthly observations; three editable demonstration cases.
- Baseline and trained gradient-boosting forecasts, calibrated ranges, and site-separated testing.
- Actual RAMP integration for seven appliance-based daily load shapes.
- Three-year growth, productive equipment additions, revenue stress tests, break-even energy and debt coverage.
- Explicit Low / Expected / High cases; 36-month cash and capacity calculations; independent mill/pump/cold-room opportunity comparisons with optional developer support payback; over-/under-sizing screens and optional capital exposure. All methods and evidence limits are visible.
- Full feasibility-screening HTML report, print/PDF action and reproducible CSV/JSON package. Optional three-year NPV is before financing/tax, not whole-life project valuation.
- Served-energy constraints, extrapolation notices, explanations and portable analysis exports.
- Investor/lender downside overview, financial-only editing, read-only technical profile, and an explicit missing-evidence checklist.
- 361 Python calculation/data/API/report tests and 84 interface-logic tests; real-browser visual checks remain pending.

See [data card](docs/DATA_CARD.md), [model card](docs/MODEL_CARD.md), [verification record](docs/TEST_REPORT.md), [data-sharing proposal](docs/DATA_SHARING.md), and [third party notices](THIRD_PARTY_NOTICES.md).

See [feasibility methods](docs/FEASIBILITY_METHODS.md) and the [completion plan](docs/COMPLETION_PLAN.md) for the newly completed features and their scope.

## Data and export contracts

Feature v1.6 adds nested `detailed` inputs, `affordability`, a 20-feature inventory, service-month horizon and monthly component totals. `/api/geography?kind=cells&parent=…` selects actual lower administrative records. `/api/location-project` now accepts all eight EAC countries; manually entered names use no coordinates. New projects enable detailed mode; missing/disabled detailed settings preserve prior calculations.\n\nFeature v1.3 adds canonical public-location identifiers/provenance and user-reported grid evidence to project context. The local geography endpoints are `/api/geography` and `/api/geography/location`. Selecting a place does not change model features. Feature v1.2 added project `context` and optional `public_data` to analysis JSON. Monetary feasibility keys formerly suffixed `_rwf` now use `_amount` (for example `extra_revenue_amount_month`); monetary CSV rows include a `currency` column. No calculations or exchange rates are changed by the denomination. A fetched public snapshot adds `public_context.json` to the export ZIP.

Public-provider notices and commercial-hosting limits are in [third party notices](THIRD_PARTY_NOTICES.md). The legacy Open-Meteo geocoder endpoint remains for compatibility and its hosted terms still apply; the new default selector uses attributed offline GeoNames data. No hosted account, paid subscription or public deployment was created.

## Evidence boundary

On 100 held-out synthetic sites, MAE is 1,294.73 kWh/month and weighted absolute error is 10.55%. The nominal 80% interval covers 91% of test outcomes. The baseline MAE is 2,236.26 kWh/month. These values measure performance inside a simulation, not actual Rwanda forecasting accuracy.

No real metered-site validation has been performed. Growth and financial assumptions are illustrative. The supply screen is not a solar/battery dispatch model or engineering design, and the results are not a lending recommendation. Browser interaction and visual checks remain pending; API and calculation tests are not substitutes for those checks.

### v1.4 API additions

`GET /api/rwanda-data` reports source status; `POST /api/location-project` accepts a Rwanda location and returns fresh provisional inputs; analysis adds `location_profile` generated from local sources. Selecting a new place now initializes model features from explicit proxies/placeholders. Correcting an existing point alone still preserves the user’s inputs. The analysis ZIP includes `location_profile.json`; `/api/rwanda-data/download` supplies the compact source pack, and `/api/rwanda-data/buildings` supplies the numerical detection dataset.
