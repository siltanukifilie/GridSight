import io
import json
import zipfile
import pytest
from app import create_app
from src.context import prepare_thin_inputs, validate_context, scenario_defaults
from src.domain import DEMOS, CONFIG, FEATURES
from src.public_data import PublicDataService, PublicDataUnavailable


def world_bank(code="RW"):
    return [{"pages": 1}, [
        {"country": {"id": code}, "indicator": {"id": "SP.POP.TOTL"}, "date": "2024", "value": 12000000},
        {"country": {"id": code}, "indicator": {"id": "SP.POP.TOTL"}, "date": "2025", "value": 13000000},
        {"country": {"id": code}, "indicator": {"id": "EG.ELC.ACCS.ZS"}, "date": "2024", "value": 72},
        {"country": {"id": code}, "indicator": {"id": "EG.ELC.ACCS.ZS"}, "date": "2025", "value": None},
    ]]


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


def test_missing_inputs_require_review_and_preserve_known_zero():
    result = prepare_thin_inputs({"site": {"households": 200, "shops": 0, "clinics": None}})
    assert result["site"]["shops"] == 0
    assert "shops" not in result["assumed_fields"]
    assert result["site"]["clinics"] == 0 and "clinics" in result["assumed_fields"]
    assert len(result["assumed_fields"]) == 7
    assert "does not include" in result["notice"]
    assert result["site"]["uptake"] == .75


@pytest.mark.parametrize("site", [{}, {"households": None}, {"households": True}, {"households": -1}, {"households": 50.5}, {"households": 1501}, {"households": 100, "mills": -1}, {"households": 100, "uptake": 2}])
def test_thin_inputs_reject_bad_known_values(site):
    with pytest.raises(ValueError):
        prepare_thin_inputs({"site": site})


@pytest.mark.parametrize("raw", [[], {"country_code": "XX"}, {"country_code": []}, {"assumed_fields": ["tariff"]}, {"assumed_fields": ["mills", "mills"]}, {"assumed_fields": [["mills"]]}, {"input_origin": "metered"}, {"location": {}}, {"public_data_id": "https://example.com"}])
def test_bad_context_rejected(raw):
    with pytest.raises(ValueError):
        validate_context(raw)


def location(**changes):
    return {"country_code": "RW", "label": "Project", "latitude": -2, "longitude": 30, "source": "manual", **changes}


@pytest.mark.parametrize("changes", [{"latitude": True}, {"latitude": float("nan")}, {"latitude": 91}, {"longitude": 181}, {"latitude": 20}, {"country_code": "UG"}, {"source": "<script>"}, {"label": ""}])
def test_bad_coordinates_rejected(changes):
    with pytest.raises(ValueError):
        validate_context({"location": location(**changes)})


def test_location_does_not_change_demand_and_is_exported(app):
    client = app.test_client()
    base = client.post("/api/analyze", json={"site": DEMOS[1]}).json
    payload = {"site": DEMOS[1], "context": {"location": location(label="<script>RWF farm</script>"), "assumed_fields": ["mills"], "input_origin": "user_entered"}}
    out = client.post("/api/analyze", json=payload).json
    assert out["forecast"] == base["forecast"] and out["finance"] == base["finance"]
    assert out["context"]["location"]["latitude"] == -2
    assert any("guessed inputs" in w for w in out["warnings"])
    assert out["provenance"]["model_training_origin"] == "synthetic"
    assert out["site"]["origin"] == "user_entered"
    report = client.post("/api/report", json=payload).text
    assert "&lt;script&gt;" in report and "<script>RWF" not in report
    assert "Explicitly assumed inputs: mills" in report


def test_uganda_configuration_resets_money_defaults_and_labels_reports(app):
    client = app.test_client()
    payload = {"site": {**DEMOS[0], "district": "Test district"}, "context": {"country_code": "UG"}}
    out = client.post("/api/analyze", json=payload).json
    assert out["context"]["currency"] == out["finance"]["currency"] == "UGX"
    assert out["assumptions"]["tariff"] == out["assumptions"]["fixed_cost"] == 0
    assert any("Transfer demonstration" in w for w in out["warnings"])
    assert scenario_defaults("RW") == CONFIG["default_scenario"]
    payload["assumptions"] = {"tariff": 1000, "fixed_cost": 20000}
    out = client.post("/api/analyze", json=payload).json
    assert out["assumptions"]["tariff"] == 1000  # not an FX conversion
    report = client.post("/api/report", json=payload).text
    assert "Currency UGX" in report and "UGX/month" in report
    assert "RWF" not in report and "{{ r.context" not in report


