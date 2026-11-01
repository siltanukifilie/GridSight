"""Local public evidence and explicitly provisional inputs for Rwanda screening.

No provider calls on selection. The original synthetic model remains frozen.
Public point objects are NOT a census or a verified mini-grid catchment.
"""
import hashlib
import json
import os
from functools import lru_cache

import numpy as np
from scipy.spatial import cKDTree

from .domain import ROOT, FEATURES, SITE_LIMITS, validate_site

DATA = ROOT / "data/rwanda"
RADIUS_M = 500
EARTH_M = 6371008.8


def xyz(lat, lon):
    lat, lon = np.radians(lat), np.radians(lon)
    return np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))


@lru_cache(maxsize=8)
def read_layer(name):
    path = DATA / name
    return json.loads(path.read_text()) if path.exists() else None


@lru_cache(maxsize=1)
def building_index():
    path = DATA / "buildings.npz"
    if not path.exists() or not read_layer("buildings.meta.json"):
        return None
    with np.load(path, allow_pickle=False) as archive:
        points = archive["points"]
    if os.environ.get("GRIDSIGHT_LOW_MEMORY") == "1":
        return points, None
    return points, cKDTree(xyz(points[:, 0].astype(float), points[:, 1].astype(float)))


@lru_cache(maxsize=1)
def facility_index():
    layer = read_layer("facilities.json")
    if not layer or not layer["features"]:
        return None
    points = layer["features"]
    tree = cKDTree(xyz([p["latitude"] for p in points], [p["longitude"] for p in points]))
    return points, tree


def nearby(index, lat, lon, radius=RADIUS_M):
    if index is None:
        return None
    if index[1] is None:
        # Same spherical chord test as cKDTree, without the country-wide 3D tree.
        # Chunked latitude prefilter bounds temporary memory on free hosting.
        points, matches = index[0], []
        latitude_delta = np.degrees(radius / EARTH_M) + 1e-9
        target = xyz([lat], [lon])[0]
        chord = 2 * np.sin(radius / (2 * EARTH_M))
        for start in range(0, len(points), 100_000):
            chunk = points[start:start + 100_000]
            candidates = np.flatnonzero(np.abs(chunk[:, 0].astype(float) - lat) <= latitude_delta)
            positions = xyz(chunk[candidates, 0].astype(float), chunk[candidates, 1].astype(float))
            keep = np.linalg.norm(positions - target, axis=1) <= chord
            matches.extend((candidates[keep] + start).tolist())
        return matches
    return index[1].query_ball_point(xyz([lat], [lon])[0], 2 * np.sin(radius / (2 * EARTH_M)))


