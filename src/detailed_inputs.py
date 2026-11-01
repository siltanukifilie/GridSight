"""Transparent detailed-input scenarios; no claim of training on these new features."""
from copy import deepcopy
from .domain import CONFIG, SECTORS, LABELS, validate_numbers, profile, demand_periods
from .connection import calendar_month, annual_outlook, first_year_finance
from .feasibility import build_feasibility, productive_options

APPLIANCE_LABELS = {"lighting": "LED lights", "phone": "Phone charging", "radio": "Radio",
                    "television": "Television", "refrigerator": "Refrigerator",
                    "fan": "Fan", "iron": "Iron", "other": "Other appliance"}
DEFAULTS = {
    "enabled": False, "months_since_connection": 0, "household_income_monthly": None,
    "connection_fee": None, "new_connections_yearly": 0, "appliance_adoption_rate": .1,
    "appliances": {key: {"units_per_household": units, "power_w": watts, "hours_per_day": hours}
                   for key, units, watts, hours in [
                       ("lighting", 4, 7, 5), ("phone", 1, 5, 3), ("radio", .3, 10, 4),
                       ("television", .25, 60, 4), ("refrigerator", .05, 100, 8),
                       ("fan", .1, 40, 4), ("iron", 0, 1000, .5), ("other", 0, 100, 1)]},
    "equipment": {key: {"power_kw": power, "hours_per_day": hours}
                  for key, power, hours in [("shops", .4, 8), ("mills", 5, 5),
                     ("pumps", 2, 6), ("cold_rooms", 1, 12), ("schools", .8, 6), ("clinics", 1, 12)]},
    "agricultural_seasonality": [1.0] * 12,
}
LIMITS = {"months_since_connection": (0, 120), "household_income_monthly": (0, 1e12),
          "connection_fee": (0, 1e10), "new_connections_yearly": (0, 1500),
          "appliance_adoption_rate": (0, 1)}
METHOD = ("Detailed-input engineering scenario, not a retrained ML model. Household energy equals connected households "
          "times appliance units per connected household times watts times daily running hours / 1000. "
          "Expected connection rate is the starting share at service Month 1; linear new connections are capped by service-area households. "
          "Appliance ownership grows at the entered annual adoption rate. Non-household energy uses entered unit power and running hours; "
          "business growth applies to shops and productive equipment, not schools or clinics. "
          "The 12 agricultural multipliers repeat by service month and affect mills and pumps only; they are not measured rainfall or crop forecasts. "
          "Time since connection shifts the 36-month forecast window. All energy months use 365/12 days. "
          "Income and connection fee support affordability checks, not uncalibrated demand elasticity. Tariff changes revenue, not physical demand. "
          "Low/high values are editable demand scenarios, not confidence intervals. Hourly timing uses illustrative sector shapes, not user operating schedules.")


def validate_detailed(raw=None):
    raw = {} if raw is None else raw
    if not isinstance(raw, dict) or set(raw) - set(DEFAULTS):
        raise ValueError("Use the supported detailed-input fields.")
    d = deepcopy(DEFAULTS)
    d.update({key: value for key, value in raw.items() if key not in ("appliances", "equipment")})
    if type(d["enabled"]) is not bool:
        raise ValueError("Detailed input mode must be true or false.")
    limits = {k: v for k, v in LIMITS.items() if not (k in ("household_income_monthly", "connection_fee") and d[k] is None)}
    d.update(validate_numbers(d, limits))
    if int(d["months_since_connection"]) != d["months_since_connection"]:
        raise ValueError("Time since connection must be whole months.")
    d["months_since_connection"] = int(d["months_since_connection"])
    for group, field_limits in (
        ("appliances", {"units_per_household": (0, 20), "power_w": (0, 10000), "hours_per_day": (0, 24)}),
        ("equipment", {"power_kw": (0, 5000), "hours_per_day": (0, 24)}),
    ):
        supplied = raw.get(group, {})
        if not isinstance(supplied, dict) or set(supplied) - set(d[group]):
            raise ValueError(f"Use the supported {group} types.")
        for key in d[group]:
            row = supplied.get(key, {})
            if not isinstance(row, dict) or set(row) - set(field_limits):
                raise ValueError(f"Invalid {group} fields for {key}.")
            d[group][key] = validate_numbers({**d[group][key], **row}, field_limits)
    values = d["agricultural_seasonality"]
    if not isinstance(values, list) or len(values) != 12:
        raise ValueError("Agricultural seasonality needs exactly 12 service-month multipliers.")
    d["agricultural_seasonality"] = [validate_numbers({"factor": v}, {"factor": (0, 2)})["factor"] for v in values]
    return d


