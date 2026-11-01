"""Ranking plumbing and proposal safety, not validation of suitability."""
import copy
import csv
import io
import json
import zipfile
import pytest
from app import create_app
from src import bugesera_ranking as ranking
from src.domain import DEMOS


@pytest.fixture(scope='module')
def client():
    return create_app().test_client()


def test_existing_order_and_score_decomposition():
    packet = ranking.summary()
    assert packet['status'] == 'available'
    assert [r['site_name'] for r in packet['rows'][:3]] == ['Juru', 'Ntarama', 'Ruhuha']
    assert len(packet['rows']) == 15
    assert packet['used_in_forecast'] is False
    assert sum(c['weight'] for c in packet['components']) == pytest.approx(1)
    for r in packet['rows']:
        assert sum(c['points'] for c in r['contributions']) == pytest.approx(r['priority_score'])
        assert r['milling_places_total'] is r['farming_generators_total'] is None
    assert '3.75' in packet['limitations'][1]
    assert 'shorter distance' in packet['limitations'][0]
    json.dumps(packet, allow_nan=False)


@pytest.mark.parametrize('country,district,sector,expected', [
    ('RW', 'Bugesera', 'Juru', 'RW-Bugesera-juru'),
    ('KE', 'Bugesera', 'Juru', None), ('RW', 'Elsewhere', 'Juru', None),
    ('RW', 'Bugesera', 'Unmapped', None),
])
def test_hierarchy_join(country, district, sector, expected):
    p = ranking.summary({'country_code': country, 'source': 'user_entered_administration',
                         'administrative_path': [district, sector, 'Survey cell']})
    assert p['selected_site_id'] == expected


@pytest.mark.parametrize('mutation', ['score', 'rank', 'feature', 'duplicate', 'nan', 'equipment'])
def test_changed_or_inconsistent_ranking_is_not_displayed(tmp_path, monkeypatch, mutation):
    rows = list(csv.DictReader(io.StringIO(ranking.RANKING.read_text())))
    if mutation == 'equipment':
        data = copy.deepcopy(ranking._sector_data())
        data['rows'][0]['milling_places_total'] = 0
        monkeypatch.setattr(ranking, '_sector_data', lambda: data)
    else:
        if mutation == 'duplicate':
            rows[1] = rows[0].copy()
        else:
            field = {'score': 'priority_score', 'rank': 'priority_rank', 'feature': 'households_2022', 'nan': 'priority_score'}[mutation]
            rows[0][field] = 'nan' if mutation == 'nan' else '99999'
        file = tmp_path/'ranking.csv'
        with file.open('w') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        monkeypatch.setattr(ranking, 'RANKING', file)
    packet = ranking.summary()
    assert packet['status'] == 'unavailable'
    assert packet['rows'] == []


def test_missing_ranking_does_not_break_forecast(client, monkeypatch, tmp_path):
    monkeypatch.setattr(ranking, 'RANKING', tmp_path/'missing.csv')
    for route in ['/api/bugesera-ranking', '/api/bugesera-ranking/download']:
        assert client.get(route).status_code == 503
    r = client.post('/api/analyze', json={'site': DEMOS[0]}).json
    assert r['bugesera_ranking']['status'] == 'unavailable'
    assert r['forecast']['central'] > 0


def test_forged_ranking_and_partner_claims_are_ignored(client):
    body = {'site': DEMOS[0], 'bugesera_ranking': {'status': 'validated'},
            'operator_pilot': {'status': 'partner secured'}, 'assessment': {'score': 100}}
    r = client.post('/api/analyze', json=body).json
    baseline = client.post('/api/analyze', json={'site': DEMOS[0]}).json
    assert r['forecast'] == baseline['forecast']
    assert r['finance'] == baseline['finance']
    assert r['bugesera_ranking']['status'] == 'available'
    assert 'no partner agreement' in r['operator_pilot']['status']
    assert 'score' not in r['assessment']
    assert sum(c['weight_percent'] for c in r['assessment']['criteria']) == 100
    assert r['delivery']['validation']['field_validated'] is False


def test_dashboard_bootstrap_and_pilot_template(client):
    assert len(client.get('/api/bootstrap').json['bugesera_ranking']['rows']) == 15
    html = client.get('/').text
    assert html.index('/static/screening.js') < html.index('/static/app.js')
    html = client.get('/api/operator-pilot').text
    for text in ['no partner agreement', 'ARC Power', 'Minimum data', 'Approval gates', 'When to stop', 'not a signed agreement']:
        assert text in html


@pytest.mark.parametrize('route', ['/api/export', '/api/deliverables-pack'])
def test_all_exports_include_ranking_pilot_and_assessment(client, route):
    response = client.post(route, json={'site': DEMOS[0]})
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.testzip() is None
        assert len(list(csv.DictReader(io.StringIO(z.read('bugesera_ranking/sector_ranking.csv').decode())))) == 15
        assert len(json.loads(z.read('assessment_checklist.json'))['criteria']) == 5
        assert 'Brief 03 assessment checklist' in z.read('report.html').decode()
        assert 'Operator data-sharing pilot' in z.read('report.html').decode()
        assert len(z.read('operator_pilot/monthly_meter_totals.csv').decode().splitlines()) == 1
        assert json.loads(z.read('operator_pilot/operator_handover.json'))['operator_permission_reference'] is None
        assert 'No message has been sent' in z.read('operator_pilot/DRAFT_REQUEST.txt').decode()


def test_standalone_downloads_work_on_public_demo_with_no_uploads(client):
    client.application.config['PUBLIC_DEMO'] = True
    try:
        for route in ['/api/operator-pilot/download', '/api/bugesera-ranking/download']:
            response = client.get(route)
            assert response.status_code == 200
            with zipfile.ZipFile(io.BytesIO(response.data)) as z:
                assert z.testzip() is None
        assert client.post('/api/validate-monthly', json={}).status_code == 403
    finally:
        client.application.config['PUBLIC_DEMO'] = False
