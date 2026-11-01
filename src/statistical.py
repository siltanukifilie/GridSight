"""Input uncertainty and site-block calibrated growth studies.

Planning simulations are not confidence intervals. Only a separately declared
fit/calibration/test study can produce an empirically calibrated comparison.
No operator data, priors learned from synthetic data, or field-validity claims.
"""
import csv
import io
import json
import math
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING

import numpy as np
from scipy.stats import binomtest

from .domain import CONFIG, SITE_LIMITS, SECTORS, validate_numbers
from .connection import calendar_month
from .detailed_inputs import month_components
from .detailed_validation import (compare_monthly, metrics, model_fingerprint,
                                  _exact, _identifier, _text, _sha)

VERSION = "1.8"
WIDTHS = {
    "household_count_fraction": .1, "non_household_counts_fraction": .2,
    "connection_rate_points": .1, "appliance_ownership_fraction": .2,
    "appliance_power_fraction": .1, "appliance_hours_fraction": .2,
    "equipment_power_fraction": .1, "equipment_hours_fraction": .2,
    "new_connections_fraction": .25, "appliance_adoption_points": .03,
    "business_growth_points": .03, "seasonality_fraction": .2,
}
LABELS = {
    "household_count_fraction": "Household count · ± %",
    "non_household_counts_fraction": "Business/service counts · ± %",
    "connection_rate_points": "Starting connection rate · ± percentage points",
    "appliance_ownership_fraction": "Appliance ownership · ± %",
    "appliance_power_fraction": "Appliance watts · ± %",
    "appliance_hours_fraction": "Appliance daily hours · ± %",
    "equipment_power_fraction": "Equipment kW · ± %",
    "equipment_hours_fraction": "Equipment daily hours · ± %",
    "new_connections_fraction": "Yearly new connections · ± %",
    "appliance_adoption_points": "Yearly appliance adoption · ± percentage points",
    "business_growth_points": "Yearly business growth · ± percentage points",
    "seasonality_fraction": "Agricultural factors · ± %",
}
SETTINGS = {"coverage": .9, "draws": 256, "seed": 1729, "widths": WIDTHS}
REFERENCES = [
    {"title": "Split conformal prediction and calibration", "url": "https://arxiv.org/abs/2107.07511"},
    {"title": "Conformal time-series forecasting", "url": "https://proceedings.neurips.cc/paper/2021/hash/312f1ba2a72318edaaa995a67835fad5-Abstract.html"},
    {"title": "Exact binomial coverage interval", "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html"},
]


def settings(raw=None):
    raw = deepcopy(SETTINGS) if raw is None else raw
    _exact(raw, SETTINGS, "Uncertainty settings")
    if isinstance(raw["coverage"], bool) or raw["coverage"] not in (.8, .9, .95):
        raise ValueError("Choose target coverage 0.8, 0.9 or 0.95.")
    nums = validate_numbers(raw, {"draws": (64, 1024), "seed": (0, 2**31-1)})
    if any(nums[k] != int(nums[k]) for k in nums):
        raise ValueError("Simulation draws and seed must be whole numbers.")
    _exact(raw["widths"], WIDTHS, "Input uncertainty widths")
    widths = validate_numbers(raw["widths"], {k: (0, .5 if k.endswith("_points") else .8) for k in WIDTHS})
    return {"coverage": raw["coverage"], **{k: int(v) for k, v in nums.items()}, "widths": widths}


def energy_path(site, assumptions, detailed, months):
    return np.array([sum(month_components(site, assumptions, detailed, int(m))[0].values())
                     for m in months], dtype=float)


