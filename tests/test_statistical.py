"""Invented histories test methods and leakage guards, NOT real forecasting accuracy."""
import copy
import io
import json
import zipfile

import numpy as np
import pytest

from app import create_app
from src.domain import CONFIG, DEMOS, ROOT
from src.detailed_inputs import DEFAULTS, detailed_months
from src.statistical import (SETTINGS, WIDTHS, settings, planning_uncertainty, energy_path,
    simulated_paths, input_band, blank_plan, calibration_rank, fit_growth, correct_growth,
    site_score, expanded_band, confidence_study, study_csv)
from test_monthly_validation import fixture_site, observation, payload as monthly_payload


def analysis():
    d=copy.deepcopy(DEFAULTS);d["enabled"]=True
    return {"site":copy.deepcopy(DEMOS[0]),"assumptions":copy.deepcopy(CONFIG["default_scenario"]),
            "detailed":d,"connection":{"connection_month":"2022-01"},"context":{"country_code":"KE"}}


def zero_settings():
    return {**copy.deepcopy(SETTINGS),"draws":64,"widths":{k:0 for k in WIDTHS}}


def study_input(coverage=.8,horizon=24):
    n_cal={.8:4,.9:9,.95:19}[coverage]
    fit=[f"FIT{i:03}" for i in range(3)]
    calibration=[f"CAL{i:03}" for i in range(n_cal)]
    test=["TEST001","TEST002"]
    sites=[fixture_site(i) for i in fit+calibration+test]
    rows=[]
    for index,site in enumerate(sites):
        for m in range(1,horizon+1):
            # Invented nonconstant uptake history, intentionally NOT from our predictor.
            energy=(300+60*min(m,6)+20*min(max(m-6,0),6)+5*max(m-12,0))*(1+.01*index)
            rows.append(observation(site["site_id"],f"{2022+(m-1)//12}-{(m-1)%12+1:02}",actual_kwh=energy))
    result=monthly_payload(sites,rows)
    plan=blank_plan()
    plan.update(fit_site_ids=fit,calibration_site_ids=calibration,test_site_ids=test,
                horizon_months=horizon,uncertainty={**zero_settings(),"coverage":coverage},
                protocol_reference="Invented software protocol; NOT field evidence",
                split_frozen_before_outcomes_reviewed=True,comparable_site_population=True)
    return {**result,"plan":plan}


@pytest.fixture(scope="module")
def studied():
    return confidence_study(study_input())


def test_zero_uncertainty_matches_exact_detailed_model_and_does_not_claim_confidence():
    a=analysis();a["detailed"]["months_since_connection"]=18
    r=planning_uncertainty(a,zero_settings())
    old=detailed_months(a["site"],a["assumptions"],{"low_factor":.8,"high_factor":1.3},a["connection"],a["detailed"])
    for p,expected in zip(r["months"],old):
        assert p["expected_kwh"]==pytest.approx(expected["central"])
        assert p["lower_kwh"]==pytest.approx(p["upper_kwh"])
    assert r["months"][0]["service_month"]==19 and r["months"][-1]["service_month"]==54
    assert r["calibrated"] is False and r["coverage_target"] is None
    assert r["forecast_error_included"] is False


def test_simulations_are_reproducible_nonnegative_and_do_not_mutate_inputs():
    a=analysis();before=copy.deepcopy(a)
    options={**copy.deepcopy(SETTINGS),"draws":64}
    r=planning_uncertainty(a,options);s=planning_uncertainty(a,options)
    assert r["months"]==s["months"] and r["years"]==s["years"] and a==before
    assert any(m["upper_kwh"]>m["lower_kwh"] for m in r["months"])
    assert all(0<=m["lower_kwh"]<=m["expected_kwh"]<=m["upper_kwh"] for m in r["months"])
    options["seed"]+=1
    assert planning_uncertainty(a,options)["months"]!=r["months"]


def test_annual_band_uses_joint_path_sums():
    a=analysis();opts={**copy.deepcopy(SETTINGS),"draws":64}
    samples=simulated_paths(a["site"],a["assumptions"],a["detailed"],range(1,37),opts)
    r=planning_uncertainty(a,opts)
    lo,hi=input_band(samples[:,:12].sum(axis=1),r["years"][0]["expected_kwh"],opts["coverage"])
    assert r["years"][0]["lower_kwh"]==pytest.approx(lo)
    assert r["years"][0]["upper_kwh"]==pytest.approx(hi)


def test_larger_width_changes_bounds_not_nominal_estimate():
    a=analysis();narrow=planning_uncertainty(a,zero_settings())
    options=zero_settings();options["widths"]["appliance_hours_fraction"]=.5
    wide=planning_uncertainty(a,options)
    assert [m["expected_kwh"] for m in narrow["months"]]==[m["expected_kwh"] for m in wide["months"]]
    assert wide["months"][0]["upper_kwh"]>narrow["months"][0]["upper_kwh"]
    assert wide["months"][0]["lower_kwh"]<narrow["months"][0]["lower_kwh"]