def source_summary():
    buildings = read_layer("buildings.meta.json")
    facilities = read_layer("facilities.json")
    electricity = read_layer("electricity.json")
    rows = [
        {"id": "buildings", "name": "Building detections", "provider": "Google Open Buildings v3", "url": "https://sites.research.google/gr/open-buildings/", "status": "Collected" if buildings else "Not collected", "records": buildings["records"] if buildings else None, "date": "2023 inference", "license": "CC BY 4.0", "use": "Detections within 500 m; household inputs are derived assumptions, not observed occupancy."},
        {"id": "facilities", "name": "Shops, schools & health facilities", "provider": "OpenStreetMap contributors", "url": "https://www.openstreetmap.org/copyright", "status": "Collected" if facilities else "Not collected", "records": facilities["records"] if facilities else None, "date": facilities.get("osm_timestamp") if facilities else None, "license": "ODbL 1.0", "use": "Mapped objects within 500 m. Incomplete coverage; not verified customers. Independent source, not an Energy Access Explorer extract."},
        {"id": "electricity", "name": "Historical electricity context", "provider": "MININFRA · Bugesera", "url": "https://infrastructure.space.gov.rw/server/rest/services/Connection_to_electricity/MapServer/0", "status": "Collected · Bugesera only" if electricity else "Not collected", "records": electricity["records"] if electricity else None, "date": "2022 layer", "license": "Public query; reuse terms unspecified", "use": "Historical sector context only. Ambiguous household field is excluded from demand inputs."},
        {"id": "viirs", "name": "Nighttime lights", "provider": "NOAA VIIRS / Earth Observation Group", "url": "https://eogdata.mines.edu/products/vnl/", "status": "Not collected", "records": None, "date": None, "license": "Check selected product terms", "use": "Radiance layer still needed. Brightness alone cannot prove demand or grid access."},
        {"id": "gridfinder", "name": "Grid lines", "provider": "GridFinder", "url": "https://gridfinder.org/", "status": "Not collected", "records": None, "date": None, "license": "Check selected release terms", "use": "Predicted lines require utility verification; current grid distance is unavailable."},
        {"id": "eae", "name": "Settlements & services", "provider": "WRI Energy Access Explorer", "url": "https://www.energyaccessexplorer.org/", "status": "Source identified", "records": None, "date": None, "license": "Layer-specific", "use": "Rwanda layer access and attribution still to be integrated. OSM is shown separately."},
        {"id": "mtf", "name": "Household energy surveys", "provider": "World Bank Multi-Tier Framework", "url": "https://datacatalog.worldbank.org/search/dataset/0039986/rwanda-multi-tier-framework-mtf-survey", "status": "Source identified", "records": None, "date": None, "license": "Dataset-specific access terms", "use": "No household microdata ingested. Survey priors are not yet calibrated into this model."},
        {"id": "meters", "name": "Metered consumption", "provider": "Mini-grid operator", "url": None, "status": "Partner needed", "records": None, "date": None, "license": "Permission required", "use": "Required for real-site training and independent validation. No actual meter data collected."},
        {"id": "costs", "name": "Cost & performance benchmarks", "provider": "ESMAP / AMDA", "url": "https://www.esmap.org/mini-grids", "status": "Source identified", "records": None, "date": None, "license": "Report-specific", "use": "No extracted cost benchmark used. Tariff, supply, costs and debt are editable illustrative defaults."},
        {"id": "gep", "name": "Electrification planning", "provider": "World Bank / ESMAP GEP", "url": "https://energydata.info/dataset/rwanda-global-electrification-platform-gep", "status": "Download requires login", "records": None, "date": "Catalog updated 2025-06-12", "license": "CC BY 4.0", "use": "Settlement/scenario download is gated by sign-in. No scenario data collected or substituted."},
    ]
    return {"scope": "Rwanda now · East Africa later", "radius_m": RADIUS_M, "layers": rows,
            "notice": "Collected public geography and remote-sensing detections are separate from the synthetic demand model. No real-site validation or financial viability is established."}


def historical_grid(location):
    layer = read_layer("electricity.json")
    path = [p.casefold().strip() for p in location.get("administrative_path", [])]
    if not layer or "bugesera" not in path:
        return {"matched_records": 0, "status": "Unknown", "note": "No matching historical sector context. Confirm current utility coverage."}
    rows = [f["properties"] for f in layer["features"] if str(f["properties"].get("sector") or "").casefold().strip() in path]
    on_grid = sum(str(r.get("electricity_source")).casefold() in ("on-grid", "1") and str(r.get("electricity_access")).casefold() in ("yes", "1") for r in rows)
    return {"matched_records": len(rows), "on_grid_records": on_grid, "source_year": 2022,
            "status": "Historical on-grid records in sector" if on_grid else "Current access unknown",
            "note": "Sector match, not a village/service-area match. Historical connection records do not establish current access at this point. Check existing and planned utility service before development."}


