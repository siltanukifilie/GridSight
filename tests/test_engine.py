"""Tests focus on independent balances, financial examples, and data leakage."""
import copy
import json
import numpy as np
import pandas as pd
import pytest
from src.domain import CONFIG, ROOT, DEMOS, SECTORS, FEATURES, SITE_LIMITS, baseline_components, baseline, profile, growth, finance, validate_site, validate_numbers, SCENARIO_LIMITS
from src.synthetic import generate
from src.model import load
from src.analysis import analyze


@pytest.fixture(scope="module")
def forecaster():
    return load()


def test_hand_calculated_baseline():
    site = {**DEMOS[0], "households": 100, "uptake": .8, "appliance_index": 1, "shops": 2, "schools": 1}
    assert baseline(site) == 1530  # 100 × .8 × 15 + 2 × 100 + 130


@pytest.mark.parametrize("site", DEMOS)
def test_hourly_energy_conservation(site, forecaster):
    estimate = forecaster.predict(site)
    p = profile(site, estimate["central"])
    assert len(p["kw"]) == 24
    assert np.isfinite(p["kw"]).all()
    assert min(p["kw"]) >= 0
    assert sum(p["kw"]) * (365 / 12) == pytest.approx(estimate["central"])
    assert p["peak_kw"] >= p["daily_kwh"] / 24
    assert 0 <= p["load_factor"] <= 1


def test_financial_hand_worked_example():
    a = {**CONFIG["default_scenario"], "tariff": 100, "collection_rate": .9, "variable_cost": 10, "fixed_cost": 1000, "debt_payment": 1000, "capacity_kwh": 1000}
    result = finance(100, a)
    assert result["base"]["revenue"] == 9000
    assert result["base"]["operating_cost"] == 2000
    assert result["base"]["cash_after_debt"] == 6000
    assert result["base"]["dscr"] == 7
    assert result["break_even_kwh"] == 25


def test_revenue_capped_by_served_energy():
    a = {**CONFIG["default_scenario"], "capacity_kwh": 100, "collection_rate": 1, "tariff": 10}
    result = finance(1000, a)["base"]
    assert result["served_kwh"] == 100
    assert result["unserved_kwh"] == 900
    assert result["revenue"] == 1000


def test_faster_demand_exposes_capacity_and_peak_risk():
    a = {**CONFIG["default_scenario"], "tariff": 100, "collection_rate": .9,
         "variable_cost": 10, "fixed_cost": 1000, "debt_payment": 1000,
         "capacity_kwh": 120, "firm_power_kw": 12}
    result = finance(100, a, peak_kw=10)
    faster = next(s for s in result["scenarios"] if s["factor"] == 1.3)
    assert faster["demand_kwh"] == 130
    assert faster["served_kwh"] == 120
    assert faster["unserved_kwh"] == 10
    assert faster["peak_shortfall_kw"] == 1
    assert faster["revenue"] == 10800
    assert faster["cash_after_debt"] == 7600


def test_lower_demand_exposes_repayment_shortfall():
    a = {**CONFIG["default_scenario"], "tariff": 100, "collection_rate": 1,
         "variable_cost": 0, "fixed_cost": 3000, "debt_payment": 6000,
         "capacity_kwh": 1000}
    result = finance(100, a)
    lower = next(s for s in result["scenarios"] if s["factor"] == .8)
    assert result["base"]["cash_after_debt"] == 1000
    assert lower["cash_after_debt"] == -1000
    assert lower["dscr"] == pytest.approx(5000 / 6000)


@pytest.mark.parametrize("override", [{"tariff": 0}, {"collection_rate": 0}, {"variable_cost": 1000}])
def test_no_finite_break_even(override):
    result = finance(1000, {**CONFIG["default_scenario"], **override})
    assert result["break_even_kwh"] is None
    assert not result["break_even_within_capacity"]


def test_zero_financing_has_no_dscr():
    result = finance(1000, {**CONFIG["default_scenario"], "debt_payment": 0})
    assert result["base"]["dscr"] is None


def test_growth_year_one_anchor_and_single_addition():
    forecast = {"central": 1000, "lower": 800, "upper": 1200}
    a = {**CONFIG["default_scenario"], "household_growth": 0, "business_growth": 0, "additional_mills": 1, "additional_pumps": 2, "adoption_year": 2}
    output = growth(DEMOS[0], forecast, a)
    assert [x["central"] for x in output] == [1000, 2700, 2700]
    assert output[0]["lower"] == 800
    a["adoption_year"] = 3
    assert [x["central"] for x in growth(DEMOS[0], forecast, a)] == [1000, 1000, 2700]


def test_zero_demand_flows_through_whole_pipeline(forecaster):
    site = {**DEMOS[0], **{key: 0 for key in SECTORS}}
    r = analyze({"site": site}, forecaster)
    assert r["forecast"]["central"] == r["forecast"]["lower"] == r["forecast"]["upper"] == 0
    assert sum(r["profile"]["kw"]) == 0
    assert r["finance"]["base"]["revenue"] == 0
    assert all(c["share"] == 0 for c in r["components"])
    json.dumps(r, allow_nan=False)


