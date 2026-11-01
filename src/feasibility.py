"""Transparent planning scenarios, not a dispatch model or lending decision."""
from .domain import CONFIG, SECTORS, baseline_components, profile, finance, validate_numbers

PLANNING_DEFAULTS = {
    "low_factor": .8, "high_factor": 1.3, "discount_rate": .1,
    "project_capex": None, "capacity_capex": None,
    "mill_support_cost": None, "pump_support_cost": None, "cold_room_support_cost": None,
    "mill_monthly_cost": 0, "pump_monthly_cost": 0, "cold_room_monthly_cost": 0,
    "household_basket_kwh": None, "household_income_monthly": None,
    "household_energy_budget_monthly": None, "household_fixed_fee_monthly": 0,
    "affordability_income_share": .05,
}
PLANNING_LIMITS = {
    "low_factor": (0, 1), "high_factor": (1, 3), "discount_rate": (0, .5),
    "project_capex": (0, 1e12), "capacity_capex": (0, 1e12),
    "mill_support_cost": (0, 1e10), "pump_support_cost": (0, 1e10), "cold_room_support_cost": (0, 1e10),
    "mill_monthly_cost": (0, 1e8), "pump_monthly_cost": (0, 1e8), "cold_room_monthly_cost": (0, 1e8),
    "household_basket_kwh": (0, 10000), "household_income_monthly": (0, 1e10),
    "household_energy_budget_monthly": (0, 1e10), "household_fixed_fee_monthly": (0, 1e8),
    "affordability_income_share": (0, 1),
}
OPTIONAL_COSTS = [key for key, value in PLANNING_DEFAULTS.items() if value is None]
PLANNING_LABELS = {
    "low_factor": "Low demand multiplier", "high_factor": "High demand multiplier",
    "discount_rate": "Annual discount rate", "project_capex": "Total project capital cost",
    "capacity_capex": "Capacity-linked portion of capital cost",
    "mill_support_cost": "One mill: developer connection/support cost",
    "pump_support_cost": "One pump: developer connection/support cost",
    "cold_room_support_cost": "One cold room: developer connection/support cost",
    "mill_monthly_cost": "One mill: extra developer operating cost per month",
    "pump_monthly_cost": "One pump: extra developer operating cost per month",
    "cold_room_monthly_cost": "One cold room: extra developer operating cost per month",
    "household_basket_kwh": "Household energy basket per month · kWh",
    "household_income_monthly": "Household income per month",
    "household_energy_budget_monthly": "Household energy budget per month",
    "household_fixed_fee_monthly": "Household fixed electricity fee per month",
    "affordability_income_share": "Editable income-share screen · fraction",
}


def validate_planning(raw=None):
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("Planning assumptions must be an object.")
    unknown = set(raw) - set(PLANNING_DEFAULTS)
    if unknown:
        raise ValueError("Unknown planning assumption: " + sorted(unknown)[0])
    values = {**PLANNING_DEFAULTS, **raw}
    present = {key: limits for key, limits in PLANNING_LIMITS.items() if not (key in OPTIONAL_COSTS and values[key] is None)}
    output = {**values, **validate_numbers(values, present)}
    if output["project_capex"] is not None and output["capacity_capex"] is not None and output["capacity_capex"] > output["project_capex"]:
        raise ValueError("Capacity-linked cost cannot exceed total project capital cost.")
    return output


def _weights(rate):
    raw = [(1 + rate) ** (month / 12) for month in range(12)]
    mean = sum(raw) / 12
    return [value / mean for value in raw]


def monthly_outlook(site, forecast, assumptions):
    """Each year's monthly mean equals domain.growth; Year 1 is not month 1."""
    parts = baseline_components(site)
    total = sum(parts.values())
    share = parts["households"] / total if total else 0
    hg, bg = assumptions["household_growth"], assumptions["business_growth"]
    hw, bw = _weights(hg), _weights(bg)
    adoption = assumptions["adoption_year"]
    additions = {"mills": assumptions["additional_mills"], "pumps": assumptions["additional_pumps"], "cold_rooms": assumptions.get("additional_cold_rooms", 0)}
    added_energy = sum(value * CONFIG["sector_kwh_month"][key] for key, value in additions.items())
    rows = []
    for year in (1, 2, 3):
        for month in range(12):
            hf, bf = (1 + hg) ** (year - 1) * hw[month], (1 + bg) ** (year - 1) * bw[month]
            added_factor = (1 + bg) ** (year - adoption) * bw[month] if year >= adoption else 0
            factor = share * hf + (1 - share) * bf
            added = added_energy * added_factor
            projected_site = {**site, **{key: site[key] * (hf if key == "households" else bf) for key in SECTORS}}
            for key, units in additions.items():
                projected_site[key] += units * added_factor
            central = forecast["central"] * factor + added
            rows.append({"month": (year - 1) * 12 + month + 1, "year": year, "month_in_year": month + 1,
                         "central": central, "lower": forecast["lower"] * factor + added,
                         "upper": forecast["upper"] * factor + added, "added_productive_kwh": added,
                         "peak_kw": profile(projected_site, central)["peak_kw"]})
    return rows


