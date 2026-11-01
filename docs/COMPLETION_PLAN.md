# Completing the decision-support MVP — 31 October 2026

Current request: include the five pictured deliverables and fix early post-connection demand growth within the Rwanda-only automatic dashboard. East Africa remains future scope. Follow the v1.5 extension in IMPLEMENTATION_PLAN.md and the connection method in FEASIBILITY_METHODS.md. The numbered features below remain implemented. Preserve the existing two roles, local app, short copy, synthetic-data notices, and existing calculations/exports unless explicitly extended below.

1. Add separately defined Low / Expected / High demand cases, with editable demand factors and comparable three-year demand, cash, repayment and capacity results. Keep these scenarios distinct from calibrated prediction bounds.
2. New projects: build a 36-month connection/appliance/existing-use adoption path from an assumed mature reference, with optional connection month. Compute Year 1 totals from the path without normalizing them back to the reference. Retain old normalized calculations only for legacy scenarios with connection growth off. Show first 12 months in the Yearly chart; allow zero and negative underlying growth honestly.
3. Compare one added mill, pump or cold room: incremental demand, energy actually served, grid revenue/contribution, peak risk, and optional developer support-cost payback. Rank by incremental grid contribution, not claimed business profitability. Options are alternatives, not automatically added together.
4. Screen under-sizing and potential over-sizing for all three cases and years: unmet energy, illustrative peak deficit, unused energy capacity, spare firm power, lost-sales exposure and optional capacity-linked capital exposure. Do not equate headroom with waste or suggest solar/battery sizes without dispatch studies.
5. Deliver a comprehensive downloadable feasibility-screening report and reproducible CSV/JSON package covering all requested features, exact assumptions, calculations, warnings and a real-evidence checklist. Allow optional user-entered capital budgets; never invent verified prices or lending approval.
6. Add a concise Feasibility workspace to both roles. Preserve drafts, saved settings, role switching and export consistency. Technical assumptions remain developer-editable; investor financial/planning adjustments remain shared and disclosed.
7. Test independent numerical examples, growth conservation, zero/negative margins, capacity limits, role consistency, input validation, downloads, markup and interaction handlers. Refresh prepared example reports; restart and health-check the local app. Browser QA remains separate if browser-control access is unavailable.

Scope boundary: feature-complete synthetic planning software is achievable here; real-site engineering feasibility, verified commercial demand, permissions and lender approval require external evidence. Demo recording and presentation deliverables remain deferred.

## Completion record

Steps 1–6 are implemented. Step 7 automated verification passed: 150 Python tests, 38 interface-logic tests, JavaScript/launcher syntax checks, live service health and standalone report download. All three prepared example reports were refreshed. The service runs feature version 1.1 at the existing local address.

Browser interaction, responsive layout and printed-report visual checks remain pending because supported browser discovery failed during app-server initialization. No claim of real-site validation, lending readiness, production hosting or final submission is made.
## Extension completed — 31 October 2026, v1.2

The later “remaining ones + live locations” request adds a sixth Locations view, opt-in GeoNames search/OSM map/device-coordinate drafts, World Bank public country context, guided missing inputs, Rwanda/Uganda currency configuration, and a frozen-model CSV consumption-comparison tool. Commercial offer and unconfirmed paying-customer status are visible. Current verification is 211 Python + 48 interface-logic checks, plus live public-data/report endpoints; the original v1.1 counts above are historical.

Still open: supported browser/mobile/print/map QA; genuine measured-site and country-transfer validation; evidence of a paying customer and validated pricing. No public hosting, customer outreach, payment integration, demo video, pitch deck or one-page summary was performed.

## Historical scope — eight-country discovery, v1.3 (superseded)

User confirmed all eight EAC countries. The location-first redesign, public offline geography, fresh-input workflow, rural-first search filters, grid-access source/date records and transparent two-role review are implemented. Current verification: 246 Python + 68 logic checks; original counts above are historical. The source model remains synthetic Rwanda-context, unchanged.

Use the numbered v1.3 extension in `IMPLEMENTATION_PLAN.md` and the latest sequence in `TEST_REPORT.md`. Remaining gates are supported browser acceptance, current local utility/administrative evidence, real consumption calibration/validation and commercial proof. Presentation deliverables remain deferred.
