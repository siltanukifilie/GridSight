"""Explicit post-connection adoption scenarios, not a learned adoption forecast."""
import re
from .domain import CONFIG, SECTORS, baseline_components, profile, finance, validate_numbers

DEFAULTS = {"enabled": False, "connection_month": None, "start_household_fraction": .35,
            "start_appliance_fraction": .6, "start_business_fraction": .5, "ramp_months": 24}
LIMITS = {"start_household_fraction": (0, 1), "start_appliance_fraction": (0, 1),
          "start_business_fraction": (0, 1), "ramp_months": (1, 60)}
METHOD = ("Post-connection scenario: the model's current-input estimate is used as an assumed mature-demand reference, not a measured mature load. "
          "Household connections, household appliance use and existing non-household use follow separate smooth S-shaped ramps from Month 1 to the chosen maturity month. "
          "Community counts and target uptake/appliance index describe the mature reference. Annual household/business growth compounds from Month 1 in addition to adoption; use it for underlying expansion, not the same adoption twice. "
          "New productive equipment starts once at the beginning of its selected service year, at full assumed unit use, then follows business growth. "
          "Year 1 totals are calculated from the ramp, not forced back to the old forecast. Months are 365/12-day energy equivalents; calendar labels anchor service months, not actual billing-day totals. "
          "Reference bounds are propagated under identical assumptions and do not cover uncertain adoption, growth or inputs. This curve is not validated against metered post-connection sites.")


def validate_connection(raw=None):
    if raw is None:
        raw = {}
    if not isinstance(raw, dict) or set(raw) - set(DEFAULTS):
        raise ValueError("Use the supported connection-growth fields.")
    values = {**DEFAULTS, **raw}
    if type(values["enabled"]) is not bool:
        raise ValueError("Connection growth enabled must be true or false.")
    values.update(validate_numbers(values, LIMITS))
    if values["ramp_months"] != int(values["ramp_months"]):
        raise ValueError("Ramp months must be a whole number.")
    values["ramp_months"] = int(values["ramp_months"])
    month = values["connection_month"]
    if month is not None and (not isinstance(month, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month) or not 1900 <= int(month[:4]) <= 2100):
        raise ValueError("Connection month must be YYYY-MM (1900–2100), or blank.")
    return values


def ramp(start, month, maturity):
    if maturity == 1:
        return 1.0
    t = min(1.0, max(0.0, (month - 1) / (maturity - 1)))
    return start + (1 - start) * t * t * (3 - 2 * t)


def calendar_month(start, month):
    if start is None:
        return None
    year, base = map(int, start.split("-"))
    year, index = divmod(year * 12 + base - 1 + month - 1, 12)
    return f"{year:04d}-{index + 1:02d}"


def factors(month, assumptions, c):
    u = ramp(c["start_household_fraction"], month, c["ramp_months"])
    a = ramp(c["start_appliance_fraction"], month, c["ramp_months"])
    b = ramp(c["start_business_fraction"], month, c["ramp_months"])
    hg = (1 + assumptions["household_growth"]) ** ((month - 1) / 12)
    bg = (1 + assumptions["business_growth"]) ** ((month - 1) / 12)
    return u, a, b, hg * u * a, bg * b, hg


def first_year_multiplier(site, assumptions, c):
    parts = baseline_components(site)
    share = parts["households"] / sum(parts.values()) if sum(parts.values()) else 0
    return sum(share * factors(m, assumptions, c)[3] + (1 - share) * factors(m, assumptions, c)[4] for m in range(1, 13)) / 12


def monthly_connection_outlook(site, reference, assumptions, c):
    parts = baseline_components(site)
    share = parts["households"] / sum(parts.values()) if sum(parts.values()) else 0
    additions = {"mills": assumptions["additional_mills"], "pumps": assumptions["additional_pumps"], "cold_rooms": assumptions.get("additional_cold_rooms", 0)}
    first_equipment_month = (assumptions["adoption_year"] - 1) * 12 + 1
    rows = []
    for month in range(1, 37):
        u, a, b, hf, bf, hg = factors(month, assumptions, c)
        factor = share * hf + (1 - share) * bf
        added_factor = (1 + assumptions["business_growth"]) ** ((month - first_equipment_month) / 12) if month >= first_equipment_month else 0
        added = sum(n * CONFIG["sector_kwh_month"][k] for k, n in additions.items()) * added_factor
        projected = {**site, **{k: site[k] * (hf if k == "households" else bf) for k in SECTORS}}
        for k, n in additions.items():
            projected[k] += n * added_factor
        central = reference["central"] * factor + added
        rows.append({"month": month, "year": (month - 1) // 12 + 1, "month_in_year": (month - 1) % 12 + 1,
                     "calendar_month": calendar_month(c["connection_month"], month), "central": central,
                     "lower": reference["lower"] * factor + added, "upper": reference["upper"] * factor + added,
                     "added_productive_kwh": added, "peak_kw": profile(projected, central)["peak_kw"],
                     "household_connection_fraction": u, "appliance_fraction": a, "business_use_fraction": b,
                     "household_factor": hf, "business_factor": bf,
                     "estimated_connected_households": site["households"] * hg * site["uptake"] * u,
                     "household_uptake": site["uptake"] * u, "household_appliance_index": site["appliance_index"] * a})
    return rows


def annual_outlook(months):
    return [{"year": year, **{k: sum(m[k] for m in months if m["year"] == year) / 12
                              for k in ("central", "lower", "upper", "added_productive_kwh")}} for year in (1, 2, 3)]


def first_year_site(site, months):
    return {**site, **{k: site[k] * sum(m["household_factor" if k == "households" else "business_factor"] for m in months[:12]) / 12 for k in SECTORS}}


def first_year_finance(months, assumptions):
    """Average actual monthly financial outcomes, preserving each month's cap."""
    first = months[:12]
    result = finance(sum(m["central"] for m in first) / 12, assumptions)
    for scenario in result["scenarios"]:
        rows = [finance(m["central"] * scenario["factor"], assumptions, m["peak_kw"] * scenario["factor"])["base"] for m in first]
        for key in ("demand_kwh", "served_kwh", "unserved_kwh", "revenue", "operating_cost", "operating_surplus", "cash_after_debt"):
            scenario[key] = sum(row[key] for row in rows) / 12
        scenario["dscr"] = scenario["operating_surplus"] / assumptions["debt_payment"] if assumptions["debt_payment"] else None
        scenario["peak_kw"] = max(r["peak_kw"] for r in rows)
        scenario["peak_shortfall_kw"] = max(r["peak_shortfall_kw"] for r in rows)
    result["basis"] = "Year 1 average of monthly cash calculations; supply limits applied month by month. Peak fields use the highest monthly typical-day peak."
    return result
