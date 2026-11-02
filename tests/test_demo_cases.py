"""Juru test-case completeness and provenance; not field validation."""
import copy
import csv
import io
import json
import zipfile

import pytest
from app import create_app
from src.demo_cases import JURU_ID, juru_case, feature_rows
from src.domain import DEMOS, SITE_LIMITS, SCENARIO_LIMITS, SECTORS
from src.detailed_inputs import DEFAULTS as DETAILED_DEFAULTS, validate_detailed
from src.feasibility import PLANNING_DEFAULTS, validate_planning
from src.connection import DEFAULTS as CONNECTION_DEFAULTS, validate_connection
from src.prepared_evidence import sector_context
from src.bugesera_ranking import summary as ranking


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def analyze(client, project):
    response = client.post('/api/analyze', json=project)
    assert response.status_code == 200, response.text
    return response.json


def read_csv(z, name):
    return list(csv.DictReader(io.StringIO(z.read(name).decode())))


def test_preset_has_every_field_without_hidden_default_imputation():
    p = juru_case()['project']
    assert set(SITE_LIMITS) <= set(p['site'])
    assert set(p['detailed']) == set(DETAILED_DEFAULTS)
    assert set(p['assumptions']) == set(SCENARIO_LIMITS)
    assert set(p['planning']) == set(PLANNING_DEFAULTS)
    assert set(p['connection']) == set(CONNECTION_DEFAULTS)
    assert all(v is not None for v in p['planning'].values())
    assert validate_detailed(p['detailed']) == p['detailed']
    assert validate_planning(p['planning']) == p['planning']
    assert validate_connection(p['connection']) == p['connection']
    rows = feature_rows(p)
    assert len(rows) == 20
    assert [r['feature_number'] for r in rows] == list(range(1, 21))
    assert all(r['value'] is not None and r['unit'] and r['data_origin'] == 'synthetic' for r in rows)
    for group in ('appliances', 'equipment'):
        assert set(p['detailed'][group]) == set(DETAILED_DEFAULTS[group])
        for key, row in p['detailed'][group].items():
            assert set(row) == set(DETAILED_DEFAULTS[group][key])
            assert all(v > 0 for v in row.values())
    assert len(p['detailed']['agricultural_seasonality']) == 12


def test_fresh_preset_cannot_be_mutated_by_another_request():
    p = juru_case()
    p['project']['site']['households'] = 999
    assert juru_case()['project']['site']['households'] == 300


@pytest.mark.parametrize('role', ['developer', 'investor'])
def test_both_roles_have_complete_calculations_and_separate_public_context(client, role):
    p = juru_case()['project']
    before = copy.deepcopy(p)
    r = analyze(client, {**p, 'role': role})
    assert p == before
    assert r['site']['id'] == JURU_ID
    assert r['context']['input_origin'] == 'synthetic'
    assert r['context']['location']['latitude'] is None
    assert r['location_profile'] is None
    assert r['context']['grid']['status'] == 'unknown'
    assert len(r['demo_case']['features']) == len(r['feature_inventory']) == 20
    assert r['forecast']['method'] == 'detailed_bottom_up'
    assert r['forecast']['interval_level'] is None
    assert not r['delivery']['validation']['field_validated']
    assert r['forecast']['lower'] < r['forecast']['central'] < r['forecast']['upper']
    assert all(x['central'] > 0 for x in r['demand_periods']['estimates'])
    assert r['affordability']['bill_share_of_income'] > 0
    assert r['affordability']['connection_fee_income_months'] > 0
    assert all(row['dscr'] is not None for row in r['finance']['scenarios'])
    public = r['prepared_evidence']['sector_context']
    assert public['sector'] == 'Juru' and public['used_in_forecast'] is False
    features = {x['field']: x['value'] for x in public['features']}
    assert features['households_2022'] == 8508 != r['site']['households']
    assert features['milling_places_total'] is None
    assert features['metered_monthly_consumption_kwh'] is None
    assert r['bugesera_ranking']['selected_site_id'] == 'RW-Bugesera-juru'


def test_monthly_arithmetic_growth_seasonality_and_daily_reconciliation(client):
    p = juru_case()['project']
    r = analyze(client, p)
    months = r['feasibility']['monthly_growth']
    assert len(months) == 36
    assert months[0]['calendar_month'] == '2027-01'
    assert months[-1]['calendar_month'] == '2029-12'
    assert months[0]['estimated_connected_households'] == 195
    assert months[12]['estimated_connected_households'] == 231
    assert months[-1]['estimated_connected_households'] == 300
    first = months[0]
    household_daily = sum(a['units_per_household'] * a['power_w'] * a['hours_per_day'] / 1000
                          for a in p['detailed']['appliances'].values())
    assert first['households_kwh'] == pytest.approx(195 * household_daily * 365 / 12)
    assert first['mills_kwh'] == pytest.approx(2 * 5 * 4 * 365 / 12)
    for m in months:
        assert m['central'] == pytest.approx(sum(m[k + '_kwh'] for k in SECTORS))
        assert m['lower'] == pytest.approx(m['central'] * .75)
        assert m['upper'] == pytest.approx(m['central'] * 1.3)
    assert months[12]['added_productive_kwh'] > 0
    assert months[11]['added_productive_kwh'] == 0
    assert r['growth'][2]['central'] > r['growth'][1]['central'] > r['growth'][0]['central']
    assert sum(r['profile']['kw']) == pytest.approx(r['profile']['daily_kwh'])
    periods = {v['period']: v['central'] for v in r['demand_periods']['estimates']}
    assert periods['year'] == pytest.approx(sum(m['central'] for m in months[:12]))
    assert periods['week'] == pytest.approx(periods['day'] * 7)


