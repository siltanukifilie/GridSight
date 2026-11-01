"""Compose demand, scenario, and evidence outputs into one consistent report."""
from datetime import datetime, timezone
import json
from .workspaces import workspace
from .feasibility import validate_planning, build_feasibility
from .domain import demand_periods
from .context import validate_context, scenario_defaults
from .rwanda_data import location_profile
from .connection import validate_connection, monthly_connection_outlook, first_year_site, first_year_finance, annual_outlook, first_year_multiplier
from .deliverables import SHARING_PROPOSAL, deliverable_status, lender_explanation, delivery_summary
from .detailed_inputs import validate_detailed, apply_detailed
from .domain import CONFIG, ROOT, FEATURES, LABELS, SECTORS, SITE_LIMITS, SCENARIO_LIMITS, validate_site, validate_numbers, baseline_components, profile, growth, finance


def analyze(payload, forecaster, public=None):
    from .financial_evidence import review, productive_sensitivity
    result = _analyze(payload, forecaster, public)
    result["financial_evidence"] = review(result, payload.get("financial_evidence"))
    result["productive_sensitivity"] = productive_sensitivity(result)
    result["delivery"] = delivery_summary(result)
    result["deliverables"] = result["delivery"]["items"]
    return result


def _analyze(payload, forecaster, public=None):
    if not isinstance(payload, dict):
        raise ValueError("Send a community and scenario inputs.")
    detailed = validate_detailed(payload.get("detailed"))
    if detailed["enabled"]:
        base = _analyze({**payload, "detailed": None}, forecaster, public)
        return apply_detailed(base, detailed)
    audience = workspace(payload.get("role", "developer"))
    context = validate_context(payload.get("context"))
    evidence = location_profile(context["location"])
    site = validate_site(payload.get("site"))
    site["origin"] = context["input_origin"]
    raw_scenario = payload.get("assumptions", {})
    if not isinstance(raw_scenario, dict):
        raise ValueError("Scenario assumptions must be an object.")
    assumptions = validate_numbers({**scenario_defaults(context["country_code"]), **raw_scenario}, SCENARIO_LIMITS)
    planning = validate_planning(payload.get("planning"))
    connection = validate_connection(payload.get("connection"))
    reference = forecaster.predict(site)
    forecast = dict(reference)
    months = monthly_connection_outlook(site, reference, assumptions, connection) if connection["enabled"] else None
    effective_site = first_year_site(site, months) if months is not None else site
    if months is not None:
        for key in ("central", "lower", "upper"):
            forecast[key] = sum(row[key] for row in months[:12]) / 12
        forecast["baseline"] = sum(baseline_components(effective_site).values())
        forecast["reference_interval_level"] = reference["interval_level"]
        forecast["interval_level"] = None  # No coverage level is calibrated for the adoption path.
        forecast["range_basis"] = "Propagated reference range; not calibrated for post-connection growth"
    daily = profile(effective_site, forecast["central"])
    financial = first_year_finance(months, assumptions) if months is not None else finance(forecast["central"], assumptions, daily["peak_kw"])
    financial["currency"] = context["currency"]
    parts = baseline_components(effective_site)
    sensitivities = []
    for key in ["households", "shops", "mills", "pumps", "cold_rooms", "uptake", "appliance_index"]:
        changed = dict(site)
        delta = 1 if key in ["mills", "pumps", "cold_rooms"] else max(1, round(site[key] * .1)) if key in ["households", "shops"] else .05
        changed[key] = min(SITE_LIMITS[key][1], site[key] + delta)
        if changed[key] != site[key]:
            sensitivities.append({"field": key, "label": LABELS.get(key, key.replace("_", " ").capitalize()), "input_change": changed[key] - site[key], "change_kwh": forecaster.predict(changed)["central"] * (first_year_multiplier(changed, assumptions, connection) if connection["enabled"] else 1) - forecast["central"]})
    sensitivities.sort(key=lambda row: abs(row["change_kwh"]), reverse=True)
    warnings = []
    if connection["enabled"]:
        warnings.append("Post-connection curve uses unvalidated adoption assumptions and treats the model output as a mature-demand reference. Year 1 cards are averages of service Months 1–12. Propagated bounds do not include adoption or growth uncertainty.")
    if evidence:
        warnings.append(evidence["notice"])
        if evidence["historical_grid"].get("on_grid_records"):
            warnings.append("Historical on-grid records exist in this sector. Do not treat this location as unserved without a current utility check.")
    if context["input_origin"] == "public_proxy":
        warnings.append("Automatically prepared public-data proxies and placeholders. Review all community, growth, supply and financial assumptions; these are not surveyed customers or actual consumption.")
    public_snapshot = public.snapshot(context["public_data_id"], context["country_code"]) if public and context["public_data_id"] else None
    if context["public_data_id"] and not public_snapshot:
        warnings.append("Saved public-data snapshot is unavailable after a restart. Fetch public context again; no national values were substituted.")
    if context["assumed_fields"]:
        warnings.append("Assumed inputs: " + ", ".join(context["assumed_fields"]) + ". The interval does not account for uncertainty in these guessed inputs.")
    if context["country_code"] != "RW":
        warnings.append(f"Transfer demonstration: the synthetic Rwanda-context model has no {context['country']} training or calibration. Review all energy, growth and cost assumptions.")
    grid_status = context["grid"]["status"]
    grid_messages = {
        "unknown": "Grid access unknown. Check existing connections and utility expansion plans before treating this as an off-grid opportunity.",
        "reported_unserved": "Reported unserved, not independently verified. Confirm the service area, utility expansion plans and site rights before development.",
        "planned": "Main-grid expansion reported. Review timing and grid-arrival risk before developing an isolated mini-grid.",
        "connected": "Main-grid connection reported. Excluded from the unserved-site shortlist; this is not an off-grid development recommendation.",
    }
    warnings.append(grid_messages[grid_status])
    if not assumptions["tariff"] or not assumptions["fixed_cost"]:
        warnings.append("Financial inputs include zero tariff or fixed costs. Complete or verify these inputs before interpreting cash or repayment.")
    if forecast["central"] == 0:
        warnings.append("No modeled customer demand. Add customers or connected households to assess a community.")
    bounds = forecaster.bundle.get("training_bounds", {})
    outside = [LABELS.get(k, k.replace("_", " ")) for k, (low, high) in bounds.items() if not low <= site[k] <= high]
    if outside:
        warnings.append("Outside the synthetic training range: " + ", ".join(outside) + ". Treat this estimate as extrapolation.")
    if financial["base"]["unserved_kwh"] > 0:
        warnings.append("Monthly demand exceeds the entered deliverable-energy limit; revenue uses only served energy.")
    if financial["base"]["peak_shortfall_kw"] > 0:
        warnings.append("At least one monthly illustrative typical-day peak exceeds the entered firm power limit." if connection["enabled"] else "The illustrative typical-day peak exceeds the entered firm power limit.")
    if financial["break_even_kwh"] is None:
        warnings.append("Tariff and collection do not cover variable cost; there is no finite break-even demand under these assumptions.")
    elif not financial["break_even_within_capacity"]:
        warnings.append("Break-even demand exceeds the entered energy-delivery limit.")
    evaluation = json.loads((ROOT / "reports/evaluation.json").read_text())
    feasibility = build_feasibility(effective_site, forecast, assumptions, planning, months=months, connection=connection)
    outlook = annual_outlook(months) if months is not None else growth(site, forecast, assumptions)
    periods = demand_periods(forecast["central"])
    if connection["enabled"]:
        periods["basis"] = "First 12 service months after connection: monthly average of the adoption curve, with daily/weekly average equivalents (365 days/year). Calendar labels locate standard 365/12-day energy months; not dated billing forecasts. No seasonality is modeled."
    # Only denomination text changes. This is not an exchange-rate conversion.
    def denomination(value):
        if isinstance(value, dict):
            return {k: denomination(v) for k, v in value.items()}
        if isinstance(value, list):
            return [denomination(v) for v in value]
        return value.replace("RWF", context["currency"]) if isinstance(value, str) else value
    feasibility = denomination(feasibility)
    feasibility["currency"] = context["currency"]
    for case in feasibility["scenarios"]:
        for row in case["years"] + case["months"]:
            row["currency"] = context["currency"]
    for row in feasibility["productive_options"]:
        row["currency"] = context["currency"]
    return {"detailed": detailed, "connection": connection, "reference_forecast": reference, "deliverables": deliverable_status(connection), "lender_explanation": lender_explanation(site, effective_site, assumptions, connection, feasibility["monthly_growth"]), "sharing_proposal": SHARING_PROPOSAL, "context": context, "location_profile": evidence, "public_data": public_snapshot, "workspace": audience, "planning": planning, "feasibility": feasibility, "site": site, "assumptions": assumptions, "forecast": forecast, "demand_periods": periods, "profile": daily, "growth": outlook, "finance": financial, "components": [{"key": k, "label": LABELS[k], "kwh": parts[k], "share": parts[k] / sum(parts.values()) if sum(parts.values()) else 0} for k in SECTORS], "sensitivities": sensitivities, "warnings": warnings, "supply_energy_kwh": forecast["central"] / (1 - assumptions["loss_rate"]), "evaluation": evaluation, "provenance": {"origin": "synthetic", "country_context": context["country"], "model_training_origin": "synthetic", "input_origin": context["input_origin"], "dataset_version": CONFIG["version"], "generated_at": datetime.now(timezone.utc).isoformat(), "notice": ("Fictional community. " if context["input_origin"] == "synthetic" else "Public-data proxies and unreviewed planning placeholders. " if context["input_origin"] == "public_proxy" else "User-entered planning assumptions. ") + "Synthetic evidence only; model not validated against real metered sites. Local public detections may initialize inputs; national indicators do not change the forecast. Neither validates consumption. Financial inputs are unverified."}}
