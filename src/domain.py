"""Explicit units, bounded inputs, and transparent engineering assumptions."""
from pathlib import Path
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/assumptions.json").read_text())
SECTORS = list(CONFIG["sector_kwh_month"])
FEATURES = SECTORS + ["uptake", "appliance_index"]
LABELS = {"households": "Households", "shops": "Shops", "schools": "Schools", "clinics": "Health clinics", "mills": "Mills", "pumps": "Irrigation pumps", "cold_rooms": "Cold rooms"}
DISTRICTS = ["Kirehe", "Nyamasheke", "Gicumbi", "Muhanga", "Bugesera", "Ngoma"]
SITE_LIMITS = {"households": (0, 1500), "shops": (0, 150), "schools": (0, 10), "clinics": (0, 5), "mills": (0, 10), "pumps": (0, 15), "cold_rooms": (0, 10), "uptake": (0, 1), "appliance_index": (0.5, 2)}
SCENARIO_LIMITS = {"household_growth": (-0.2, 0.5), "business_growth": (-0.2, 0.5), "additional_mills": (0, 10), "additional_pumps": (0, 15), "additional_cold_rooms": (0, 10), "adoption_year": (2, 3), "tariff": (0, 1000000), "collection_rate": (0, 1), "variable_cost": (0, 1000000), "fixed_cost": (0, 100000000), "debt_payment": (0, 100000000), "capacity_kwh": (0, 1000000), "firm_power_kw": (0, 10000), "loss_rate": (0, 0.4)}
INTEGER_FIELDS = set(SECTORS + ["additional_mills", "additional_pumps", "additional_cold_rooms", "adoption_year"])

DEMOS = [
    {"id": "RW-DEMO-01", "name": "Hillside community", "district": "Nyamasheke", "archetype": "Residential", "description": "An evening-led community with small shops and a school.", "households": 120, "shops": 8, "schools": 1, "clinics": 0, "mills": 0, "pumps": 0, "cold_rooms": 0, "uptake": 0.75, "appliance_index": 0.85},
    {"id": "RW-DEMO-02", "name": "Market centre", "district": "Kirehe", "archetype": "Trading", "description": "A trading community with milling, refrigeration and public services.", "households": 300, "shops": 25, "schools": 2, "clinics": 1, "mills": 1, "pumps": 0, "cold_rooms": 2, "uptake": 0.85, "appliance_index": 1.15},
    {"id": "RW-DEMO-03", "name": "Farming cooperative", "district": "Bugesera", "archetype": "Agricultural", "description": "A growing community with irrigation and productive daytime demand.", "households": 450, "shops": 18, "schools": 2, "clinics": 1, "mills": 1, "pumps": 2, "cold_rooms": 0, "uptake": 0.8, "appliance_index": 1.0},
]


def validate_numbers(values, limits):
    if not isinstance(values, dict):
        raise ValueError("Inputs must be an object with named fields.")
    result = {}
    for key, (low, high) in limits.items():
        value = values.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key.replace('_', ' ').capitalize()} must be a finite number.")
        if value < low or value > high:
            raise ValueError(f"{key.replace('_', ' ').capitalize()} must be between {low:g} and {high:g}.")
        if key in INTEGER_FIELDS and value != int(value):
            raise ValueError(f"{key.replace('_', ' ').capitalize()} must be a whole number.")
        result[key] = int(value) if key in INTEGER_FIELDS else float(value)
    return result


def validate_site(raw):
    site = validate_numbers(raw, SITE_LIMITS)
    for key, default in [("name", "Custom community"), ("district", "Rwanda"), ("id", "CUSTOM"), ("archetype", "Custom")]:
        value = raw.get(key, default)
        if not isinstance(value, str) or not value.strip() or len(value) > 100:
            raise ValueError(f"{key.capitalize()} must contain 1–100 characters.")
        site[key] = value.strip()
    site["origin"] = "synthetic"
    return site


def baseline_components(site):
    rates = CONFIG["sector_kwh_month"]
    return {k: float(site[k] * rates[k] * (site["uptake"] * site["appliance_index"] if k == "households" else 1)) for k in SECTORS}


def baseline(site):
    return sum(baseline_components(site).values())


