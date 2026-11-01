"""Read-only public evidence. Never supplies model features or consumption labels.

Only reviewed, checksum-pinned summaries are bundled; no external calls, meter
uploads, training, imputation, or cross-site label joins happen in this module.
"""
import csv
import hashlib
import io
import json
import math

from .domain import ROOT
from .operational_evidence import summary as operational_summary, write_archive as write_operational_archive

DATA = ROOT / "data/prepared"
SECTOR_FILES = ("bugesera_sectors.csv", "source_dictionary.csv", "engineered_dictionary.csv", "source_manifest.csv")
BENCHMARK_FILES = ("benchmark_metrics.csv", "benchmark_quality.csv", "benchmark_protocol.json", "meter_site_catalog.csv")
PREPARATION_FILES = ("preparation_report.json", "preparation_summary.csv", "training_contract.json", "original_20_feature_coverage.csv")
SCOPE = "Bugesera administrative sector; not a cell or mini-grid service area"
NOTICE = ("Sector context does not replace service-area inputs. Census 2022 and historical map proxies are not current customer counts. "
          "Missing values remain unavailable. No matched monthly consumption or peak labels exist for these sectors.")
BENCHMARK_NOTICE = ("Exploratory three-site power-transfer benchmark only. Rwanda ECOS is not Bugesera; Haiti is outside East Africa. "
                    "These results do not validate the current 20-input estimate, monthly kWh, peak sizing, growth or confidence ranges.")
MODEL_STATUS = {"current_model_validation": "Pending matched pre-connection inputs and monthly metered histories",
                "growth": "36-month engineering scenarios; no observed multi-year growth labels",
                "range": "Low / expected / high scenarios, not calibrated confidence intervals",
                "integration": "Public context and completed hourly-model evidence only; monthly calculation and frozen reference model unchanged"}
TEXT_FIELDS = {"sector", "sector_key", "osm_coverage_note", "operator_data_status", "geography_warning",
               "osm_snapshot_date", "source_ids", "gridfinder_network_vintage", "nightlights_status", "label_status"}
CATEGORIES = [
    {"name": "Observed census / sensor data", "meaning": "Published counts or measured delivered power; retain year, unit and geographic scope."},
    {"name": "Map / remote-sensing proxies", "meaning": "Detected buildings, mapped services and historical grid/light proxies; verify locally."},
    {"name": "Derived features", "meaning": "Calculations from source values; not new observations."},
    {"name": "User assumptions", "meaning": "Editable service-area, equipment, growth and finance inputs; not filled from sector totals."},
    {"name": "Synthetic demos", "meaning": "Fictional communities and synthetic reference-model tests remain separate."},
    {"name": "Unavailable inputs", "meaning": "Missing measurements stay null, not zero or guessed labels."},
]


