"""Twenty-input engineering scenarios: arithmetic, safety, persistence and geography."""
import copy
import csv
import io
import json
import zipfile

import pytest

from app import create_app
from src.domain import CONFIG, DEMOS, SECTORS
from src.detailed_inputs import validate_detailed, month_components, detailed_months
from src.connection import validate_connection
from src.feasibility import validate_planning
from src.context import validate_context
from src.geography import browse, public_location, record, within


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def site():
    return {**DEMOS[0], **{k: 0 for k in SECTORS}, "households": 100, "uptake": .5}


def assumptions(**changes):
    return {**CONFIG["default_scenario"], "business_growth": 0,
            "additional_mills": 0, "additional_pumps": 0, "additional_cold_rooms": 0, **changes}


def details(**changes):
    d = validate_detailed({"enabled": True, "appliance_adoption_rate": 0})
    for row in d["appliances"].values():
        row["units_per_household"] = 0
    d["appliances"]["lighting"] = {"units_per_household": 2, "power_w": 10, "hours_per_day": 5}
    d.update(changes)
    return validate_detailed(d)


@pytest.mark.parametrize("bad", [
    [], "", True, {"enabled": 1}, {"unknown": 4},
    {"months_since_connection": -1}, {"months_since_connection": 121},
    {"months_since_connection": 1.5}, {"months_since_connection": True},
    {"household_income_monthly": -1}, {"connection_fee": "500"},
    {"new_connections_yearly": float("inf")}, {"appliance_adoption_rate": 1.1},
    {"appliances": []}, {"appliances": {"oven": {}}},
    {"appliances": {"lighting": {"watts": 5}}},
    {"appliances": {"lighting": {"power_w": float("nan")}}},
    {"appliances": {"lighting": {"hours_per_day": 25}}},
    {"equipment": {"mills": {"power_kw": -1}}},
    {"equipment": {"pumps": {"hours_per_day": True}}},
    {"agricultural_seasonality": [1]*11},
    {"agricultural_seasonality": [1]*11+[3]},
])
def test_bad_inputs_rejected(bad):
    with pytest.raises(ValueError):
        validate_detailed(bad)


def test_defaults_are_independent_and_nullable_not_fabricated():
    a, b = validate_detailed(), validate_detailed()
    a["appliances"]["lighting"]["power_w"] = 999
    assert b["appliances"]["lighting"]["power_w"] == 7
    assert b["household_income_monthly"] is b["connection_fee"] is None
    assert validate_detailed({"connection_fee": 0})["connection_fee"] == 0


def test_household_arithmetic_and_cap():
    s, a, d = site(), assumptions(), details(new_connections_yearly=12)
    before = copy.deepcopy((s,a,d))
    p, connected, daily, *_ = month_components(s,a,d,1)
    assert connected == 50
    assert daily == pytest.approx(.1)
    assert p["households"] == pytest.approx(50*.1*365/12)
    assert month_components(s,a,d,13)[1] == 62
    assert month_components(s,a,d,121)[1] == 100
    assert (s,a,d) == before


@pytest.mark.parametrize("feature", ["units_per_household","power_w","hours_per_day"])
def test_each_appliance_factor_drives_energy(feature):
    d = details()
    expected = month_components(site(),assumptions(),d,1)[0]["households"]
    d["appliances"]["lighting"][feature] *= 2
    assert month_components(site(),assumptions(),d,1)[0]["households"] == pytest.approx(2*expected)


@pytest.mark.parametrize("key", ["shops","mills","pumps","cold_rooms","schools","clinics"])
def test_each_nonhousehold_count_power_and_hours_are_used(key):
    s,a,d = site(),assumptions(),details()
    s[key] = 2
    d["equipment"][key] = {"power_kw": 3, "hours_per_day": 4}
    expected = 2*3*4*365/12
    assert month_components(s,a,d,1)[0][key] == pytest.approx(expected)
    s[key] = 4
    assert month_components(s,a,d,1)[0][key] == pytest.approx(2*expected)
    d["equipment"][key]["power_kw"] = 6
    d["equipment"][key]["hours_per_day"] = 8
    assert month_components(s,a,d,1)[0][key] == pytest.approx(8*expected)