def _case(key, label, factor, months, assumptions, planning):
    rows = []
    for month in months:
        demand = month["central"] * factor
        peak = month["peak_kw"] * factor
        base = finance(demand, assumptions, peak)["base"]
        rows.append({"scenario": key, "month": month["month"], "year": month["year"], "factor": factor,
                     "calendar_month": month.get("calendar_month"),
                     **{k: v for k, v in base.items() if k not in ("label", "factor")}})
    years = []
    for year in (1, 2, 3):
        group = [row for row in rows if row["year"] == year]
        totals = {key: sum(row[key] for row in group) for key in ("demand_kwh", "served_kwh", "unserved_kwh", "revenue", "operating_cost", "operating_surplus", "cash_after_debt")}
        annual_capacity = assumptions["capacity_kwh"] * 12
        unused = max(0, annual_capacity - totals["served_kwh"])
        unused_share = unused / annual_capacity if annual_capacity else None
        peak = max(row["peak_kw"] for row in group)
        shortfall = max(0, peak - assumptions["firm_power_kw"])
        debt = assumptions["debt_payment"] * 12
        years.append({"scenario": key, "label": label, "year": year, **totals,
                      "average_monthly_kwh": totals["demand_kwh"] / 12, "peak_kw": peak,
                      "dscr": totals["operating_surplus"] / debt if debt else None,
                      "cash_shortfall_months": sum(row["cash_after_debt"] < 0 for row in group),
                      "unused_capacity_kwh": unused, "unused_capacity_share": unused_share,
                      "energy_utilization": totals["served_kwh"] / annual_capacity if annual_capacity else None,
                      "spare_power_kw": max(0, assumptions["firm_power_kw"] - peak), "peak_shortfall_kw": shortfall,
                      "lost_sales_amount": totals["unserved_kwh"] * assumptions["tariff"] * assumptions["collection_rate"],
                      "idle_capital_exposure_amount": planning["capacity_capex"] * unused_share if planning["capacity_capex"] is not None and unused_share is not None else None,
                      "supply_gap": totals["unserved_kwh"] > 1e-7 or shortfall > 1e-7})
    capex = planning["project_capex"]
    discounted_surplus = sum(row["operating_surplus"] / (1 + planning["discount_rate"]) ** (row["month"] / 12) for row in rows)
    return {"key": key, "label": label, "factor": factor, "months": rows, "years": years,
            "three_year_cash_after_debt": sum(row["cash_after_debt"] for row in rows),
            "three_year_operating_surplus": sum(row["operating_surplus"] for row in rows),
            "three_year_npv_before_financing": discounted_surplus - capex if capex is not None else None}


def productive_options(site, forecast, assumptions, planning, unit_rates=None, base_parts=None):
    """Separate one-unit alternatives, with operator economics, not enterprise ROI."""
    base = finance(forecast["central"], assumptions)["base"]
    margin = assumptions["tariff"] * assumptions["collection_rate"] - assumptions["variable_cost"]
    options = []
    for sector, key, label in [("mills", "mill", "One mill"), ("pumps", "pump", "One irrigation pump"), ("cold_rooms", "cold_room", "One cold room")]:
        extra = (unit_rates or CONFIG["sector_kwh_month"])[sector]
        changed = {**site, sector: site[sector] + 1}
        changed_parts = {**base_parts, sector: base_parts[sector] + extra} if base_parts is not None else None
        p = profile(changed, forecast["central"] + extra, parts=changed_parts)
        new = finance(forecast["central"] + extra, assumptions, p["peak_kw"])["base"]
        served = new["served_kwh"] - base["served_kwh"]
        incremental_cost = planning[f"{key}_monthly_cost"]
        cash = served * margin - incremental_cost
        support = planning[f"{key}_support_cost"]
        supply_gap = new["unserved_kwh"] > 1e-7 or new["peak_shortfall_kw"] > 1e-7
        reason = "No spare energy" if served < 1e-7 else "No positive grid contribution" if cash <= 0 else "Supply upgrade needed" if supply_gap else "Fits entered supply limits"
        options.append({"key": key, "label": label, "extra_demand_kwh_month": extra,
                        "extra_served_kwh_month": served, "extra_unserved_kwh_month": extra - served,
                        "extra_revenue_amount_month": served * assumptions["tariff"] * assumptions["collection_rate"],
                        "extra_operating_cost_amount_month": served * assumptions["variable_cost"] + incremental_cost,
                        "extra_contribution_amount_month": cash, "extra_fixed_cost_amount_month": incremental_cost,
                        "developer_support_cost_amount": support,
                        "simple_payback_years": support / (cash * 12) if support is not None and cash > 0 else None,
                        "total_peak_kw": p["peak_kw"], "peak_shortfall_kw": new["peak_shortfall_kw"],
                        "supply_gap": supply_gap, "screen": reason})
    options.sort(key=lambda row: (-row["extra_contribution_amount_month"], row["key"]))
    for rank, row in enumerate(options, 1):
        row["rank"] = rank
    return options


