import io
import json
import runpy
import zipfile

import numpy as np
import pytest
from scipy.spatial import cKDTree

from app import create_app
from src import rwanda_data as rd
from src.domain import DEMOS, ROOT


@pytest.fixture
def public_client(monkeypatch):
    monkeypatch.setenv("GRIDSIGHT_PUBLIC_DEMO", "1")
    return create_app().test_client()


@pytest.mark.parametrize("route", [
    "/api/validate-consumption", "/api/validate-monthly",
    "/api/confidence-study", "/api/evaluate-update",
])
def test_public_demo_rejects_meter_processing_before_parsing(public_client, route):
    response = public_client.post(route, data="not json", content_type="application/json")
    assert response.status_code == 403
    assert "disabled" in response.json["error"]
    assert response.headers["Cache-Control"] == "no-store"


def test_public_demo_keeps_calculations_and_deliverables(public_client):
    body = {"site": DEMOS[0]}
    assert public_client.get("/health").json["status"] == "ok"
    assert public_client.post("/api/analyze", json=body).status_code == 200
    response = public_client.post("/api/deliverables-pack", json=body)
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        assert archive.testzip() is None
        assert "START_HERE.html" in archive.namelist()
        assert json.loads(archive.read("analysis.json"))["site"]["id"] == DEMOS[0]["id"]
    html = public_client.get("/").text
    assert 'data-public-demo="true"' in html
    assert "Calculations run on the hosting server" in html
    assert "/static/deployment.js" in html


def test_local_mode_retains_validation(monkeypatch):
    monkeypatch.delenv("GRIDSIGHT_PUBLIC_DEMO", raising=False)
    client = create_app().test_client()
    assert client.post("/api/validate-consumption", json={}).status_code == 400
    assert 'data-public-demo="false"' in client.get("/").text


@pytest.mark.parametrize("lat,lon", [(-2, 30), (0, 179.999), (89.999, -50)])
def test_low_memory_lookup_matches_tree_at_wraparound_and_pole(lat, lon):
    rng = np.random.default_rng(42)
    points = np.column_stack((np.clip(lat + rng.uniform(-.02, .02, 1000), -90, 90),
                              (lon + rng.uniform(-.02, .02, 1000) + 180) % 360 - 180)).astype(np.float32)
    tree = cKDTree(rd.xyz(points[:, 0].astype(float), points[:, 1].astype(float)))
    assert sorted(rd.nearby((points, None), lat, lon)) == sorted(rd.nearby((points, tree), lat, lon))
    assert rd.nearby((points[:0], None), lat, lon) == []


def test_missing_government_layer_is_unknown(monkeypatch):
    monkeypatch.setattr(rd, "read_layer", lambda name: None)
    assert rd.historical_grid({"administrative_path": ["Bugesera", "Gashora"]})["status"] == "Unknown"


def test_hosting_server_uses_platform_port_and_one_worker(monkeypatch):
    monkeypatch.setenv("PORT", "10000")
    config = runpy.run_path(str(ROOT / "gunicorn.conf.py"))
    assert config["bind"] == "0.0.0.0:10000"
    assert config["workers"] == 1 and config["threads"] == 1
    assert config["accesslog"] is None