def test_public_context_and_existing_demos_unchanged(client):
    p = juru_case()['project']
    before = sector_context(p['context']['location']), ranking()
    original = analyze(client, {'site': DEMOS[0]})
    analyze(client, p)
    assert before == (sector_context(p['context']['location']), ranking())
    assert 'demo_case' not in original
    assert analyze(client, {'site': DEMOS[0]})['forecast'] == original['forecast']


def test_preset_and_download_routes_are_complete_and_reproducible(client):
    packet = client.get('/api/demo-cases/juru')
    assert packet.status_code == 200 and packet.headers['Cache-Control'] == 'no-store'
    assert packet.json == juru_case()
    archives = [client.get('/api/demo-cases/juru/download') for _ in range(2)]
    assert all(r.status_code == 200 for r in archives)
    with zipfile.ZipFile(io.BytesIO(archives[0].data)) as a, zipfile.ZipFile(io.BytesIO(archives[1].data)) as b:
        assert a.testzip() is b.testzip() is None
        assert len(read_csv(a, 'features_20.csv')) == 20
        assert len(read_csv(a, 'synthetic_monthly_36.csv')) == 36
        assert len(read_csv(a, 'synthetic_hourly_profile.csv')) == 24
        assert len(read_csv(a, 'daily_weekly_monthly_yearly.csv')) == 4
        assert len(read_csv(a, 'financial_stress.csv')) == 4
        for name in ['features_20.csv', 'synthetic_monthly_36.csv', 'project.json', 'all_inputs.csv']:
            assert a.read(name) == b.read(name)
        for name in ['synthetic_monthly_36.csv', 'synthetic_hourly_profile.csv', 'financial_stress.csv']:
            assert all(r['is_metered'] == 'False' and r['data_origin'] == 'synthetic_engineering_scenario' for r in read_csv(a, name))
        assert b'NOT actual meter readings' in a.read('README.txt')
        assert b'demo data' in a.read('report.html')
        assert json.loads(a.read('metadata.json'))['is_metered'] is False


@pytest.mark.parametrize('route', ['/api/export', '/api/deliverables-pack'])
def test_edited_case_exports_current_values_and_retains_label(client, route):
    p = juru_case()['project']
    p['site']['households'] = 333
    p['detailed']['household_income_monthly'] = 180000
    p['context']['input_origin'] = 'user_entered'
    r = analyze(client, p)
    assert r['context']['input_origin'] == 'synthetic'
    response = client.post(route, json=p)
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.testzip() is None
        project = json.loads(z.read('juru_test_case/project.json'))
        assert project['site']['households'] == 333
        assert project['detailed']['household_income_monthly'] == 180000
        assert project['context']['input_origin'] == 'synthetic'
        assert '333 households' in json.loads(z.read('juru_test_case/metadata.json'))['scope']
        assert read_csv(z, 'juru_test_case/features_20.csv')[0]['value'] == '333'


def test_ui_assets_and_download_are_available_in_public_mode(client):
    html = client.get('/').text
    assert html.index('/static/demo-cases.js') < html.index('/static/app.js')
    assert client.get('/static/demo-cases.js').status_code == 200
    client.application.config['PUBLIC_DEMO'] = True
    try:
        assert client.get('/api/demo-cases/juru/download').status_code == 200
        assert client.post('/api/validate-monthly', json={}).status_code == 403
    finally:
        client.application.config['PUBLIC_DEMO'] = False


def test_invalid_inputs_still_surface_errors(client):
    p = juru_case()['project']
    p['detailed']['appliances']['lighting']['hours_per_day'] = 25
    response = client.post('/api/analyze', json=p)
    assert response.status_code == 400
    assert 'hours per day' in response.json['error'].lower()


def test_clean_demo_labels_preserve_data_origin_and_upgrade_old_saved_labels(client):
    p = juru_case()['project']
    assert p['site']['name'] == 'Juru demo'
    p['site']['name'] = 'Juru — synthetic test service area'
    old_label = 'Synthetic service area (not a real cell)'
    p['context']['location']['label'] = old_label
    p['context']['location']['administrative_path'][-1] = old_label
    r = analyze(client, p)
    assert r['site']['name'] == 'Juru demo'
    assert r['context']['location']['label'] == 'Demo service area (not a surveyed cell)'
    assert r['context']['location']['administrative_path'][-1] == r['context']['location']['label']
    assert r['context']['input_origin'] == r['demo_case']['data_origin'] == 'synthetic'
    assert r['demo_case']['is_metered'] is False
    assert 'generated for testing, not measured consumption' in r['demo_case']['notice']
    p['site']['name'] = 'My edited Juru case'
    assert analyze(client, p)['site']['name'] == 'My edited Juru case'
