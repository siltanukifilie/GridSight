"""Retrospective, site-held-out checks of the CURRENT engineering calculation.

No fitting, target-derived inputs, imputation, or claim of independent verification.
Uploaded records remain in memory; publication and source authentication are manual.
"""
import calendar
import csv
import hashlib
import io
import json
import math
import re
from datetime import date, datetime, timezone

from .domain import ROOT, CONFIG, SITE_LIMITS, SCENARIO_LIMITS, validate_numbers
from .context import COUNTRIES
from .detailed_inputs import DEFAULTS, validate_detailed, detailed_months

SCHEMA = "gridsight-monthly-holdout-v1"
SITE_KEYS = tuple(k for k in SITE_LIMITS if k != "appliance_index")
ASSUMPTION_KEYS = ("business_growth", "additional_mills", "additional_pumps",
                   "additional_cold_rooms", "adoption_year", "tariff")
COLUMNS = ["site_id", "month", "actual_kwh", "coverage_fraction",
           "availability_fraction", "quality"]
ATTESTATIONS = ("permission", "customer_side_kwh", "independent_sites",
                "preconnection_inputs", "not_tuned_to_targets", "disclosure_review")
MAX_SITES, MAX_ROWS = 30, 1080


def _text(value, label, maximum=300):
    if not isinstance(value, str) or not 3 <= len(value.strip()) <= maximum:
        raise ValueError(f"{label}: enter 3–{maximum} characters; no personal information.")
    return value.strip()


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label}: fields must exactly match the blank template; unknown is not zero.")


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,59}", value):
        raise ValueError("Use anonymous site IDs: 3–60 letters, digits, underscores or hyphens.")
    if value.upper().startswith(("RW-DEMO", "RW-SYN", "SYN-")):
        raise ValueError("Synthetic/demo site IDs are not metered evidence.")
    return value.upper()


def _month(value):
    if not isinstance(value, str) or not re.fullmatch(r"(19|20)\d{2}-(0[1-9]|1[0-2])", value):
        raise ValueError("Use calendar months YYYY-MM (1900–2099).")
    return date.fromisoformat(value + "-01")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def model_fingerprint():
    # Freeze all local modules/config involved, not just the old fitted artifact.
    paths = sorted((ROOT / "src").glob("*.py")) + sorted((ROOT / "config").glob("*.json"))
    files = {str(p.relative_to(ROOT)): _sha(p.read_bytes()) for p in paths}
    return {"method": "detailed_bottom_up", "calculation_version": "1.6",
            "validation_schema": SCHEMA, "files": files,
            "sha256": _sha(json.dumps(files, sort_keys=True).encode())}


def blank_manifest():
    d = {k: None for k in DEFAULTS}
    d.update(enabled=True, months_since_connection=0,
             appliances={k: {field: None for field in row} for k, row in DEFAULTS["appliances"].items()},
             equipment={k: {field: None for field in row} for k, row in DEFAULTS["equipment"].items()},
             agricultural_seasonality=[None] * 12)
    return {"schema": SCHEMA, "source_name": "", "source_reference": "",
            "license_or_permission": "", "development_site_ids": [],
            "attestations": {k: False for k in ATTESTATIONS},
            "sites": [{"site_id": "", "country_code": "", "connection_month": "",
                       "inputs_as_of": "", "input_evidence_reference": "",
                       "site": {k: None for k in SITE_KEYS},
                       "assumptions": {k: None for k in ASSUMPTION_KEYS}, "detailed": d}]}