def test_public_data_live_adapter_selects_latest_and_caches():
    calls = []
    public = PublicDataService(lambda url: calls.append(url) or world_bank())
    first = public.public_context("RW")
    again = public.public_context("RW")
    assert len(calls) == 1 and first == again
    assert [r["year"] for r in first["indicators"]] == [2025, 2024]
    assert first["indicators"][0]["value"] == 13000000
    assert all(r["license"] == "CC BY 4.0" for r in first["indicators"])
    again["indicators"][0]["value"] = 0
    assert public.snapshot(first["id"], "RW")["indicators"][0]["value"] == 13000000
    assert public.snapshot(first["id"], "UG") is None


@pytest.mark.parametrize("body", [{}, [None, None], [{}, []], [{}, [{"indicator": None}]], [{}, [{"country": {"id": "RW"}, "indicator": {"id": "SP.POP.TOTL"}, "date": "2025", "value": float("nan")}]]])
def test_invalid_public_data_never_becomes_fabricated_context(body):
    with pytest.raises(PublicDataUnavailable):
        PublicDataService(lambda url: body).public_context("RW")


def test_geocoder_filters_country_and_invalid_rows():
    body = {"results": [{"name": "Valid town", "country_code": "RW", "latitude": -2, "longitude": 30}, {"name": "Wrong country", "country_code": "UG", "latitude": 0, "longitude": 32}, {"country_code": "RW", "latitude": 999}]}
    public = PublicDataService(lambda url: body)
    out = public.locations("Town & <x>", "RW")
    assert len(out["locations"]) == 1
    assert out["locations"][0]["source"] == "Open-Meteo / GeoNames"
    assert "%26" in out["source_url"] and "%3Cx%3E" in out["source_url"]
    assert PublicDataService(lambda url: {}).locations("Unknown", "RW")["locations"] == []


def test_public_routes_snapshot_export_and_offline_path(app):
    client = app.test_client()
    service = app.extensions["public_data"]
    service.fetcher = lambda url: world_bank()
    snapshot = client.get("/api/public-data?country=RW").json
    payload = {"site": DEMOS[0], "context": {"public_data_id": snapshot["id"]}}
    out = client.post("/api/analyze", json=payload).json
    assert out["public_data"] == snapshot
    assert out["forecast"] == client.post("/api/analyze", json={"site": DEMOS[0]}).json["forecast"]
    with zipfile.ZipFile(io.BytesIO(client.post("/api/export", json=payload).data)) as archive:
        assert json.loads(archive.read("public_context.json")) == snapshot
        assert b"CC BY 4.0" in archive.read("report.html")
    service.snapshots.clear()
    out = client.post("/api/analyze", json=payload).json
    assert out["public_data"] is None
    assert any("snapshot is unavailable" in w for w in out["warnings"])
    def fail(url):
        raise PublicDataUnavailable("Source offline")
    service.fetcher = fail
    service.cache.clear()
    assert client.get("/api/public-data?country=RW").status_code == 503
    assert client.get("/api/locations?q=Ki&country=RW").status_code == 503
    assert client.post("/api/analyze", json={"site": DEMOS[0]}).status_code == 200


def test_new_api_invalid_and_valid_contracts(app):
    client = app.test_client()
    settings = client.get("/api/context-settings").json
    assert set(settings["countries"]) == {"RW", "UG", "KE", "TZ", "BI", "SS", "SO", "CD"}
    assert client.get("/api/locations?q=x").status_code == 400
    assert client.get("/api/public-data?country=ZZ").status_code == 400
    assert client.post("/api/prepare-inputs", json={"site": {"households": 100}}).status_code == 200
    assert client.post("/api/analyze", json={"site": {"households": 100}}).status_code == 400
