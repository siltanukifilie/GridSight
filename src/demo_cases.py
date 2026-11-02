"""Explicit synthetic examination cases; never fill gaps in public evidence."""
import csv
import io
import json

from .domain import ROOT, FEATURES
from .detailed_inputs import feature_inventory

JURU_ID = "RW-JURU-SYNTHETIC-01"
# Verified GeoNames records for Bugesera's Juru sector, cell and settlement.
# Same-named places in Kayonza or Rulindo must not load this case.
JURU_LOCATION_IDS = frozenset({"11186838", "11186926", "384473"})
JURU_FILE = ROOT / "data/examples/juru_synthetic_project.json"
FEATURE_UNITS = (
    "households", "fraction", "months", "RWF/month", "RWF/kWh", "RWF/connection",
    "units/connected household", "W", "hours/day", "businesses", "mills", "pumps",
    "kW/unit", "hours/day", "schools", "clinics", "service-month multipliers",
    "connections/year", "fraction/year", "fraction/year",
)


def juru_case():
    # A fresh object per request keeps edits to a loaded case from changing the preset.
    return json.loads(JURU_FILE.read_text())


def is_juru_demo_location(location):
    """Match only the Juru selection covered by the examination case."""
    if not location or location.get("country_code") != "RW":
        return False
    if location.get("source") == "GeoNames":
        return location.get("id") in JURU_LOCATION_IDS
    if location.get("source") == "user_entered_administration":
        names = [name.strip().casefold() for name in location.get("administrative_path", [])]
        return (len(names) == 3 and names[0] in {"bugesera", "bugesera district"}
                and names[1] in {"juru", "juru sector"} and names[2] == "juru")
    return False


def _value(project, field):
    value = project
    for key in field.split("."):
        if key in value:
            value = value[key]
        else:
            value = {name: row[key] for name, row in value.items()}
    return value


def feature_rows(project):
    rows = []
    for i, ((name, field, use), unit) in enumerate(zip(feature_inventory(), FEATURE_UNITS), 1):
        value = _value(project, field)
        rows.append({"feature_number": i, "feature": name, "field": field,
                     "value": json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value,
                     "unit": unit, "use": use, "data_origin": "synthetic", "is_metered": False,
                     "scope": "demo service area; not whole-sector observations"})
    return rows


def annotate(result):
    """Retain the synthetic warning even after editing, saving or changing roles."""
    if result["site"]["id"] != JURU_ID:
        return
    case = juru_case()
    # Migrate only the original preset's old labels, without changing user edits
    # or the machine-readable synthetic provenance.
    if result["site"]["name"] == "Juru — synthetic test service area":
        result["site"]["name"] = case["project"]["site"]["name"]
    location = result["context"].get("location")
    if location and location.get("source") == "user_entered_administration":
        old_label = "Synthetic service area (not a real cell)"
        new_label = case["project"]["context"]["location"]["label"]
        if location.get("label") == old_label:
            location["label"] = new_label
        location["administrative_path"] = [new_label if label == old_label else label
                                           for label in location.get("administrative_path", [])]
    result["demo_case"] = {k: v for k, v in case.items() if k != "project"}
    result["demo_case"]["scope"] = (f"Demo service area of {result['site']['households']} households associated with "
                                    "Juru, Bugesera, Rwanda; not the entire sector or a surveyed cell.")
    result["demo_case"]["features"] = feature_rows(result)
    result["context"].update(input_origin="synthetic", assumed_fields=list(FEATURES))
    result["site"]["origin"] = "synthetic"
    result["provenance"]["input_origin"] = "synthetic"
    result["provenance"]["notice"] = case["notice"] + " " + result["provenance"]["notice"]
    result["warnings"].insert(0, case["notice"])


def csv_text(rows):
    out = io.StringIO()
    if rows:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return out.getvalue()


