# Data catalogue

GridSight keeps **public context**, **measured-study data**, **model outputs** and
**synthetic demos** separate. All files below are in GitHub. Large raw source
archives and confidential operator records are not required to run the app.

## Start with these tables

| File | Rows | Grain / unit | Meaning |
| --- | ---: | --- | --- |
| [Bugesera features](processed/bugesera_site_features.csv) | 15 | Administrative sector; 78 fields | Canonical public/derived context, not service-area demand |
| [Sector ranking](processed/bugesera_site_priority_ranking.csv) | 15 | Sector; relative score | Candidate screening, not feasibility or investment rating |
| [Source sector snapshot](prepared/bugesera_sectors.csv) | 15 | Sector; 71 fields | Pinned source behind the canonical table |
| [Hourly measured features](operational/operational_features.csv) | 1,540 | Qualified hourly example; target in kW | KIT-derived calendar/past-power inputs and observed delivered power |
| [Hourly predictions](operational/predictions.csv) | 4,216 | Site/model/split/hour; kW | Model outputs and observed targets are separate columns |
| [Hourly metrics](operational/metrics.csv) | 48 | Site/model/split; kW and percent | Errors for five ML families and three baselines |
| [Held-out operational predictions](transfer_uncertainty/held_out_predictions.csv) | 237 | Site/origin/horizon; kWh | Kenya/Nigeria forecast errors requiring prior consumption |
| [Synthetic sites](synthetic_sites.csv) | 500 | Fictional site | Legacy training/calibration/test data |
| [Synthetic monthly records](synthetic_monthly.csv) | 18,000 | Fictional site × simulated month; kWh | 36 simulated months per site, not meter readings |

The [machine-readable catalogue](catalog.json) records counts and evidence types.
Tests check it against the actual files. Open a CSV in GitHub or use its
**Raw / Download raw file** action.

## Geography and source context

| Directory / file | Contents | Important distinction |
| --- | --- | --- |
| [locations/](locations/) | GeoNames extracts for RW, UG, KE, TZ, BI, SS, SO and CD | Dated administrative coverage, not utility boundaries |
| [Building index](rwanda/buildings.npz) | 4,251,978 filtered building detection points | Points, not footprint polygons, households or connections |
| [Building metadata](rwanda/buildings.meta.json) | Provenance, clipping and thresholds | Google Open Buildings v3 |
| [OSM facilities](rwanda/facilities.json) | 2,232 facility/shop objects | Incomplete mapped inventory, not a field survey |
| [Rwanda boundary](rwanda/boundary.json) | Country clipping geometry | Not an authoritative mini-grid service area |
| [Financial references](financial_benchmarks.json) | Dated regional benchmarks | Not locally verified project costs/tariffs |
| [Load shapes](load_shapes.json) | Seven RAMP-generated hourly shapes | Simulated timing, not measured peak demand |

The building index is compressed because it is large. Inspect it with NumPy:

```python
import numpy as np
points = np.load("data/rwanda/buildings.npz", allow_pickle=False)["points"]
print(points.shape)  # (4251978, 4)
# Columns: latitude, longitude, area_m2, confidence
```

## Provenance and dictionaries

- Bugesera: [source manifest](prepared/source_manifest.csv),
  [source dictionary](prepared/source_dictionary.csv),
  [derived features](prepared/engineered_dictionary.csv),
  [snapshot inventory](prepared/inventory.json),
  [canonical table metadata](processed/bugesera_site_features_metadata.json).
- KIT: [README](operational/README.txt),
  [feature dictionary](operational/feature_dictionary.csv),
  [source manifest](operational/source_manifest.csv),
  [splits](operational/split_summary.csv), [protocol](operational/protocol.json),
  [inventory](operational/inventory.json).
- Kenya/Nigeria: [summary](transfer_uncertainty/summary.json),
  [split audit](transfer_uncertainty/split_audit.csv),
  [site metrics](transfer_uncertainty/site_metrics.csv),
  [inventory](transfer_uncertainty/inventory.json).
- Synthetic reference: [metadata](metadata.json),
  [data card](../docs/DATA_CARD.md), [model card](../docs/MODEL_CARD.md).

Source manifests can reference upstream pack paths. Those are provenance records,
not promises that all raw inputs or the complete training environment are included.
The app ships compact study snapshots. [Rebuild guide](../scripts/README.md).

## Interpretation rules

1. Blank CSV / JSON null means **unavailable**, not zero. Bugesera has no matched
   monthly energy or peak-demand labels. Unknown device/equipment totals stay blank.
2. Processed Bugesera `site_name` means a **sector candidate**, not an operating
   mini-grid. Use stable identifiers and the documented administrative hierarchy.
3. Sector household totals must not replace project catchment counts. Census is
   2022; buildings are a 2023 release over older boundaries; historic grid distance
   does not confirm current service. Non-grid does not mean unelectrified.
4. Do not join KIT or Kenya/Nigeria outcomes to Bugesera rows. Sites, periods,
   units and forecasting tasks are different.
5. KIT model comparisons test later hours at observed sites. Kenya/Nigeria tests
   hold out operating sites but require prior consumption. Neither establishes
   the current Rwanda pre-construction model's accuracy.
6. Synthetic observations remain labelled; never mix them into measured studies
   without preserving origin and study design.

## Deliberately excluded

Customer identifiers, private operator files, user-saved exports, private update
registries, survey microdata, restricted EAE layers, noncommercial Tanzania
telemetry, full third-party reports and the historical MININFRA extract with
unconfirmed redistribution terms.

Source rights differ: CC BY, CC BY-SA, ODbL and unconfirmed general reuse terms
for limited census facts. No blanket licence covers this compilation. See
[reuse](../docs/REUSE.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).

**Data integration and analysis by the GridSight Team. Original sources retain
their attribution.**
