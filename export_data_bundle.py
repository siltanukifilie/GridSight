"""Export unchanged GridSight source datasets with provenance and explicit exclusions."""
from pathlib import Path
import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone

import numpy as np

from src.connection import DEFAULTS as CONNECTION_DEFAULTS, LIMITS as CONNECTION_LIMITS, METHOD
from src.feasibility import PLANNING_DEFAULTS
from src.rwanda_data import source_summary

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "exports/gridsight-data-v1.5-2026-10-31.zip"
FILES = [
    "data/synthetic_sites.csv", "data/synthetic_monthly.csv", "data/metadata.json",
    "data/load_shapes.json", "config/assumptions.json",
    "data/locations/RW.json", "data/rwanda/buildings.npz",
    "data/rwanda/buildings.meta.json", "data/rwanda/boundary.json",
    "data/rwanda/facilities.json",
    "reports/test_predictions.csv", "reports/evaluation.json",
    "docs/DATA_CARD.md", "docs/MODEL_CARD.md", "docs/FEASIBILITY_METHODS.md",
    "docs/RWANDA_DATA_PIPELINE.md", "THIRD_PARTY_NOTICES.md",
]
README = """GRIDSIGHT DATA EXPORT
Feature version 1.5. Synthetic dataset/model version 1.0.0.
Export date: 31 October 2026. Rwanda active; East Africa expansion is future work.

START HERE
data/synthetic_sites.csv: 500 fictional communities, one row per site.
data/synthetic_monthly.csv: 18,000 simulated records, 500 sites x 36 months.
Join site_id in the monthly table to id in the site table.
The target is average customer energy in the first 12 simulated months,
in kWh/month. Months 1-36 are relative simulated months, not calendar dates.
These CSV files are unchanged and open in Excel, Python, R or a text editor.
See docs/DATA_CARD.md for fields, units, preparation and limitations.

TRAINING AND TESTING
300 training sites, 100 calibration sites, 100 held-out test sites.
All months for each site stay in one partition.
reports/test_predictions.csv contains 100 synthetic test-site predictions.
No authentic meter readings or verified real-site demand labels are included.
Public geographic records did not become consumption training labels.

PUBLIC RWANDA LOCATION DATA
data/locations/RW.json: attributed GeoNames administrative/place snapshot.
The app applies rural-first filters; all records in the snapshot are not
necessarily eligible sites. A place record does not prove off-grid status.

data/rwanda/buildings.npz: the exact numerical index used by the app.
Contains 4,251,978 building detections, NOT households or connected customers.
NumPy archive key: points. Shape: (4251978, 4). Type: float32.
Column order: latitude, longitude, area_m2, confidence.
Filtered at confidence >= 0.738 and clipped to the included Rwanda outline.
Example: np.load("data/rwanda/buildings.npz", allow_pickle=False)["points"]
This is a numerical point extract, not building-footprint polygons.
Google Open Buildings v3, May 2023 inference. Imagery can be older.
Source URLs, dates, transformations and licence are in buildings.meta.json.

data/rwanda/boundary.json: geoBoundaries Rwanda ADM0 clipping boundary.
data/rwanda/facilities.json: OpenStreetMap facility/shop point objects.
These sources initialize provisional counts within 500 metres of a location.
Building use, occupancy, customer connections and business operations are
not verified by these detections. This is dated public data, not live metering.
Keep the datasets separate and preserve each source's attribution/licence.

GROWTH, PROFILE AND FINANCIAL INPUTS
config/assumptions.json: original synthetic generator and scenario assumptions.
config/connection_growth.json: current connection-growth defaults and method.
config/feasibility_defaults.json: low/high factors and optional financial inputs.
data/load_shapes.json: RAMP-generated hourly shares, not measured power.
The new post-connection ramp is an editable assumption-based transformation,
not a measured dataset or a retrained model. New projects enable it; old/API
scenarios can leave it off. The original model estimate is interpreted as an
assumed mature reference. Defaults are not measured Rwanda adoption rates.
This bundle exports source data and defaults, not the currently selected
browser project's inputs. Use Export report in the app for that scenario.

EXCLUDED OR UNAVAILABLE
The 236 historical MININFRA Bugesera electricity records are not redistributed:
the service's reuse terms are unspecified. Their URL, status, date, count
and limitations remain in source_manifest.json and the source documentation.
The app uses them only as historical sector context, not household energy
labels or proof of a site's current grid access.
VIIRS, GridFinder, WRI Energy Access Explorer layers, MTF microdata,
ESMAP/AMDA cost tables and GEP scenario data were not collected.
No missing layer is replaced with invented observations.
Optional in-memory World Bank national-context fetches are not included.
They do not train or alter local demand forecasts.

PROVENANCE AND INTEGRITY
Original data files are copied byte-for-byte into this ZIP; no records were
regenerated, rounded or relabelled. checksums.json records their SHA-256.
source_manifest.json distinguishes collected, missing and partner-needed layers.
data_inventory.json records verified sizes/counts and the original model hash.
Preserve THIRD_PARTY_NOTICES.md and the per-source metadata when sharing.
The OSM extract retains ODbL terms; it is not relicensed as synthetic data.

No real metered-site validation or investment viability is established.
"""


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    if OUTPUT.exists():
        raise FileExistsError(f"Existing export preserved: {OUTPUT}")
    for name in FILES:
        if not (ROOT / name).is_file():
            raise FileNotFoundError(name)
    sites = csv_rows(ROOT / "data/synthetic_sites.csv")
    months = csv_rows(ROOT / "data/synthetic_monthly.csv")
    tests = csv_rows(ROOT / "reports/test_predictions.csv")
    assert len(sites) == 500 and len(months) == 18000 and len(tests) == 100
    assert len({s["id"] for s in sites}) == 500
    assert len({(m["site_id"], m["month"]) for m in months}) == 18000
    assert {m["site_id"] for m in months} == {s["id"] for s in sites}
    with np.load(ROOT / "data/rwanda/buildings.npz", allow_pickle=False) as a:
        assert a["points"].shape == (4251978, 4)
        assert str(a["points"].dtype) == "float32"
    locations = json.loads((ROOT / "data/locations/RW.json").read_text())
    facilities = json.loads((ROOT / "data/rwanda/facilities.json").read_text())
    inventory = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "active_country": "RW", "feature_version": "1.5", "synthetic_version": "1.0.0",
        "synthetic_sites": len(sites), "synthetic_monthly_records": len(months),
        "held_out_synthetic_predictions": len(tests),
        "rwanda_geographic_records": len(locations["records"]),
        "building_detections": 4251978, "osm_objects": len(facilities["features"]),
        "real_metered_sites": 0,
        "frozen_model_sha256": sha(ROOT / "models/forecast.joblib"),
        "files": [{"path": name, "bytes": (ROOT / name).stat().st_size} for name in FILES],
        "excluded": ["MININFRA raw extract: reuse terms unspecified",
                     "Other EAC countries: not active Rwanda scope",
                     "Session-only national statistics and browser-selected scenario"],
    }
    checksums = {name: sha(ROOT / name) for name in FILES}
    extra = {
        "README.txt": README,
        "data_inventory.json": json.dumps(inventory, indent=2),
        "checksums.json": json.dumps(checksums, indent=2),
        "source_manifest.json": json.dumps(source_summary(), indent=2),
        "config/connection_growth.json": json.dumps({
            "defaults": CONNECTION_DEFAULTS, "limits": CONNECTION_LIMITS,
            "new_projects_enabled": True, "source": "GridSight planning assumptions, not observations",
            "method": METHOD}, indent=2),
        "config/feasibility_defaults.json": json.dumps(PLANNING_DEFAULTS, indent=2),
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "x", zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(ROOT / name, name,
                          compress_type=zipfile.ZIP_STORED if name.endswith(".npz") else zipfile.ZIP_DEFLATED)
        for name, value in extra.items():
            archive.writestr(name, value)
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(FILES) + len(extra)
        assert "data/rwanda/electricity.json" not in archive.namelist()
        for name, expected in checksums.items():
            with archive.open(name) as stream:
                assert hashlib.file_digest(stream, "sha256").hexdigest() == expected, name
        assert json.loads(archive.read("config/connection_growth.json"))["defaults"] == CONNECTION_DEFAULTS
    print(json.dumps({"file": str(OUTPUT), "bytes": OUTPUT.stat().st_size,
                      "original_files_verified": len(FILES), "inventory": {
                          k: v for k, v in inventory.items() if k not in ("files", "excluded")
                      }}, indent=2))


if __name__ == "__main__":
    main()
