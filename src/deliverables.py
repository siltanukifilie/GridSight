"""User-visible deliverables and a non-operational meter-sharing proposal."""
import hashlib
import json
from .domain import LABELS, baseline_components

SHARING_PROPOSAL = {
    "title": "Safe meter-data sharing proposal",
    "status": "Proposal only — no operator integration or hosted secure portal exists",
    "steps": [
        {"title": "Agree the purpose and authority", "detail": "Operator and project owner approve the evaluation purpose, permitted fields, recipients, retention period and deletion process before sharing. Confirm applicable requirements with the responsible data-protection/legal owner; this proposal is not compliance certification."},
        {"title": "Aggregate at the operator", "detail": "Keep raw customer readings with the operator. Export site-level totals only. Exclude names, phone numbers, meter/account IDs, household coordinates, payment records and interval-level household traces. Review small sites and rare business combinations for disclosure risk; merge or withhold unsafe groups."},
        {"title": "Use protected site identifiers", "detail": "Assign random study site IDs. Keep the mapping to real locations with the operator, separate from the evaluation extract. Replacing names with codes does not guarantee anonymity. Limit country, timing and customer-group details to what the approved study needs."},
        {"title": "Freeze independent holdouts", "detail": "Before training or tuning, split by entire site, ideally also operator. Never put months from one site into both training and test sets. Record the split manifest, model/data versions, coverage, outages, connection dates and input timing. Do not tune on the final held-out results."},
        {"title": "Transfer only approved aggregates", "detail": "Proposed hosted workflow: authenticated, encrypted transfer to a restricted research workspace, named access, audit logs and a fixed deletion deadline. Those controls are not implemented here. This MVP processes the approved CSV locally in memory, does not persist the upload and does not send it to public providers. Do not expose this local server publicly or upload identifiable data."},
        {"title": "Publish metrics, not customer data", "detail": "Return MAE, RMSE, weighted error and bias with site counts, exclusions and limitations. Review aggregate results before release and delete working extracts on the agreed schedule. The monthly workflow tests the current 20-input engineering forecast and growth; the older annual tool tests only the frozen reference model. Neither authenticates uploaded evidence or assigns an automatic validation pass."},
    ],
    "minimum_data": "Current detailed-model template: anonymous site IDs, EAC country codes, connection month, documented pre-connection inputs and independent development/test site lists in a JSON manifest; customer-side monthly kWh, coverage, availability and measured/estimated flags in a separate CSV. Use the monthly starter pack in Evidence. No personal/customer records or guessed missing inputs.",
    "future_curve_study": "The monthly workflow supports the first 36 service months. Growth comparisons require adjacent complete service years; missing or outage-affected months are excluded and reported. The old annual CSV template remains separate and cannot test the detailed-input curve. Real paired data and external source review are still needed.",
    "references": [
        {"title": "NIST SP 800-188: de-identification and disclosure-risk governance", "url": "https://csrc.nist.gov/pubs/sp/800/188/final"},
        {"title": "NIST Privacy Framework", "url": "https://www.nist.gov/privacy-framework"},
    ],
}


def deliverable_status(connection):
    return [
        {"name": "Location demand estimate + range", "status": "Implemented for Rwanda screening", "detail": "Mapped locations or validated Rwanda points; proxies and missing inputs are labelled. Not a guarantee of local accuracy."},
        {"name": "First-years post-connection curve", "status": "Active" if connection["enabled"] else "Available — enable in Feasibility", "detail": "36 service months, connection month, connection/appliance/use ramp and low/expected/high scenarios. Assumption-based, not metered validation."},
        {"name": "Validation on held-out metered sites", "status": "Pending genuine operator data", "detail": "Frozen annual-average comparison tool available. No matched monthly meter dataset supplied; the separate KIT power benchmark does not validate this reference forecast or ramp."},
        {"name": "Plain-language lender explanation", "status": "Implemented", "detail": "Demand drivers, adoption assumptions, downside risk and evidence gaps; baseline drivers are not causal ML attribution."},
        {"name": "Safe meter-data sharing proposal", "status": "Available — proposal only", "detail": "Operator-side aggregation, disclosure review, independent holdouts, restricted transfer and retention. Hosted security controls are not implemented."},
    ]