def connected_households(site, d, service_month):
    return min(site["households"], site["households"] * site["uptake"] +
               d["new_connections_yearly"] * max(0, service_month - 1) / 12)


def month_components(site, a, d, service_month):
    age = (service_month - 1) / 12
    connected = connected_households(site, d, service_month)
    appliance_factor = (1 + d["appliance_adoption_rate"]) ** age
    household_daily = sum(v["units_per_household"] * v["power_w"] * v["hours_per_day"] / 1000
                          for v in d["appliances"].values()) * appliance_factor
    parts = {"households": connected * household_daily * CONFIG["days_per_month"]}
    business_factor = (1 + a["business_growth"]) ** age
    season = d["agricultural_seasonality"][(service_month - 1) % 12]
    added = 0
    first_equipment = (a["adoption_year"] - 1) * 12 + 1
    for key, unit in d["equipment"].items():
        rate = unit["power_kw"] * unit["hours_per_day"] * CONFIG["days_per_month"]
        factor = business_factor if key in ("shops", "mills", "pumps", "cold_rooms") else 1
        seasonal = season if key in ("mills", "pumps") else 1
        extra = 0
        if key in ("mills", "pumps", "cold_rooms") and service_month >= first_equipment:
            extra = a["additional_" + key] * (1 + a["business_growth"]) ** ((service_month-first_equipment)/12)
        parts[key] = (site[key] * factor + extra) * rate * seasonal
        added += extra * rate * seasonal
    return parts, connected, household_daily, added, season


def detailed_months(site, a, p, c, d):
    rows = []
    for i in range(1, 37):
        service = d["months_since_connection"] + i
        parts, connected, household_daily, added, season = month_components(site, a, d, service)
        expected = sum(parts.values())
        shape = profile(site, expected, parts=parts)
        rows.append({"month": i, "service_month": service, "year": (i-1)//12+1, "month_in_year": (i-1)%12+1,
                     "calendar_month": calendar_month(c["connection_month"], service),
                     "central": expected, "lower": expected*p["low_factor"], "upper": expected*p["high_factor"],
                     "peak_kw": shape["peak_kw"], "added_productive_kwh": added,
                     "estimated_connected_households": connected, "household_kwh_day": household_daily,
                     "seasonality_factor": season, **{key+"_kwh": value for key, value in parts.items()}})
    return rows


