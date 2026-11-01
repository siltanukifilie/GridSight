"""GridSight planning web application. Run: .venv/bin/python app.py"""
import csv
import io
import json
import os
import zipfile
from flask import Flask, Response, jsonify, render_template, request, send_file
from werkzeug.exceptions import HTTPException
from src.domain import ROOT, CONFIG, DEMOS, SITE_LIMITS, SCENARIO_LIMITS
from src.model import load
from src.analysis import analyze
from src.workspaces import WORKSPACES
from src.feasibility import PLANNING_DEFAULTS, PLANNING_LIMITS, PLANNING_LABELS
from src.context import COUNTRIES, scenario_defaults, prepare_thin_inputs
from src.public_data import PublicDataService, PublicDataUnavailable
from src.validation import COLUMNS, compare_consumption
from src.geography import browse, public_location
from src.rwanda_data import initial_project, source_summary, DATA
from src.connection import DEFAULTS as CONNECTION_DEFAULTS, LIMITS as CONNECTION_LIMITS
from src.detailed_inputs import DEFAULTS as DETAILED_DEFAULTS, LIMITS as DETAILED_LIMITS, APPLIANCE_LABELS
from src.deliverables import sharing_text, sharing_handover, lender_text
from src.detailed_validation import (blank_manifest, compare_monthly, comparisons_csv,
                                     COLUMNS as MONTHLY_COLUMNS)
from src.statistical import (SETTINGS as STATISTICAL_SETTINGS, LABELS as UNCERTAINTY_LABELS,
                             blank_plan, planning_uncertainty, confidence_study, study_csv)