def lender_explanation(site, effective_site, assumptions, connection, months):
    parts = baseline_components(effective_site)
    total = sum(parts.values())
    leaders = sorted(parts, key=parts.get, reverse=True)
    messages = []
    if total:
        messages.append(f"{LABELS[leaders[0]]} account for about {parts[leaders[0]] / total:.0%} of the transparent Year 1 baseline. More customers or more equipment can increase demand, but these counts still need verification.")
    else:
        messages.append("No starting customer energy is entered. Future equipment additions are separate assumptions, not evidence of existing demand.")
    if connection["enabled"]:
        first, last = months[0], months[35]
        messages.append(f"Demand starts at about {first['central']:,.0f} kWh in service Month 1 and reaches about {last['central']:,.0f} kWh in Month 36 under this scenario. Household connections begin at {first['household_connection_fraction']:.0%} of the target and appliance use at {first['appliance_fraction']:.0%}; both reach their target in Month {connection['ramp_months']}.")
    else:
        messages.append("This view uses the earlier annual-growth reference, not a post-connection adoption curve. Enable connection growth in Feasibility to model early uptake.")
    messages.append(f"Household expansion is assumed at {assumptions['household_growth']:.0%} per year and non-household expansion at {assumptions['business_growth']:.0%}. These are editable assumptions, not measured trends. Lower use or slower adoption can reduce cash available for debt; faster use can exceed supply.")
    messages.append("Public building/service records suggest inputs, not consumption. The model was trained on synthetic data. Check actual customers, utility coverage, productive-user commitments and financing terms before relying on the result. These baseline explanations are not proven causes or exact ML feature attribution.")
    return messages


def sharing_text():
    p = SHARING_PROPOSAL
    return p["title"] + "\n" + p["status"] + "\n\n" + "\n\n".join(f"{i}. {s['title']}\n{s['detail']}" for i, s in enumerate(p["steps"], 1)) + "\n\n" + p["minimum_data"] + "\n\n" + p["future_curve_study"] + "\n\nReferences:\n" + "\n".join(r["title"] + ": " + r["url"] for r in p["references"]) + "\n"