def test_growth_and_seasonal_effects_are_separate():
    s = {**site(), **{k: 1 for k in SECTORS if k != "households"}}
    d = details(appliance_adoption_rate=.2)
    first = month_components(s,assumptions(business_growth=.1),d,1)[0]
    year = month_components(s,assumptions(business_growth=.1),d,13)[0]
    assert year["households"] == pytest.approx(first["households"]*1.2)
    for key in ("shops","mills","pumps","cold_rooms"):
        assert year[key] == pytest.approx(first[key]*1.1)
    for key in ("schools","clinics"):
        assert year[key] == first[key]
    d["agricultural_seasonality"][0] = 0
    seasonal = month_components(s,assumptions(),d,1)[0]
    assert seasonal["mills"] == seasonal["pumps"] == 0
    assert seasonal["households"] == first["households"]
    assert seasonal["shops"] == first["shops"]


def test_time_shift_calendar_and_scenarios():
    d = details(months_since_connection=18,new_connections_yearly=12)
    rows = detailed_months(site(),assumptions(),validate_planning({"low_factor":.6,"high_factor":1.5}),
                           validate_connection({"connection_month":"2026-11"}),d)
    assert len(rows) == 36
    assert (rows[0]["service_month"],rows[-1]["service_month"]) == (19,54)
    assert rows[0]["calendar_month"] == "2028-05"
    for m in rows:
        assert m["lower"] == pytest.approx(m["central"]*.6)
        assert m["upper"] == pytest.approx(m["central"]*1.5)
        assert m["central"] == pytest.approx(sum(m[k+"_kwh"] for k in SECTORS))


def test_new_equipment_added_once_at_service_year_not_forecast_year():
    a = assumptions(additional_mills=2,adoption_year=2)
    d = details()
    assert month_components(site(),a,d,12)[0]["mills"] == 0
    value = 2*d["equipment"]["mills"]["power_kw"]*d["equipment"]["mills"]["hours_per_day"]*365/12
    assert month_components(site(),a,d,13)[0]["mills"] == pytest.approx(value)
    assert month_components(site(),a,d,25)[0]["mills"] == pytest.approx(value)


def payload(**extra):
    return {"site":site(),"assumptions":assumptions(),"detailed":details(),**extra}


def analyze(client, p):
    response = client.post("/api/analyze",json=p)
    assert response.status_code == 200, response.json
    return response.json


def test_affordability_and_tariff_not_untrained_energy_elasticity(client):
    p=payload(detailed=details(household_income_monthly=10000,connection_fee=20000))
    r=analyze(client,p)
    aff=r["affordability"]
    assert aff["monthly_bill_per_connected_household"] == pytest.approx(.1*365/12*p["assumptions"]["tariff"])
    assert aff["connection_fee_income_months"] == 2
    assert aff["bill_share_of_income"] == pytest.approx(aff["monthly_bill_per_connected_household"]/10000)
    p["detailed"].update(household_income_monthly=20000,connection_fee=0)
    q=analyze(client,p)
    assert q["forecast"] == r["forecast"]
    assert q["finance"] == r["finance"]  # fee is not recurring revenue
    p["assumptions"]["tariff"] *= 2
    t=analyze(client,p)
    assert t["forecast"] == r["forecast"]
    assert t["affordability"]["monthly_bill_per_connected_household"] == pytest.approx(2*aff["monthly_bill_per_connected_household"])
    assert t["finance"]["base"]["revenue"] == pytest.approx(2*r["finance"]["base"]["revenue"])


def test_zero_load_and_zero_income_are_safe(client):
    d=details(household_income_monthly=0,connection_fee=0)
    for row in d["appliances"].values():
        row["units_per_household"]=0
    r=analyze(client,payload(detailed=d))
    assert r["forecast"]["central"] == r["profile"]["peak_kw"] == 0
    assert r["affordability"]["bill_share_of_income"] is None
    assert r["affordability"]["connection_fee_income_months"] is None