@pytest.mark.parametrize("field,value", [("households", -1), ("shops", 1.2), ("uptake", 1.1), ("appliance_index", float("nan")), ("mills", True), ("pumps", float("inf"))])
def test_bad_site_inputs_rejected(field, value):
    with pytest.raises(ValueError):
        validate_site({**DEMOS[0], field: value})


def test_missing_value_is_not_zero():
    site = dict(DEMOS[0])
    del site["households"]
    with pytest.raises(ValueError):
        validate_site(site)


def test_generator_repeatability_and_component_totals():
    sites, monthly = generate(seed=113, n_sites=15)
    again_sites, again_monthly = generate(seed=113, n_sites=15)
    pd.testing.assert_frame_equal(sites, again_sites)
    pd.testing.assert_frame_equal(monthly, again_monthly)
    np.testing.assert_allclose(monthly[[f"{s}_kwh" for s in SECTORS]].sum(axis=1), monthly["demand_kwh"])
    first_year = monthly[monthly["month"] <= 12].groupby("site_id")["demand_kwh"].mean()
    np.testing.assert_allclose(first_year.reindex(sites["id"]), sites["target_kwh_month"])


def test_data_partition_has_no_site_leakage():
    sites = pd.read_csv(ROOT / "data/synthetic_sites.csv")
    monthly = pd.read_csv(ROOT / "data/synthetic_monthly.csv")
    assert len(sites) == 500
    assert len(monthly) == 18000
    assert sites["id"].is_unique
    assert monthly.groupby("site_id")["split"].nunique().max() == 1
    partitions = {key: set(sites[sites["split"] == key]["id"]) for key in ["train", "calibration", "test"]}
    assert len(partitions["train"]) == 300
    assert len(partitions["calibration"]) == len(partitions["test"]) == 100
    assert not (partitions["train"] & partitions["test"] or partitions["train"] & partitions["calibration"] or partitions["test"] & partitions["calibration"])
    merged = monthly.merge(sites[["id", "split"]], left_on="site_id", right_on="id", suffixes=("_month", "_site"))
    assert (merged["split_month"] == merged["split_site"]).all()


def test_prepared_synthetic_data_quality():
    sites = pd.read_csv(ROOT / "data/synthetic_sites.csv")
    monthly = pd.read_csv(ROOT / "data/synthetic_monthly.csv")
    assert np.isfinite(sites[FEATURES + ["target_kwh_month"]]).all().all()
    assert (sites["target_kwh_month"] >= 0).all()
    for key, (low, high) in SITE_LIMITS.items():
        assert sites[key].between(low, high).all(), key
    for key in SECTORS:
        assert (sites[key] % 1 == 0).all(), key
    assert not monthly.duplicated(["site_id", "month"]).any()
    assert monthly.groupby("site_id")["month"].nunique().eq(36).all()
    assert monthly["month"].between(1, 36).all()
    assert np.isfinite(monthly["demand_kwh"]).all()
    assert monthly["demand_kwh"].ge(0).all()


def test_saved_metrics_recompute_from_test_predictions():
    rows = pd.read_csv(ROOT / "reports/test_predictions.csv")
    report = json.loads((ROOT / "reports/evaluation.json").read_text())
    actual, predicted = rows["target_kwh_month"], rows["prediction_kwh"]
    assert report["test"]["mae_kwh"] == pytest.approx(np.abs(actual - predicted).mean())
    coverage = ((actual >= rows["lower_kwh"]) & (actual <= rows["upper_kwh"])).mean() * 100
    assert coverage == pytest.approx(report["test"]["coverage_pct"])
    assert (rows["lower_kwh"] <= predicted).all()
    assert (predicted <= rows["upper_kwh"]).all()


def test_tariff_change_does_not_change_demand(forecaster):
    low = analyze({"site": DEMOS[1], "assumptions": {"tariff": 100}}, forecaster)
    high = analyze({"site": DEMOS[1], "assumptions": {"tariff": 800}}, forecaster)
    assert low["forecast"] == high["forecast"]
    assert low["finance"]["base"]["revenue"] < high["finance"]["base"]["revenue"]


def test_losses_change_supply_not_customer_revenue(forecaster):
    low = analyze({"site": DEMOS[1], "assumptions": {"loss_rate": 0}}, forecaster)
    high = analyze({"site": DEMOS[1], "assumptions": {"loss_rate": .2}}, forecaster)
    assert low["finance"] == high["finance"]
    assert high["supply_energy_kwh"] == pytest.approx(low["supply_energy_kwh"] / .8)


def test_ramp_shapes_are_normalized():
    shapes = json.loads((ROOT / "data/load_shapes.json").read_text())
    assert shapes["engine"].startswith("RAMP")
    for values in shapes["shapes"].values():
        assert len(values) == 24
        assert sum(values) == pytest.approx(1)
        assert min(values) >= 0


def test_extreme_valid_inputs_remain_finite(forecaster):
    site = {**DEMOS[1], "households": 1500, "shops": 150, "mills": 10, "pumps": 15, "cold_rooms": 10, "schools": 10, "clinics": 5, "appliance_index": 2}
    r = analyze({"site": site, "assumptions": {"household_growth": .5, "business_growth": .5, "capacity_kwh": 0, "firm_power_kw": 0}}, forecaster)
    json.dumps(r, allow_nan=False)
    assert r["warnings"]
    assert r["finance"]["base"]["served_kwh"] == 0