def delivery_summary(r):
    """Package final applied outputs, never fabricate evidence or change forecasts.

    Feasibility scenarios are intentionally separate from any nominal reference
    interval. Batch validation uploads are not selected-project evidence.
    """
    cases = {c["key"]: c for c in r["feasibility"]["scenarios"]}
    growth = r["feasibility"]["monthly_growth"]
    detailed = r["detailed"]["enabled"]
    active = detailed or r["connection"]["enabled"]
    start = r.get("horizon", {}).get("first_service_month", 1) if active else None
    applied = {key: r[key] for key in ("site", "assumptions", "planning", "detailed", "connection", "context")}
    fingerprint = hashlib.sha256(json.dumps(applied, sort_keys=True, allow_nan=False).encode()).hexdigest()
    items = [dict(item) for item in r["deliverables"]]
    additions = [
        ("demand", "Available · scope limited", "available", "demand_range.csv",
         "Choose an EAC location, review missing inputs and verify grid access and customer counts."),
        ("growth", "Scenario available · calibration pending" if active else "Enable connection growth", "partial", "growth_curve.csv",
         "Collect observed first-two-year histories for calibration. " +
         ("For a separate first-years scenario, set time since connection to 0 and apply; this export retains your current horizon." if start and start > 1 else
          "Enable connection growth or the detailed inputs to model the first service years." if not active else
          "Keep the assumed trajectory separate from measured growth.")),
        ("validation", "Pending genuine operator data", "blocked", "validation/",
         "Obtain permissioned monthly meter totals and dated pre-connection inputs for independent sites; run the holdout and confidence studies."),
        ("explanation", "Available · lender review", "available", "lender_explanation.txt",
         "Review the dominant customer groups, assumed growth and downside cash with the operator."),
        ("sharing", "Available · proposal only", "available", "meter_sharing_proposal.txt",
         "Agree purpose, recipients, disclosure review and deletion date before any transfer; complete the handover worksheet."),
    ]
    for item, (key, status, state, artifact, action) in zip(items, additions):
        item.update(id=key, status=status, state=state, artifact=artifact, next_action=action)
    items[0]["detail"] = ("Country → district → sector → cell/local equivalents in the eight EAC countries. "
                           "Missing areas allow unverified name entry. Public proxy coverage is Rwanda-only; "
                           "no claim of measured demand or universal location accuracy. Low/high here are scenarios, not confidence bounds.")
    items[1]["detail"] = (
        f"36 forecast months covering service Months {start}–{start + 35}; "
        + ("not the first years after connection. " if start > 1 else "first three years after connection. ")
        + "Connection, appliance, business and agricultural assumptions are uncalibrated."
    ) if active else "36 forecast months use legacy expansion assumptions, not a post-connection adoption curve."
    items[2]["detail"] = ("The monthly comparison tests the current 20-input calculation. The separate observed-history "
                           "study fits growth, calibrates ranges and tests untouched sites. No independently reviewed metered study is attached. "
                           "Synthetic accuracy, the separate KIT hourly-power benchmark and uploaded batch results do not validate this location.")
    periods = []
    for period, label, divisor, unit in (("day", "Daily", 365, "kWh/day"), ("week", "Weekly", 365 / 7, "kWh/week"),
                                         ("month", "Monthly", 12, "kWh/month"), ("year", "Yearly", 1, "kWh/year")):
        periods.append({"period": period, "label": label, "unit": unit,
                        **{key: cases[key]["years"][0]["demand_kwh"] / divisor for key in ("low", "expected", "high")}})
    months = [{"forecast_month": i + 1, "service_month": start + i if start else None,
               "calendar_month": row.get("calendar_month"),
               **{key + "_kwh": cases[key]["months"][i]["demand_kwh"] for key in ("low", "expected", "high")}}
              for i, row in enumerate(growth)]
    checks = [
        {"step": 1, "owner": "Operator", "action": "Approve authority and aggregate customer-side monthly kWh; review small-site disclosure risk."},
        {"step": 2, "owner": "Operator + analyst", "action": "Pair stable study IDs with documented inputs collected before connection; record gaps, outages and commissioning month."},
        {"step": 3, "owner": "Analyst", "action": "Freeze whole-site development/calibration/test splits and acceptance thresholds before reviewing outcomes. Never split one site's months across sets."},
        {"step": 4, "owner": "Analyst", "action": "Run Test the current forecast: report MAE, RMSE, WAPE, bias, site counts and exclusions. Use actual calendar-month energy units."},
        {"step": 5, "owner": "Analyst", "action": "Run Calibrate confidence & growth on separate fit/calibration/test sites; report coverage and width plus first-24-month growth error. A 24-month study does not validate Year 3."},
        {"step": 6, "owner": "Independent reviewer", "action": "Review source authority, leakage, representativeness and errors before attaching results or making accuracy claims. No automatic approval."},
    ]
    return {"schema": "gridsight-deliverables-v1", "generated_at": r["provenance"]["generated_at"],
            "project": r["site"]["name"], "country": r["context"]["country"],
            "location": r["context"].get("location"), "input_origin": r["context"]["input_origin"],
            "input_sha256": fingerprint, "items": items, "periods": periods, "months": months,
            "range_basis": "Low / expected / high feasibility scenarios, not a statistically calibrated confidence range.",
            "period_basis": "Forecast Year 1 averages: 365 days, 365/7 weeks and 12 standard months. Daily/weekly values are not timed load forecasts.",
            "horizon": {"first_service_month": start, "last_service_month": start + 35 if start else None,
                        "starts_at_connection": start == 1, "postconnection_enabled": active},
            "validation": {"status": "No independently reviewed metered study attached", "field_validated": False,
                           "verified_test_sites": None, "mae_kwh": None, "coverage_pct": None,
                           "steps": checks, "batch_notice": "Upload studies are separate, user-attested batches. Download their results separately; they do not certify this project."},
            "explanation": list(r["lender_explanation"]), "drivers": r["components"],
            "driver_basis": "Calculated energy contributions, not causal effects." if detailed else "Transparent baseline contributions, not an exact ML attribution.",
            "notice": "Prototype deliverables, not proof of field accuracy, financial viability or investment approval. Templates contain no measured results."}


def lender_text(r):
    d = r["delivery"]
    return (f"GridSight · Lender explanation\nProject: {d['project']} · {d['country']}\n"
            f"Inputs: {d['input_origin']}\nInput fingerprint: {d['input_sha256']}\n\n{d['notice']}\n\n"
            + "\n\n".join(d["explanation"]) + "\n\n" + d["range_basis"] + "\n\n"
            + d["driver_basis"] + "\n" + "\n".join(f"{c['label']}: {c['kwh']:,.1f} kWh/month ({c['share']:.1%})" for c in d["drivers"])
            + "\n\nEvidence status: " + d["validation"]["status"] + "\n")


def sharing_handover():
    """A blank planning worksheet, not a signed agreement or security control."""
    return {"schema": "gridsight-sharing-handover-v1", "status": "Blank proposal worksheet — not authorization",
            "purpose": None, "operator_permission_reference": None, "permitted_fields": None,
            "authorized_recipient_roles": [], "disclosure_review_reference": None,
            "transfer_method_approved_by_operator": None, "retention_end_date": None,
            "deletion_owner_role": None, "publication_review_reference": None,
            "incident_contact_role": None, "revocation_process": None,
            "warning": "Keep raw customer data and site-ID mappings with the operator. Do not put names, credentials, customer IDs or sensitive records in this worksheet. No hosted secure portal is implemented."}