def demand_periods(monthly_kwh):
    """Convert Year 1 average customer energy; do not imply dated forecasts."""
    if isinstance(monthly_kwh, bool) or not isinstance(monthly_kwh, (int, float)) or not math.isfinite(monthly_kwh) or monthly_kwh < 0:
        raise ValueError("Monthly customer energy must be a finite nonnegative number.")
    days_per_month = CONFIG["days_per_month"]
    daily_kwh = monthly_kwh / days_per_month
    days_per_year = days_per_month * 12
    return {
        "basis": f"Year 1 average equivalents: {days_per_year:g} days per year, 12 months per year, and 7 days per week. Not forecasts for specific dates; seasonal variation and future growth are not applied.",
        "estimates": [
            {"period": "day", "label": "Per day", "central": daily_kwh, "unit": "kWh/day", "days_per_period": 1},
            {"period": "week", "label": "Per week", "central": daily_kwh * 7, "unit": "kWh/week", "days_per_period": 7},
            {"period": "month", "label": "Per month", "central": monthly_kwh, "unit": "kWh/month", "days_per_period": days_per_month},
            {"period": "year", "label": "Per year", "central": monthly_kwh * 12, "unit": "kWh/year", "days_per_period": days_per_year},
        ],
    }


def default_shapes():
    hour = np.arange(24)
    household = 0.15 + 0.7 * np.exp(-((hour - 6.5) / 1.5) ** 2) + 2.0 * np.exp(-((hour - 19.5) / 2.1) ** 2)
    business = 0.1 + np.exp(-((hour - 13) / 4.5) ** 2)
    school = 0.03 + np.exp(-((hour - 12) / 3) ** 4)
    continuous = 0.6 + 0.3 * np.exp(-((hour - 15) / 5) ** 2)
    raw = dict(zip(SECTORS, [household, business, school, continuous, business, business, continuous]))
    return {k: (v / v.sum()).tolist() for k, v in raw.items()}


def profile(site, monthly_kwh, parts=None):
    path = ROOT / "data/load_shapes.json"
    saved = json.loads(path.read_text()) if path.exists() else {"engine": "GridSight normalized illustrative shapes", "shapes": default_shapes()}
    parts = baseline_components(site) if parts is None else parts
    total = sum(parts.values())
    daily = monthly_kwh / CONFIG["days_per_month"]
    hourly = np.zeros(24)
    for key, amount in parts.items():
        if total:
            hourly += np.array(saved["shapes"][key]) * daily * amount / total
    return {"hours": list(range(24)), "kw": hourly.tolist(), "daily_kwh": daily, "peak_kw": float(hourly.max()), "peak_hour": int(hourly.argmax()), "load_factor": float(hourly.mean() / hourly.max()) if hourly.max() else 0, "engine": saved["engine"]}


def finance(monthly_kwh, assumptions, peak_kw=0):
    a = assumptions
    margin = a["tariff"] * a["collection_rate"] - a["variable_cost"]
    break_even = (a["fixed_cost"] + a["debt_payment"]) / margin if margin > 0 else None
    scenarios = []
    for label, factor in [("Demand −40%", 0.6), ("Demand −20%", 0.8), ("Base case", 1.0), ("Demand +30%", 1.3)]:
        demand = monthly_kwh * factor
        served = min(demand, a["capacity_kwh"])
        revenue = served * a["tariff"] * a["collection_rate"]
        operating_cost = a["fixed_cost"] + served * a["variable_cost"]
        surplus = revenue - operating_cost
        scenarios.append({"label": label, "factor": factor, "demand_kwh": demand, "served_kwh": served, "unserved_kwh": demand - served, "revenue": revenue, "operating_cost": operating_cost, "operating_surplus": surplus, "cash_after_debt": surplus - a["debt_payment"], "dscr": surplus / a["debt_payment"] if a["debt_payment"] else None, "peak_kw": peak_kw * factor, "peak_shortfall_kw": max(0, peak_kw * factor - a["firm_power_kw"])})
    return {"currency": "RWF", "break_even_kwh": break_even, "contribution_margin": margin, "break_even_within_capacity": break_even is not None and break_even <= a["capacity_kwh"], "scenarios": scenarios, "base": scenarios[2]}


def growth(site, forecast, assumptions):
    components = baseline_components(site)
    total = sum(components.values())
    household_share = components["households"] / total if total else 0
    result = []
    for year in [1, 2, 3]:
        factor = household_share * (1 + assumptions["household_growth"]) ** (year - 1) + (1 - household_share) * (1 + assumptions["business_growth"]) ** (year - 1)
        added = 0
        if year >= assumptions["adoption_year"]:
            added = (assumptions["additional_mills"] * CONFIG["sector_kwh_month"]["mills"] + assumptions["additional_pumps"] * CONFIG["sector_kwh_month"]["pumps"] + assumptions.get("additional_cold_rooms", 0) * CONFIG["sector_kwh_month"]["cold_rooms"]) * (1 + assumptions["business_growth"]) ** (year - assumptions["adoption_year"])
        result.append({"year": year, "central": forecast["central"] * factor + added, "lower": forecast["lower"] * factor + added, "upper": forecast["upper"] * factor + added, "added_productive_kwh": added})
    return result