def simulated_paths(site, assumptions, detailed, months, options):
    """One coherent input draw per site path; no independent month-wise jitter."""
    rng = np.random.default_rng(options["seed"])
    widths = options["widths"]
    changes = {k: rng.triangular(-v, 0, v, options["draws"]) if v else np.zeros(options["draws"])
               for k, v in widths.items()}
    output = np.empty((options["draws"], len(months)))
    for i in range(options["draws"]):
        s, a, d = dict(site), dict(assumptions), deepcopy(detailed)
        delta = {k: float(v[i]) for k, v in changes.items()}
        for key in SECTORS:
            group = "household_count_fraction" if key == "households" else "non_household_counts_fraction"
            s[key] = int(np.clip(round(site[key]*(1+delta[group])), *SITE_LIMITS[key]))
        s["uptake"] = float(np.clip(site["uptake"]+delta["connection_rate_points"], 0, 1))
        for unit in d["appliances"].values():
            for key, width, cap in (("units_per_household", "appliance_ownership_fraction", 20),
                                    ("power_w", "appliance_power_fraction", 10000),
                                    ("hours_per_day", "appliance_hours_fraction", 24)):
                unit[key] = min(cap, unit[key]*(1+delta[width]))
        for unit in d["equipment"].values():
            unit["power_kw"] = min(5000, unit["power_kw"]*(1+delta["equipment_power_fraction"]))
            unit["hours_per_day"] = min(24, unit["hours_per_day"]*(1+delta["equipment_hours_fraction"]))
        d["new_connections_yearly"] = min(1500, d["new_connections_yearly"]*(1+delta["new_connections_fraction"]))
        d["appliance_adoption_rate"] = float(np.clip(d["appliance_adoption_rate"]+delta["appliance_adoption_points"], 0, 1))
        a["business_growth"] = float(np.clip(a["business_growth"]+delta["business_growth_points"], -.2, .5))
        d["agricultural_seasonality"] = [min(2, v*(1+delta["seasonality_fraction"])) for v in d["agricultural_seasonality"]]
        output[i] = energy_path(s, a, d, months)
    return output


def input_band(paths, central, coverage):
    tail = (1-coverage)/2
    lower, upper = np.quantile(paths, [tail, 1-tail], axis=0)
    # Always include the entered nominal path; these are explicitly uncalibrated.
    return np.minimum(lower, central), np.maximum(upper, central)


def planning_uncertainty(analysis, options=None):
    options = settings(options)
    if not analysis.get("detailed", {}).get("enabled"):
        raise ValueError("Enable the current detailed-input model before exploring uncertainty.")
    s, a, d = analysis["site"], analysis["assumptions"], analysis["detailed"]
    months = np.arange(d["months_since_connection"]+1, d["months_since_connection"]+37)
    central = energy_path(s, a, d, months)
    paths = simulated_paths(s, a, d, months, options)
    lower, upper = input_band(paths, central, options["coverage"])
    rows = [{"service_month": int(m), "calendar_month": calendar_month(analysis["connection"]["connection_month"], int(m)),
             "expected_kwh": float(c), "lower_kwh": float(lo), "upper_kwh": float(hi)}
            for m, c, lo, hi in zip(months, central, lower, upper)]
    yearly = []
    for y in range(3):
        total = float(sum(central[y*12:y*12+12]))
        lo, hi = input_band(paths[:, y*12:y*12+12].sum(axis=1), total, options["coverage"])
        yearly.append({"forecast_year": y+1, "expected_kwh": total, "lower_kwh": float(lo), "upper_kwh": float(hi)})
    inputs = {k: analysis[k] for k in ("site", "assumptions", "detailed", "connection", "context")}
    return {"version": VERSION, "status": "Input-assumption band — not calibrated",
            "calibrated": False, "coverage_target": None, "simulation_mass": options["coverage"],
            "forecast_error_included": False, "settings": options, "inputs": inputs,
            "input_sha256": _sha(json.dumps(inputs, sort_keys=True, allow_nan=False).encode()),
            "model": model_fingerprint(), "months": rows, "years": yearly,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "limitations": [
                "This band propagates user-assumed input distributions. It is NOT an empirically calibrated prediction interval or a confidence claim.",
                "Symmetric triangular input errors, independent between groups; one draw is shared across appliance types and all months. Physical limits clip draws. Correlations between groups are unknown.",
                "Zero multiplicative inputs remain zero. Planned equipment additions and timing are fixed. Unlisted risks, outages, forecast error and unforeseen businesses are not included.",
                "Income, tariff and connection fee have no demand elasticity in this engineering model and are not sampled as energy drivers.",
                "Monthly energy uses 365/12 days. Annual bands come from summed simulated paths, not sums of monthly quantiles.",
                "Calibrating forecast error and learning growth requires measured histories with separate fit, calibration and untouched test sites. No suitable genuine dataset has been imported."
            ]}


def blank_plan():
    return {"schema": "gridsight-confidence-growth-v1", "horizon_months": 24,
            "fit_site_ids": [], "calibration_site_ids": [], "test_site_ids": [],
            "uncertainty": deepcopy(SETTINGS), "protocol_reference": "",
            "split_frozen_before_outcomes_reviewed": False, "comparable_site_population": False}


