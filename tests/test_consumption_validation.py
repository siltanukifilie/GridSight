import csv
import io
import hashlib
import pytest
from app import create_app
from src.domain import ROOT, DEMOS, FEATURES
from src.model import load
from src.validation import COLUMNS, compare_consumption


@pytest.fixture(scope="module")
def model():
    return load()


def observation(**changes):
    return {"site_id": "TEST-ONLY-NOT-FIELD-EVIDENCE", "country_code": "RW", "period_start": "2025-01-01", "period_end": "2025-12-31", "actual_kwh": 12000, **{k: DEMOS[0][k] for k in FEATURES}, **changes}


def payload(rows=None):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows if rows is not None else [observation()])
    return {"csv": buffer.getvalue(), "source_name": "Automated test fixture — not measured evidence", "attestation": True}


def test_frozen_comparison_metrics_and_provenance(model):
    before = hashlib.sha256((ROOT / "models/forecast.joblib").read_bytes()).hexdigest()
    predicted = model.predict(DEMOS[0])
    out = compare_consumption(payload([observation(actual_kwh=predicted["central"] * 12)]), model)
    assert out["metrics"]["mae_kwh"] == pytest.approx(0, abs=1e-8)
    assert out["metrics"]["coverage_pct"] == 100
    assert out["model_sha256"] == before
    assert hashlib.sha256((ROOT / "models/forecast.joblib").read_bytes()).hexdigest() == before
    assert out["retrained"] is False
    assert "not independently verified" in out["status"]
    assert out["source_attested_by_user"] is True


def test_leap_year_normalization_and_group_metrics(model):
    result = compare_consumption(payload([observation(period_start="2024-01-01", period_end="2024-12-31", actual_kwh=3660), observation(site_id="ANOTHER-TEST", country_code="UG", actual_kwh=3650)]), model)
    assert all(r["actual_normalized_monthly_kwh"] == pytest.approx(3650 / 12) for r in result["sites"])
    assert set(result["by_country"]) == {"RW", "UG"}
    assert result["sites"][0]["days_observed"] == 366


def test_zero_actual_has_no_wape(model):
    result = compare_consumption(payload([observation(actual_kwh=0)]), model)
    assert result["metrics"]["wape_pct"] is None


@pytest.mark.parametrize("changes", [{"actual_kwh": -1}, {"actual_kwh": "nan"}, {"actual_kwh": "inf"}, {"period_start": "2025-01-02"}, {"period_end": "2025-11-30"}, {"period_end": "2026-01-01"}, {"period_start": "2040-01-01", "period_end": "2040-12-31"}, {"households": ""}, {"households": 2.5}, {"uptake": 5}, {"country_code": "XX"}, {"site_id": "SYN-RW-001"}, {"site_id": "RW-DEMO-01"}])
def test_bad_observation_rejected(changes, model):
    with pytest.raises(ValueError):
        compare_consumption(payload([observation(**changes)]), model)


@pytest.mark.parametrize("change", [{"attestation": False}, {"attestation": "true"}, {"source_name": ""}, {"csv": "site_id,bad\nfoo,3"}, {"csv": "x" * 50001}, {"csv": ",".join(COLUMNS) + "\n"}])
def test_bad_upload_metadata_rejected(change, model):
    with pytest.raises(ValueError):
        compare_consumption({**payload(), **change}, model)


def test_duplicate_sites_and_too_many_sites_rejected(model):
    with pytest.raises(ValueError, match="unique"):
        compare_consumption(payload([observation(), observation()]), model)
    with pytest.raises(ValueError, match="100"):
        compare_consumption(payload([observation(site_id=f"T{i}") for i in range(101)]), model)


def test_validation_routes_and_unchanged_global_evidence():
    client = create_app().test_client()
    template = client.get("/api/validation-template")
    assert template.text.strip().split(",") == COLUMNS
    assert "attachment" in template.headers["Content-Disposition"]
    before = client.get("/api/dataset/evaluation").data
    response = client.post("/api/validate-consumption", json=payload())
    assert response.status_code == 200 and response.json["metrics"]["n_sites"] == 1
    assert client.get("/api/dataset/evaluation").data == before
    assert client.post("/api/validate-consumption", json={}).status_code == 400
