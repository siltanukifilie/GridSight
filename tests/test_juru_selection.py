"""Normal Juru selection uses its demo; other places and public evidence do not."""
import io
import json
import zipfile

import pytest

from app import create_app
from src.demo_cases import JURU_ID, JURU_LOCATION_IDS, is_juru_demo_location, juru_case
from src.geography import public_location


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def select(client, identifier="11186926", **options):
    location = public_location("RW", identifier)
    response = client.post("/api/location-project", json={"location": location, **options})
    assert response.status_code == 200, response.text
    return response.json


@pytest.mark.parametrize("identifier", sorted(JURU_LOCATION_IDS))
@pytest.mark.parametrize("role", ["developer", "investor"])
def test_normal_juru_selection_loads_all_demo_inputs_and_calculated_cash(client, identifier, role):
    project = select(client, identifier)
    assert project == juru_case()["project"]
    assert project["context"]["input_origin"] == "synthetic"
    assert project["site"]["name"] == "Juru demo"
    assert project["assumptions"]["debt_payment"] == 500000
    response = client.post("/api/analyze", json={**project, "role": role})
    assert response.status_code == 200, response.text
    result = response.json
    assert len(result["demo_case"]["features"]) == 20
    assert len(result["feasibility"]["monthly_growth"]) == 36
    expected = next(s for s in result["feasibility"]["scenarios"] if s["key"] == "expected")
    year = expected["years"][0]
    assert year["demand_kwh"] / 12 == pytest.approx(7369.997956, abs=.01)
    assert year["cash_after_debt"] / 12 == pytest.approx(2145399.14, abs=.01)
    assert year["cash_after_debt"] == pytest.approx(year["revenue"] - year["operating_cost"] - 12 * 500000)
    assert year["dscr"] == pytest.approx(5.29079828)
    assert year["cash_shortfall_months"] == 0
    assert result["location_profile"] is None
    assert result["prepared_evidence"]["sector_context"]["used_in_forecast"] is False
    assert not result["delivery"]["validation"]["field_validated"]


def test_public_juru_screen_remains_available_without_demo_substitution(client):
    project = select(client, project_mode="public_proxy")
    assert project["site"]["id"] == "CUSTOM"
    assert project["context"]["input_origin"] == "public_proxy"
    assert project["context"]["location"]["id"] == "11186926"
    result = client.post("/api/analyze", json=project).json
    assert "demo_case" not in result
    assert result["location_profile"] is not None
    expected = next(s for s in result["feasibility"]["scenarios"] if s["key"] == "expected")
    # Real deficits are preserved; switching datasets is not a sign/format change.
    assert expected["years"][0]["cash_after_debt"] < 0
    assert result["site"]["households"] != 300


@pytest.mark.parametrize("identifier", ["11186987", "7321572", "7620047"])
def test_other_places_named_juru_keep_their_public_inputs(client, identifier):
    project = select(client, identifier)
    assert project["site"]["id"] != JURU_ID
    assert project["context"]["input_origin"] == "public_proxy"
    assert project["context"]["location"]["id"] == identifier
    assert not is_juru_demo_location(project["context"]["location"])


@pytest.mark.parametrize("country,path,expected", [
    ("RW", ["Bugesera", "Juru", "Juru"], True),
    ("RW", ["Bugesera District", "Juru Sector", "Juru"], True),
    ("RW", ["Kayonza", "Gahini", "Juru"], False),
    ("RW", ["Bugesera", "Juru", "Another cell"], False),
    ("UG", ["Bugesera", "Juru", "Juru"], False),
])
def test_manual_juru_selection_is_scoped_to_the_requested_case(client, country, path, expected):
    location = {"country_code": country, "source": "user_entered_administration",
                "administrative_path": path, "label": path[-1]}
    response = client.post("/api/location-project", json={"location": location})
    assert response.status_code == 200
    assert (response.json["site"]["id"] == JURU_ID) is expected


def test_juru_edits_can_still_produce_negative_cash(client):
    project = select(client)
    project["assumptions"]["debt_payment"] = 5000000
    result = client.post("/api/analyze", json=project).json
    expected = next(s for s in result["feasibility"]["scenarios"] if s["key"] == "expected")
    assert expected["years"][0]["cash_after_debt"] < 0
    assert result["context"]["input_origin"] == "synthetic"
    assert juru_case()["project"]["assumptions"]["debt_payment"] == 500000


def test_normal_juru_selection_exports_the_same_inputs_and_provenance(client):
    project = select(client)
    response = client.post("/api/export", json=project)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        result = json.loads(archive.read("analysis.json"))
        assert result["site"]["id"] == JURU_ID
        assert result["context"]["input_origin"] == "synthetic"
        assert len(result["demo_case"]["features"]) == 20
        assert "juru_test_case/features_20.csv" in archive.namelist()
        assert "demo data" in archive.read("report.html").decode().lower()


def test_invalid_selection_mode_is_not_silently_accepted(client):
    location = public_location("RW", "11186926")
    response = client.post("/api/location-project", json={"location": location, "project_mode": "fake"})
    assert response.status_code == 400
