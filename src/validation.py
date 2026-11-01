"""Frozen-model comparison of permissioned annual site aggregates; no training."""
import csv
import hashlib
import io
import math
from datetime import date, datetime, timezone
import numpy as np
from .domain import ROOT, FEATURES, CONFIG, validate_site
from .context import country
from .model import metrics

COLUMNS = ["site_id", "country_code", "period_start", "period_end", "actual_kwh"] + FEATURES


def compare_consumption(payload, forecaster):
    if not isinstance(payload, dict) or payload.get("attestation") is not True:
        raise ValueError("Confirm permission, measured aggregates, independent sites and consistent input definitions before comparing.")
    source = payload.get("source_name")
    if not isinstance(source, str) or not 3 <= len(source.strip()) <= 160:
        raise ValueError("Give the source or study name (3–160 characters), without personal information.")
    raw = payload.get("csv")
    if not isinstance(raw, str) or not raw.strip() or len(raw.encode("utf-8")) > 50000:
        raise ValueError("Upload a CSV of at most 50 KB and 100 independent sites.")
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))
    if reader.fieldnames != COLUMNS:
        raise ValueError("CSV headers must match the downloadable template, in order.")
    rows, ids = [], set()
    for index, row in enumerate(reader, start=2):
        if len(rows) >= 100:
            raise ValueError("Use at most 100 independent sites per comparison.")
        if None in row or any(v is None or not v.strip() for v in row.values()):
            raise ValueError(f"Row {index}: all columns must be present; unknown inputs cannot be guessed for validation.")
        identifier = row["site_id"].strip()
        if len(identifier) > 80 or identifier in ids or identifier.upper().startswith(("RW-DEMO", "RW-SYN", "SYN-")):
            raise ValueError(f"Row {index}: use unique, anonymous, non-demo site IDs.")
        ids.add(identifier)
        country(row["country_code"])
        try:
            start, end = date.fromisoformat(row["period_start"]), date.fromisoformat(row["period_end"])
            next_year = date(start.year + 1, start.month, 1)
            if start.day != 1 or (next_year - end).days != 1 or end >= datetime.now(timezone.utc).date():
                raise ValueError()
        except (ValueError, OverflowError):
            raise ValueError(f"Row {index}: use 12 complete, consecutive, historical calendar months (inclusive start/end).") from None
        try:
            actual_total = float(row["actual_kwh"])
            if not math.isfinite(actual_total) or not 0 <= actual_total <= 1e9:
                raise ValueError()
            site = validate_site({key: float(row[key]) for key in FEATURES})
        except (TypeError, ValueError):
            raise ValueError(f"Row {index}: check nonnegative measured energy and bounded, numeric community inputs.") from None
        days = (end - start).days + 1
        actual = actual_total / days * CONFIG["days_per_month"]
        prediction = forecaster.predict(site)
        bounds = forecaster.bundle.get("training_bounds", {})
        rows.append({"site_id": identifier, "country_code": row["country_code"], "period_start": start.isoformat(), "period_end": end.isoformat(), "days_observed": days, "actual_annual_kwh": actual_total, "actual_normalized_monthly_kwh": actual, **prediction, "outside_training_fields": [k for k, (lo, hi) in bounds.items() if not lo <= site[k] <= hi]})
    if not rows:
        raise ValueError("The CSV has no site observations.")
    actual, predicted, lower, upper = (np.array([r[k] for r in rows]) for k in ("actual_normalized_monthly_kwh", "central", "lower", "upper"))
    def summarize(subset):
        a, p, lo, hi = (np.array([r[k] for r in subset]) for k in ("actual_normalized_monthly_kwh", "central", "lower", "upper"))
        return metrics(a, p, lo, hi)
    return {"status": "User-supplied measured-data comparison; not independently verified", "source_name": source.strip(), "source_attested_by_user": True, "generated_at": datetime.now(timezone.utc).isoformat(), "model_version": CONFIG["version"], "model_sha256": hashlib.sha256((ROOT / "models/forecast.joblib").read_bytes()).hexdigest(), "input_sha256": hashlib.sha256(raw.encode()).hexdigest(), "retrained": False, "metrics": {**metrics(actual, predicted, lower, upper), "bias_kwh": float((predicted - actual).mean()), "baseline_mae_kwh": float(np.mean([abs(r["baseline"] - r["actual_normalized_monthly_kwh"]) for r in rows]))}, "by_country": {code: summarize([r for r in rows if r["country_code"] == code]) for code in sorted({r["country_code"] for r in rows})}, "sites": rows, "limitations": ["Source authenticity, completeness, independence and customer-input timing are user attestations, not independently verified.", "Customer-side annual metered energy is normalized to 365/12 days per month. Losses must not be included in uploaded customer consumption.", "Outages and supply rationing can make metered consumption lower than latent demand. This comparison cannot resolve that gap.", "This is an annual-average diagnostic, not a dated forecasting backtest. Seasonal timing and within-year customer changes are not modeled.", "No training or recalibration is performed. This compares the frozen annual-average reference model, not the post-connection adoption curve. Synthetic interval coverage does not guarantee real-site coverage.", "A small or nonrepresentative sample cannot establish general accuracy. No automated validation pass, credit approval or lender-ready claim is assigned."]}