def test_known_zero_site_stays_zero():
    a=analysis()
    for k in ("households","shops","schools","clinics","mills","pumps","cold_rooms"):a["site"][k]=0
    for k in ("additional_mills","additional_pumps","additional_cold_rooms"):a["assumptions"][k]=0
    r=planning_uncertainty(a,{**copy.deepcopy(SETTINGS),"draws":64})
    assert all(m["expected_kwh"]==m["lower_kwh"]==m["upper_kwh"]==0 for m in r["months"])


@pytest.mark.parametrize("change",[
    {"coverage":True},{"coverage":.99},{"draws":63},{"draws":1.5},{"draws":True},
    {"draws":1025},{"seed":-1},{"seed":float("nan")},{"seed":3.5},{"unexpected":1}])
def test_settings_reject_bad_numbers(change):
    with pytest.raises(ValueError):settings({**copy.deepcopy(SETTINGS),**change})


@pytest.mark.parametrize("key",list(WIDTHS))
def test_uncertainty_widths_are_bounded_and_required(key):
    opts=zero_settings();opts["widths"][key]=1
    with pytest.raises(ValueError):settings(opts)
    del opts["widths"][key]
    with pytest.raises(ValueError):settings(opts)


@pytest.mark.parametrize("coverage,n,rank",[(.8,3,4),(.8,4,4),(.9,8,9),(.9,9,9),(.95,18,19),(.95,19,19),(.9,19,18)])
def test_exact_finite_sample_rank(coverage,n,rank):
    assert calibration_rank(n,coverage)==rank


def test_score_uses_worst_month_one_score_per_site_and_expands_only():
    p={"center":np.array([100.,100.,0.]),"lower":np.array([90.,90.,0.]),"upper":np.array([110.,110.,0.])}
    q=site_score([100,130,0],p)
    assert q==pytest.approx(.2)
    lo,hi=expanded_band(p,q)
    assert lo.tolist()==pytest.approx([70,70,0])
    assert hi.tolist()==pytest.approx([130,130,.2])
    assert site_score([100,100,2],p)==2
    zero_lo,zero_hi=expanded_band(p,0)
    assert np.array_equal(zero_lo,p["lower"]) and np.array_equal(zero_hi,p["upper"])


def test_growth_fits_can_decrease_and_cannot_extrapolate():
    rows=[{"service_month":m,"predicted_kwh":1000,"actual_kwh":1000-25*m,"days":30} for m in range(1,25)]
    model=fit_growth([rows,rows,rows],24)
    corrected=correct_growth(np.ones(24)*1000,np.arange(1,25),model)
    assert corrected[-1]<corrected[0]
    assert model["drivers_identified"] is False
    with pytest.raises(ValueError,match="extrapolate"):correct_growth([1000],[25],model)
    assert np.isfinite(correct_growth([1e9],[24],model)).all()


def test_study_reports_heldout_coverage_growth_and_distinct_metrics(studied):
    r=studied
    assert r["test"]["n_sites"]==2 and r["test"]["growth_adjusted"]["n_months"]==48
    assert r["calibration"]["n_sites"]==4 and r["calibration"]["rank"]==4
    assert r["calibration"]["correction"]==max(r["calibration"]["site_scores"].values())
    assert set(r["by_site"])=={"TEST001","TEST002"}
    assert len(r["growth_comparisons"])==2 and len(r["monthly_comparisons"])==48
    assert all(m["site_id"].startswith("TEST") for m in r["monthly_comparisons"])
    assert r["by_stage"]["Months 1–6"]["growth_adjusted"]["n_months"]==12
    assert r["by_stage"]["Months 13–24"]["growth_adjusted"]["n_months"]==24
    assert r["by_stage"]["Months 25–36"]["growth_adjusted"]["n_months"]==0
    assert r["field_validation_complete"] is False and r["independently_verified"] is False
    assert r["calibrated_on_supplied_records"] is True and r["forecast_error_included"] is True
    lo,hi=r["test"]["site_coverage_ci95_pct"]
    assert 0<=lo<=r["test"]["site_path_coverage_pct"]<=hi<=100 and hi-lo>50
    assert r["country_split_counts"]["KE"]["test_site_ids"]==2
    assert "lower_kwh" in study_csv(r).splitlines()[0]


def test_test_outcomes_cannot_change_fit_or_calibration(studied):
    p=study_input()
    lines=p["csv"].splitlines()
    for i,line in enumerate(lines):
        if line.startswith("TEST"):
            fields=line.split(",");fields[2]=str(float(fields[2])*5);lines[i]=",".join(fields)
    p["csv"]="\n".join(lines)+"\n"
    r=confidence_study(p)
    assert r["growth_model"]==studied["growth_model"]
    assert r["calibration"]==studied["calibration"]
    assert [m["predicted_kwh"] for m in r["monthly_comparisons"]]==[m["predicted_kwh"] for m in studied["monthly_comparisons"]]
    assert r["test"]["growth_adjusted"]["mae_kwh"]>studied["test"]["growth_adjusted"]["mae_kwh"]
    assert r["test"]["covered_site_paths"]==0


