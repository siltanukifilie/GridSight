"""Invented software fixtures ONLY. These tests are not real-site evidence."""
import calendar
import copy
import csv
import io
import json
import zipfile
from datetime import date

import pytest
from app import create_app
from src.domain import CONFIG, DEMOS, ROOT
from src.detailed_inputs import DEFAULTS, detailed_months
from src.detailed_validation import (ASSUMPTION_KEYS, ATTESTATIONS, COLUMNS,
    SITE_KEYS, blank_manifest, compare_monthly, comparisons_csv, metrics)


def fixture_site(identifier="CASE001", country="KE"):
    raw = blank_manifest()["sites"][0]
    raw.update(site_id=identifier, country_code=country, connection_month="2022-01",
               inputs_as_of="2021-12-01", input_evidence_reference="Invented test input record, not field evidence",
               site={k: DEMOS[0][k] for k in SITE_KEYS},
               assumptions={k: CONFIG["default_scenario"][k] for k in ASSUMPTION_KEYS},
               detailed=copy.deepcopy(DEFAULTS))
    raw["detailed"]["enabled"] = True
    return raw


def observation(site="CASE001", month="2022-01", **changes):
    return {"site_id": site, "month": month, "actual_kwh": 1000,
            "coverage_fraction": 1, "availability_fraction": 1, "quality": "measured", **changes}


def payload(sites=None, rows=None):
    manifest = blank_manifest()
    manifest.update(source_name="Software fixture — NOT genuine metered evidence",
                    source_reference="tests/test_monthly_validation.py",
                    license_or_permission="Invented test data only",
                    attestations={k: True for k in ATTESTATIONS}, sites=sites or [fixture_site()])
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows if rows is not None else [observation()])
    return {"manifest": manifest, "csv": out.getvalue()}


def test_same_calculation_as_dashboard_calendar_adjustment_and_not_legacy():
    site = fixture_site()
    site["detailed"]["appliances"]["lighting"]["power_w"] = 15
    months = detailed_months({**site["site"], "appliance_index": 1}, site["assumptions"],
                            {"low_factor": .8, "high_factor": 1.3},
                            {"connection_month": "2022-01"}, site["detailed"])
    result = compare_monthly(payload([site]))
    assert result["monthly_comparisons"][0]["predicted_kwh"] == pytest.approx(months[0]["central"] * 31 / (365/12))
    assert result["model"]["method"] == "detailed_bottom_up"
    assert result["retrained"] is False
    assert result["field_validation_complete"] is False
    assert result["independently_verified"] is False
    assert result["coverage"]["multi_site_sample"] is False
    assert len(result["csv_sha256"]) == len(result["manifest_sha256"]) == 64
    assert "src/detailed_inputs.py" in result["model"]["files"]
    assert "legacy" not in result["model"]["method"]


def test_hand_calculated_household_kwh_not_model_derived_target():
    site = fixture_site()
    site["site"].update({k: 0 for k in SITE_KEYS})
    site["site"].update(households=100, uptake=.5)
    d=site["detailed"]
    for v in d["appliances"].values():
        v.update(units_per_household=0, power_w=0, hours_per_day=0)
    d["appliances"]["lighting"].update(units_per_household=2, power_w=10, hours_per_day=5)
    # 50 connected homes × 2 lamps × 10 W × 5 h × 31 days / 1000 = 155 kWh.
    r = compare_monthly(payload([site], [observation(actual_kwh=155)]))
    assert r["monthly_comparisons"][0]["predicted_kwh"] == pytest.approx(155)
    assert r["metrics"]["mae_kwh"] == pytest.approx(0)


def test_metrics_hand_calculated_zero_and_empty_cases():
    rows=[{"site_id":"A","actual_kwh":100,"predicted_kwh":120},
          {"site_id":"B","actual_kwh":200,"predicted_kwh":170}]
    m=metrics(rows)
    assert m["mae_kwh"] == 25
    assert m["rmse_kwh"] == pytest.approx(650**.5)
    assert m["wape_pct"] == pytest.approx(50/300*100)
    assert m["bias_kwh"] == -5
    assert m["bias_pct"] == pytest.approx(-10/300*100)
    assert m["n_sites"] == 2 and m["n_months"] == 2
    assert metrics([])["mae_kwh"] is None
    assert metrics([{"site_id":"A","actual_kwh":0,"predicted_kwh":1}])["wape_pct"] is None