def feature_inventory():
    return [
        ("Households in service area", "site.households", "Connection ceiling and household energy"),
        ("Expected household connection rate", "site.uptake", "Starting connected share in service Month 1"),
        ("Time since electricity connection", "detailed.months_since_connection", "Forecast starts at the next service month"),
        ("Household income", "detailed.household_income_monthly", "Bill burden and connection-fee burden; no demand elasticity"),
        ("Electricity tariff", "assumptions.tariff", "Revenue and household bill, not physical energy"),
        ("Connection fee", "detailed.connection_fee", "One-time household affordability burden; excluded from recurring cash"),
        ("Appliance ownership by type", "detailed.appliances.units_per_household", "Average units per connected household"),
        ("Appliance power ratings", "detailed.appliances.power_w", "Watts used in energy calculation"),
        ("Daily appliance operating hours", "detailed.appliances.hours_per_day", "Effective running hours, including duty cycle"),
        ("Businesses", "site.shops", "Business count excluding separately listed productive equipment"),
        ("Milling facilities", "site.mills", "Milling energy and seasonal demand"),
        ("Irrigation pumps", "site.pumps", "Pumping energy and seasonal demand"),
        ("Productive equipment power ratings", "detailed.equipment.power_kw", "Kilowatts per unit"),
        ("Productive equipment operating hours", "detailed.equipment.hours_per_day", "Effective running hours per day"),
        ("Schools", "site.schools", "School count times entered load"),
        ("Clinics", "site.clinics", "Clinic count times entered load"),
        ("Agricultural seasonality", "detailed.agricultural_seasonality", "12 repeating service-month factors for mills and pumps"),
        ("Expected new connections per year", "detailed.new_connections_yearly", "Linear household additions, capped at service-area households"),
        ("Appliance adoption rate", "detailed.appliance_adoption_rate", "Proportional annual growth in entered appliance ownership"),
        ("Business growth rate", "assumptions.business_growth", "Annual growth of businesses and productive use"),
    ]


