# Rwanda data pipeline — v1.4

31 October 2026. Active country: Rwanda. East Africa remains future scope.

## What was actually collected

| Source | Stored records | Meaning and limits |
| --- | ---: | --- |
| Google Open Buildings v3 | 4,251,978 | Building detections at confidence >= 0.738, clipped to the geoBoundaries Rwanda ADM0 land outline. May 2023 inference on potentially older imagery. Not occupancy, residential use, households or consumption. |
| OpenStreetMap / Overpass | 2,232 | Rwanda shop and selected education, health and market objects. Names/contact details excluded. Incomplete mapping, possible duplicate node/building representations, unverified operation. |
| MININFRA Bugesera electricity | 236 | Historical 2022 mixed-grain points. Sector-level context only; not current village coverage. Ambiguous `households_energy` field is not used as household count. |
| GeoNames Rwanda gazetteer | 12,808 | Administrative/place records from the existing public import. 9,788 settlements pass the rural-first search heuristic; 27 districts remain after excluding Kigali. Not an official current administrative register. |
| geoBoundaries Rwanda ADM0 | 1 country feature | 2021 representation, CC BY 4.0. Used to clip building points and reject automatic points outside the imported land geometry. Not cadastral or utility coverage. |

Primary references: [Google](https://sites.research.google/gr/open-buildings/), [OSM](https://www.openstreetmap.org/copyright), [MININFRA layer](https://infrastructure.space.gov.rw/server/rest/services/Connection_to_electricity/MapServer/0), [GeoNames](https://download.geonames.org/export/dump/readme.txt), [geoBoundaries metadata](https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM0/).

The Google source tile `19d` contains 22,106,220 detections. The confidence/bounding-box filter retained 6,243,498; the final country clip retained 4,251,978. The larger intermediate count is **not a Rwanda national building count**. The numeric dataset stores latitude, longitude, footprint area in m² and confidence as float32. Source ZIP SHA-256, boundary hash, dates, filter and licence are recorded in `data/rwanda/buildings.meta.json`. All layers are dated snapshots, not live telemetry.

## Numbered implementation steps

1. **Collect — completed for the rows above.** Run `scripts/collect_rwanda.py`; import only public fields needed for screening. Preserve source URL/date/checksum. No project/customer information is sent to source providers.
2. **Clean — completed for these layers.** Validate finite coordinates/areas, check full government response and Overpass completion, threshold Google detections, clip the country geometry. Keep original field semantics. No invented local observations.
3. **Index — completed.** Build local numerical spatial indexes. Radius is 500 metres geodesic distance around the selected gazetteer/survey point. Catchments are not village boundaries, may overlap, and must not be summed. Border clipping and mapping omissions can undercount.
4. **Prepare initial inputs — completed.** Households = round(detections × assumed 70% residential share × one household/building), bounded to 1–1,500. No usable detections means a labelled 150-household illustrative placeholder, not a local forecast input observed from data. Shops/schools/clinics use mapped-object proxies where positive, capped at the existing model limits. Where no objects are mapped, labelled planning placeholders apply. Productive equipment defaults to unknown/assumed none; uptake 75%, appliance index 1. Every initial model input remains unverified.
5. **Open dashboard — completed.** Rwanda → district → sector → settlement opens the preliminary analysis immediately. A failed preparation preserves the previous valid project; survey entry is a fallback. Fresh illustrative supply/money defaults come from the existing Rwanda model configuration, not another project or extracted public benchmarks. Capital budgets remain unknown.
6. **Explain/export — completed.** Both roles retain day/week/month/year demand, low/expected/high cases, growth, productive uses, sizing risk, stress cases and reports. Locations shows initial vs current inputs and the complete source-status table. Report and ZIP include the server-generated location profile and provenance. The compact public source pack includes OSM objects and building metadata; the separate numerical building dataset is also downloadable. Raw government records are excluded from the redistributable pack while reuse terms are unspecified.
7. **Validate — software checks completed; field accuracy open.** The original synthetic model and its training data are unchanged. Public proxies do not validate the predicted consumption; model ranges exclude uncertainty in those proxies. Current utility coverage, local customer/equipment counts, real financial terms and independent consumption measurements still require evidence.

## Not collected or not integrated

- **NOAA VIIRS/EOG:** source identified; no radiance raster collected or sampled. No fabricated radiance values.
- **GridFinder:** source identified; no line layer or verified distance-to-grid computed. Do not read unknown distance as distant/unserved.
- **WRI Energy Access Explorer:** source identified, Rwanda layer access not integrated. The OSM import is an independent source, not relabelled EAE data.
- **World Bank MTF:** survey source identified; no household microdata imported and no survey-derived energy priors fitted.
- **Operator meters:** partner needed. No real-site training/validation data, no measured demand performance claim.
- **ESMAP/AMDA:** references identified, but no cost benchmark table extracted or calibrated. All prefilled tariff/cost/debt/supply figures remain illustrative.
- **GEP:** public catalog and licence verified; settlement/scenario resource pages require sign-in. No account created, sign-in bypass attempted or scenario values substituted.

The source manifest reports these states individually. Source links, failed downloads and the earlier external synthetic templates are not counted as collected observations.

## Refresh and reproduction

From the app folder: `.venv/bin/python scripts/collect_rwanda.py electricity facilities buildings boundary`. Google tile download is about 576 MB; its temporary archive is removed automatically after processing. Use `boundary` alone to clip an existing search-bounds index without re-downloading the tile. Do not run refreshes during a live report session: preserve a copy of the previous snapshot, refresh, rerun tests, then restart the service to clear in-memory indexes.

The importer writes only `data/rwanda/`. It does not edit the user's separate data-pack directories, synced `sources/`, original synthetic training data, or model. The API accepts only canonical Rwanda places or validated coordinates for automatic screens. Source evidence is computed server-side; client-supplied source counts are not trusted.

## Acceptance still open

Supported browser control fails at app-server initialization, so desktop/mobile visuals, real clicks, map interaction and browser printing have not been verified. API/handler tests are not substitutes for this check. No public deployment, financial commitment, actual lending decision or customer outreach occurred.