def test_two_country_36_month_growth_and_country_grouping():
    sites=[fixture_site(), fixture_site("CASE002","TZ")]
    rows=[]
    for site in sites:
        for year in (2022,2023,2024):
            for month in range(1,13):
                rows.append(observation(site["site_id"], f"{year}-{month:02}", actual_kwh=100*(year-2021)))
    r=compare_monthly(payload(sites,rows))
    assert r["metrics"]["n_sites"] == 2 and r["metrics"]["n_months"] == 72
    assert set(r["by_country"]) == {"KE","TZ"}
    assert r["coverage"]["sites_with_complete_36_months"] == 2
    assert r["coverage"]["multi_country_sample"] is True
    assert r["by_service_year"]["3"]["n_months"] == 24
    assert [g["actual_growth_pct"] for g in r["growth_comparisons"]] == [100,50,100,50]
    assert all(not s["missing_or_excluded_service_months"] for s in r["by_site"].values())
    assert next(x for x in r["monthly_comparisons"] if x["month"]=="2024-02")["days"]==29


@pytest.mark.parametrize("changes,reason", [
    ({"coverage_fraction":.99},"coverage"),({"availability_fraction":.9},"supply"),
    ({"quality":"estimated"},"Estimated"),({"month":"2025-01"},"36 service")])
def test_exclusion_not_zero_fill(changes,reason):
    r=compare_monthly(payload(rows=[observation(**changes)]))
    assert r["metrics"]["mae_kwh"] is None and not r["monthly_comparisons"]
    assert reason in ";".join(r["excluded_rows"][0]["reasons"])
    assert r["by_site"]["CASE001"]["missing_or_excluded_service_months"] == list(range(1,37))
    assert not r["growth_comparisons"]


def test_missing_month_prevents_growth_and_zero_growth_base_is_unknown():
    rows=[observation(month=f"{y}-{m:02}", actual_kwh=0) for y in (2022,2023) for m in range(1,13)]
    full=compare_monthly(payload(rows=rows))
    assert full["growth_comparisons"][0]["actual_growth_pct"] is None
    assert full["growth_comparisons"][0]["error_percentage_points"] is None
    missing=compare_monthly(payload(rows=rows[1:]))
    assert not missing["growth_comparisons"]
    assert missing["by_site"]["CASE001"]["years"]["1"]["actual_kwh"] is None


@pytest.mark.parametrize("field",SITE_KEYS)
def test_missing_demand_input_rejected(field):
    p=payload();del p["manifest"]["sites"][0]["site"][field]
    with pytest.raises(ValueError,match="template"):compare_monthly(p)


@pytest.mark.parametrize("field",ASSUMPTION_KEYS)
def test_null_assumption_rejected(field):
    p=payload();p["manifest"]["sites"][0]["assumptions"][field]=None
    with pytest.raises(ValueError):compare_monthly(p)


@pytest.mark.parametrize("change",[
    {"country_code":"NG"}, {"country_code":["KE"]}, {"site_id":"SYN-001"},
    {"site_id":"=FORMULA"}, {"inputs_as_of":"2022-01-01"}, {"inputs_as_of":None},
    {"connection_month":"2022-13"}, {"input_evidence_reference":""}])
def test_bad_site_metadata_rejected(change):
    p=payload();p["manifest"]["sites"][0].update(change)
    with pytest.raises(ValueError):compare_monthly(p)


@pytest.mark.parametrize("change",[
    {"actual_kwh":"nan"}, {"actual_kwh":"inf"}, {"actual_kwh":-1},
    {"actual_kwh":""}, {"coverage_fraction":1.1}, {"availability_fraction":-1},
    {"quality":"unknown"}, {"site_id":"UNKNOWN"}, {"month":"2022-1"},
    {"month":"2026-11"}, {"month":"2027-01"}])
