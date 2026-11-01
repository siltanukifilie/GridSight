"""Country and input provenance. Context never silently changes model features."""
import json
from datetime import date
from .domain import ROOT, CONFIG, FEATURES, SITE_LIMITS, validate_site, validate_numbers

COUNTRIES = json.loads((ROOT / "config/countries.json").read_text())
MONEY_FIELDS = ("tariff", "variable_cost", "fixed_cost", "debt_payment")


def country(code):
    if not isinstance(code, str) or code not in COUNTRIES:
        raise ValueError("Choose one of the eight supported EAC countries.")
    return COUNTRIES[code]


def scenario_defaults(code):
    country(code)
    defaults = dict(CONFIG["default_scenario"])
    if code != "RW":
        defaults.update({k: 0 for k in MONEY_FIELDS})
    return defaults


def validate_context(raw=None):
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("Project context must be an object.")
    code = raw.get("country_code", "RW")
    profile = country(code)
    assumed = raw.get("assumed_fields", [])
    if not isinstance(assumed, list) or any(not isinstance(k, str) or k not in FEATURES for k in assumed) or len(set(assumed)) != len(assumed):
        raise ValueError("Assumed fields must be unique community input names.")
    origin = raw.get("input_origin", "synthetic")
    if origin not in ("synthetic", "user_entered", "public_proxy"):
        raise ValueError("Input origin must be synthetic, user_entered or public_proxy.")
    location = raw.get("location")
    if origin == "public_proxy" and (code != "RW" or location is None):
        raise ValueError("Automatic public-data screening currently requires a Rwanda location.")
    if isinstance(location, dict) and location.get("source") == "user_entered_administration":
        if location.get("country_code") != code:
            raise ValueError("Administrative names must match the selected country.")
        names = location.get("administrative_path")
        if not isinstance(names, list) or len(names) != 3 or any(not isinstance(n, str) or not 1 <= len(n.strip()) <= 100 for n in names):
            raise ValueError("Enter district, sector and cell (or local equivalent) names.")
        if origin == "public_proxy":
            raise ValueError("User-entered administrative names are not public-data proxies.")
        names = [n.strip() for n in names]
        location = {"country_code": code, "source": "user_entered_administration", "label": names[-1],
                    "administrative_path": names, "latitude": None, "longitude": None,
                    "kind": "User-entered administrative names; not geographically verified", "timezone": profile["timezone"]}
    elif location is not None:
        if not isinstance(location, dict):
            raise ValueError("Location must contain a label and coordinates.")
        coords = validate_numbers(location, {"latitude": (-90, 90), "longitude": (-180, 180)})
        label = location.get("label")
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 120:
            raise ValueError("Location name must contain 1–120 characters.")
        if location.get("country_code") != code:
            raise ValueError("Location must match the selected country.")
        south, west, north, east = profile["bounds"]
        if not south <= coords["latitude"] <= north or not west <= coords["longitude"] <= east:
            raise ValueError("Coordinates are outside the selected country's approximate search bounds. Check the country and coordinates.")
        source = location.get("source", "manual")
        if source not in ("manual", "Open-Meteo / GeoNames", "device_rounded", "GeoNames"):
            raise ValueError("Unknown location source.")
        if source == "GeoNames":
            from .geography import public_location
            location = public_location(code, location.get("id"))
        else:
            location = {**coords, "label": label.strip(), "source": source, "country_code": code}
    grid = raw.get("grid", {"status": "unknown", "source": "", "checked_on": None})
    if not isinstance(grid, dict) or grid.get("status") not in ("unknown", "reported_unserved", "planned", "connected"):
        raise ValueError("Choose a valid grid-access status.")
    source = grid.get("source", "")
    checked = grid.get("checked_on") or None
    if not isinstance(source, str) or len(source) > 240:
        raise ValueError("Grid evidence note must be at most 240 characters.")
    if checked is not None:
        try:
            parsed = date.fromisoformat(checked)
            if parsed > date.today() or parsed.isoformat() != checked:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Grid check date must be a valid date, not in the future.")
    if grid["status"] != "unknown" and (len(source.strip()) < 3 or not checked):
        raise ValueError("Add a source note and check date for a reported grid status.")
    grid = {"status": grid["status"], "source": source.strip(), "checked_on": checked, "verification": "User-reported; not independently verified"}
    snapshot = raw.get("public_data_id")
    if snapshot is not None and (not isinstance(snapshot, str) or len(snapshot) != 24 or any(c not in "0123456789abcdef" for c in snapshot)):
        raise ValueError("Invalid public-data snapshot identifier.")
    return {"country_code": code, "country": profile["name"], "currency": profile["currency"], "timezone": (location or {}).get("timezone") or profile["timezone"], "model_status": profile["model_status"], "location": location, "grid": grid, "assumed_fields": assumed, "input_origin": origin, "public_data_id": snapshot}


def prepare_thin_inputs(payload):
    """Propose, never silently apply, editable assumptions for explicitly blank inputs."""
    if not isinstance(payload, dict) or not isinstance(payload.get("site"), dict):
        raise ValueError("Provide the known community inputs.")
    raw = payload["site"]
    households = validate_numbers(raw, {"households": SITE_LIMITS["households"]})["households"]
    defaults = {"shops": round(households * .05), "schools": int(households >= 100), "clinics": 0, "mills": 0, "pumps": 0, "cold_rooms": 0, "uptake": .75, "appliance_index": 1}
    site = dict(raw)
    proposed = []
    for key, value in defaults.items():
        if raw.get(key) is None:
            site[key] = value
            reason = "Planning placeholder, not a public-data estimate."
            if key in ("clinics", "mills", "pumps", "cold_rooms"):
                reason = "No verified count: assume none for this screen; this may understate demand."
            proposed.append({"field": key, "value": value, "reason": reason})
    return {"site": validate_site(site), "assumptions": proposed, "assumed_fields": [r["field"] for r in proposed], "notice": "Review every proposed value before applying. Missing does not mean zero. The prediction interval does not include uncertainty in these guessed inputs."}