def _prepare_sites(manifest):
    _exact(manifest, blank_manifest(), "Site manifest")
    if manifest["schema"] != SCHEMA:
        raise ValueError("Unsupported validation schema.")
    for key in ("source_name", "source_reference", "license_or_permission"):
        _text(manifest[key], key)
    _exact(manifest["attestations"], ATTESTATIONS, "Attestations")
    if not all(v is True for v in manifest["attestations"].values()):
        raise ValueError("Confirm every permission, privacy, independence and input-timing statement.")
    dev = manifest["development_site_ids"]
    if not isinstance(dev, list) or len(dev) > 500:
        raise ValueError("List all development/calibration site IDs (maximum 500); use [] only if none.")
    development = {_identifier(v) for v in dev}
    supplied = manifest["sites"]
    if not isinstance(supplied, list) or not 1 <= len(supplied) <= MAX_SITES:
        raise ValueError(f"Supply 1–{MAX_SITES} independent sites.")
    prepared = {}
    for raw in supplied:
        _exact(raw, blank_manifest()["sites"][0], "Site record")
        identifier = _identifier(raw["site_id"])
        if identifier in prepared or identifier in development:
            raise ValueError("Duplicate site or development/test overlap: hold out whole sites, not months.")
        if not isinstance(raw["country_code"], str) or raw["country_code"] not in COUNTRIES:
            raise ValueError("This workflow covers RW, UG, KE, TZ, BI, SS, SO and CD.")
        start = _month(raw["connection_month"])
        try:
            as_of = date.fromisoformat(raw["inputs_as_of"])
        except (ValueError, TypeError):
            raise ValueError("inputs_as_of must be YYYY-MM-DD.") from None
        if as_of >= start:
            raise ValueError("Use documented inputs recorded before connection, not after seeing meter results.")
        _text(raw["input_evidence_reference"], "Input evidence reference")
        _exact(raw["site"], SITE_KEYS, "Community inputs")
        site = validate_numbers(raw["site"], {k: SITE_LIMITS[k] for k in SITE_KEYS})
        # Legacy appliance_index is unused by detailed energy, and must not be inferred.
        site["appliance_index"] = 1
        _exact(raw["assumptions"], ASSUMPTION_KEYS, "Growth/tariff inputs")
        assumptions = validate_numbers(raw["assumptions"], {k: SCENARIO_LIMITS[k] for k in ASSUMPTION_KEYS})
        d = raw["detailed"]
        _exact(d, DEFAULTS, "Detailed inputs")
        for group in ("appliances", "equipment"):
            _exact(d[group], DEFAULTS[group], group)
            for key, fields in DEFAULTS[group].items():
                _exact(d[group][key], fields, f"{group}.{key}")
        d = validate_detailed(d)
        if d["enabled"] is not True or d["months_since_connection"] != 0:
            raise ValueError("Enable detailed mode and set elapsed months to zero for the pre-connection test.")
        predictions = detailed_months(site, assumptions, {"low_factor": 1, "high_factor": 1},
                                      {"connection_month": raw["connection_month"]}, d)
        prepared[identifier] = {"raw": raw, "predictions": {r["calendar_month"]: r for r in predictions}}
    return prepared


def metrics(rows):
    if not rows:
        return {"n_sites": 0, "n_months": 0, "mae_kwh": None, "rmse_kwh": None,
                "wape_pct": None, "bias_kwh": None, "bias_pct": None}
    errors = [r["predicted_kwh"] - r["actual_kwh"] for r in rows]
    actual = sum(r["actual_kwh"] for r in rows)
    n = len(rows)
    return {"n_sites": len({r["site_id"] for r in rows}), "n_months": n,
            "mae_kwh": sum(abs(e) for e in errors) / n,
            "rmse_kwh": math.sqrt(sum(e*e for e in errors) / n),
            "wape_pct": 100 * sum(abs(e) for e in errors) / actual if actual else None,
            "bias_kwh": sum(errors) / n,
            "bias_pct": 100 * sum(errors) / actual if actual else None}