def build_feasibility(site, forecast, assumptions, planning, months=None, connection=None):
    months = months if months is not None else monthly_outlook(site, forecast, assumptions)
    cases = [_case(key, label, factor, months, assumptions, planning) for key, label, factor in
             [("low", "Low", planning["low_factor"]), ("expected", "Expected", 1), ("high", "High", planning["high_factor"])]]
    low, expected, high = [case["years"][0] for case in cases]
    findings = []
    if low["cash_after_debt"] < 0:
        findings.append({"title": "Downside repayment gap", "detail": "Low demand leaves negative Year 1 cash after the stated debt payments.", "action": "Review financing payments, collection and fixed costs."})
    if high["supply_gap"]:
        findings.append({"title": "High-demand supply gap", "detail": "The high case exceeds entered monthly energy or typical-peak power limits.", "action": "Check phased expansion with an hourly resource and battery study."})
    if low["unused_capacity_kwh"] > 1e-7:
        findings.append({"title": "Potential over-sizing", "detail": "The low case leaves part of the entered annual energy capacity unused.", "action": "Compare staged construction and productive-use commitments. Spare capacity can support future growth."})
    if not findings:
        findings.append({"title": "No flagged Year 1 cash or capacity gap", "detail": "This limited screen has not established technical reliability or project viability.", "action": "Validate demand, engineering, capital costs and financing terms."})
    from .connection import METHOD
    return {"version": "1.5", "scenarios": cases, "monthly_growth": months,
            "productive_options": productive_options(site, forecast, assumptions, planning), "findings": findings,
            "evidence_gaps": ["Real meter data or independent demand and willingness-to-pay surveys",
                              "Resource assessment, network design and hourly generation/storage dispatch",
                              "Productive-user commitments, business demand and ability to pay",
                              "Verified capital quotations, maintenance/replacement budgets and financing terms",
                              "Site rights, environmental/social requirements and applicable permissions"],
            "methods": {
                "scenarios": "Low/Expected/High multiply all expected monthly demand, including future productive-use additions. These are editable what-if cases, not probabilities or the calibrated prediction interval.",
                "growth": METHOD if connection and connection["enabled"] else "Monthly compounding is normalized within each year to match the existing three-year average-demand projection. Year 1 totals remain unchanged. New equipment starts in month 1 of the chosen adoption year. No seasonality is claimed.",
                "sizing": "Energy utilization uses served energy / entered annual customer-side energy capacity. Firm power is compared with illustrative monthly typical-day peaks, not annual maximum demand. Unused capacity is potential over-sizing, not proven waste. Capacity-linked capital × unused energy share is an allocation proxy, not recoverable savings. Energy and power gaps can coexist with spare capacity. No dispatch or equipment sizing is performed.",
                "productive": "Each option is a static one-unit comparison against average Year 1 demand, not a staged adoption forecast. It independently adds one unit at baseline monthly energy. Ranked by added developer operating contribution after variable and entered extra operating costs. Support costs belong to the developer, not the productive business. Simple payback assumes constant contribution and excludes discounting, tax, financing, replacements and supply upgrades; values with a supply gap are provisional. Options are not additive or adoption recommendations.",
                "finance": "Three-year NPV uses end-of-month operating surplus discounted with the annual effective rate, less entered initial project capex. It is before financing and tax, with no terminal value, replacements, expansion capex or residual asset value. It is a limited 36-month screen, not a whole-life project or equity NPV. Debt coverage and cash after debt use the stated monthly debt payment; no loan amortization is inferred. Prices, costs and capacity stay fixed. Missing budgets produce no cost/NPV/payback claim. Zero extra productive-use costs are assumptions, not verified estimates."
            }}