@lru_cache(maxsize=256)
def profile_at(location_json):
    location = json.loads(location_json)
    lat, lon = location["latitude"], location["longitude"]
    buildings = building_index()
    bids = nearby(buildings, lat, lon)
    count = len(bids) if bids is not None else None
    area = round(float(buildings[0][bids, 2].astype(float).sum()), 1) if bids else (0 if bids == [] else None)
    facilities = facility_index()
    fids = nearby(facilities, lat, lon)
    objects = [facilities[0][i] for i in fids] if fids is not None else []
    mapped = {"shops": sum(bool(r.get("shop")) for r in objects),
              "schools": sum(r.get("amenity") in ("school", "college", "university") for r in objects),
              "clinics": sum(r.get("amenity") in ("hospital", "clinic", "health_post") for r in objects),
              "markets": sum(r.get("amenity") == "marketplace" for r in objects)}
    inputs, reasons = {}, []
    # A small pilot catchment; cap explicit to stay inside the model's input contract.
    raw_households = round(count * .70) if count else 150
    inputs["households"] = max(1, min(1500, raw_households))
    reasons.append({"field": "households", "value": inputs["households"], "kind": "Derived assumption" if count else "Placeholder",
                    "basis": f"{count} building detections × 70% assumed residential share × 1 household/building; capped at 1,500 for this pilot. Not verified occupancy." if count else "No usable building detections: 150-household illustrative starting case, not a local estimate."})
    for key in ("shops", "schools", "clinics"):
        fallback = round(inputs["households"] * .05) if key == "shops" else int(inputs["households"] >= 100) if key == "schools" else 0
        proposed = mapped[key] if mapped[key] else fallback
        inputs[key] = min(SITE_LIMITS[key][1], proposed)
        reasons.append({"field": key, "value": inputs[key], "kind": "Mapped-object proxy" if mapped[key] else "Placeholder",
                        "basis": f"{mapped[key]} mapped objects in 500 m; assumes one operating customer per object, capped at model limit. Duplicates/coverage require field checking." if mapped[key] else "No matching mapped objects. Planning placeholder, not verified absence or a local census."})
    for key, value in {"mills": 0, "pumps": 0, "cold_rooms": 0, "uptake": .75, "appliance_index": 1}.items():
        inputs[key] = value
        reasons.append({"field": key, "value": value, "kind": "Placeholder", "basis": "Unsurveyed planning assumption; zero equipment means unknown assumed none, not confirmed absence." if value == 0 else "Illustrative planning default; not measured locally."})
    meta = {name: {k: v for k, v in (read_layer(name) or {}).items() if k not in ("features", "query")} for name in ("buildings.meta.json", "facilities.json", "electricity.json")}
    fingerprint = hashlib.sha256(json.dumps([location, meta], sort_keys=True).encode()).hexdigest()[:24]
    return {"id": fingerprint, "location": location, "radius_m": RADIUS_M,
            "building_detections": count, "building_area_m2": area,
            "mapped_facilities": mapped if fids is not None else None, "mapped_object_ids": [o["id"] for o in objects],
            "input_basis": reasons, "suggested_inputs": inputs, "historical_grid": historical_grid(location),
            "sources": meta, "data_pack": source_summary(),
            "notice": "Preliminary 500 m-radius screen, not an administrative boundary or confirmed service area. Catchments may overlap or cross borders. Do not sum different place profiles. Local input uncertainty is not included in the model range. Financial defaults are illustrative, not public cost benchmarks."}


def location_profile(location):
    if not location or location.get("country_code") != "RW" or location.get("latitude") is None or location.get("longitude") is None:
        return None
    return profile_at(json.dumps(location, sort_keys=True))


def initial_project(raw):
    from .context import validate_context, scenario_defaults
    from .feasibility import PLANNING_DEFAULTS
    if not isinstance(raw, dict) or not isinstance(raw.get("location"), dict):
        raise ValueError("Choose an East African location.")
    loc = raw["location"]
    code = loc.get("country_code")
    public_proxy = code == "RW" and loc.get("source") != "user_entered_administration"
    context = validate_context({"country_code": code, "location": loc, "input_origin": "public_proxy" if public_proxy else "user_entered", "assumed_fields": list(FEATURES)})
    if not context["location"]:
        raise ValueError("Choose an East African location.")
    boundary = read_layer("boundary.json")
    if boundary and public_proxy:
        from shapely.geometry import shape, Point
        loc = context["location"]
        if not any(shape(f["geometry"]).covers(Point(loc["longitude"], loc["latitude"])) for f in boundary["features"]):
            raise ValueError("Point is outside the imported Rwanda land boundary. Check the coordinates or choose a nearby Rwanda settlement.")
    profile = location_profile(context["location"])
    suggested = profile["suggested_inputs"] if profile else {"households": 150, "shops": 8, "schools": 1, "clinics": 0, "mills": 0, "pumps": 0, "cold_rooms": 0, "uptake": .75, "appliance_index": 1}
    site = validate_site({**suggested, "id": "CUSTOM", "name": context["location"]["label"][:100],
                          "district": (" / ".join(context["location"].get("administrative_path", [])) or context["country"])[:100], "archetype": "Custom"})
    assumptions = scenario_defaults(code)
    if not public_proxy:
        assumptions.update(capacity_kwh=0, firm_power_kw=0)
    return {"site": site, "context": context, "connection": {"enabled": True}, "detailed": {"enabled": True}, "assumptions": assumptions, "planning": dict(PLANNING_DEFAULTS)}