def compare_monthly(payload, today=None):
    _exact(payload, ("manifest", "csv"), "Request")
    manifest, raw = payload["manifest"], payload["csv"]
    sites = _prepare_sites(manifest)
    if not isinstance(raw, str) or not raw.strip() or len(raw.encode()) > 90000:
        raise ValueError("Choose a nonempty monthly CSV of at most 90 KB.")
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))
    if reader.fieldnames != COLUMNS:
        raise ValueError("Monthly CSV headers must match the downloadable template, in order.")
    today = today or datetime.now(timezone.utc).date()
    rows, excluded, seen = [], [], set()
    for index, row in enumerate(reader, 2):
        if index > MAX_ROWS + 1:
            raise ValueError(f"Use at most {MAX_ROWS} monthly rows.")
        if None in row or any(v is None or not v.strip() for v in row.values()):
            raise ValueError(f"Row {index}: complete every column; missing is not zero.")
        identifier = _identifier(row["site_id"])
        if identifier not in sites:
            raise ValueError(f"Row {index}: site is absent from the frozen-input manifest.")
        month = _month(row["month"])
        if month.year == today.year and month.month == today.month or month > today:
            raise ValueError(f"Row {index}: only completed historical calendar months can be tested.")
        key = (identifier, row["month"])
        if key in seen:
            raise ValueError(f"Row {index}: duplicate site-month.")
        seen.add(key)
        try:
            actual, coverage, availability = (float(row[k]) for k in
                                              ("actual_kwh", "coverage_fraction", "availability_fraction"))
            if not all(math.isfinite(v) for v in (actual, coverage, availability)) or not (
                    0 <= actual <= 1e9 and 0 <= coverage <= 1 and 0 <= availability <= 1):
                raise ValueError()
        except ValueError:
            raise ValueError(f"Row {index}: energy must be finite/nonnegative and fractions within 0–1.") from None
        if row["quality"] not in ("measured", "estimated"):
            raise ValueError(f"Row {index}: quality must be measured or estimated.")
        prediction = sites[identifier]["predictions"].get(row["month"])
        reasons = []
        if prediction is None:
            reasons.append("Outside the first 36 service months")
        if coverage != 1:
            reasons.append("Incomplete meter coverage")
        if availability != 1:
            reasons.append("Outage or supply-constrained month")
        if row["quality"] != "measured":
            reasons.append("Estimated, not fully measured")
        base = {"site_id": identifier, "country_code": sites[identifier]["raw"]["country_code"],
                "month": row["month"], "actual_kwh": actual,
                "coverage_fraction": coverage, "availability_fraction": availability, "quality": row["quality"]}
        if reasons:
            excluded.append({**base, "reasons": reasons})
            continue
        days = calendar.monthrange(month.year, month.month)[1]
        predicted = prediction["central"] * days / CONFIG["days_per_month"]
        rows.append({**base, "service_month": prediction["service_month"],
                     "service_year": prediction["year"], "days": days,
                     "predicted_kwh": predicted, "error_kwh": predicted - actual,
                     "absolute_error_kwh": abs(predicted - actual)})
    if not seen:
        raise ValueError("The CSV contains no monthly observations.")
    rows.sort(key=lambda r: (r["site_id"], r["month"]))
    per_site, growth = {}, []
    for identifier, info in sites.items():
        subset = [r for r in rows if r["site_id"] == identifier]
        years = {}
        for year in (1, 2, 3):
            group = [r for r in subset if r["service_year"] == year]
            years[str(year)] = {"complete": len(group) == 12, "months": len(group),
                               "actual_kwh": sum(r["actual_kwh"] for r in group) if len(group) == 12 else None,
                               "predicted_kwh": sum(r["predicted_kwh"] for r in group) if len(group) == 12 else None}
        per_site[identifier] = {**metrics(subset), "country_code": info["raw"]["country_code"],
                               "missing_or_excluded_service_months": sorted(set(range(1, 37)) - {r["service_month"] for r in subset}),
                               "years": years}
        for year in (2, 3):
            previous, current = years[str(year - 1)], years[str(year)]
            if previous["complete"] and current["complete"]:
                a = (current["actual_kwh"] / previous["actual_kwh"] - 1) * 100 if previous["actual_kwh"] else None
                p = (current["predicted_kwh"] / previous["predicted_kwh"] - 1) * 100 if previous["predicted_kwh"] else None
                growth.append({"site_id": identifier, "from_year": year-1, "to_year": year,
                               "actual_growth_pct": a, "predicted_growth_pct": p,
                               "error_percentage_points": p-a if p is not None and a is not None else None})
    evaluated = {r["site_id"] for r in rows}
    return {
        "status": "Retrospective held-out comparison — source and independence are user-attested" if rows else "No eligible measured months",
        "schema": SCHEMA, "source_name": manifest["source_name"].strip(),
        "generated_at": datetime.now(timezone.utc).isoformat(), "model": model_fingerprint(),
        "manifest_sha256": _sha(json.dumps(manifest, sort_keys=True, allow_nan=False).encode()),
        "csv_sha256": _sha(raw.encode()), "manifest": manifest,
        "retrained": False, "independently_verified": False, "field_validation_complete": False,
        "metrics": metrics(rows), "by_site": per_site,
        "by_country": {c: metrics([r for r in rows if r["country_code"] == c])
                       for c in sorted({r["country_code"] for r in rows})},
        "by_service_year": {str(y): metrics([r for r in rows if r["service_year"] == y]) for y in (1, 2, 3)},
        "monthly_comparisons": rows, "excluded_rows": excluded, "growth_comparisons": growth,
        "coverage": {"submitted_sites": len(sites), "evaluated_sites": len(evaluated),
                     "eligible_months": len(rows), "excluded_months": len(excluded),
                     "sites_with_complete_36_months": sum(v["n_months"] == 36 for v in per_site.values()),
                     "multi_site_sample": len(evaluated) >= 2,
                     "multi_country_sample": len({r["country_code"] for r in rows}) >= 2},
        "limitations": [
            "A retrospective test of the current 20-input engineering estimate, not the older ML reference or proof of prospective accuracy. Input dates and holdout independence require external evidence review.",
            "No training, tuning, missing-input defaults or target-derived assumptions. Whole-site overlap is rejected; aliases and false declarations cannot be detected.",
            "Customer-side energy only. Model 365/12-day energy is rescaled to actual calendar days, including leap years. No conversion from amperes or generated energy.",
            "Incomplete, estimated and outage-affected months are listed but excluded, never filled with zeros. Excluding outages limits results to unconstrained service.",
            "Annual growth comparisons require two complete consecutive service years. No 3-year growth evidence without 36 eligible months per site.",
            "MAE/RMSE are kWh per calendar month. WAPE is total absolute error / total measured energy; null at zero total. Positive bias means overprediction. Countries and sites are reported separately; pooled months are not independent sites.",
            "Low/high scenarios are not calibrated confidence intervals. This test does not validate peak demand, tariff/income elasticity, financial viability or unobserved demand.",
            "No automatic pass, regional accuracy claim or selected-project validation. Data remain in memory; downloadable reports contain the supplied anonymous inputs and require disclosure review before sharing."
        ]}


def comparisons_csv(result):
    fields = ["site_id", "country_code", "month", "service_month", "service_year", "days",
              "actual_kwh", "predicted_kwh", "error_kwh", "absolute_error_kwh"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(result["monthly_comparisons"])
    return out.getvalue()
