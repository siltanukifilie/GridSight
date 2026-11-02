"""Public geography provenance, coverage and country-safe project tests."""
import io
import json
import zipfile
from datetime import date, timedelta
import pytest
from app import create_app
from src.context import COUNTRIES, validate_context
from src.domain import DEMOS
from src.geography import browse, catalog, eligible, level, public_location, record, within
from scripts.import_locations import parse_dump


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


@pytest.mark.parametrize("code", list(COUNTRIES))
def test_all_eight_have_real_attributed_offline_places_and_country_safe_forecasts(client, code):
    data = catalog(code)
    assert data["source_url"] == f"https://download.geonames.org/export/dump/{code}.zip"
    assert data["license"] == "CC BY 4.0" and len(data["source_sha256"]) == 64
    assert data["fetched_at"] and len(data["records"]) > 100
    areas = client.get(f"/api/geography?country={code}").json
    assert areas["items"] and areas["coverage_note"]
    places = client.get(f"/api/geography?country={code}&kind=places").json
    assert places["items"] and places["next_offset"] == 60
    point = client.get(f"/api/geography/location?country={code}&id={places['items'][0]['id']}").json
    assert point["country_code"] == code and point["grid_status"] == "unknown"
    payload = {"site": DEMOS[0], "context": {"country_code": code, "location": point, "input_origin": "user_entered"}, "assumptions": {"tariff": 12345, "variable_cost": 4321}}
    out = client.post("/api/analyze", json=payload)
    assert out.status_code == 200, out.json
    assert out.json["context"]["currency"] == COUNTRIES[code]["currency"]
    assert out.json["assumptions"]["tariff"] == 12345  # no implicit FX conversion
    if code != "RW":
        assert any(COUNTRIES[code]["name"] in w and "training" in w for w in out.json["warnings"])
    html = client.post("/api/report", json=payload).text
    assert "GeoNames country extract" in html and "Grid-access screening" in html
    assert "User-reported" in html and "CC BY 4.0" in html


def test_rwanda_district_sector_settlement_hierarchy():
    district = next(r for r in browse("RW")["items"] if r["name"] == "Kirehe District")
    sectors = browse("RW", district["id"], "local")
    assert len(sectors["items"]) == 12
    sector = sectors["items"][0]
    places = browse("RW", sector["id"], "places")
    assert places["items"]
    assert places["reference_location"]["kind"] == "administrative reference point"
    for row in places["items"]:
        assert within(record("RW", row["id"]), record("RW", sector["id"]))
        point = public_location("RW", row["id"])
        assert district["name"] in point["administrative_path"]
        assert sector["name"] in point["administrative_path"]


def test_incomplete_hierarchy_never_invents_a_subdivision():
    # Kenyan source has many counties with no linked ADM2 records.
    county = next(r for r in browse("KE")["items"] if not browse("KE", r["id"], "local")["items"])
    out = browse("KE", county["id"], "local")
    assert out["items"] == [] and out["total"] == 0
    assert "not a complete" in out["coverage_note"]
    assert out["reference_location"]["kind"] == "administrative reference point"


def test_population_filter_is_not_grid_evidence_and_unknown_stays_unknown():
    rows = catalog("RW")["records"]
    assert all(not r["feature"].startswith("PPLA") and r["feature"] != "PPLC" for r in rows)
    assert not any(r["codes"][0] == "12" for r in rows if eligible(r, "RW"))
    unknown = next(r for r in rows if not level(r) and eligible(r, "RW") and r["population"] is None)
    point = public_location("RW", unknown["id"])
    assert point["population"] is None and point["grid_status"] == "unknown"
    assert "reference year not supplied" in point["population_note"]
    assert not eligible({**unknown, "population": 20000}, "RW")


def test_descendants_of_explicitly_urban_areas_are_excluded():
    rows = catalog("CD")["records"]
    city = next(r for r in rows if r["feature"] == "ADM1" and r["name"] == "Kinshasa City")
    places = [r for r in rows if not level(r) and within(r, city)]
    assert places and all(not eligible(r, "CD") for r in places)


@pytest.mark.parametrize("suffix", ["country=ZZ", "country=../RW", "country=RW&kind=bad", "country=RW&kind=local", "country=RW&offset=-1", "country=RW&offset=bad", "country=RW&parent=nope", "country=RW&kind=places&q=" + "x" * 101])
def test_malformed_hierarchy_queries_are_clean_400s(client, suffix):
    assert client.get("/api/geography?" + suffix).status_code == 400


