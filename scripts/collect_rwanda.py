"""Reproducible public-data import. Run explicitly; never on a dashboard request.

Downloads one Google v3 points tile (~576 MB) to a temporary directory, filters
it to the Rwanda search bounds and >=0.738 confidence, then retains numeric
points for local-radius queries. These are detections, not households.
"""
import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/rwanda"
GOOGLE = "https://storage.googleapis.com/open-buildings-data/v3/points_s2_level_4_gzip/19d_buildings.csv.gz"
GOV = "https://infrastructure.space.gov.rw/server/rest/services/Connection_to_electricity/MapServer/0"


def fetch(url, data=None, timeout=90):
    return urlopen(Request(url, data=data, headers={"User-Agent": "GridSight-Rwanda-research/1.4"}), timeout=timeout)


def save(name, value):
    path = OUT / name
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    temp.replace(path)


def stamp(url, raw):
    return {"url": url, "fetched_at": datetime.now(timezone.utc).isoformat(), "sha256": hashlib.sha256(raw).hexdigest()}


def buildings():
    digest = hashlib.sha256()
    with tempfile.TemporaryDirectory(prefix="gridsight-buildings-") as folder:
        path = Path(folder) / "19d.csv.gz"
        with fetch(GOOGLE) as response, path.open("wb") as dest:
            size = int(response.headers.get("Content-Length", 0))
            if size > 650_000_000:
                raise ValueError("Tile exceeds the 650 MB download budget.")
            done = 0
            while block := response.read(4 * 1024 * 1024):
                dest.write(block); digest.update(block); done += len(block)
                if done > 650_000_000:
                    raise ValueError("Tile exceeds download budget.")
                if done // 50_000_000 != (done - len(block)) // 50_000_000:
                    print(f"Buildings download: {done // 1_000_000} MB", flush=True)
        selected, total = [], 0
        for chunk in pd.read_csv(path, chunksize=500_000, usecols=["latitude", "longitude", "area_in_meters", "confidence"]):
            total += len(chunk)
            keep = chunk.loc[chunk.latitude.between(-2.85, -1) & chunk.longitude.between(28.8, 31) & (chunk.confidence >= .738)]
            selected.append(keep[["latitude", "longitude", "area_in_meters", "confidence"]].to_numpy(dtype=np.float32))
            if total % 5_000_000 == 0:
                print(f"Buildings processed: {total:,}", flush=True)
        values = np.concatenate(selected)
        if len(values) == 0 or not np.isfinite(values).all() or (values[:, 2] <= 0).any():
            raise ValueError("Invalid or empty building detections.")
        # npz is an internal numerical index, not a spreadsheet deliverable.
        np.savez_compressed(OUT / "buildings.npz", points=values)
        save("buildings.meta.json", {"source": "Google Open Buildings v3", "url": GOOGLE,
             "license": "CC BY 4.0", "source_year": 2023, "fetched_at": datetime.now(timezone.utc).isoformat(),
             "source_sha256": digest.hexdigest(), "source_rows": total, "records": len(values),
             "columns": ["latitude", "longitude", "area_m2", "confidence"], "confidence_threshold": .738,
             "bounds": [-2.85, 28.8, -1, 31],
             "note": "Search-bounds extract, not a national-boundary clip. Includes border-area detections. May 2023 inference; imagery may be older. Threshold estimated at 90% precision for tile 19d, not a guaranteed local accuracy. Building use and occupancy unknown."})
        print(f"Saved {len(values):,} filtered building detections", flush=True)


def electricity():
    fields = "objectid,province,district,sector,cell,village,households_energy,electricity_access,electricity_source,productive_use,year"
    url = GOV + "/query?" + urlencode({"where": "1=1", "outFields": fields, "outSR": 4326, "f": "geojson", "resultRecordCount": 2000})
    raw = fetch(url).read()
    result = json.loads(raw)
    if result.get("exceededTransferLimit") or result.get("properties", {}).get("exceededTransferLimit"):
        raise ValueError("Electricity layer exceeded page size; do not publish a partial extract.")
    if not result.get("features"):
        raise ValueError("No electricity records returned.")
    save("electricity.json", {**stamp(url, raw), "source": "MININFRA Bugesera electricity layer", "source_year": 2022,
         "license": "Publicly queryable; redistribution terms not specified", "records": len(result["features"]),
         "note": "Historical mixed-grain point records. household_energy definition/units are not documented; never used as a household total. Not a current service-area boundary or verified unserved-site list.", "features": result["features"]})
    print(f"Saved {len(result['features'])} Bugesera electricity records", flush=True)