from src.financial_evidence import CATALOG, template as financial_template, fields as financial_fields, benchmark_check
from src.maintenance import blank_release, blank_policy, evaluate_candidate
from src.prepared_evidence import summary as prepared_summary, write_archive as write_prepared_archive
from src.operational_evidence import summary as operational_summary, write_archive as write_operational_archive


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    app.config["PUBLIC_DEMO"] = os.environ.get("GRIDSIGHT_PUBLIC_DEMO") == "1"
    forecaster = load()
    public = PublicDataService()
    app.extensions["public_data"] = public

    @app.before_request
    def upload_limits():
        if app.config["PUBLIC_DEMO"] and request.path in (
            "/api/validate-consumption", "/api/validate-monthly",
            "/api/confidence-study", "/api/evaluate-update",
        ):
            return jsonify(error="Meter uploads are disabled on the public demo. Run GridSight locally with approved anonymized data; secure hosted access is not implemented."), 403
        if request.path in ("/api/validate-monthly", "/api/confidence-study", "/api/evaluate-update"):
            request.max_content_length = 256 * 1024

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        if request.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(ValueError)
    def invalid(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(PublicDataUnavailable)
    def unavailable(error):
        return jsonify(error=str(error)), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith("/api"):
            return jsonify(error=error.description), error.code
        return error

    @app.get("/")
    def index():
        return render_template("index.html", public_demo=app.config["PUBLIC_DEMO"])

    @app.get("/health")
    def health():
        return jsonify(status="ok", model_version=CONFIG["version"], feature_version="1.11")

    @app.get("/api/bootstrap")
    def bootstrap():
        return jsonify(public_sources=source_summary(), roles=WORKSPACES, demos=DEMOS, defaults=CONFIG["default_scenario"], site_limits=SITE_LIMITS, scenario_limits=SCENARIO_LIMITS, data=json.loads((ROOT / "data/metadata.json").read_text()), evaluation=json.loads((ROOT / "reports/evaluation.json").read_text()))

    def result():
        if not request.is_json:
            raise ValueError("Send application/json input.")
        return analyze(request.get_json(), forecaster, public)

    @app.get("/api/context-settings")
    def context_settings():
        return jsonify(countries=COUNTRIES, active_countries=list(COUNTRIES), future_countries=[], defaults={code: scenario_defaults(code) for code in COUNTRIES})

    @app.get("/api/rwanda-data")
    def rwanda_data():
        return jsonify(source_summary())

    @app.get("/api/prepared-evidence")
    def prepared_evidence():
        return jsonify(prepared_summary())

    @app.get("/api/operational-models")
    def operational_models():
        return jsonify(operational_summary())

    @app.get("/api/operational-models/download")
    def operational_models_download():
        evidence = operational_summary()
        if evidence["status"] != "trained_exploratory":
            return jsonify(error=evidence["reason"]), 503
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            write_operational_archive(z, evidence)
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True,
                         download_name="gridsight-real-hourly-data-and-model-results.zip")

    @app.get("/api/prepared-evidence/download")
    def prepared_evidence_download():
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            write_prepared_archive(z, prepared_summary())
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True,
                         download_name="gridsight-prepared-evidence.zip")

    @app.post("/api/location-project")
    def location_project():
        if not request.is_json:
            raise ValueError("Send application/json input.")
        return jsonify(initial_project(request.get_json()))

    @app.get("/api/rwanda-data/download")
    def rwanda_download():
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("source_manifest.json", json.dumps(source_summary(), indent=2))
            # Government reuse terms are unspecified: include its source link/status,
            # not the raw government extract in a redistributable download.
            for name in ("buildings.meta.json", "facilities.json"):
                if (DATA / name).exists():
                    z.write(DATA / name, name)
            z.writestr("README.txt", "GridSight Rwanda public evidence pack. Building points are supplied separately in the local numeric index; this compact download contains their metadata, OSM facility objects and source status. Google Open Buildings: CC BY 4.0, https://sites.research.google/gr/open-buildings/. OSM contributors: ODbL 1.0, https://www.openstreetmap.org/copyright; preserve attribution and share-alike obligations. This is not meter data or validated demand. Uncollected layers are not represented as collected. MININFRA raw records omitted pending reuse terms.\n")
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True, download_name="gridsight-rwanda-public-data.zip")

    @app.get("/api/rwanda-data/buildings")
    def rwanda_buildings():
        path = DATA / "buildings.npz"
        if not path.exists():
            return jsonify(error="Building index not collected."), 404
        return send_file(path, as_attachment=True, download_name="gridsight-rwanda-building-detections.npz")

    @app.get("/api/locations")
    def locations():
        return jsonify(public.locations(request.args.get("q", ""), request.args.get("country", "RW")))

    @app.get("/api/geography")
    def geography():
        return jsonify(browse(request.args.get("country", "RW"), request.args.get("parent") or None,
                              request.args.get("kind", "areas"), request.args.get("q", ""), int(request.args.get("offset", "0"))))

    @app.get("/api/geography/location")
    def geography_location():
        return jsonify(public_location(request.args.get("country", "RW"), request.args.get("id")))

    @app.get("/api/public-data")
    def public_data():
        return jsonify(public.public_context(request.args.get("country", "RW")))

    @app.post("/api/prepare-inputs")
    def prepare_inputs():
        return jsonify(prepare_thin_inputs(request.get_json()))

    @app.get("/api/meter-sharing-proposal")
    def meter_sharing_proposal():
        return Response(sharing_text(), mimetype="text/plain", headers={"Content-Disposition": "attachment; filename=gridsight-meter-sharing-proposal.txt"})

    @app.get("/api/validation-template")
    def validation_template():
        return Response(",".join(COLUMNS) + "\n", mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=gridsight-meter-template.csv"})

    @app.post("/api/validate-consumption")
    def validate_consumption():
        return jsonify(compare_consumption(request.get_json(), forecaster))

    @app.get("/api/validation-sources")
    def validation_sources():
        return jsonify(json.loads((ROOT / "data/validation/source_catalog.json").read_text()))

    @app.get("/api/monthly-validation-template")
    def monthly_validation_template():
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("site_inputs.json", json.dumps(blank_manifest(), indent=2))
            z.writestr("monthly_meter_totals.csv", ",".join(MONTHLY_COLUMNS) + "\n")
            z.write(ROOT / "docs/MONTHLY_VALIDATION.md", "README.md")
            z.write(ROOT / "data/validation/source_catalog.json", "public_source_review.json")
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True,
                         download_name="gridsight-monthly-validation-starter.zip")

    @app.post("/api/validate-monthly")
    def validate_monthly():
        if not request.is_json:
            raise ValueError("Send application/json input.")
        comparison = compare_monthly(request.get_json())
        return jsonify(**comparison, comparisons_csv=comparisons_csv(comparison))

    @app.post("/api/forecast-uncertainty")
    def forecast_uncertainty():
        body = request.get_json()
        if not isinstance(body, dict) or set(body) != {"project", "settings"}:
            raise ValueError("Send a project and uncertainty settings.")
        return jsonify(planning_uncertainty(analyze(body["project"], forecaster, public), body["settings"]))

    @app.get("/api/confidence-study-template")
    def confidence_study_template():
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("site_inputs.json", json.dumps(blank_manifest(), indent=2))
            z.writestr("monthly_meter_totals.csv", ",".join(MONTHLY_COLUMNS) + "\n")
            z.writestr("study_plan.json", json.dumps(blank_plan(), indent=2))
            z.write(ROOT / "docs/CONFIDENCE_AND_GROWTH.md", "README.md")
            z.write(ROOT / "docs/MONTHLY_VALIDATION.md", "MONTHLY_DATA_CONTRACT.md")
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True,
                         download_name="gridsight-confidence-growth-starter.zip")

    @app.post("/api/confidence-study")
    def run_confidence_study():
        comparison = confidence_study(request.get_json())
        return jsonify(**comparison, comparisons_csv=study_csv(comparison))

    @app.post("/api/analyze")
    def forecast():
        return jsonify(result())

    @app.get("/api/update-template")
    def update_template():
        spec = {"release": blank_release(), "policy": blank_policy(), "plan": blank_plan()}
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("release_spec.json", json.dumps(spec, indent=2))
            z.writestr("site_inputs.json", json.dumps(blank_manifest(), indent=2))
            z.writestr("monthly_meter_totals.csv", ",".join(MONTHLY_COLUMNS) + "\n")
            z.writestr("update_request.json", json.dumps({**spec, "manifest": blank_manifest(), "csv": ""}, indent=2))
            z.write(ROOT / "docs/REAL_DATA_UPDATES.md", "READ_ME.md")
            z.write(ROOT / "docs/MONTHLY_VALIDATION.md", "MONTHLY_DATA_CONTRACT.md")
            z.write(ROOT / "docs/CONFIDENCE_AND_GROWTH.md", "CONFIDENCE_PROTOCOL.md")
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True, download_name="gridsight-real-data-update-starter.zip")

    @app.post("/api/evaluate-update")
    def evaluate_update():
        # HTTP evaluation cannot accept a forged preparation or mutate a registry.
        return jsonify(evaluate_candidate(request.get_json()))

    @app.get("/api/financial-benchmarks")
    def financial_benchmarks():
        return jsonify(CATALOG)

    @app.post("/api/financial-evidence-template")
    def financial_evidence_template():
        r = result()
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("evidence.json", json.dumps(financial_template(r), indent=2))
            z.writestr("applied_input_guide.json", json.dumps(financial_fields(r), indent=2))
            z.writestr("benchmark_sources.json", json.dumps(CATALOG, indent=2))
            z.write(ROOT / "docs/FINANCIAL_EVIDENCE.md", "READ_ME.md")
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True, download_name="gridsight-financial-evidence-starter.zip")

    @app.post("/api/benchmark-check")
    def check_benchmarks():
        body = request.get_json()
        if not isinstance(body, dict) or set(body) != {"project", "comparison"}:
            raise ValueError("Provide a project and benchmark comparison inputs.")
        return jsonify(benchmark_check(analyze(body["project"], forecaster, public), body["comparison"]))

    @app.post("/api/report")
    def report():
        return render_template("report.html", r=result())

    @app.get("/api/planning-settings")
    def planning_settings():
        return jsonify(defaults=PLANNING_DEFAULTS, limits=PLANNING_LIMITS, labels=PLANNING_LABELS, connection_defaults=CONNECTION_DEFAULTS, connection_limits=CONNECTION_LIMITS, detailed_defaults=DETAILED_DEFAULTS, detailed_limits=DETAILED_LIMITS, appliance_labels=APPLIANCE_LABELS, statistical_defaults=STATISTICAL_SETTINGS, uncertainty_labels=UNCERTAINTY_LABELS)

    @app.post("/api/feasibility-report")
    def feasibility_report():
        html = render_template("report.html", r=result())
        return Response(html, mimetype="text/html", headers={"Content-Disposition": "attachment; filename=gridsight-feasibility-report.html"})

    @app.post("/api/export")
    def export():
        return analysis_archive(result())

    @app.post("/api/deliverables-pack")
    def deliverables_pack():
        return analysis_archive(result(), include_deliverables=True)

    def analysis_archive(r, include_deliverables=False):
        archive = io.BytesIO()
        def csv_text(rows):
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            return out.getvalue()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("analysis.json", json.dumps(r, indent=2))
            write_prepared_archive(z, r["prepared_evidence"])
            z.writestr("financial_evidence.json", json.dumps(r["financial_evidence"], indent=2))
            z.writestr("benchmark_sources.json", json.dumps(CATALOG, indent=2))
            z.writestr("productive_use_stress.csv", csv_text(r["productive_sensitivity"]["rows"]))
            z.writestr("central_demand_estimates.csv", csv_text(r["demand_periods"]["estimates"]))
            z.writestr("financial_scenarios.csv", csv_text([{**row, "currency": r["context"]["currency"]} for row in r["finance"]["scenarios"]]))
            z.writestr("demand_scenarios.csv", csv_text([year for case in r["feasibility"]["scenarios"] for year in case["years"]]))
            z.writestr("monthly_scenarios.csv", csv_text([month for case in r["feasibility"]["scenarios"] for month in case["months"]]))
            z.writestr("monthly_growth.csv", csv_text(r["feasibility"]["monthly_growth"]))
            z.writestr("productive_options.csv", csv_text(r["feasibility"]["productive_options"]))
            z.writestr("growth_scenarios.csv", csv_text(r["growth"]))
            z.writestr("daily_profile.csv", csv_text([{"hour": h, "power_kw": kw} for h, kw in zip(r["profile"]["hours"], r["profile"]["kw"])]))
            z.writestr("report.html", render_template("report.html", r=r))
            if include_deliverables:
                z.writestr("START_HERE.html", render_template("deliverables_report.html", r=r))
                z.writestr("deliverables/status.json", json.dumps(r["delivery"], indent=2))
                z.writestr("deliverables/demand_range.csv", csv_text(r["delivery"]["periods"]))
                z.writestr("deliverables/growth_curve.csv", csv_text(r["delivery"]["months"]))
                z.writestr("deliverables/lender_explanation.txt", lender_text(r))
                z.writestr("deliverables/meter_sharing_proposal.txt", sharing_text())
                z.writestr("deliverables/operator_handover.json", json.dumps(sharing_handover(), indent=2))
                z.writestr("deliverables/validation/site_inputs.json", json.dumps(blank_manifest(), indent=2))
                z.writestr("deliverables/validation/monthly_meter_totals.csv", ",".join(MONTHLY_COLUMNS) + "\n")
                z.writestr("deliverables/validation/study_plan.json", json.dumps(blank_plan(), indent=2))
                z.write(ROOT / "docs/MONTHLY_VALIDATION.md", "deliverables/validation/MONTHLY_VALIDATION.md")
                z.write(ROOT / "docs/CONFIDENCE_AND_GROWTH.md", "deliverables/validation/CONFIDENCE_AND_GROWTH.md")
                z.write(ROOT / "data/validation/source_catalog.json", "deliverables/validation/public_source_review.json")
            if r.get("public_data"):
                z.writestr("public_context.json", json.dumps(r["public_data"], indent=2))
            if r.get("location_profile"):
                z.writestr("location_profile.json", json.dumps(r["location_profile"], indent=2))
            z.writestr("README.txt", f"GridSight scenario export. Detailed mode uses engineering scenarios; the legacy reference model was trained on synthetic data. Community inputs are {r['context']['input_origin']}. Open report.html to review or print. analysis.json includes country, location, assumed fields, units and provenance. Public national context is not consumption evidence. Growth is conditional; financial values are {r['context']['currency']}. No accuracy for the current monthly model or investment viability is established. The prepared_evidence folder contains separate public context, KIT power benchmark and source/feature summaries, not forecast validation.\n")
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True,
                         download_name="gridsight-deliverables.zip" if include_deliverables else "gridsight-analysis.zip")

    @app.get("/api/dataset/<kind>")
    def dataset(kind):
        files = {"sites": ROOT / "data/synthetic_sites.csv", "monthly": ROOT / "data/synthetic_monthly.csv", "evaluation": ROOT / "reports/evaluation.json", "test": ROOT / "reports/test_predictions.csv"}
        if kind not in files:
            return jsonify(error="Unknown dataset."), 404
        return send_file(files[kind], as_attachment=True)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("GRIDSIGHT_PORT", "8050")), debug=False)
