# Financial evidence and productive-use survey pack

## What this upgrade does

GridSight records sources for exact applied inputs, provides a separate historical cost comparison, and tests productive-use shortfalls. It does not authenticate uploaded documents, certify bankability, or claim demonstrated capital savings. The engineering forecast and synthetic reference model are unchanged.

## 1. Survey the site before changing assumptions

Use anonymous business categories and aggregate counts. Obtain permission; do not put names, phone numbers, account IDs or confidential contracts in this prototype. Keep source documents in the operator's approved system; use an opaque reference here.

For each mill, pump, cold store and other business category, collect:

- Existing operating businesses, equipment already installed, signed prospective commitments and merely interested customers separately. Count shared meters once; avoid counting a business twice as both a shop and a listed machine.
- Measured running power (not just motor nameplate), effective running hours, operating days, idle periods, availability and seasonal throughput. Convert to effective hours per calendar day: hours per operating day × operating days / calendar days. Record sample size and measurement dates.
- Wet/dry/harvest schedules, crop volumes and competing businesses. Do not assume a 24-hour cold-room motor duty cycle or year-round irrigation.
- Willingness and ability to pay, finance access and equipment acquisition timing. Interest is not guaranteed uptake; a commitment is not measured use. Meter histories and follow-up surveys are needed to test growth.
- Itemised supply/installation quotations; currency/date; tax, shipping, civil works, network, generation, storage, meters and connections; contingency; validity; included/excluded items. Separate CAPEX, recurring OPEX, replacements and expansion.
- Maintenance, staff, fuel, travel, collections, equipment support, debt schedule and applicable approved tariff. Do not insert a national utility tariff as an independent mini-grid tariff without checking applicability.

The original 20-input engineering method accepts these values but does not infer them from a survey automatically. Apply reviewed values in the dashboard first.

## 2. Attach evidence to the applied scenario

Download the pack again after changing inputs. `applied_input_guide.json` lists exact field names, applied values and units. Add records to `evidence.json`; retain its project signature and schema. Example structure (replace every placeholder with actual permissioned evidence; do not upload this illustration):

```json
{
  "field": "detailed.equipment.mills.hours_per_day",
  "value": 4,
  "unit": "effective hours / calendar day",
  "kind": "meter_log",
  "source_reference": "REPLACE-WITH-APPROVED-AGGREGATE-REFERENCE",
  "observed_on": "2026-01-15",
  "sample_size": 3
}
```

Kinds: quotation, invoice, survey, meter_log, commitment, tariff_approval. A reference must substantiate the particular field; e.g. a price quote does not substantiate runtime. A commitment does not establish a business-growth rate. Sample size is observed enterprises for a survey/log or number of documents for a quote/approval. The app checks shape, units, dates and exact values, not the truth or adequacy of evidence. Set `permission_confirmed` and `no_personal_data` to true only after review. Upload the JSON in Feasibility. Inputs are not changed by upload. Any project input change detaches the packet; deliberate review and a new signature are required.

Sources more than 365 days old get a review flag (a configurable-workflow convention, not a legal validity rule). Source-attached counts are documentation coverage, not a quality score. Save/Restore, the analysis export and HTML report preserve attached evidence; browser Save is not secure storage. Do not attach confidential or identifying content. The server does not persist the uploaded packet. Delete browser saves if retention is not appropriate.

## 3. Compare costs without replacing the budget

The source catalogue uses AMDA's 2024 report, Figure 12 page 45 and Figure 14 page 46, for Eastern/Southern African historical averages: USD 1,948 capital per connection and USD 26 operating cost per connection/year. These are regional samples, not Rwanda quotations or recommended values. Other EAC countries are not assumed represented or comparable. Site technology, remoteness, customer mix, subsidy/accounting boundaries and cost dates can differ. We do not use per-kW benchmarks because the app's firm deliverable power is not installed PV kWp.

The comparison takes an explicit total metered connection count and a user-sourced local-currency-per-USD rate/date. It divides entered capital cost and modeled expected Year 1 total OPEX by that count and rate. It does not fetch FX, adjust inflation, change the budget or add a second OPEX charge. A rate older than 90 days is flagged for review. A blank capital budget stays unknown. Download the separate comparison for its exact conversion assumptions; it is not automatically attached to the feasibility report.

Primary context links are in `benchmark_sources.json`. CLASP's Rwanda pilot involved 12 entrepreneurs in four districts; it motivates field measurement, not a transferable uptake or runtime coefficient. The Kenya milling guide is methodological, not a current site survey. No local operating-hours distribution was obtained for the selected site.

## 4. Test productive-use downside

Each one-unit alternative now shows no uptake, half the assumed use and full assumed use. They are explicit usage factors, not event probabilities. Additional monthly support costs persist even with no uptake; upfront support capital remains sunk. The calculation caps served energy but does not design a supply upgrade. The headline ranking remains hypothetical developer contribution, not customer business profit. Do not sum alternative options.

## 5. Measure impact before claiming savings

No measured capital-savings value is supplied. To evaluate GridSight in a pilot, register the evaluation BEFORE final designs and outcomes are known:

1. Record eligible sites, operator, anonymous IDs, baseline engineering design and dated itemised budget, the GridSight-assisted design, pricing basis and decision dates. Keep equivalent reliability, service coverage, demand and expansion requirements.
2. Register a comparison strategy and analysis plan: preferably randomised rollout or a defensible matched comparison, not a retrospective cherry-picked before/after story. Record concurrent subsidies, price changes and other design interventions.
3. Collect as-built invoices, financing and replacement obligations, meter energy and interval peaks, outages/unserved demand, connections, productive use and seasonal follow-ups for at least a full year (longer for growth).
4. Report cost differences, utilization, service quality, forecast errors and uncertainty together. Reduced upfront cost with worse service or deferred required expansion is not proven avoided waste. Account for later capital and operating expenses.
5. Independent review must assess attribution and comparability. A scenario proxy, budget difference, or before/after correlation alone cannot establish savings caused by GridSight.

This is a proposed evaluation protocol; no pilot or control group has been created and no savings have been measured.
