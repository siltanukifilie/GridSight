"""Judge-facing packaging checks, not scientific validation or licence approval."""
import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "data/catalog.json").read_text())["datasets"]
DOCS = [ROOT / name for name in ("README.md", "AUTHORS.md", "CONTRIBUTING.md", "THIRD_PARTY_NOTICES.md")]
DOCS += list((ROOT / "docs").rglob("*.md"))
DOCS += [ROOT / p / "README.md" for p in ("data", "scripts", "reports", "tests/fixtures")]


@pytest.mark.parametrize("entry", CATALOG, ids=lambda e: e["path"])
def test_data_catalog_counts_and_documentation(entry):
    path = ROOT / "data" / entry["path"]
    assert path.is_file()
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    assert len(rows) == entry["rows"]
    assert all(None not in row for row in rows), "CSV has unexpected extra columns"
    if "columns" in entry:
        assert len(fields) == entry["columns"]
    assert (ROOT / "data" / entry["documentation"]).is_file()
    assert entry["kind"] and entry["grain"]


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_documentation_relative_links_exist(doc):
    text = re.sub(r"```.*?```", "", doc.read_text(), flags=re.S)
    for target in re.findall(r"\]\(([^)]+)\)", text):
        target = target.strip().strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or not parsed.path or target.startswith("//"):
            continue
        resolved = (doc.parent / unquote(parsed.path)).resolve()
        assert resolved.is_relative_to(ROOT), (doc, target)
        assert resolved.exists(), (doc, target)


def test_canonical_features_retain_source_values_and_missing_labels():
    data = ROOT / "data"
    with (data / "prepared/bugesera_sectors.csv").open(newline="") as f:
        source = {r["sector"]: r for r in csv.DictReader(f)}
    with (data / "processed/bugesera_site_features.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len({r["site_id"] for r in rows}) == len(source) == 15
    for row in rows:
        assert row["country"] == "Rwanda" and row["district"] == "Bugesera"
        assert row["is_metered_demand"] == "False"
        assert row["data_origin"] == "public_context"
        original = source[row["site_name"]]
        for key, expected in original.items():
            actual = row["site_name" if key == "sector" else key]
            if actual == expected:
                continue
            # The existing pandas export normalizes numeric formatting only.
            assert actual != "" and expected != ""
            assert float(actual) == pytest.approx(float(expected), rel=1e-12)
        for field in ("metered_monthly_consumption_kwh", "metered_peak_kw", "milling_places_total", "farming_generators_total"):
            assert row[field] == ""
    metadata = json.loads((data / "processed/bugesera_site_features_metadata.json").read_text())
    assert metadata["rows"] == 15 and metadata["columns"] == 78
    assert metadata["measured_demand_rows"] == 0
    assert metadata["source_table"] == "data/prepared/bugesera_sectors.csv"
    assert (ROOT / metadata["source_table"]).is_file()


def test_banner_is_accessible_svg_without_external_resources():
    banner = ROOT / "docs/assets/gridsight-banner.svg"
    svg = ET.parse(banner).getroot()
    ns = {"s": "http://www.w3.org/2000/svg"}
    assert svg.find("s:title", ns).text == "GridSight"
    assert "GridSight Team" in svg.find("s:desc", ns).text
    assert svg.attrib["viewBox"] == "0 0 1200 330"
    assert not svg.findall(".//s:script", ns)
    assert not svg.findall(".//s:image", ns)
    assert "docs/assets/gridsight-banner.svg" in (ROOT / "README.md").read_text()


def test_generated_and_restricted_data_are_explicitly_ignored():
    rules = set((ROOT / ".gitignore").read_text().splitlines())
    for path in ("reports/examples/", "reports/planning_review/", "reports/screening_review/",
                 "exports/", "private/", "data/operator/", "data/rwanda/electricity.json", ".env"):
        assert path in rules
    for name in ("rw-demo-01.json", "rw-demo-02.json", "rw-demo-03.json", "connection-ramp.json", "detailed-inputs.json"):
        assert isinstance(json.loads((ROOT / "tests/fixtures" / name).read_text()), dict)
    for path in (ROOT / "tests").glob("*.test.cjs"):
        assert "reports/examples/" not in path.read_text()
