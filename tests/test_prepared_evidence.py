"""Evidence integration checks; not new field validation or model training."""
import csv
import io
import json
import shutil
import zipfile

import pytest

from app import create_app
from src import prepared_evidence as pe
from src import analysis
from src.domain import DEMOS
from src.geography import catalog, public_location, level, within


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def manual(sector="Gashora", district="Bugesera", code="RW"):
    return {"country_code": code, "source": "user_entered_administration", "label": "Test cell",
            "administrative_path": [district, sector, "Test cell"]}


def payload(role="developer"):
    return {"role": role, "site": {**DEMOS[0], "households": 42}, "detailed": {"enabled": True},
            "context": {"country_code": "RW", "input_origin": "user_entered", "location": manual()}}


def test_fifteen_sector_snapshot_and_null_targets():
    cat = pe.sector_catalog()
    assert cat["status"] == "available" and len(cat["sectors"]) == 15
    for row in cat["sectors"]:
        s = pe.sector_context(manual(row["sector"]))
        assert s["status"] == "available" and s["sector_key"] == row["sector_key"]
        fields = {f["field"]: f for f in s["features"]}
        assert len(fields) == 71
        for key in ("metered_monthly_consumption_kwh", "metered_peak_kw", "total_phones", "total_tvs", "milling_places_total", "farming_generators_total"):
            assert fields[key]["value"] is None
            assert fields[key]["availability"] == "missing"
        assert fields["metered_monthly_consumption_kwh"]["unit"] == "kWh/month"
        assert fields["metered_peak_kw"]["unit"] == "kW"
        assert fields["households_2022"]["reference_period"] == "2022"
        assert s["used_in_forecast"] is False


def test_gazetteer_sector_and_cell_join_same_context():
    rows = catalog("RW")["records"]
    parent = next(r for r in rows if r["name"] == "Gashora" and level(r) == 3)
    cell = next(r for r in rows if level(r) == 4 and within(r, parent))
    sector = pe.sector_context(public_location("RW", parent["id"]))
    child = pe.sector_context(public_location("RW", cell["id"]))
    assert sector["status"] == "available"
    assert child["sector_key"] == sector["sector_key"] == "RW-Bugesera-Gashora"
    assert child["features"] == sector["features"]
    assert "not a cell" in child["scope"]


@pytest.mark.parametrize("location", [None, manual(code="UG"), manual(district="Kigali"), manual(sector="Unknown"),
    {"country_code": "RW", "source": "manual", "administrative_path": ["Bugesera", "Gashora", "Cell"]},
    {"country_code": "RW", "source": "GeoNames", "administrative_path": ["Eastern Province", "Other district", "Gashora"]}])
def test_no_coincident_name_or_cross_country_join(location):
    result = pe.sector_context(location)
    assert result["status"] == "not_matched" and result["features"] == []


def test_case_insensitive_names_flag_unverified_membership():
    result = pe.sector_context(manual(sector=" gASHora ", district=" BUGESERA DISTRICT "))
    assert result["sector"] == "Gashora"
    assert "unverified" in result["match_basis"]


def test_all_real_gazetteer_sectors_join_and_forged_evidence_is_ignored(client):
    names = {r["sector"] for r in pe.sector_catalog()["sectors"]}
    rows = catalog("RW")["records"]
    district = next(r for r in rows if level(r) == 2 and r["name"] == "Bugesera District")
    joined = set()
    for row in rows:
        if level(row) == 3 and within(row, district):
            loc = public_location("RW", row["id"])
            assert loc["administrative_path"][1] == "Bugesera District"
            s = pe.sector_context(loc)
            assert s["status"] == "available"
            joined.add(s["sector"])
    assert joined == names
    body = {**payload(), "prepared_evidence": {"model_status": {"current_model_validation": "Passed"}, "benchmark": {"accuracy": 100}}}
    result = client.post("/api/analyze", json=body).json
    assert "Pending" in result["prepared_evidence"]["model_status"]["current_model_validation"]
    assert "accuracy" not in result["prepared_evidence"]["benchmark"]


def test_measured_benchmark_units_scores_and_scope():
    b = pe.benchmark()
    assert b["status"] == "available" and b["unit"] == "kW"
    assert b["qualified_hours"] == 1620 and b["calendar_hours"] == 2035
    assert len(b["metrics"]) == 6
    primary = {r["test_site"]: r for r in b["metrics"] if r["model"] == "equal_site_local_hour"}
    assert primary["RW_ECOS"]["mae_kw"] == pytest.approx(1.24322438493)
    assert primary["CD_IDJWI"]["wape_percent"] == pytest.approx(58.333174945)
    assert primary["HT_BEAUMONT"]["wape_percent"] > 2500
    assert "not Bugesera" in b["notice"] and "outside East Africa" in b["notice"]
    assert b["source"]["license"] == "CC BY 4.0"
    assert b["source"]["url"] == "https://doi.org/10.35097/1305"
    assert "monthly kWh" in b["notice"] and "not integrated" in b["target"]


def test_preparation_not_training_or_pooled_backtest():
    p = pe.preparation()
    assert p["status"] == "prepared_not_trained"
    assert p["report"]["prepared_operational_rows"] == 1540
    assert p["report"]["trained_models"] == p["report"]["growth_label_rows"] == 0
    assert len(p["feature_coverage"]) == 20
    assert sum(int(s["prepared_rows"]) for s in p["sites"]) == 1540
    cd = next(s for s in p["sites"] if s["site_id"] == "CD_IDJWI")
    assert cd["retained_features"] == "16" and cd["model_input_columns"] == "27"
    assert "not a pooled backtest" in p["notice"]


