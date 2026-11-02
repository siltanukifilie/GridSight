# Judge's guide

**GridSight — developed by the GridSight Team.**

[Live app](https://gridsight-0al3.onrender.com/) · [Data](../data/README.md) ·
[Architecture](ARCHITECTURE.md) · [Tests](TEST_REPORT.md)

## The problem and the proposed product

Developers need to plan mini-grids with limited local demand information.
Investors need to see the assumptions, uncertainty and repayment consequences.
GridSight combines a transparent planning calculator, public location context,
productive-use and financial scenarios, and separately identified measured-data
experiments in one web app.

The proposed buyer is a mini-grid developer, with investor/lender review as a
second workflow. Per-project assessment and portfolio subscriptions are proposed
business models, not demonstrated revenue. No paying customer is claimed.

## Suggested review route

For a complete test case, choose **Load Juru test case** on the starting screen
or in Locations. All 20 inputs and financial assumptions are populated with
synthetic test values. Download the [examination dataset](../data/examples/README.md)
or export your edited report. Public sector observations stay separate.

Selecting **Rwanda → Bugesera District → Juru → Juru** also opens that
complete demo, not the generic 500 m public-proxy screen. The Juru card's
**Open public-data screen** button opens the separate public-proxy calculation;
its financial result may be negative. Neither view is measured-site validation.

| Step | Try | Check |
| --- | --- | --- |
| 1. Location | Developer → Rwanda → Bugesera District → Gashora → a listed cell | District/sector/cell hierarchy and dated sources; no map required |
| 2. Inputs | Open Community; change households, connection uptake or equipment hours; update | Assumptions are editable. Sector census households are separate from service-area households |
| 3. Demand | Overview → compare periods, scenarios and years; select a month | Units, energy totals and a 36-month curve; low/high are scenarios |
| 4. Feasibility | Enter non-confidential tariff, capacity and cost assumptions | Productive-use uptake, affordability, sizing and cash/debt stress; missing finance stays unknown |
| 5. Lender | Switch to Investor / lender | Same demand scenario, read-only customer inputs, reviewable assumptions |
| 6. Evidence | Review measured experiments, five deliverables and operator pilot | Study units/splits, weak results and gaps are disclosed |
| 7. Export | Download deliverables and data/results | Inspect HTML, CSV, JSON, sources and blank operator handover templates |

The rural-first location filter is not utility coverage verification. A listed
location may already have grid service. Confirm utility access and expansion
plans before treating any location as a viable mini-grid site.

## Brief 03 deliverables

1. **Estimate with a range:** implemented as a 20-input engineering calculation
   with low / expected / high cases. Not yet calibrated against matched Rwanda
   pre-build inputs and outcomes.
2. **Growth after connection:** 36 months of connection, appliance, business and
   productive-use scenarios. Observed early-connection calibration is still needed.
3. **Held-out metered sites:** a Kenya/Nigeria operational transfer study is
   included. It uses previous consumption, so it is not a pre-construction
   Rwanda validation result. The local importer for the current monthly model
   awaits permissioned, matched site inputs and histories.
4. **Plain-language lender explanation:** assumptions, customer-group demand,
   risks and evidence appear in the dashboard and report.
5. **Safe sharing proposal:** operator pilot and blank request/handover templates
   are included. A proposal is not partner approval or a secure transfer system.

## What the experiments do and do not show

| Evidence | Evaluation boundary | Important limitation |
| --- | --- | --- |
| Synthetic reference | Separate fictional training/calibration/test sites | Synthetic accuracy does not establish field accuracy |
| KIT hourly experiment | Later hours at three already-observed sites; validation-selected models | Prior power is available; Rwanda ECOS is not Bugesera; Haiti is an external reference |
| KIT calendar-only benchmark | Exploratory whole-site power transfer | Poor transfer is retained, not hidden or converted to an accuracy claim |
| Kenya/Nigeria monthly study | Outer held-out operating site, with distinct fitting/calibration sites | Needs operational history; persistence outperforms Ridge; empirical ranges are not Rwanda confidence guarantees |
| Bugesera screening | Fifteen whole-sector public-context rows | No matched consumption labels; ranking is not investment suitability |

Inspect [the actual CSVs](../data/README.md) and [experiment details](OPERATIONAL_EVIDENCE.md).
Real-data experiments support research transparency; they do not certify the
selected planning project or prove capital savings.

## Remaining gaps

- Matched pre-construction surveys and independent monthly metered histories for
  Rwanda sites, including outages, connection dates and service quality.
- Observed first-years adoption and growth, calibrated intervals and transfer
  evaluation for the actual 20-input planning model.
- Current local equipment quotes, tariffs, operating hours, business uptake and
  utility-grid confirmation. Public proxies do not replace field surveys.
- Secure multi-user accounts, role authorization, operator transfer/storage,
  retention, production monitoring and comprehensive accessibility/print QA.
- Independent evidence of improved decisions or avoided capital cost, partner
  approvals, customer willingness to pay and actual commercial traction.

## Safety and reproducibility

The live service blocks all four meter-upload/recalibration routes. Planning
inputs are processed on Render; saved scenarios remain in the visitor's browser.
Use fictional or otherwise non-confidential inputs for review.

The committed snapshots run without external data collection or retraining.
See [setup](../README.md#run-locally), [tests](TEST_REPORT.md),
[source rights](REUSE.md) and [AI assistance](DISCLOSURE.md).
