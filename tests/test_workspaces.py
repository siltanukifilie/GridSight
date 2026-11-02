"""Audience routing must not alter the underlying engineering or finance result."""
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


def test_exactly_two_roles_and_visible_local_mvp_limits(client):
    assert client.get("/api/bootstrap").json["roles"] == {
        "developer": "Mini-grid developer", "investor": "Investor / lender"
    }
    page = client.get("/").get_data(as_text=True)
    assert 'id="role-select"' in page
    assert 'value="developer"' in page and 'value="investor"' in page
    assert 'Shared project · no login or access control.' in page
    assert '/static/workspaces.js' in page
    assert client.get("/static/workspaces.js").status_code == 200


@pytest.mark.parametrize("site", DEMOS)
def test_same_numbers_for_both_workspaces(client, site):
    body = {"site": site, "assumptions": {"tariff": 400, "collection_rate": .8, "additional_mills": 2}}
    developer = client.post("/api/analyze", json={**body, "role": "developer"}).json
    investor = client.post("/api/analyze", json={**body, "role": "investor"}).json
    for key in ("site", "assumptions", "forecast", "demand_periods", "profile", "growth", "finance", "components", "sensitivities", "warnings", "supply_energy_kwh", "evaluation"):
        assert developer[key] == investor[key], key
    assert developer["workspace"]["role"] == "developer"
    assert investor["workspace"]["role"] == "investor"
    assert investor["workspace"]["access_control"] is False


def test_legacy_payload_defaults_to_developer(client):
    assert client.post("/api/analyze", json={"site": DEMOS[0]}).json["workspace"]["role"] == "developer"


@pytest.mark.parametrize("endpoint", ["analyze", "report", "export", "feasibility-report"])
@pytest.mark.parametrize("role", ["admin", "lender", "", None, [], {}, True])
def test_invalid_roles_are_rejected_cleanly(client, endpoint, role):
    response = client.post(f"/api/{endpoint}", json={"site": DEMOS[0], "role": role})
    assert response.status_code == 400
    assert "Role must be" in response.json["error"]


@pytest.mark.parametrize("role,label", [("developer", "Planning analysis"), ("investor", "Investment screening review")])
def test_role_specific_export_preserves_full_inputs_and_evidence(client, role, label):
    body = {"site": DEMOS[1], "role": role, "assumptions": {"debt_payment": 0}}
    result = client.post("/api/analyze", json=body).json
    report = client.post("/api/report", json=body).get_data(as_text=True)
    assert label in report
    assert ("Investor / lender screening snapshot" in report) == (role == "investor")
    assert "Not applicable" in report
    assert "Synthetic evidence only" in report
    with zipfile.ZipFile(io.BytesIO(client.post("/api/export", json=body).data)) as archive:
        exported = json.loads(archive.read("analysis.json"))
        assert exported["workspace"]["role"] == role
        for key in ("site", "assumptions", "forecast", "finance", "growth"):
            assert exported[key] == result[key]
        assert label in archive.read("report.html").decode()