def _flat_inputs(project):
    """All editable leaves, including finance and nested appliance/equipment inputs."""
    def walk(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                yield from walk(item, path + "." + key)
        elif isinstance(value, list):
            for i, item in enumerate(value, 1):
                yield from walk(item, path + f".M{i}")
        else:
            yield {"field": path, "value": value, "data_origin": "synthetic", "is_metered": False}
    return [row for key in ("site", "detailed", "assumptions", "planning", "connection")
            for row in walk(project[key], key)]


def write_archive(archive, result, prefix="juru_test_case/"):
    """Export the analyzed inputs, never silently substitute the original preset."""
    if not result.get("demo_case"):
        return
    case = result["demo_case"]
    project = {key: result[key] for key in ("site", "context", "detailed", "assumptions", "planning", "connection")}
    def tagged(rows):
        return [{**r, "data_origin": "synthetic_engineering_scenario", "is_metered": False} for r in rows]
    archive.writestr(prefix + "project.json", json.dumps(project, indent=2, allow_nan=False))
    archive.writestr(prefix + "metadata.json", json.dumps({k: v for k, v in case.items() if k != "features"}, indent=2))
    archive.writestr(prefix + "features_20.csv", csv_text(feature_rows(project)))
    archive.writestr(prefix + "all_inputs.csv", csv_text(_flat_inputs(project)))
    months = [{"month": m["month"], "calendar_month": m["calendar_month"],
               "low_kwh": m["lower"], "expected_kwh": m["central"], "high_kwh": m["upper"],
               "connected_households": m.get("estimated_connected_households"),
               "peak_kw": m["peak_kw"], "agricultural_factor": m.get("seasonality_factor"),
               **{k: v for k, v in m.items() if k.endswith("_kwh")}}
              for m in result["feasibility"]["monthly_growth"]]
    archive.writestr(prefix + "synthetic_monthly_36.csv", csv_text(tagged(months)))
    archive.writestr(prefix + "daily_weekly_monthly_yearly.csv", csv_text(tagged(result["demand_periods"]["estimates"])))
    archive.writestr(prefix + "synthetic_hourly_profile.csv", csv_text(tagged([
        {"hour": h, "power_kw": kw} for h, kw in zip(result["profile"]["hours"], result["profile"]["kw"])])))
    archive.writestr(prefix + "financial_stress.csv", csv_text(tagged([
        {**r, "currency": result["context"]["currency"]} for r in result["finance"]["scenarios"]])))
    evidence = result["prepared_evidence"]["sector_context"]
    archive.writestr(prefix + "public_sector_context.json", json.dumps(evidence, indent=2, allow_nan=False))
    if evidence["status"] == "available":
        archive.writestr(prefix + "public_sector_context.csv", csv_text(evidence["features"]))
    archive.writestr(prefix + "README.txt", case["notice"] + "\n\n" + case["scope"] + "\n\n"
        "features_20.csv: the 20 requested features, units and synthetic values.\n"
        "all_inputs.csv / project.json: current editable values, including finance and all appliance/equipment types.\n"
        "synthetic_monthly_36.csv: deterministic engineering scenarios, NOT actual meter readings or independent targets.\n"
        "daily_weekly_monthly_yearly.csv: forecast-Year-1 average equivalents; not dated billing totals.\n"
        "synthetic_hourly_profile.csv: illustrative Year-1 average-day shape, NOT measured peak demand.\n"
        "financial_stress.csv: synthetic inputs; RWF denomination, not verified Rwanda prices or costs.\n"
        "public_sector_context.*: separate source-backed sector context, mixed vintages; blanks remain unavailable.\n"
        "No random meter outcomes are generated. No retraining, calibrated confidence or validation is claimed.\n"
        "The legacy appliance_index, household_growth and S-curve fractions are retained for compatibility but not used by detailed demand.\n"
        "Seasonality is synthetic, indexed by service month; some months can fall despite positive long-run growth.\n"
        "A known zero is an explicit test assumption, not a missing public observation.\n"
        "Download test data gives the original preset. Export report includes your current edited case.\n"
        "Developed by the GridSight Team.\n")
