"""Offline location browsing. Geographic candidates are NOT verified off-grid sites."""
import json
import re
from functools import lru_cache
from .domain import ROOT

URBAN_WORDS = re.compile(r"\b(city|ville|urban|municipality|municipal|town council)\b", re.I)


@lru_cache(maxsize=8)
def catalog(code):
    from .context import country
    country(code)
    path = ROOT / "data/locations" / f"{code}.json"
    if not path.exists():
        raise ValueError("Public location index is unavailable. Enter the administrative names instead.")
    return json.loads(path.read_text())


def level(row):
    return int(row["feature"][-1]) if row["feature"].startswith("ADM") else 0


def within(row, parent):
    n = level(parent)
    return n > 0 and all(parent["codes"][i] and row["codes"][i] == parent["codes"][i] for i in range(n))


def eligible(row, code):
    # A search heuristic, never electricity-access evidence.
    if URBAN_WORDS.search(row["name"]) or (code == "RW" and row["codes"][0] == "12"):
        return False
    if any(tuple(row["codes"][:len(prefix)]) == prefix for prefix in urban_prefixes(code)):
        return False
    return level(row) > 0 or (row["population"] is None or row["population"] < 20000)


@lru_cache(maxsize=8)
def urban_prefixes(code):
    # Exclude descendants of an explicitly urban-labelled administrative area too.
    return tuple(tuple(r["codes"][:level(r)]) for r in catalog(code)["records"]
                 if level(r) and URBAN_WORDS.search(r["name"]) and all(r["codes"][:level(r)]))


def record(code, identifier):
    if not isinstance(identifier, str) or not identifier.isdigit() or len(identifier) > 12:
        raise ValueError("Invalid public location identifier.")
    row = next((r for r in catalog(code)["records"] if r["id"] == identifier), None)
    if not row:
        raise ValueError("Location does not belong to the selected country.")
    return row


def provenance(data):
    return {k: data[k] for k in ("source", "source_url", "license", "fetched_at", "source_sha256")}


def public_location(code, identifier):
    row = record(code, identifier)
    if not eligible(row, code):
        raise ValueError("This location is excluded by the rural-first search filter.")
    data = catalog(code)
    path = [r["name"] for r in sorted(data["records"], key=level) if level(r) and within(row, r)]
    return {"id": row["id"], "label": row["name"], "latitude": row["latitude"], "longitude": row["longitude"],
            "source": "GeoNames", "country_code": code, "timezone": row["timezone"],
            "kind": "administrative reference point" if level(row) else "mapped settlement",
            "administrative_path": path, "modified": row["modified"], "population": row["population"],
            "population_note": "Source value; reference year not supplied. Not a customer or household count.",
            "grid_status": "unknown", "provenance": provenance(data)}


def browse(code, parent_id=None, kind="areas", query="", offset=0):
    from .context import country
    profile = country(code)
    if kind not in ("areas", "local", "cells", "places"):
        raise ValueError("Choose areas, local areas, cells or places.")
    if not isinstance(query, str) or len(query) > 100 or not isinstance(offset, int) or not 0 <= offset <= 200000:
        raise ValueError("Invalid location search or offset.")
    data = catalog(code)
    parent = record(code, parent_id) if parent_id else None
    if parent and (not level(parent) or not eligible(parent, code)):
        raise ValueError("Choose an eligible administrative area.")
    if kind == "local" and (not parent or level(parent) != profile["area_level"]):
        raise ValueError("Choose a parent area before its local subdivision.")
    if kind == "cells" and (not parent or level(parent) != profile["area_level"] + 1):
        raise ValueError("Choose a sector/local subdivision before its cell-level areas.")
    if kind == "areas" and parent:
        raise ValueError("Top-level browsing does not accept a parent.")
    rows = [r for r in data["records"] if eligible(r, code) and (not parent or within(r, parent))]
    target = profile["area_level"] + {"areas": 0, "local": 1, "cells": 2, "places": 0}[kind]
    rows = [r for r in rows if level(r) == target] if kind != "places" else [r for r in rows if not level(r)]
    if query:
        rows = [r for r in rows if query.casefold() in r["name"].casefold()]
    limit = 60 if kind == "places" else 500
    return {"country_code": code, "kind": kind, "parent_id": parent_id, "total": len(rows),
            "next_offset": offset + limit if offset + limit < len(rows) else None,
            "items": [{"id": r["id"], "name": r["name"], "feature": r["feature"]} for r in rows[offset:offset + limit]],
            "reference_location": public_location(code, parent_id) if parent else None,
            "coverage_note": profile["coverage_note"], "provenance": provenance(data),
            "notice": "Rural-first search excludes capitals, administrative seats, urban-labelled areas and settlements with reported population of 20,000 or more. Unknown population is retained. This is not proof of rural character or absence of a main grid. Coverage and administrative links are incomplete."}
