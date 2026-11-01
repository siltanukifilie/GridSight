"""Create locally reviewable analysis outputs for all three prepared communities."""
import json
from app import create_app
from src.domain import DEMOS, ROOT

if __name__ == "__main__":
    client = create_app().test_client()
    destination = ROOT / "reports/examples"
    destination.mkdir(parents=True, exist_ok=True)
    summary = []
    for site in DEMOS:
        payload = {"site": site}
        analysis = client.post("/api/analyze", json=payload)
        report = client.post("/api/report", json=payload)
        archive = client.post("/api/export", json=payload)
        if not all(r.status_code == 200 for r in [analysis, report, archive]):
            raise RuntimeError(f"Example export failed for {site['id']}")
        stem = site["id"].lower()
        (destination / f"{stem}.json").write_text(json.dumps(analysis.json, indent=2))
        (destination / f"{stem}.html").write_bytes(report.data)
        (destination / f"{stem}.zip").write_bytes(archive.data)
        summary.append({"community": site["name"], "district_context": site["district"], "origin": "synthetic", "forecast": analysis.json["forecast"], "year_3_kwh_month": analysis.json["growth"][2]["central"], "peak_kw": analysis.json["profile"]["peak_kw"], "cash_after_debt_rwf_month": analysis.json["finance"]["base"]["cash_after_debt"]})
    (destination / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Created three analysis reports and export packages in {destination}")
    connection_payload = {"site": DEMOS[1], "connection": {"enabled": True, "connection_month": "2026-11"}}
    connection_example = client.post("/api/analyze", json=connection_payload)
    if connection_example.status_code != 200:
        raise RuntimeError("Connection example failed")
    (destination / "connection-ramp.json").write_text(json.dumps(connection_example.json, indent=2))
    print("Created connection-ramp fixture (assumed November 2026 connection, not a real site).")
    detailed_payload = {**connection_payload, "detailed": {"enabled": True, "months_since_connection": 18, "household_income_monthly": 100000, "connection_fee": 50000}}
    detailed = client.post("/api/analyze", json=detailed_payload)
    if detailed.status_code != 200:
        raise RuntimeError("Detailed input example failed")
    (destination / "detailed-inputs.json").write_text(json.dumps(detailed.json, indent=2))