def calibration_rank(n, coverage):
    # Decimal avoids ceil turning a mathematically integral rank into n+1.
    return int((Decimal(n+1)*Decimal(str(coverage))).to_integral_value(rounding=ROUND_CEILING))


def _plan(raw, identifiers):
    _exact(raw, blank_plan(), "Study plan")
    if raw["schema"] != blank_plan()["schema"] or type(raw["horizon_months"]) is not int or raw["horizon_months"] not in (24, 36):
        raise ValueError("Use the confidence-growth schema and a 24- or 36-month horizon.")
    _text(raw["protocol_reference"], "Frozen protocol reference")
    if raw["split_frozen_before_outcomes_reviewed"] is not True or raw["comparable_site_population"] is not True:
        raise ValueError("Confirm the predeclared site split and comparable population; these remain unverified declarations.")
    options = settings(raw["uncertainty"])
    groups, seen = {}, set()
    for group in ("fit_site_ids", "calibration_site_ids", "test_site_ids"):
        values = raw[group]
        if not isinstance(values, list) or len(values) > 30:
            raise ValueError("Each split must list anonymous site IDs (maximum 30).")
        ids = [_identifier(v) for v in values]
        if len(set(ids)) != len(ids) or seen.intersection(ids):
            raise ValueError("Fit, calibration and test groups must be disjoint whole sites, without duplicates.")
        groups[group] = sorted(ids)
        seen.update(ids)
    if seen != set(identifiers):
        raise ValueError("Assign every manifest site exactly once; unknown or unassigned site IDs are not allowed.")
    if len(groups["fit_site_ids"]) < 3 or len(groups["test_site_ids"]) < 2:
        raise ValueError("Use at least 3 growth-fit sites and 2 untouched test sites. These minimums do not establish representativeness.")
    n = len(groups["calibration_site_ids"])
    rank = calibration_rank(n, options["coverage"])
    if rank > n:
        minimum = next(k for k in range(1, 100) if calibration_rank(k, options["coverage"]) <= k)
        raise ValueError(f"A finite {options['coverage']:.0%} site-level band needs at least {minimum} separate calibration sites; months are not independent sites.")
    return {**deepcopy(raw), **groups, "uncertainty": options}, rank


def growth_basis(months, knots):
    eye = np.eye(len(knots))
    return np.column_stack([np.interp(months, knots, eye[:, i]) for i in range(len(knots))])


def fit_growth(site_rows, horizon):
    """Fixed piecewise-log correction of total energy, not causal driver fitting."""
    knots = [1, 6, 12, 24] + ([36] if horizon == 36 else [])
    rows = [r for group in site_rows for r in group]
    x = growth_basis([r["service_month"] for r in rows], knots)
    # Normalize both to the dashboard's standard energy month before fitting.
    target = np.array([math.log1p(r["actual_kwh"]*CONFIG["days_per_month"]/r["days"]) -
                       math.log1p(r["predicted_kwh"]*CONFIG["days_per_month"]/r["days"]) for r in rows])
    ridge = .1  # Fixed in advance, never selected from calibration/test outcomes.
    coef = np.linalg.solve(x.T@x + ridge*np.eye(len(knots)), x.T@target)
    return {"knots": knots, "log_corrections": coef.tolist(), "ridge": ridge,
            "max_multiplier": 10, "horizon_months": horizon,
            "method": "Ridge piecewise-linear correction of log(standard-month energy + 1)",
            "drivers_identified": False}


def correct_growth(values, months, model):
    if min(months) < 1 or max(months) > model["horizon_months"]:
        raise ValueError("Do not extrapolate an observed growth fit beyond its tested service months.")
    residual = growth_basis(months, model["knots"])@np.asarray(model["log_corrections"])
    residual = np.clip(residual, -math.log(model["max_multiplier"]), math.log(model["max_multiplier"]))
    return np.maximum(0, (np.asarray(values)+1)*np.exp(residual)-1)


def _summary(rows):
    original = [{**r, "predicted_kwh": r["original_kwh"]} for r in rows]
    inside = sum(r["covered"] for r in rows)
    return {"original": metrics(original), "growth_adjusted": metrics(rows),
            "monthly_coverage_pct": 100*inside/len(rows) if rows else None,
            "n_covered_months": inside,
            "mean_width_kwh": sum(r["upper_kwh"]-r["lower_kwh"] for r in rows)/len(rows) if rows else None}