def facilities():
    query = '[out:json][timeout:70];area["ISO3166-1"="RW"]["admin_level"="2"]->.a;(nwr["amenity"~"^(school|college|university|hospital|clinic|health_post|marketplace)$"](area.a);nwr["shop"](area.a););out center tags;'
    url = "https://overpass-api.de/api/interpreter"
    raw = fetch(url, urlencode({"data": query}).encode()).read()
    data = json.loads(raw)
    if data.get("remark") or not data.get("elements"):
        raise ValueError("Overpass response incomplete or empty.")
    rows = []
    for obj in data["elements"]:
        point = obj.get("center", obj)
        if "lat" not in point or "lon" not in point:
            continue
        tags = obj.get("tags", {})
        rows.append({"id": f"{obj['type']}/{obj['id']}", "latitude": point["lat"], "longitude": point["lon"],
                     "amenity": tags.get("amenity"), "shop": tags.get("shop")})
    # No names, contact details or individual customer identifiers retained.
    save("facilities.json", {**stamp(url, raw), "query": query, "source": "OpenStreetMap contributors", "license": "ODbL 1.0",
         "records": len(rows), "osm_timestamp": data.get("osm3s", {}).get("timestamp_osm_base"),
         "note": "Mapped objects only; incomplete coverage and possible duplicate node/building representations. Not a census, not proof of operation or electricity use.", "features": rows})
    print(f"Saved {len(rows):,} mapped facility/shop objects", flush=True)


def boundary():
    """Clip the existing search-bounds building index; no repeat tile download."""
    import shapely
    url = "https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM0/"
    raw_meta = fetch(url).read()
    meta = json.loads(raw_meta)
    if not meta["gjDownloadURL"].startswith("https://github.com/wmgeolab/geoBoundaries/"):
        raise ValueError("Unexpected boundary download host; inspect the source before importing.")
    raw = fetch(meta["gjDownloadURL"]).read()
    geometry = json.loads(raw)
    polygons = [shapely.geometry.shape(f["geometry"]) for f in geometry["features"]]
    boundary_shape = shapely.union_all(polygons)
    if not boundary_shape.is_valid:
        boundary_shape = shapely.make_valid(boundary_shape)
    if boundary_shape.is_empty:
        raise ValueError("Empty country boundary.")
    path = OUT / "buildings.npz"
    with np.load(path, allow_pickle=False) as archive:
        points = archive["points"]
    keep = shapely.intersects_xy(boundary_shape, points[:, 1].astype(float), points[:, 0].astype(float))
    selected = points[keep]
    if not 100000 < len(selected) <= len(points):
        raise ValueError("Unexpected country-clipped count; original index retained.")
    temp = OUT / "buildings.clipped.npz"
    np.savez_compressed(temp, points=selected)
    temp.replace(path)
    bmeta = json.loads((OUT / "buildings.meta.json").read_text())
    bmeta["search_bounds_records"] = bmeta.get("search_bounds_records", len(points))
    bmeta["records"] = len(selected)
    bmeta["country_clip"] = {**stamp(meta["gjDownloadURL"], raw), "source": "geoBoundaries gbOpen", "boundary_id": meta["boundaryID"], "year_represented": meta["boundaryYearRepresented"], "license": meta["boundaryLicense"]}
    bmeta["note"] = "Clipped to geoBoundaries Rwanda ADM0 (2021 representation). Not a cadastral or utility boundary. May 2023 building inference; imagery may be older. Tile 19d threshold estimated at 90% precision, not guaranteed local accuracy. Building use and occupancy unknown. Boundary and detection omissions can undercount border catchments."
    save("buildings.meta.json", bmeta)
    save("boundary.json", geometry)
    print(f"Rwanda-boundary clip: {len(selected):,} building detections (from {len(points):,} search-bounds detections)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("layers", nargs="+", choices=["buildings", "electricity", "facilities", "boundary"])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    for layer in args.layers:
        try:
            globals()[layer]()
        except Exception as exc:
            failures.append(layer)
            print(f"{layer}: import failed: {exc}", file=sys.stderr, flush=True)
    sys.exit(bool(failures))
