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


@pytest.mark.parametrize("path", ["/", "/health", "/api/bootstrap", "/static/app.js", "/static/demand-charts.js", "/static/styles.css", "/api/dataset/sites", "/api/dataset/monthly", "/api/dataset/evaluation", "/api/dataset/test"])
def test_routes_available(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("site", DEMOS)
def test_each_demo_end_to_end(client, site):
    r = client.post("/api/analyze", json={"site": site})
    assert r.status_code == 200
    output = r.json
    assert output["site"]["id"] == site["id"]
    assert output["provenance"]["origin"] == "synthetic"
    assert output["forecast"]["lower"] <= output["forecast"]["central"] <= output["forecast"]["upper"]
    assert output["growth"][0]["central"] == output["forecast"]["central"]
    assert len(output["finance"]["scenarios"]) == 4
    json.dumps(output, allow_nan=False)


@pytest.mark.parametrize("body", [None, [], {}, {"site": None}, {"site": {"households": -1}}, {"site": DEMOS[0], "assumptions": []}, {"site": DEMOS[0], "assumptions": {"tariff": -1}}])
def test_malformed_inputs_return_useful_errors(client, body):
    r = client.post("/api/analyze", json=body)
    assert r.status_code == 400
    assert r.json["error"]


def test_bad_content_type_and_json(client):
    assert client.post("/api/analyze", data="not json").status_code == 400
    assert client.post("/api/analyze", data="{", content_type="application/json").status_code == 400


def test_unknown_dataset_cannot_read_arbitrary_path(client):
    assert client.get("/api/dataset/secrets").status_code == 404
    assert client.get("/api/dataset/../../config/assumptions.json").status_code == 404


def test_export_matches_analysis_and_contains_provenance(client):
    body = {"site": DEMOS[2], "assumptions": {"tariff": 410, "additional_mills": 2}}
    result = client.post("/api/analyze", json=body).json
    response = client.post("/api/export", json=body)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        evidence_folders = ("prepared_evidence/", "operational_models/", "kenya_nigeria_uncertainty/", "bugesera_ranking/", "operator_pilot/")
        assert {name for name in archive.namelist() if not name.startswith(evidence_folders)} == {
            "analysis.json", "central_demand_estimates.csv", "financial_scenarios.csv", "growth_scenarios.csv",
            "daily_profile.csv", "report.html", "README.txt", "demand_scenarios.csv", "monthly_scenarios.csv",
            "monthly_growth.csv", "productive_options.csv", "financial_evidence.json", "benchmark_sources.json",
            "productive_use_stress.csv", "growth_36_months.csv", "growth_annual_totals.csv",
            "affordability_scenarios.csv", "productive_growth_monthly.csv", "productive_growth_annual.csv",
            "assessment_checklist.json"}
        assert "prepared_evidence/summary.json" in archive.namelist()
        assert "operational_models/summary.json" in archive.namelist()
        exported = json.loads(archive.read("analysis.json"))
        assert exported["forecast"] == result["forecast"]
        assert exported["finance"] == result["finance"]
        assert exported["assumptions"] == result["assumptions"]
        assert b"Synthetic evidence only" in archive.read("report.html")


def test_report_escapes_user_text(client):
    body = {"site": {**DEMOS[0], "name": '<script>alert("x")</script>'}}
    response = client.post("/api/report", json=body)
    assert response.status_code == 200
    assert b'<script>alert(' not in response.data
    assert b'&lt;script&gt;' in response.data


def test_large_payload_rejected(client):
    response = client.post("/api/analyze", data="a" * 70000, content_type="application/json")
    assert response.status_code == 413
