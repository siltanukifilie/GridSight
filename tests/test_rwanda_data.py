import io
import json
import zipfile

import numpy as np
import pytest
from scipy.spatial import cKDTree

from app import create_app
from src import rwanda_data as rd
from src.context import validate_context
from src.geography import catalog, eligible, level, public_location


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def point(**changes):
    return {"latitude": -2, "longitude": 30, "country_code": "RW", "source": "manual", "label": "Survey point", **changes}


def test_active_scope_covers_eight_eac_countries(client):
    settings = client.get("/api/context-settings").json
    assert set(settings["active_countries"]) == {"RW","UG","KE","TZ","BI","SS","SO","CD"}
    assert settings["future_countries"] == []
    html = client.get("/").text
    assert "rwanda-data.js" in html and "Rwanda workspace" in html


def test_local_radius_is_geodesic_and_does_not_pull_remote_evidence():
    points = np.array([[-2, 30], [-2, 30.001], [-2, 30.1]])
    tree = cKDTree(rd.xyz(points[:, 0], points[:, 1]))
    assert sorted(rd.nearby((points, tree), -2, 30)) == [0, 1]
    assert rd.nearby(None, -2, 30) is None


def test_missing_layers_remain_unknown_with_explicit_placeholders(monkeypatch):
    rd.profile_at.cache_clear()
    monkeypatch.setattr(rd, "building_index", lambda: None)
    monkeypatch.setattr(rd, "facility_index", lambda: None)
    monkeypatch.setattr(rd, "read_layer", lambda name: None)
    result = rd.location_profile(point(label="Missing source case"))
    assert result["building_detections"] is None
    assert result["building_area_m2"] is None
    assert result["mapped_facilities"] is None
    assert result["suggested_inputs"]["households"] == 150
    assert all(r["kind"] == "Placeholder" for r in result["input_basis"])
    assert "not a local estimate" in result["input_basis"][0]["basis"]
    rd.profile_at.cache_clear()


def test_building_proxy_math_and_caps_are_exposed(monkeypatch):
    rd.profile_at.cache_clear()
    points = np.array([[-2, 30, 50, .9]] * 3000)
    monkeypatch.setattr(rd, "building_index", lambda: (points, cKDTree(rd.xyz(points[:, 0], points[:, 1]))))
    monkeypatch.setattr(rd, "facility_index", lambda: None)
    result = rd.location_profile(point(label="Proxy arithmetic"))
    assert result["building_detections"] == 3000
    assert result["building_area_m2"] == 150000
    assert result["suggested_inputs"]["households"] == 1500
    assert "70%" in result["input_basis"][0]["basis"]
    assert "capped" in result["input_basis"][0]["basis"]
    assert result["suggested_inputs"]["mills"] == 0
    rd.profile_at.cache_clear()


@pytest.mark.parametrize("body", [None, [], {}, {"location": point(country_code="UG")}, {"location": point(latitude=50)}, {"location": point(latitude=True)}, {"location": point(source="arbitrary-provider")}])
def test_invalid_auto_project_is_rejected(client, body):
    response = client.post("/api/location-project", data=json.dumps(body), content_type="application/json")
    assert response.status_code == 400


def test_public_proxy_origin_needs_a_real_location():
    with pytest.raises(ValueError):
        validate_context({"input_origin": "public_proxy"})


def test_actual_collected_sources_are_not_synthetic_templates(client):
    pack = client.get("/api/rwanda-data").json
    rows = {s["id"]: s for s in pack["layers"]}
    assert rows["buildings"]["records"] > 10000
    assert rows["facilities"]["records"] > 1000
    if (rd.DATA / "electricity.json").exists():
        assert rows["electricity"]["records"] == 236
    else:
        assert rows["electricity"]["records"] is None
        assert rows["electricity"]["status"] == "Not collected"
    for key in ("meters", "viirs", "costs"):
        assert rows[key]["records"] is None
    for key in ("gep", "gridfinder", "eae", "bugesera_prepared"):
        assert rows[key]["records"] == 15
    assert "exact VIIRS year unresolved" in rows["gep"]["use"]
    assert rows["meters"]["status"] == "Partner needed"
    b = rd.read_layer("buildings.meta.json")
    assert b["source_rows"] == 22106220 and b["confidence_threshold"] == .738
    assert len(b["source_sha256"]) == 64
    assert b["records"] == 4251978
    assert b["country_clip"]["boundary_id"] == "RWA-ADM0-41251308"


def test_automatic_point_outside_rwanda_land_boundary_is_rejected(client):
    response = client.post("/api/location-project", json={"location": point(latitude=-2.8, longitude=30.9)})
    assert response.status_code == 400
    assert "boundary" in response.json["error"]


@pytest.mark.parametrize("role", ["developer", "investor"])
def test_selection_analysis_and_report_preserve_evidence(client, role):
    row = next(r for r in catalog("RW")["records"] if not level(r) and eligible(r, "RW"))
    location = public_location("RW", row["id"])
    project = client.post("/api/location-project", json={"location": location}).json
    assert project["context"]["input_origin"] == "public_proxy"
    assert project["connection"]["enabled"] is True
    assert len(project["context"]["assumed_fields"]) == 9
    assert project["context"]["grid"]["status"] == "unknown"
    assert project["planning"]["project_capex"] is None
    payload = {**project, "role": role}
    result = client.post("/api/analyze", json=payload)
    assert result.status_code == 200
    data = result.json
    assert data["location_profile"]["building_detections"] is not None
    assert data["provenance"]["model_training_origin"] == "synthetic"
    assert data["forecast"]["lower"] <= data["forecast"]["central"] <= data["forecast"]["upper"]
    report = client.post("/api/feasibility-report", json=payload)
    assert report.status_code == 200
    assert "Local public evidence" in report.text
    assert "Partner needed" in report.text
    assert "accepted by the user" not in report.text
    exported = zipfile.ZipFile(io.BytesIO(client.post("/api/export", json=payload).data))
    profile = json.loads(exported.read("location_profile.json"))
    assert profile["id"] == data["location_profile"]["id"]
    # Editing a customer count must not rewrite the imported starting evidence.
    payload["site"]["households"] = 42
    changed = client.post("/api/analyze", json=payload).json
    assert changed["site"]["households"] == 42
    assert changed["location_profile"]["suggested_inputs"] == profile["suggested_inputs"]


def test_download_keeps_licences_and_does_not_redistribute_government_records(client):
    response = client.get("/api/rwanda-data/download")
    assert response.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(response.data))
    assert "source_manifest.json" in z.namelist()
    assert "facilities.json" in z.namelist()
    assert "electricity.json" not in z.namelist()
    assert "ODbL" in z.read("README.txt").decode()


def test_historical_sector_connection_is_not_a_site_grid_status(monkeypatch):
    # Fictional schema fixture: public repo intentionally excludes the raw layer.
    monkeypatch.setattr(rd, "read_layer", lambda name: {"features": [
        {"properties": {"sector": "Gashora", "electricity_source": "on-grid", "electricity_access": "yes"}}
    ]})
    result = rd.historical_grid({"administrative_path": ["Eastern Province", "Bugesera", "Gashora"]})
    assert result["on_grid_records"] > 0
    assert result["status"] == "Historical on-grid records in sector"
    assert "not a village" in result["note"]