def test_calibration_outcomes_affect_bounds_but_not_fitted_growth(studied):
    p=study_input();lines=p["csv"].splitlines()
    for i,line in enumerate(lines):
        if line.startswith("CAL"):
            fields=line.split(",");fields[2]=str(float(fields[2])*4);lines[i]=",".join(fields)
    p["csv"]="\n".join(lines)+"\n"
    r=confidence_study(p)
    assert r["growth_model"]==studied["growth_model"]
    assert r["calibration"]["correction"]>studied["calibration"]["correction"]
    assert r["test"]["mean_width_kwh"]>studied["test"]["mean_width_kwh"]


@pytest.mark.parametrize("coverage",[.9,.95])
def test_valid_higher_targets_and_36_month_horizon(coverage):
    r=confidence_study(study_input(coverage,horizon=36))
    assert r["growth_model"]["horizon_months"]==36 and r["growth_model"]["knots"][-1]==36
    assert len(r["growth_comparisons"])==4 and len(r["monthly_comparisons"])==72
    assert r["calibration"]["target_coverage"]==coverage


@pytest.mark.parametrize("change",[
    {"fit_site_ids":["FIT000","FIT001"]},
    {"test_site_ids":["TEST001"]},
    {"test_site_ids":["TEST001","fit000"]},
    {"test_site_ids":["TEST001","test001"]},
    {"test_site_ids":["TEST001","UNKNOWN"]},
    {"horizon_months":12},{"horizon_months":True},{"protocol_reference":""},
    {"split_frozen_before_outcomes_reviewed":False},{"comparable_site_population":False},
    {"schema":"bad"}
])
def test_study_rejects_invalid_predeclared_plan(change):
    p=study_input();p["plan"].update(change)
    with pytest.raises(ValueError):confidence_study(p)


def test_small_calibration_is_rejected_not_silently_downgraded():
    p=study_input();p["plan"]["uncertainty"]["coverage"]=.9
    with pytest.raises(ValueError,match="at least 9"):confidence_study(p)


@pytest.mark.parametrize("column,value",[(None,None),(3,"0.99"),(4,"0.5"),(5,"estimated")])
def test_complete_first_two_years_required_and_quality_not_faked(column,value):
    p=study_input();lines=p["csv"].splitlines()
    if column is None:del lines[1]
    else:
        fields=lines[1].split(",");fields[column]=value;lines[1]=",".join(fields)
    p["csv"]="\n".join(lines)+"\n"
    with pytest.raises(ValueError,match="all first 24"):confidence_study(p)


def test_country_transfer_is_flagged_and_never_auto_deployed():
    p=study_input()
    for site in p["manifest"]["sites"]:
        if site["site_id"].startswith("TEST"):site["country_code"]="TZ"
    r=confidence_study(p)
    assert r["transfer_warnings"] and "TZ" in r["transfer_warnings"][0]
    assert set(r["by_country"])=={"TZ"}
    assert "not automatically applied" in r["scope"]


def test_study_is_reproducible_and_preserves_raw_inputs(studied):
    p=study_input();before=copy.deepcopy(p);r=confidence_study(p)
    assert p==before
    for key in ("calibration","growth_model","test","monthly_comparisons","plan_sha256"):
        assert r[key]==studied[key]


def test_routes_templates_and_no_global_model_changes():
    client=create_app().test_client()
    model_before=(ROOT/"models/forecast.joblib").read_bytes()
    evaluation_before=(ROOT/"reports/evaluation.json").read_bytes()
    r=client.get("/api/confidence-study-template")
    with zipfile.ZipFile(io.BytesIO(r.data)) as z:
        assert json.loads(z.read("study_plan.json"))==blank_plan()
        assert not json.loads(z.read("site_inputs.json"))["source_name"]
        assert "README.md" in z.namelist()
    r=client.post("/api/forecast-uncertainty",json={"project":analysis(),"settings":zero_settings()})
    assert r.status_code==200 and r.json["calibrated"] is False
    p=analysis();p["detailed"]["enabled"]=False
    assert client.post("/api/forecast-uncertainty",json={"project":p,"settings":zero_settings()}).status_code==400
    r=client.post("/api/confidence-study",json=study_input())
    assert r.status_code==200 and "covered" in r.json["comparisons_csv"]
    assert client.post("/api/confidence-study",json={}).status_code==400
    assert client.post("/api/confidence-study",data="x"*270000,content_type="application/json").status_code==413
    assert (ROOT/"models/forecast.joblib").read_bytes()==model_before
    assert (ROOT/"reports/evaluation.json").read_bytes()==evaluation_before
    assert "statistical_defaults" in client.get("/api/planning-settings").json