def _bundle(names):
    """Fail closed on absent, changed or malformed snapshots, without breaking planning."""
    try:
        inventory = json.loads((DATA / "inventory.json").read_text())
        hashes = {f["bundled"]: f["bundled_sha256"] for f in inventory["files"]}
        content = {}
        for name in names:
            raw = (DATA / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != hashes[name]:
                raise ValueError("Snapshot checksum mismatch")
            text = raw.decode("utf-8")
            content[name] = json.loads(text) if name.endswith(".json") else list(csv.DictReader(io.StringIO(text)))
        return content, inventory["version"]
    except (OSError, ValueError, KeyError, TypeError, csv.Error):
        return None, None


def _number(value):
    if value is None or value == "":
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite source value")
    return int(number) if number.is_integer() else number


def _sector_data():
    data, version = _bundle(SECTOR_FILES)
    if data is None:
        return None
    try:
        rows = [{key: (value or None) if key in TEXT_FIELDS else _number(value)
                 for key, value in row.items()} for row in data["bugesera_sectors.csv"]]
        keys = [r["sector_key"] for r in rows]
        if len(rows) != 15 or len(set(keys)) != 15 or any(r["label_status"] != "NO_MATCHED_METER_LABELS" or
                r["metered_monthly_consumption_kwh"] is not None or r["metered_peak_kw"] is not None for r in rows):
            return None
        return {"rows": rows, "dictionary": data["source_dictionary.csv"], "engineered": data["engineered_dictionary.csv"],
                "sources": data["source_manifest.csv"], "version": version}
    except (ValueError, KeyError, TypeError):
        return None


def sector_catalog():
    data = _sector_data()
    return {"status": "available" if data else "unavailable", "scope": SCOPE, "notice": NOTICE,
            "sectors": [{"sector": r["sector"], "sector_key": r["sector_key"]} for r in data["rows"]] if data else [],
            "version": data["version"] if data else None}


def _match(location):
    if not location or location.get("country_code") != "RW":
        return None
    path = location.get("administrative_path", [])
    if not isinstance(path, list) or not all(isinstance(p, str) for p in path):
        return None
    # Strict hierarchy: a coincident cell/settlement name elsewhere must not join.
    if location.get("source") == "GeoNames":
        if len(path) < 3 or path[1].strip().casefold() not in ("bugesera", "bugesera district"):
            return None
        return path[2].strip().casefold(), "Gazetteer administrative hierarchy; not a service-boundary match"
    if location.get("source") == "user_entered_administration":
        if len(path) != 3 or path[0].strip().casefold() not in ("bugesera", "bugesera district"):
            return None
        return path[1].strip().casefold(), "User-entered district/sector names; geographic membership unverified"
    return None


def sector_context(location=None):
    data = _sector_data()
    base = {"status": "unavailable" if data is None else "not_matched", "scope": SCOPE, "notice": NOTICE,
            "sector": None, "sector_key": None, "features": [], "sources": [], "match_basis": None,
            "reason": "Prepared sector files unavailable or changed; no substitute values loaded." if data is None else
                      "Choose Rwanda → Bugesera → a supported sector/cell to inspect sector context. No sector match was inferred."}
    match = _match(location)
    if data is None or match is None:
        return base
    row = next((r for r in data["rows"] if r["sector"].casefold() == match[0]), None)
    if row is None:
        return base
    definitions = {r["feature"]: r for r in data["dictionary"]}
    for item in data["engineered"]:
        definitions[item["feature"]] = {**item, "evidence_type": "derived_screening_feature", "source_id": row["source_ids"],
                                         "reference_period": "Mixed source vintages; see source manifest", "how_added": item["formula"]}
    definitions["label_status"] = {"unit": "status", "source_id": "PARTNER_METERS", "reference_period": "2026-11-01 preparation",
                                     "evidence_type": "missing_target", "limitation": "No matched meter labels; not a trained dataset."}
    features = []
    for key, value in row.items():
        definition = definitions.get(key, {})
        features.append({"field": key, "value": value, "unit": definition.get("unit", "metadata"),
                         "evidence_type": definition.get("evidence_type", "provenance"), "scope": SCOPE,
                         "reference_period": definition.get("reference_period", "See source manifest"),
                         "source_ids": definition.get("source_id", row["source_ids"]),
                         "method": definition.get("how_added", "Preserved source snapshot"),
                         "limitation": definition.get("limitation", "Sector context only"),
                         "availability": "missing" if value is None else "available"})
    return {**base, "status": "available", "sector": row["sector"], "sector_key": row["sector_key"],
            "features": features, "sources": data["sources"], "match_basis": match[1], "reason": None,
            "version": data["version"], "used_in_forecast": False}


def benchmark():
    data, version = _bundle(BENCHMARK_FILES)
    result = {"status": "unavailable", "notice": BENCHMARK_NOTICE, "metrics": [], "quality": [], "sites": [],
              "unit": "kW", "evidence_type": "exploratory_baseline_on_published_measurements",
              "scope": "Three independent published sites, not the selected project", "evaluated_on": "2026-11-01",
              "source": {"attribution": "Luh et al., KIT / RADAR4KIT, High-Resolution Real-World Electricity Data from Three Microgrids in the Global South",
                         "url": "https://doi.org/10.35097/1305", "license": "CC BY 4.0", "accessed_on": "2026-11-01"},
              "reason": "Benchmark files unavailable or changed; no example scores substituted."}
    if data is None:
        return result
    try:
        metrics = [{k: v if k in ("test_site", "country", "model") else _number(v) for k, v in row.items()}
                   for row in data["benchmark_metrics.csv"]]
        quality = [{k: v if k in ("site_id", "country") else _number(v) for k, v in row.items()}
                   for row in data["benchmark_quality.csv"]]
        if len(metrics) != 6 or len(quality) != 3:
            return result
        return {**result, "status": "available", "reason": None, "version": version, "metrics": metrics, "quality": quality,
                "sites": data["meter_site_catalog.csv"], "protocol": data["benchmark_protocol.json"],
                "target": "Hourly arithmetic sample-mean delivered active power; not integrated or billed kWh",
                "primary_model": "equal_site_local_hour", "comparison_model": "equal_site_constant",
                "calendar_hours": sum(r["calendar_hours"] for r in quality),
                "qualified_hours": sum(r["eligible_hours"] for r in quality),
                "interpretation": "Poor transfer across heterogeneous systems. WAPE is error, may exceed 100%, and must not be converted to an accuracy percentage.",
                "limitations": ["Short 18–36 day campaigns in 2021–2022, with faults and gaps; delivered power may be supply-constrained.",
                                "Retrospective whole-site transfer, not a chronological or blinded deployment test. Training campaigns may postdate test campaigns.",
                                "Only three sites; correlated hours do not create more independent sites. Scores exclude failed-quality hours.",
                                "Both fixed baselines are reported. No synthetic observations, calibrated intervals or significance claims."]}
    except (ValueError, KeyError, TypeError):
        return result


def preparation():
    data, version = _bundle(PREPARATION_FILES)
    if data is None:
        return {"status": "unavailable", "reason": "Preparation summaries unavailable or changed.", "sites": [], "feature_coverage": []}
    report = data["preparation_report.json"]
    if report.get("trained_models") != 0 or report.get("growth_label_rows") != 0:
        return {"status": "unavailable", "reason": "Unexpected preparation contract; review required.", "sites": [], "feature_coverage": []}
    return {"status": "prepared_not_trained", "version": version, "report": report, "sites": data["preparation_summary.csv"],
            "contract": data["training_contract.json"], "feature_coverage": data["original_20_feature_coverage.csv"],
            "notice": "1,540 eligible hourly examples prepared, no prediction model trained in this preparation. Calendar/past-power predictors are not the original 20 pre-construction inputs. Training-only preprocessing and separate per-site chronological splits; not a pooled backtest. Missing targets were never imputed."}


def summary(location=None):
    return {"schema": "gridsight-prepared-evidence-v1", "categories": CATEGORIES, "model_status": MODEL_STATUS,
            "sector_catalog": sector_catalog(), "sector_context": sector_context(location),
            "benchmark": benchmark(), "preparation": preparation(), "operational_models": operational_summary()}


def csv_text(rows, fields):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def write_archive(archive, evidence):
    """Exports preserve meanings and missingness. No private/raw operator data."""
    archive.writestr("prepared_evidence/summary.json", json.dumps(evidence, indent=2, allow_nan=False))
    write_operational_archive(archive, evidence.get("operational_models"))
    context = evidence["sector_context"]
    fields = ["sector_key", "sector", "field", "value", "unit", "availability", "evidence_type", "scope", "reference_period", "source_ids", "method", "limitation"]
    rows = [{"sector_key": context["sector_key"], "sector": context["sector"], **f} for f in context["features"]]
    archive.writestr("prepared_evidence/selected_sector_features.csv", csv_text(rows, fields))
    # Fixed reviewed allowlist from inventory, never a user-supplied filesystem path.
    try:
        inventory = json.loads((DATA / "inventory.json").read_text())
        allowed = set(SECTOR_FILES + BENCHMARK_FILES + PREPARATION_FILES +
                      ("operational_feature_dictionary.csv", "BENCHMARK_RESULTS.txt", "BENCHMARK_METHOD.txt"))
        omitted = []
        for entry in inventory["files"]:
            name = entry["bundled"]
            if name not in allowed:
                continue
            path = DATA / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["bundled_sha256"]:
                omitted.append(name)
                continue
            archive.write(path, "prepared_evidence/" + name)
        archive.writestr("prepared_evidence/inventory.json", json.dumps(inventory, indent=2))
        archive.writestr("prepared_evidence/download_status.json", json.dumps({"omitted_unavailable_files": omitted}))
    except (OSError, ValueError, KeyError, TypeError):
        archive.writestr("prepared_evidence/download_status.json", json.dumps({"status": "Source inventory unavailable; only current summary exported"}))
    archive.writestr("prepared_evidence/README.txt", (DATA / "README.txt").read_text() if (DATA / "README.txt").exists() else
                     NOTICE + "\n" + BENCHMARK_NOTICE + "\nSources unavailable; do not infer missing values or model results.")