def test_country_mismatch_and_tampered_metadata(client):
    identifier = browse("UG", kind="places")["items"][0]["id"]
    assert client.get(f"/api/geography/location?country=RW&id={identifier}").status_code == 400
    point = public_location("RW", browse("RW", kind="places")["items"][0]["id"])
    tampered = {**point, "label": "Verified off-grid", "latitude": -2, "longitude": 30, "provenance": {"source": "invented"}}
    canonical = validate_context({"location": tampered})["location"]
    assert canonical == point  # public identifiers resolve to trusted local source records


def test_pagination_search_and_parent_filter_are_consistent():
    first = browse("CD", kind="places")
    second = browse("CD", kind="places", offset=first["next_offset"])
    assert not {r["id"] for r in first["items"]} & {r["id"] for r in second["items"]}
    name = first["items"][0]["name"]
    matches = browse("CD", kind="places", query=name)
    assert matches["items"] and all(name.casefold() in r["name"].casefold() for r in matches["items"])


@pytest.mark.parametrize("status", ["reported_unserved", "planned", "connected"])
def test_grid_claim_requires_source_and_date_and_remains_unverified(client, status):
    raw = {"status": status, "source": "Field visit / fixture, not real evidence", "checked_on": "2026-01-01"}
    for incomplete in ({"status": status}, {**raw, "source": ""}, {**raw, "checked_on": None}):
        with pytest.raises(ValueError):
            validate_context({"grid": incomplete})
    out = client.post("/api/analyze", json={"site": DEMOS[0], "context": {"grid": raw}}).json
    assert out["context"]["grid"]["verification"] == "User-reported; not independently verified"
    assert out["context"]["grid"]["status"] == status
    if status == "connected":
        assert any("Excluded from" in w for w in out["warnings"])
    if status == "planned":
        assert any("grid-arrival" in w for w in out["warnings"])


@pytest.mark.parametrize("grid", [None, [], {"status": "verified"}, {"status": "unknown", "source": []}, {"status": "unknown", "checked_on": True}, {"status": "unknown", "checked_on": "2026-02-30"}, {"status": "unknown", "checked_on": (date.today()+timedelta(days=1)).isoformat()}])
def test_bad_grid_evidence_rejected(grid):
    with pytest.raises(ValueError):
        validate_context({"grid": grid})


def test_export_preserves_site_source_grid_and_fresh_currency(client):
    point = public_location("TZ", browse("TZ", kind="places")["items"][0]["id"])
    payload = {"site": DEMOS[0], "context": {"country_code": "TZ", "location": point, "grid": {"status": "planned", "source": "Test expansion-plan reference", "checked_on": "2026-01-01"}}}
    response = client.post("/api/export", json=payload)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        out = json.loads(archive.read("analysis.json"))
        assert out["context"]["location"]["provenance"] == point["provenance"]
        assert out["context"]["grid"]["status"] == "planned"
        assert out["finance"]["currency"] == "TZS"
        assert point["id"] in archive.read("report.html").decode()


def test_importer_excludes_seats_bad_coordinates_and_other_countries():
    row = ["1", "Test", "Test", "", "-2", "30", "P", "PPL", "RW", "", "11", "56", "1", "", "0", "", "1", "Africa/Kigali", "2026-01-01"]
    samples = [row, [*row[:7], "PPLC", *row[8:]], [*row[:4], "nan", *row[5:]], [*row[:8], "UG", *row[9:]]]
    result = parse_dump("\n".join("\t".join(r) for r in samples), "RW")
    assert len(result) == 1 and result[0]["population"] is None


def test_landing_has_discovery_not_auto_forecast(client):
    page = client.get("/").text
    assert 'id="discovery-panel"' in page and '/static/discovery.js' in page
    script = client.get("/static/app.js").text
    boot = script[script.rfind("(async()=>"):]
    assert "await openInitialWorkspace(window.location.search)" in boot
    assert "await selectSite" not in boot
    loader = client.get("/static/demo-cases.js").text
    startup = loader[loader.index("async function openInitialWorkspace"):loader.index("function juruDemoCardHtml")]
    assert "await openDiscovery()" in startup
    assert "if(new URLSearchParams(search).get('demo')==='juru')await loadJuruDemo();" in startup