def test_rollups_finance_profile_feature_inventory_and_legacy_no_double_count(client):
    p=payload(detailed=details(new_connections_yearly=12,appliance_adoption_rate=.1))
    r=analyze(client,p)
    assert len(r["feature_inventory"]) == 20
    assert r["forecast"]["interval_level"] is None
    assert r["forecast"]["method"] == "detailed_bottom_up"
    assert r["sensitivities"] == []
    months=r["feasibility"]["monthly_growth"]
    assert sum(m["central"] for m in months[:12]) == pytest.approx(r["forecast"]["central"]*12)
    assert sum(r["profile"]["kw"]) == pytest.approx(r["forecast"]["central"]/(365/12))
    for g in r["growth"]:
        assert g["central"]*12 == pytest.approx(sum(m["central"] for m in months if m["year"] == g["year"]))
    expected=next(s for s in r["feasibility"]["scenarios"] if s["factor"] == 1)
    assert expected["years"][0]["revenue"] == pytest.approx(r["finance"]["base"]["revenue"]*12)
    p["site"]["appliance_index"]=2
    p["assumptions"]["household_growth"]=.5
    p["connection"]={"enabled":True,"start_household_fraction":0,"start_appliance_fraction":0}
    assert analyze(client,p)["forecast"] == r["forecast"]


@pytest.mark.parametrize("role", ["developer","investor"])
def test_reports_and_exports_preserve_all_detailed_inputs(client,role):
    p=payload(role=role,detailed=details(months_since_connection=18,household_income_monthly=10000,connection_fee=20000))
    r=analyze(client,p)
    for url in ("/api/report","/api/feasibility-report"):
        response=client.post(url,json=p)
        assert response.status_code == 200
        html=response.text
        for text in ("20-feature","Household affordability","19–54","Agricultural","Appliance ownership","not a retrained ML"):
            assert text in html
        assert "Propagated lower" not in html
    response=client.post("/api/export",json=p)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        saved=json.loads(z.read("analysis.json"))
        assert saved["detailed"] == r["detailed"]
        rows=list(csv.DictReader(io.StringIO(z.read("monthly_growth.csv").decode())))
        assert len(rows) == 36 and rows[0]["service_month"] == "19"


@pytest.mark.parametrize("code", ["RW","UG","KE","TZ","BI","SS","SO","CD"])
def test_name_only_location_is_explicit_no_invented_coordinates(client,code):
    loc={"country_code":code,"source":"user_entered_administration","administrative_path":["District example","Sector example","Cell example"]}
    response=client.post("/api/location-project",json={"location":loc})
    assert response.status_code == 200, response.json
    p=response.json
    assert p["context"]["country_code"] == code
    assert p["context"]["location"]["latitude"] is None
    assert p["context"]["location"]["longitude"] is None
    assert p["detailed"]["enabled"]
    r=analyze(client,p)
    assert r["location_profile"] is None
    assert r["context"]["input_origin"] == "user_entered"
    assert r["context"]["grid"]["status"] == "unknown"
    assert r["assumptions"]["capacity_kwh"] == 0


@pytest.mark.parametrize("path", [[],["a","b"],["a","b",""],["a","b",3],["a","b","c"*101]])
def test_manual_hierarchy_requires_three_valid_names(path):
    with pytest.raises(ValueError):
        validate_context({"country_code":"RW","input_origin":"user_entered","location":{
            "country_code":"RW","source":"user_entered_administration","administrative_path":path}})


def test_rwanda_cascades_resolve_actual_adm4_cells_not_settlements():
    area=browse("RW")["items"][0]
    sector=browse("RW",area["id"],"local")["items"][0]
    cells=browse("RW",sector["id"],"cells")["items"]
    assert cells
    for cell in cells:
        assert cell["feature"] == "ADM4"
        assert within(record("RW",cell["id"]),record("RW",sector["id"]))
        assert public_location("RW",cell["id"])["country_code"] == "RW"
    with pytest.raises(ValueError):
        browse("RW",area["id"],"cells")
    assert browse("SS",browse("SS")["items"][0]["id"],"local")["items"]