def apply_detailed(r, d):
    site, a, p, c = r["site"], r["assumptions"], r["planning"], r["connection"]
    months = detailed_months(site, a, p, c, d)
    first = months[:12]
    parts = {key: sum(m[key+"_kwh"] for m in first)/12 for key in SECTORS}
    forecast = {"central": sum(m["central"] for m in first)/12,
                "lower": sum(m["lower"] for m in first)/12, "upper": sum(m["upper"] for m in first)/12,
                "baseline": sum(parts.values()), "interval_level": None,
                "method": "detailed_bottom_up", "version": "1.6",
                "range_basis": "Low / expected / high scenarios; no calibrated probability"}
    f = build_feasibility(site, forecast, a, p, months=months)
    f["version"] = "1.6"
    f["methods"]["growth"] = METHOD
    f["methods"]["scenarios"] = "Low / expected / high multiply the detailed expected path. The displayed demand range is this same scenario range, not a prediction interval."
    rates = {key: unit["power_kw"]*unit["hours_per_day"]*CONFIG["days_per_month"]*
             (sum(d["agricultural_seasonality"])/12 if key in ("mills", "pumps") else 1)
             for key, unit in d["equipment"].items()}
    f["productive_options"] = productive_options(site, forecast, a, p, unit_rates=rates, base_parts=parts)
    f["methods"]["productive"] = f["methods"]["productive"].replace("baseline monthly energy", "entered power × daily hours × 365/12, with the mean agricultural factor for mills/pumps")
    for row in f["productive_options"]:
        row["currency"] = r["context"]["currency"]
    for case in f["scenarios"]:
        for row in case["months"] + case["years"]:
            row["currency"] = r["context"]["currency"]
    f["currency"] = r["context"]["currency"]
    bill = sum(m["household_kwh_day"] for m in first)/12 * CONFIG["days_per_month"] * a["tariff"]
    income, fee = d["household_income_monthly"], d["connection_fee"]
    affordability = {"monthly_bill_per_connected_household": bill, "household_income_monthly": income,
                     "bill_share_of_income": bill/income if income else None, "connection_fee": fee,
                     "connection_fee_income_months": fee/income if fee is not None and income else None,
                     "currency": r["context"]["currency"],
                     "basis": "Gross-income screening, not disposable income, willingness to pay or credit eligibility. Unknown/zero income has no ratio. Connection fees are one-time customer costs, excluded from recurring operating revenue, cash and debt coverage."}
    periods = demand_periods(forecast["central"])
    periods["basis"] = (f"Forecast Year 1 averages service Months {months[0]['service_month']}–{months[11]['service_month']}. "
                        "Daily/weekly equivalents use 365 days/year. Agricultural multipliers affect mills/pumps; calendar labels anchor standard 365/12-day months, not exact billing totals.")
    finance = first_year_finance(months, a)
    finance["currency"] = r["context"]["currency"]
    # Discard warnings tied to the replaced ML/adoption calculation, retain location/grid evidence.
    retained = [w for w in r["warnings"] if not any(w.startswith(prefix) for prefix in (
        "Post-connection", "Outside the synthetic", "Monthly demand exceeds", "The illustrative",
        "At least one monthly", "No modeled customer", "Transfer demonstration"))]
    retained.insert(0, "Detailed estimate uses entered counts, watts and hours, not a model trained on these 20 features. Defaults and seasonal factors are unverified. No real metered-site validation or country-specific calibration.")
    retained.append("Connection rate is the starting share at service Month 1. New connections are capped by service-area households. The old household-growth percentage, appliance index and S-curve fractions are not applied in detailed mode.")
    if not forecast["central"]:
        retained.append("No modeled customer demand. Check connected households, appliance ownership and equipment.")
    if finance["base"]["unserved_kwh"] > 0:
        retained.append("Monthly demand exceeds supply in at least one forecast month; only served energy earns revenue.")
    if finance["base"]["peak_shortfall_kw"] > 0:
        retained.append("An illustrative monthly peak exceeds entered firm power; verify hourly dispatch and equipment start-up loads.")
    largest = max(parts, key=parts.get)
    explanation = [
        f"{LABELS[largest]} contribute about {parts[largest]/sum(parts.values()):.0%} of forecast-Year-1 energy." if sum(parts.values()) else "No energy is entered for the starting customer groups.",
        f"The next 36 months cover service Months {months[0]['service_month']}–{months[-1]['service_month']}. Expected demand starts at {months[0]['central']:,.0f} and ends at {months[-1]['central']:,.0f} kWh/month. These are calculated scenarios, not observed growth.",
        "Appliance units × watts × daily hours determine household use. New connections, appliance adoption and business growth change future use; agricultural multipliers affect mills and pumps.",
        "Income and connection fees show affordability burdens. Tariff sets bills and revenue; this version does not infer price or income effects on electricity use. Verify customer surveys, operating schedules, utility access and costs before investment."
    ]
    deliverables = deepcopy(r["deliverables"])
    deliverables[0].update(status="Implemented across eight EAC country selectors", detail="Administrative selection with local equivalents and visible coverage gaps. Detailed engineering estimates, not verified local demand.")
    deliverables[1].update(status="Scenario active · observed calibration pending", detail="36-month assumption curve plus a separate observed-history growth fitting workflow in Evidence. Fit and test Months 1–24 or 1–36 on independent sites. No genuine calibrated growth curve yet; total energy cannot identify individual adoption drivers.")
    deliverables[2]["detail"] = "Monthly current-model comparison and separate growth-fit / conformal-calibration / untouched-test study are available. Requires genuine paired histories and pre-connection inputs. Input simulations are not measured confidence; no real-site study is loaded. Annual reference-model comparison remains separate."
    provenance = {**r["provenance"], "calculation_origin": "assumption_based_engineering",
                  "notice": "Detailed engineering planning scenario from entered/proxy inputs and illustrative defaults. No real metered-site validation. The synthetic-trained model is retained for comparison/evidence, not used for this headline estimate. Financial inputs require verification."}
    r.update(detailed=d, forecast=forecast, feasibility=f, growth=annual_outlook(months),
             profile=profile(site, forecast["central"], parts=parts), finance=finance,
             demand_periods=periods, affordability=affordability, warnings=retained,
             lender_explanation=explanation, deliverables=deliverables, provenance=provenance,
             supply_energy_kwh=forecast["central"]/(1-a["loss_rate"]),
             components=[{"key": k, "label": LABELS[k], "kwh": parts[k],
                          "share": parts[k]/sum(parts.values()) if sum(parts.values()) else 0} for k in SECTORS],
             sensitivities=[], feature_inventory=[{"number": i, "name": name, "field": field, "use": use}
                for i, (name, field, use) in enumerate(feature_inventory(), 1)],
             horizon={"first_service_month": months[0]["service_month"], "last_service_month": months[-1]["service_month"],
                      "first_year_end": months[11]["service_month"]})
    return r
