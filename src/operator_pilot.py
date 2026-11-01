"""An operator-reviewable request; no agreement, outreach or transfer is implied."""
import json
from .domain import ROOT
from .deliverables import sharing_text, sharing_handover
from .detailed_validation import blank_manifest, COLUMNS
from .statistical import blank_plan

PILOT = {
    'title': 'Operator data-sharing pilot',
    'status': 'Draft for operator review — no partner agreement or data access secured',
    'purpose': 'Evaluate pre-build monthly demand and first-years growth for Rwanda mini-grids, then return an operator-reviewed error and downside-risk report. ARC Power or another operator may be approached; none is represented as a partner.',
    'request': 'First request a non-sensitive catalogue: number of eligible sites, countries, commissioning years, months of available site-level metered totals, and whether pre-connection surveys exist. Do not send raw readings yet. Agree the independent-site sample and disclosure rules before preparing extracts.',
    'scope': 'Ask for up to 36 complete months after connection where available, across independent sites with varied customer mixes. Less history can support shorter-horizon tests only. Sample size and development/calibration/test counts must be agreed before outcomes are inspected; a tiny pilot is exploratory, not proof of generalization.',
    'data_contract': [
        {'item': 'Study manifest', 'detail': 'Random site ID, country code, connection month, development/test membership and documented pre-connection inputs in site_inputs.json. Keep the location lookup with the operator. Record survey date and source in a separate approved provenance note; never reconstruct pre-build inputs from future consumption.'},
        {'item': 'Monthly totals', 'detail': 'One row per site/month: site_id, month (YYYY-MM), actual_kwh (customer-side monthly energy), coverage_fraction, availability_fraction, quality. Use monthly_meter_totals.csv exactly; do not substitute generation or sales revenue for customer energy.'},
        {'item': 'Quality and gaps', 'detail': 'Document meter coverage, outages, additions and estimation methods. Missing is not zero. Exclude or separately report incomplete/estimated months. Agree any small-group suppression threshold with the operator; do not invent a universal anonymity threshold.'},
        {'item': 'Optional later study', 'detail': 'Tariff, aggregated connection counts, productive-use adoption and aggregate survey spending can help later affordability/growth studies after separate approval. They are not required extra columns in the current upload template. No household income, payments or meter-level traces are requested.'},
    ],
    'gates': [
        {'stage': '1. Scope and permissions', 'owner': 'Operator data owner + project lead', 'exit': 'Approve purpose, field list, recipients, permitted outputs, retention deadline, withdrawal process and responsible contacts. No transfer while any approval is missing.'},
        {'stage': '2. Operator-side preparation', 'owner': 'Operator analyst + disclosure reviewer', 'exit': 'Aggregate, pseudonymize and review small/rare groups. Keep raw data and identity mappings at the operator. Approve the release manifest and file hashes.'},
        {'stage': '3. Protected evaluation', 'owner': 'Named analyst + independent reviewer', 'exit': 'Use an approved operator-controlled environment or agreed protected transfer. Freeze model version, whole-site splits, baseline, metrics and acceptance thresholds. The public demo accepts no meter uploads; a local prototype is not a secure portal.'},
        {'stage': '4. Return results and close', 'owner': 'Analyst + operator approver', 'exit': 'Return per-site error, baseline comparison, coverage/width, growth error, exclusions and limitations privately. Release only approved aggregates. Delete extracts/backups by the agreed deadline and record confirmation; retained results need explicit permission.'},
    ],
    'operator_value': 'A confidential demand-versus-observation review, baseline comparison, growth and oversizing-risk findings, a reproducible input-quality checklist, and review of any proposed public attribution. Participation does not require public release of commercially sensitive site data.',
    'stop_rules': 'Stop if authority, disclosure review, protected handling or retention responsibility is unresolved. Revoke access and notify the operator through the agreed incident channel if unauthorized disclosure is suspected. No onward sharing, model-training reuse or commercial reuse without specific permission.',
    'evaluation': 'Report MAE, RMSE, WAPE, signed bias, range coverage and width, sites/months and exclusions by country and horizon. Compare operational forecasts with last-month persistence; for pre-build predictions use a baseline that needs no post-connection history. Fit/calibrate on separate sites and evaluate the frozen model once on untouched sites. Do not claim Year 3 validation from only 24 months.',
}


def proposal_text():
    p = PILOT
    sections = [p['title'], p['status'], p['purpose'], 'Initial request\n' + p['request'],
                'Study scope\n' + p['scope'], 'Data contract']
    sections.extend(f"{x['item']}: {x['detail']}" for x in p['data_contract'])
    sections.append('Approval gates')
    sections.extend(f"{x['stage']} — {x['owner']}\n{x['exit']}" for x in p['gates'])
    sections.extend(['Value to the operator\n' + p['operator_value'], 'Evaluation\n' + p['evaluation'],
                     'Stop rules\n' + p['stop_rules'], sharing_text()])
    return '\n\n'.join(sections) + '\n'


def request_text():
    return ('DRAFT — review before sending. No message has been sent.\n\n'
            'Subject: Proposed operator-controlled mini-grid demand validation pilot\n\n'
            'Dear operator data team,\n\n'
            'We are developing GridSight, a mini-grid demand and growth planning prototype for Bugesera and other East African locations. '
            'We would like to discuss a limited, permissioned evaluation using independent operating sites. '
            'Our public-data screening and Kenya/Nigeria operational benchmarks do not establish pre-build Rwanda accuracy.\n\n'
            + PILOT['request'] + '\n\n' + PILOT['operator_value'] + '\n\n'
            'Raw customer records and the site-identity lookup would stay with you. We propose agreeing data minimization, '
            'protected handling, the holdout protocol, publication review and a deletion deadline before any transfer. '
            'If useful, please nominate a data owner for a scoping discussion. There is no obligation to share data.\n\n'
            'GridSight project team\n')


def write_archive(z, prefix='operator_pilot/'):
    z.writestr(prefix + 'PROPOSAL.txt', proposal_text())
    z.writestr(prefix + 'DRAFT_REQUEST.txt', request_text())
    z.writestr(prefix + 'operator_handover.json', json.dumps(sharing_handover(), indent=2))
    z.writestr(prefix + 'site_inputs.json', json.dumps(blank_manifest(), indent=2))
    z.writestr(prefix + 'monthly_meter_totals.csv', ','.join(COLUMNS) + '\n')
    z.writestr(prefix + 'study_plan.json', json.dumps(blank_plan(), indent=2))
    z.write(ROOT / 'docs/MONTHLY_VALIDATION.md', prefix + 'MONTHLY_VALIDATION.md')
    z.write(ROOT / 'docs/CONFIDENCE_AND_GROWTH.md', prefix + 'CONFIDENCE_AND_GROWTH.md')