def test_bad_meter_rows_rejected(change):
    with pytest.raises(ValueError):
        compare_monthly(payload(rows=[observation(**change)]),today=date(2026,11,1))


def test_no_silent_appliance_defaults_and_preconnection_only():
    for action in (
        lambda d:d["appliances"].pop("fan"),
        lambda d:d["appliances"]["lighting"].pop("power_w"),
        lambda d:d["equipment"]["mills"].update(power_kw=None),
        lambda d:d.update(months_since_connection=1),
        lambda d:d.update(enabled=False),
        lambda d:d.update(agricultural_seasonality=[1]*11),
    ):
        p=payload();action(p["manifest"]["sites"][0]["detailed"])
        with pytest.raises(ValueError):compare_monthly(p)


def test_overlap_duplicate_ids_alias_case_and_duplicate_month_rejected():
    p=payload();p["manifest"]["development_site_ids"]=["case001"]
    with pytest.raises(ValueError,match="overlap"):compare_monthly(p)
    with pytest.raises(ValueError,match="Duplicate"):
        compare_monthly(payload([fixture_site(),fixture_site("case001")]))
    with pytest.raises(ValueError,match="duplicate site-month"):
        compare_monthly(payload(rows=[observation(),observation()]))


@pytest.mark.parametrize("key",ATTESTATIONS)
def test_attestations_required(key):
    p=payload();p["manifest"]["attestations"][key]=False
    with pytest.raises(ValueError,match="Confirm"):compare_monthly(p)


def test_input_and_size_shape_guards():
    for p in (None,{},{"manifest":{},"csv":""},payload(rows=[])):
        with pytest.raises(ValueError):compare_monthly(p)
    p=payload();p["csv"]="a"*90001
    with pytest.raises(ValueError,match="90 KB"):compare_monthly(p)
    p=payload();p["manifest"]["sites"]=[fixture_site(f"CASE{i:03}") for i in range(31)]
    with pytest.raises(ValueError,match="30"):compare_monthly(p)
    p=payload();p["csv"] += "CASE001,2022-02,1,1,1,measured,extra\n"
    with pytest.raises(ValueError,match="column"):compare_monthly(p)
    p=payload();p["manifest"]["extra"]="not supported"
    with pytest.raises(ValueError):compare_monthly(p)


def test_input_not_mutated_no_target_used_for_prediction_and_deterministic_hash():
    p=payload();before=copy.deepcopy(p)
    a=compare_monthly(p);b=compare_monthly(payload(rows=[observation(actual_kwh=9000)]))
    assert p==before
    assert a["monthly_comparisons"][0]["predicted_kwh"]==b["monthly_comparisons"][0]["predicted_kwh"]
    assert a["model"]==b["model"] and a["manifest_sha256"]==b["manifest_sha256"]
    assert a["csv_sha256"]!=b["csv_sha256"]
    assert "predicted_kwh" in comparisons_csv(a).splitlines()[0]


def test_routes_empty_template_sources_and_no_global_evidence_overwrite():
    client=create_app().test_client()
    before=(ROOT/"reports/evaluation.json").read_bytes()
    response=client.get("/api/monthly-validation-template")
    assert response.status_code==200 and "attachment" in response.headers["Content-Disposition"]
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert json.loads(z.read("site_inputs.json"))==blank_manifest()
        assert z.read("monthly_meter_totals.csv").decode().strip()==",".join(COLUMNS)
        assert "README.md" in z.namelist()
    sources=client.get("/api/validation-sources").json
    assert sources["genuine_sites_evaluated"]==0
    assert all(s["imported"] is False for s in sources["sources"])
    result=client.post("/api/validate-monthly",json=payload())
    assert result.status_code==200 and result.json["metrics"]["n_sites"]==1
    assert "predicted_kwh" in result.json["comparisons_csv"]
    assert (ROOT/"reports/evaluation.json").read_bytes()==before
    assert client.post("/api/validate-monthly",json={}).status_code==400
    assert client.post("/api/validate-monthly",data="bad").status_code==400
    assert client.post("/api/validate-monthly",data="x"*270000,content_type="application/json").status_code==413
    assert client.get("/health").json["feature_version"]=="1.10"
