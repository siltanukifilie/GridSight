"""Packaging checks, not empirical metered-site validation."""
import csv
import io
import json
import zipfile
import pytest
from app import create_app
from src.domain import DEMOS


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize("role", ["developer", "investor"])
@pytest.mark.parametrize("mode,age", [("detailed", 0), ("detailed", 18), ("connection", 0), ("legacy", 0)])
def test_all_five_deliverables_preserve_mode_horizon_and_ranges(client, role, mode, age):
    body = {"site": DEMOS[1], "role": role}
    if mode == "detailed":
        body["detailed"] = {"enabled": True, "months_since_connection": age}
    if mode == "connection":
        body["connection"] = {"enabled": True}
    r = client.post("/api/analyze", json=body).json
    d = r["delivery"]
    assert [item["id"] for item in d["items"]] == ["demand", "growth", "validation", "explanation", "sharing"]
    assert d["items"] == r["deliverables"]
    assert d["items"][2]["state"] == "blocked"
    assert d["validation"]["field_validated"] is False
    assert d["validation"]["mae_kwh"] is None
    assert d["validation"]["coverage_pct"] is None
    assert len(d["months"]) == 36
    expected_start = None if mode == "legacy" else age + 1
    assert d["horizon"]["first_service_month"] == expected_start
    assert d["months"][0]["service_month"] == expected_start
    assert d["months"][-1]["service_month"] == (age + 36 if mode != "legacy" else None)
    if age:
        assert "not the first years" in d["items"][1]["detail"]
        assert "time since connection to 0" in d["items"][1]["next_action"]
    cases = {c["key"]: c for c in r["feasibility"]["scenarios"]}
    for period, divisor in zip(d["periods"], [365, 365 / 7, 12, 1]):
        for key in ["low", "expected", "high"]:
            assert period[key] * divisor == pytest.approx(cases[key]["years"][0]["demand_kwh"])
    for i, month in enumerate(d["months"]):
        assert month["low_kwh"] <= month["expected_kwh"] <= month["high_kwh"]
        assert month["expected_kwh"] == cases["expected"]["months"][i]["demand_kwh"]
    assert "not a statistically calibrated" in d["range_basis"]
    json.dumps(d, allow_nan=False)


@pytest.mark.parametrize("role", ["developer", "investor"])
def test_bundle_contains_all_artifacts_and_only_blank_meter_template(client, role):
    body = {"site": DEMOS[2], "role": role, "detailed": {"enabled": True}}
    result = client.post("/api/analyze", json=body).json
    response = client.post("/api/deliverables-pack", json=body)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "gridsight-deliverables.zip" in response.headers["Content-Disposition"]
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.testzip() is None
        for name in ["START_HERE.html", "report.html", "analysis.json", "deliverables/status.json",
                     "deliverables/demand_range.csv", "deliverables/growth_curve.csv",
                     "deliverables/lender_explanation.txt", "deliverables/meter_sharing_proposal.txt",
                     "deliverables/operator_handover.json", "deliverables/validation/site_inputs.json",
                     "deliverables/validation/monthly_meter_totals.csv", "deliverables/validation/study_plan.json",
                     "deliverables/validation/MONTHLY_VALIDATION.md", "deliverables/validation/CONFIDENCE_AND_GROWTH.md",
                     "deliverables/validation/public_source_review.json"]:
            assert name in z.namelist()
        exported = json.loads(z.read("analysis.json"))
        assert exported["forecast"] == result["forecast"]
        assert exported["finance"] == result["finance"]
        assert exported["delivery"]["input_sha256"] == result["delivery"]["input_sha256"]
        months = list(csv.DictReader(io.StringIO(z.read("deliverables/growth_curve.csv").decode())))
        assert len(months) == 36
        assert float(months[-1]["expected_kwh"]) == result["delivery"]["months"][-1]["expected_kwh"]
        readings = z.read("deliverables/validation/monthly_meter_totals.csv").decode().splitlines()
        assert readings == ["site_id,month,actual_kwh,coverage_fraction,availability_fraction,quality"]
        worksheet = json.loads(z.read("deliverables/operator_handover.json"))
        assert worksheet["operator_permission_reference"] is None
        assert worksheet["retention_end_date"] is None
        html = z.read("START_HERE.html").decode()
        for text in ["1. Demand estimate", "2. Demand growth", "3. Held-out", "4. Plain-language",
                     "5. Safe meter-data", "not available", "not field-validated", "<svg",
                     "report.html", "not a statistically calibrated"]:
            assert text in html
        assert "No independently reviewed metered study attached" in z.read("report.html").decode()
        assert result["lender_explanation"][0] in z.read("deliverables/lender_explanation.txt").decode()


def test_bundle_escapes_names_and_does_not_trust_forged_evidence(client):
    body = {"site": {**DEMOS[0], "name": '<img src=x onerror="alert(1)">'},
            "detailed": {"enabled": True}, "delivery": {"validation": {"field_validated": True}},
            "deliverables": [{"status": "Real data validated"}]}
    response = client.post("/api/deliverables-pack", json=body)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        html = z.read("START_HERE.html").decode()
        assert "<img src=x" not in html
        assert "&lt;img" in html
        assert json.loads(z.read("deliverables/status.json"))["validation"]["field_validated"] is False


def test_role_neutral_inputs_hash_and_no_synthetic_growth_relabel(client):
    body = {"site": DEMOS[0], "detailed": {"enabled": True}}
    dev = client.post("/api/analyze", json=body).json
    inv = client.post("/api/analyze", json={**body, "role": "investor"}).json
    changed = client.post("/api/analyze", json={**body, "site": {**DEMOS[0], "households": 400}}).json
    assert dev["delivery"]["input_sha256"] == inv["delivery"]["input_sha256"]
    assert dev["delivery"]["input_sha256"] != changed["delivery"]["input_sha256"]
    assert "uncalibrated" in dev["delivery"]["items"][1]["detail"]


@pytest.mark.parametrize("body", [None, {}, {"site": None}, {"site": DEMOS[0], "detailed": {"months_since_connection": -1}}])
def test_pack_validates_inputs(client, body):
    assert client.post("/api/deliverables-pack", json=body).status_code == 400
