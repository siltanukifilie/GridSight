"""Average-period conversions must agree across dashboard, profile and exports."""
import csv
import io
import json
import zipfile

import pytest

from app import create_app
from src.domain import DEMOS, demand_periods, finance


@pytest.mark.parametrize("monthly", [0, 3650, 12.3456, .000001])
def test_average_period_conversions(monthly):
    result = demand_periods(monthly)
    values = {p["period"]: p for p in result["estimates"]}
    assert list(values) == ["day", "week", "month", "year"]
    assert values["day"]["central"] == pytest.approx(monthly * 12 / 365)
    assert values["week"]["central"] == pytest.approx(monthly * 12 * 7 / 365)
    assert values["month"]["central"] == monthly
    assert values["year"]["central"] == monthly * 12
    for period, value in values.items():
        assert value["unit"] == f"kWh/{period}"
        assert value["central"] == pytest.approx(values["day"]["central"] * value["days_per_period"])
    assert "365 days" in result["basis"]
    assert "Not forecasts for specific dates" in result["basis"]


@pytest.mark.parametrize("invalid", [-1, float("nan"), float("inf"), True, None])
def test_invalid_energy_cannot_be_converted(invalid):
    with pytest.raises(ValueError, match="finite nonnegative"):
        demand_periods(invalid)


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize("role", ["developer", "investor"])
@pytest.mark.parametrize("site", DEMOS)
def test_periods_consistent_with_profile_finance_and_exports(client, role, site):
    body = {"role": role, "site": site, "assumptions": {"household_growth": .3, "business_growth": .4}}
    response = client.post("/api/analyze", json=body)
    assert response.status_code == 200
    r = response.json
    rows = r["demand_periods"]["estimates"]
    daily, weekly, monthly, annual = [p["central"] for p in rows]
    assert daily == r["profile"]["daily_kwh"]
    assert daily == pytest.approx(sum(r["profile"]["kw"]))
    assert weekly == daily * 7
    assert monthly == r["forecast"]["central"]
    assert annual == r["growth"][0]["central"] * 12  # Year 1, not Year 3 growth.
    assert r["finance"] == finance(monthly, r["assumptions"], r["profile"]["peak_kw"])
    report = client.post("/api/report", json=body).get_data(as_text=True)
    assert "Central demand estimate" in report
    assert r["demand_periods"]["basis"] in report
    for p in rows:
        assert p["label"] in report and p["unit"] in report
        assert f'{p["central"]:,.1f}' in report
    with zipfile.ZipFile(io.BytesIO(client.post("/api/export", json=body).data)) as archive:
        saved = json.loads(archive.read("analysis.json"))
        assert saved["demand_periods"] == r["demand_periods"]
        csv_rows = list(csv.DictReader(io.StringIO(archive.read("central_demand_estimates.csv").decode())))
        for expected, actual in zip(rows, csv_rows, strict=True):
            assert float(actual["central"]) == expected["central"]
            assert float(actual["days_per_period"]) == expected["days_per_period"]
            assert actual["period"] == expected["period"]
            assert actual["unit"] == expected["unit"]
