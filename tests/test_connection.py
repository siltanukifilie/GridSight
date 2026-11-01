"""Post-connection assumptions are explicit, conserved and not field-validated."""
import copy
import csv
import io
import json
import zipfile
import pytest
from app import create_app
from src.domain import CONFIG, DEMOS, SECTORS
from src.connection import (validate_connection, monthly_connection_outlook,
                            annual_outlook, first_year_multiplier, first_year_finance)
from src.feasibility import build_feasibility, validate_planning

REFERENCE = {"central": 1000, "lower": 700, "upper": 1400}


def inputs(**changes):
    return {**CONFIG["default_scenario"], "household_growth": 0, "business_growth": 0,
            "additional_mills": 0, "additional_pumps": 0, "additional_cold_rooms": 0,
            **changes}


def household_site():
    return {**DEMOS[0], **{key: 0 for key in SECTORS}, "households": 100,
            "uptake": .75, "appliance_index": 1}


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


@pytest.mark.parametrize("bad", [
    [], "yes", {"unknown": 1}, {"enabled": 1}, {"enabled": "true"},
    {"start_household_fraction": -0.1}, {"start_household_fraction": 1.1},
    {"start_appliance_fraction": None}, {"start_business_fraction": True},
    {"ramp_months": 0}, {"ramp_months": 61}, {"ramp_months": 2.5},
    {"ramp_months": float("nan")}, {"ramp_months": float("inf")},
    {"connection_month": "2026-13"}, {"connection_month": "2026-00"},
    {"connection_month": "2026-1"}, {"connection_month": "2026-01-01"},
    {"connection_month": "1899-12"}, {"connection_month": "2101-01"},
    {"connection_month": True}, {"connection_month": "<script>"},
])
def test_connection_input_rejected(bad):
    with pytest.raises(ValueError):
        validate_connection(bad)


def test_backward_compatibility_and_explicit_zero():
    assert validate_connection()["enabled"] is False
    c = validate_connection({"enabled": True, "start_household_fraction": 0,
                             "start_appliance_fraction": 0, "start_business_fraction": 0,
                             "connection_month": None})
    assert c["start_household_fraction"] == c["start_appliance_fraction"] == c["start_business_fraction"] == 0


def test_hand_calculated_adoption_and_calendar_rollover():
    site = household_site()
    c = validate_connection({"enabled": True, "connection_month": "2026-11"})
    original = copy.deepcopy((site, REFERENCE, c))
    months = monthly_connection_outlook(site, REFERENCE, inputs(), c)
    assert months[0]["central"] == pytest.approx(1000*.35*.6)
    assert months[0]["estimated_connected_households"] == pytest.approx(100*.75*.35)
    assert months[0]["household_uptake"] == pytest.approx(.75*.35)
    assert months[23]["central"] == months[35]["central"] == 1000
    assert months[0]["calendar_month"] == "2026-11"
    assert months[2]["calendar_month"] == "2027-01"
    assert months[-1]["calendar_month"] == "2029-10"
    assert all(b["central"] >= a["central"] for a, b in zip(months, months[1:]))
    annual = annual_outlook(months)
    assert annual[0]["central"] < 1000
    assert annual[0]["central"] == pytest.approx(1000*first_year_multiplier(site, inputs(), c))
    for year in annual:
        for key in ("central", "lower", "upper", "added_productive_kwh"):
            assert year[key]*12 == pytest.approx(sum(m[key] for m in months if m["year"] == year["year"]))
    assert (site, REFERENCE, c) == original


@pytest.mark.parametrize("maturity", [1, 24, 60])
def test_zero_starts_and_instant_maturity(maturity):
    c = validate_connection({"enabled": True, "ramp_months": maturity,
                             "start_household_fraction": 0, "start_appliance_fraction": 0,
                             "start_business_fraction": 0})
    rows = monthly_connection_outlook(household_site(), REFERENCE, inputs(), c)
    assert rows[0]["central"] == (1000 if maturity == 1 else 0)
    assert rows[1]["central"] > 0
    assert all(m["calendar_month"] is None for m in rows)
    assert (rows[-1]["central"] < 1000) is (maturity > 36)
    json.dumps(rows, allow_nan=False)


@pytest.mark.parametrize("rate", [-.2, 0, .12])
def test_growth_is_not_forced_up(rate):
    c = validate_connection({"enabled": True, "ramp_months": 1})
    rows = monthly_connection_outlook(household_site(), REFERENCE,
                                     inputs(household_growth=rate), c)
    for before, after in zip(rows, rows[1:]):
        assert after["central"]/before["central"] == pytest.approx((1+rate)**(1/12))


@pytest.mark.parametrize("year", [2, 3])
def test_productive_addition_once_even_with_zero_starting_demand(year):
    site = {**household_site(), "households": 0}
    c = validate_connection({"enabled": True})
    rows = monthly_connection_outlook(site, {key: 0 for key in REFERENCE},
                                     inputs(additional_mills=1, adoption_year=year), c)
    start = (year-1)*12
    assert all(m["central"] == 0 for m in rows[:start])
    assert all(m["central"] == 800 for m in rows[start:])
    assert rows[start]["peak_kw"] > 0
    assert rows[-1]["estimated_connected_households"] == 0


