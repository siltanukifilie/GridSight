"""Brief 03 criterion mapping, not a predicted judge score."""


def summary(r):
    measured = r['transfer_uncertainty']['status'] == 'empirical_reference'
    ranking = r['bugesera_ranking']['status'] == 'available'
    return {
        'source': 'GEH Brief 03, pages 3–4 (Oct 30–Nov 1, 2026)',
        'notice': 'Criterion weights from the brief, not earned scores. Implemented features do not establish measured impact or partner validation.',
        'criteria': [
            {'criterion': 'Impact', 'weight_percent': 25,
             'evidence': 'Kenya/Nigeria held-out operational-site error study available.' if measured else 'Measured-site error study unavailable.',
             'gap': 'No matched Bugesera pre-build holdout. The operational study uses prior consumption and the last-month baseline outperforms Ridge. Do not present it as Rwanda accuracy or avoided capital cost.',
             'view': 'feasibility'},
            {'criterion': 'Innovation', 'weight_percent': 25,
             'evidence': '36-month connection/adoption scenarios, productive-use additions and affordability sensitivity.',
             'gap': 'Growth and affordability assumptions require measured adoption and permissioned survey evidence. A scenario band is not a calibrated Rwanda confidence interval.',
             'view': 'feasibility'},
            {'criterion': 'Sustainability', 'weight_percent': 25,
             'evidence': ('Versioned Bugesera screening, ' if ranking else '') + 'public-source provenance, reproducible exports and update-review workflow.',
             'gap': 'Agree a refresh owner and cadence, refresh dated layers, and demonstrate reduced oversizing against an engineering baseline. No realized capital savings are measured.',
             'view': 'evidence'},
            {'criterion': 'Feasibility', 'weight_percent': 15,
             'evidence': 'Local app runs with public context and explicit assumptions; operator request and blank validation pack available.',
             'gap': 'Secure operator agreement, paired pre-connection inputs and monthly metered data. Proposed sharing safeguards are not a hosted implementation.',
             'view': 'evidence'},
            {'criterion': 'Scalability', 'weight_percent': 10,
             'evidence': 'Eight EAC country selectors and separate Kenya/Nigeria transfer evidence.',
             'gap': 'A country selector is not multicountry predictive validity. Rwanda public-feature coverage is not universal. Test country-held-out performance before claiming minimal-retraining portability.',
             'view': 'locations'},
        ],
        'submission': 'Required: working prototype/model, 3-minute pitch and one-page impact estimate. This evidence checklist supports those submissions; it is not itself proof of impact or a completed pitch.',
    }