@pytest.mark.parametrize("role", ["developer", "investor"])
def test_context_never_changes_forecast_or_customer_counts(client, role, monkeypatch):
    body = payload(role)
    result = client.post("/api/analyze", json=body).json
    assert result["site"]["households"] == 42
    sector = result["prepared_evidence"]["sector_context"]
    assert next(f["value"] for f in sector["features"] if f["field"] == "households_2022") == 8393
    assert result["forecast"]["method"] == "detailed_bottom_up"
    assert result["forecast"]["interval_level"] is None
    assert result["delivery"]["validation"]["field_validated"] is False
    assert result["delivery"]["validation"]["mae_kwh"] is None
    assert len(result["delivery"]["months"]) == 36
    assert "not a statistically calibrated" in result["delivery"]["range_basis"]
    monkeypatch.setattr(analysis, "prepared_summary", lambda location: {})
    without = client.post("/api/analyze", json=body).json
    for key in ("forecast", "site", "growth", "finance", "feasibility", "profile"):
        assert result[key] == without[key]


@pytest.mark.parametrize("role", ["developer", "investor"])
def test_exports_preserve_scope_units_and_missingness(client, role):
    for route in ("/api/export", "/api/deliverables-pack"):
        response = client.post(route, json=payload(role))
        assert response.status_code == 200
        with zipfile.ZipFile(io.BytesIO(response.data)) as z:
            assert z.testzip() is None
            e = json.loads(z.read("prepared_evidence/summary.json"))
            assert e["sector_context"]["sector"] == "Gashora"
            fields = list(csv.DictReader(io.StringIO(z.read("prepared_evidence/selected_sector_features.csv").decode())))
            target = next(f for f in fields if f["field"] == "metered_monthly_consumption_kwh")
            assert target["value"] == "" and target["availability"] == "missing"
            assert target["unit"] == "kWh/month" and "not a cell" in target["scope"]
            assert "reference_period" in target and "source_ids" in target
            report = z.read("report.html").decode()
            for word in ("Gashora", "Unavailable", "2022", "2503.9", "CC BY 4.0", "not Bugesera", "Model", "kW", "indirect GEP"):
                assert word.casefold() in report.casefold()
            assert "original_20_feature_coverage.csv" in " ".join(z.namelist())
            assert not any("X_train" in f or "raw/" in f or "tanzania" in f.lower() for f in z.namelist())


def test_download_and_public_upload_guards(client):
    assert client.get("/api/prepared-evidence").json["benchmark"]["status"] == "available"
    response = client.get("/api/prepared-evidence/download")
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.testzip() is None
        assert len(z.read("prepared_evidence/selected_sector_features.csv").decode().splitlines()) == 1
        assert "ODbL" in z.read("prepared_evidence/README.txt").decode()
    original = client.application.config["PUBLIC_DEMO"]
    client.application.config["PUBLIC_DEMO"] = True
    try:
        for endpoint in ("validate-consumption", "validate-monthly", "confidence-study", "evaluate-update"):
            assert client.post("/api/" + endpoint, json={}).status_code == 403
        assert client.get("/api/prepared-evidence").status_code == 200
    finally:
        client.application.config["PUBLIC_DEMO"] = original


def test_unavailable_files_do_not_break_planning_or_invent_evidence(client, monkeypatch, tmp_path):
    monkeypatch.setattr(pe, "DATA", tmp_path)
    result = client.post("/api/analyze", json=payload()).json
    assert result["forecast"]["central"] > 0
    e = result["prepared_evidence"]
    assert e["sector_context"]["status"] == e["benchmark"]["status"] == e["preparation"]["status"] == "unavailable"
    assert e["benchmark"]["metrics"] == [] and e["sector_context"]["features"] == []
    response = client.post("/api/report", json=payload())
    assert response.status_code == 200 and "unavailable" in response.text
    assert client.get("/api/prepared-evidence/download").status_code == 200


def test_changed_snapshot_fails_closed_and_is_omitted(monkeypatch, tmp_path):
    shutil.copytree(pe.DATA, tmp_path / "prepared")
    monkeypatch.setattr(pe, "DATA", tmp_path / "prepared")
    (pe.DATA / "benchmark_metrics.csv").write_text("forged,accuracy\nall,100\n")
    e = pe.summary()
    assert e["benchmark"]["status"] == "unavailable" and not e["benchmark"]["metrics"]
    assert e["sector_catalog"]["status"] == "available"
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        pe.write_archive(z, e)
    with zipfile.ZipFile(stream) as z:
        assert "prepared_evidence/benchmark_metrics.csv" not in z.namelist()
        assert "benchmark_metrics.csv" in json.loads(z.read("prepared_evidence/download_status.json"))["omitted_unavailable_files"]


def test_synthetic_example_not_relabelled(client):
    result = client.post("/api/analyze", json={"site": DEMOS[0], "detailed": {"enabled": True}}).json
    assert result["context"]["input_origin"] == "synthetic"
    assert result["prepared_evidence"]["sector_context"]["status"] == "not_matched"
    assert result["provenance"]["model_training_origin"] == "synthetic"