def test_monthly_caps_and_stress_finance_match_feasibility():
    a = inputs(capacity_kwh=300)
    c = validate_connection({"enabled": True, "ramp_months": 12})
    rows = monthly_connection_outlook(household_site(), REFERENCE, a, c)
    financial = first_year_finance(rows, a)
    f = build_feasibility(household_site(), REFERENCE, a, validate_planning(),
                          months=rows, connection=c)
    assert financial["base"] is financial["scenarios"][2]
    # Saturated later months cannot compensate for idle capacity at connection.
    assert financial["base"]["served_kwh"] < min(300, sum(m["central"] for m in rows[:12])/12)
    for scenario, case in zip(financial["scenarios"][1:], f["scenarios"]):
        for key in ("demand_kwh", "served_kwh", "unserved_kwh", "revenue",
                    "operating_cost", "operating_surplus", "cash_after_debt"):
            assert scenario[key]*12 == pytest.approx(case["years"][0][key])
        assert scenario["dscr"] == pytest.approx(case["years"][0]["dscr"])
        assert scenario["peak_kw"] == pytest.approx(case["years"][0]["peak_kw"])


def test_zero_supply_and_debt_remain_finite():
    c = validate_connection({"enabled": True})
    rows = monthly_connection_outlook(household_site(), REFERENCE, inputs(), c)
    result = first_year_finance(rows, inputs(capacity_kwh=0, debt_payment=0))
    assert result["base"]["served_kwh"] == 0
    assert result["base"]["dscr"] is None
    json.dumps(result, allow_nan=False)


def test_dashboard_and_both_roles_share_one_curve(client):
    body = {"site": DEMOS[1], "connection": {"enabled": True, "connection_month": "2026-11"}}
    dev = client.post("/api/analyze", json={**body, "role": "developer"}).json
    inv = client.post("/api/analyze", json={**body, "role": "investor"}).json
    for key in ("connection", "forecast", "reference_forecast", "feasibility", "growth",
                "demand_periods", "finance", "profile", "lender_explanation", "deliverables"):
        assert dev[key] == inv[key]
    rows = dev["feasibility"]["monthly_growth"]
    total = sum(m["central"] for m in rows[:12])
    assert dev["forecast"]["central"]*12 == pytest.approx(total)
    assert dev["growth"][0]["central"]*12 == pytest.approx(total)
    assert dev["profile"]["daily_kwh"]*365 == pytest.approx(total)
    assert sum(dev["profile"]["kw"])*365 == pytest.approx(total)
    periods = {r["period"]: r["central"] for r in dev["demand_periods"]["estimates"]}
    assert periods["year"] == pytest.approx(total)
    assert periods["week"] == pytest.approx(total/365*7)
    assert dev["forecast"]["central"] < dev["reference_forecast"]["central"]
    assert "not calibrated" in dev["forecast"]["range_basis"]
    assert dev["forecast"]["interval_level"] is None
    assert dev["forecast"]["reference_interval_level"] == .8
    assert len(dev["deliverables"]) == 5
    assert "Pending genuine operator data" in dev["deliverables"][2]["status"]
    assert "not proven causes" in dev["lender_explanation"][-1]


@pytest.mark.parametrize("route", ["/api/analyze", "/api/report", "/api/feasibility-report", "/api/export"])
def test_all_output_routes_validate_connection_inputs(client, route):
    response = client.post(route, json={"site": DEMOS[0], "connection": {"ramp_months": 0}})
    assert response.status_code == 400


@pytest.mark.parametrize("role", ["developer", "investor"])
def test_reports_and_exports_preserve_connection_and_five_deliverables(client, role):
    body = {"role": role, "site": DEMOS[1],
            "connection": {"enabled": True, "connection_month": "2026-11"}}
    r = client.post("/api/analyze", json=body).json
    for route in ("/api/report", "/api/feasibility-report"):
        response = client.post(route, json=body)
        assert response.status_code == 200
        text = response.get_data(as_text=True)
        for expected in ("Demand after connection", "2026-11", "2029-10",
                         "Safe meter-data sharing proposal", "Pending genuine operator data",
                         "Plain-language lender explanation", "proposal", "<svg"):
            assert expected in text
        assert "80% nominal prediction range</small>" not in text
    archive = client.post("/api/export", json=body)
    with zipfile.ZipFile(io.BytesIO(archive.data)) as z:
        exported = json.loads(z.read("analysis.json"))
        assert exported["connection"] == r["connection"]
        monthly = list(csv.DictReader(io.StringIO(z.read("monthly_growth.csv").decode())))
        assert len(monthly) == 36
        assert monthly[0]["calendar_month"] == "2026-11"
        assert monthly[-1]["calendar_month"] == "2029-10"
        assert float(monthly[0]["household_connection_fraction"]) == .35
        assert float(monthly[-1]["central"]) == r["feasibility"]["monthly_growth"][-1]["central"]
        assert b"Safe meter-data sharing proposal" in z.read("report.html")


def test_sharing_proposal_download_and_settings(client):
    response = client.get("/api/meter-sharing-proposal")
    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]
    text = response.get_data(as_text=True)
    for phrase in ("Proposal only", "not implemented", "monthly workflow", "raw customer",
                   "split by entire site", "deletion", "800-188"):
        assert phrase in text
    settings = client.get("/api/planning-settings").json
    assert settings["connection_defaults"]["ramp_months"] == 24
    assert settings["connection_limits"]["ramp_months"] == [1, 60]