def site_score(actual, prediction):
    actual = np.asarray(actual)
    exceedance = np.maximum(np.maximum(prediction["lower"]-actual, actual-prediction["upper"]), 0)
    return float(np.max(exceedance / np.maximum(prediction["center"], 1)))


def expanded_band(prediction, correction):
    expansion = correction*np.maximum(prediction["center"], 1)
    return np.maximum(0, prediction["lower"]-expansion), prediction["upper"]+expansion


def confidence_study(payload):
    _exact(payload, ("manifest", "csv", "plan"), "Study request")
    # Reuse the strict current-model importer, without publishing its pooled scores.
    comparison = compare_monthly({k: payload[k] for k in ("manifest", "csv")})
    plan, rank = _plan(payload["plan"], comparison["by_site"])
    horizon, options = plan["horizon_months"], plan["uncertainty"]
    observations = {}
    for identifier in comparison["by_site"]:
        group = [r for r in comparison["monthly_comparisons"] if r["site_id"] == identifier and r["service_month"] <= horizon]
        missing = sorted(set(range(1, horizon+1)) - {r["service_month"] for r in group})
        if missing:
            raise ValueError(f"{identifier}: needs all first {horizon} eligible service months. Missing/excluded: {', '.join(map(str, missing))}. No imputation or shortened horizon.")
        observations[identifier] = group
    # Only fit outcomes can influence this growth model.
    fitted = fit_growth([observations[k] for k in plan["fit_site_ids"]], horizon)
    inputs = {_identifier(s["site_id"]): s for s in payload["manifest"]["sites"]}
    predictions = {}
    months = np.arange(1, horizon+1)
    for identifier in plan["calibration_site_ids"] + plan["test_site_ids"]:
        raw = inputs[identifier]
        base = energy_path(raw["site"], raw["assumptions"], raw["detailed"], months)
        samples = simulated_paths(raw["site"], raw["assumptions"], raw["detailed"], months, options)
        center = correct_growth(base, months, fitted)
        lo, hi = input_band(correct_growth(samples, months, fitted), center, options["coverage"])
        days = np.array([r["days"] for r in observations[identifier]])/CONFIG["days_per_month"]
        predictions[identifier] = {"center": center*days, "lower": lo*days, "upper": hi*days}
    # One maximum score per whole site path: months are never treated as IID.
    scores = {}
    for identifier in plan["calibration_site_ids"]:
        p = predictions[identifier]
        actual = np.array([r["actual_kwh"] for r in observations[identifier]])
        scores[identifier] = site_score(actual, p)
    q = sorted(scores.values())[rank-1]
    test_rows = []
    for identifier in plan["test_site_ids"]:
        p = predictions[identifier]
        lower, upper = expanded_band(p, q)
        for i, r in enumerate(observations[identifier]):
            prediction = float(p["center"][i])
            test_rows.append({**r, "original_kwh": r["predicted_kwh"], "predicted_kwh": prediction,
                              "error_kwh": prediction-r["actual_kwh"], "absolute_error_kwh": abs(prediction-r["actual_kwh"]),
                              "input_lower_kwh": float(p["lower"][i]), "input_upper_kwh": float(p["upper"][i]),
                              "lower_kwh": float(lower[i]), "upper_kwh": float(upper[i]),
                              "covered": bool(lower[i] <= r["actual_kwh"] <= upper[i])})
    by_site = {}
    growth = []
    for identifier in plan["test_site_ids"]:
        group = [r for r in test_rows if r["site_id"] == identifier]
        by_site[identifier] = {**_summary(group), "whole_path_covered": all(r["covered"] for r in group)}
        for year in range(2, horizon//12+1):
            first = [r for r in group if r["service_year"] == year-1]
            second = [r for r in group if r["service_year"] == year]
            ratios = {}
            for key in ("actual_kwh", "original_kwh", "predicted_kwh"):
                denominator = sum(r[key] for r in first)
                ratios[key] = 100*(sum(r[key] for r in second)/denominator-1) if denominator else None
            growth.append({"site_id": identifier, "from_year": year-1, "to_year": year,
                           "actual_growth_pct": ratios["actual_kwh"], "original_growth_pct": ratios["original_kwh"],
                           "fitted_growth_pct": ratios["predicted_kwh"]})
    covered = sum(s["whole_path_covered"] for s in by_site.values())
    n_test = len(by_site)
    ci = binomtest(covered, n_test).proportion_ci(confidence_level=.95, method="exact")
    country_splits = {code: {key: sum(inputs[i]["country_code"] == code for i in plan[key])
                            for key in ("fit_site_ids", "calibration_site_ids", "test_site_ids")}
                      for code in sorted({s["country_code"] for s in inputs.values()})}
    transfers = [f"{code}: test sites lack growth-fit or calibration sites from the same country. This is a transfer diagnostic, not country-specific calibrated coverage."
                 for code, counts in country_splits.items() if counts["test_site_ids"] and
                 (not counts["fit_site_ids"] or not counts["calibration_site_ids"])]
    return {"version": VERSION, "status": "Fitted and calibrated on supplied histories — independent verification pending",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "field_validation_complete": False, "independently_verified": False,
            "calibrated_on_supplied_records": True, "forecast_error_included": True,
            "scope": "Retrospective batch study; not automatically applied to dashboard or new countries",
            "source_name": comparison["source_name"], "manifest": payload["manifest"], "plan": plan,
            "model": comparison["model"], "manifest_sha256": comparison["manifest_sha256"],
            "csv_sha256": comparison["csv_sha256"], "plan_sha256": _sha(json.dumps(plan, sort_keys=True).encode()),
            "growth_model": fitted, "calibration": {"target_coverage": options["coverage"],
                "scope": f"Simultaneous coverage of all first {horizon} months of a comparable new site",
                "n_sites": len(scores), "rank": rank, "site_scores": scores, "correction": q},
            "test": {**_summary(test_rows), "n_sites": n_test, "covered_site_paths": covered,
                "site_path_coverage_pct": 100*covered/n_test, "site_coverage_ci95_pct": [100*ci.low, 100*ci.high]},
            "by_site": by_site,
            "country_split_counts": country_splits, "transfer_warnings": transfers,
            "by_country": {c: _summary([r for r in test_rows if r["country_code"] == c])
                           for c in sorted({r["country_code"] for r in test_rows})},
            "by_stage": {label: _summary([r for r in test_rows if lo <= r["service_month"] <= hi])
                         for label, lo, hi in (("Months 1–6", 1, 6), ("Months 7–12", 7, 12),
                                              ("Months 13–24", 13, 24), ("Months 25–36", 25, 36))},
            "growth_comparisons": growth, "monthly_comparisons": test_rows,
            "excluded_rows": comparison["excluded_rows"], "references": REFERENCES,
            "limitations": [
                "A prediction band for realized energy, not a confidence interval for the mean or a financial guarantee. Field/source authenticity and predeclared splits remain unverified.",
                "Growth is fitted only on fit sites; input distributions are fixed in the plan; error expansion uses only calibration sites; coverage and errors use only untouched test sites. Do not tune after viewing test outcomes.",
                "Finite-sample conformal coverage needs exchangeable whole-site trajectories from a comparable population. Dependence within a site's months is allowed; shared operators, selection bias, new-country transfer or distribution shifts may break the guarantee.",
                "The target covers the entire declared 24/36-month path. Monthly coverage is descriptive, not a collection of independent trials. The 95% exact site-coverage interval assumes independent comparable test sites; small samples are inconclusive.",
                "Total-energy histories learn an aggregate age-dependent correction only. They do not separately identify connection uptake, appliance adoption or business growth. Dated customer counts, appliance panels and business registers are still needed for those drivers.",
                "A 24-month fit is not extrapolated to Months 25–36. A 36-month claim needs complete 36-month fit, calibration and test trajectories. Growth may decrease; increases are not forced.",
                "Only complete, fully metered, unconstrained service histories enter the study. Missing/outage exclusions limit applicability. Nominal engineering arithmetic and its low/high planning scenarios remain unchanged.",
                "Minimum counts permit the computation; they are not proof of broad accuracy. Test error may worsen after fitting. No automatic pass, country-wide claim, or deployment to new sites."
            ]}


def study_csv(result):
    fields = ["site_id", "country_code", "month", "service_month", "actual_kwh", "original_kwh",
              "predicted_kwh", "input_lower_kwh", "input_upper_kwh", "lower_kwh", "upper_kwh", "covered", "error_kwh"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(result["monthly_comparisons"])
    return out.getvalue()
