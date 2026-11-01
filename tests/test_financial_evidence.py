"""Invented documents test plumbing only, never real financial evidence."""
from copy import deepcopy
from datetime import date, timedelta
import io
import json
import zipfile
import pytest
from app import create_app
from src.domain import DEMOS, CONFIG, ROOT
from src.financial_evidence import template, review, benchmark_check, productive_sensitivity
from test_maintenance import request as update_fixture


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def project():
    return {"site":deepcopy(DEMOS[1]),"assumptions":deepcopy(CONFIG["default_scenario"]),
            "detailed":{"enabled":True},"planning":{"project_capex":1000000,"mill_monthly_cost":1200}}


@pytest.fixture(scope="module")
def result(client):
    response=client.post('/api/analyze',json=project())
    assert response.status_code==200,response.json
    return response.json


def packet(r):
    p=template(r);p.update(permission_confirmed=True,no_personal_data=True)
    p['records']=[{'field':'planning.project_capex','value':r['planning']['project_capex'],
                   'unit':r['context']['currency'],'kind':'quotation','source_reference':'INVENTED test document only',
                   'observed_on':date.today().isoformat(),'sample_size':1}]
    return p


def test_defaults_are_assumptions_not_site_benchmarks(result):
    e=result['financial_evidence']
    assert e['source_attached']==0 and e['independently_verified'] is False
    assert e['measured_capital_savings'] is None
    assert any(x['status']=='missing' for x in e['rows'])
    assert any(x['field']=='detailed.equipment.mills.hours_per_day' for x in e['rows'])
    assert e['benchmarks']['benchmarks'][0]['value']==1948


def test_packet_attaches_only_exact_input_without_changing_forecast(client,result):
    p=project();p['financial_evidence']=packet(result)
    r=client.post('/api/analyze',json=p).json
    assert r['financial_evidence']['source_attached']==1
    for key in ('forecast','finance','planning','productive_sensitivity'):
        assert r[key]==result[key]
    assert r['financial_evidence']['packet']==p['financial_evidence']


@pytest.mark.parametrize('change',[{'value':999},{'unit':'USD'},{'kind':[]},{'sample_size':True},{'sample_size':1.5},
    {'value':float('nan')},{'observed_on':'2099-01-01'},{'observed_on':'invalid'},{'source_reference':''},{'field':'other'}])
def test_invalid_evidence_is_rejected(result,change):
    p=packet(result);p['records'][0].update(change)
    with pytest.raises(ValueError):review(result,p)


def test_permissions_and_duplicates(result):
    p=packet(result);p['permission_confirmed']=False
    with pytest.raises(ValueError):review(result,p)
    p=packet(result);p['records']*=2
    with pytest.raises(ValueError):review(result,p)
    p=packet(result);p['unexpected']=1
    with pytest.raises(ValueError):review(result,p)


def test_changed_country_or_input_detaches_evidence(client,result):
    for changes in ({'planning':{'project_capex':2000000}},{'context':{'country_code':'KE'}},{'detailed':{'enabled':False}}):
        p={**project(),**changes,'financial_evidence':packet(result)}
        response=client.post('/api/analyze',json=p)
        assert response.status_code==200,response.json
        e=response.json['financial_evidence']
        assert e['stale_project'] and e['packet'] is None and e['source_attached']==0


def test_old_evidence_needs_review(result):
    p=packet(result);p['records'][0]['observed_on']=(date.today()-timedelta(days=366)).isoformat()
    r=review(result,p)
    row=next(x for x in r['rows'] if x['field']=='planning.project_capex')
    assert row['status']=='review_due' and r['source_attached']==0


def comparison():
    return {'connections':100,'local_currency_per_usd':1000,'fx_date':date.today().isoformat(),
            'fx_reference':'Invented rate for arithmetic test only','scope_confirmed':True}


def test_benchmark_units_and_no_double_counting(result):
    r=benchmark_check(result,comparison())
    assert r['capex_usd_per_connection']==10
    expected=result['feasibility']['scenarios'][1]['years'][0]['operating_cost']/100000
    assert r['opex_usd_per_connection_year']==pytest.approx(expected)
    assert r['costs_changed'] is False
    p=deepcopy(result);p['planning']['project_capex']=None
    assert benchmark_check(p,comparison())['capex_usd_per_connection'] is None


@pytest.mark.parametrize('change',[{'connections':0},{'connections':1.5},{'local_currency_per_usd':0},
    {'local_currency_per_usd':float('inf')},{'scope_confirmed':False},{'fx_date':'2099-01-01'},{'fx_reference':''}])
def test_invalid_benchmark_inputs(result,change):
    with pytest.raises(ValueError):benchmark_check(result,{**comparison(),**change})


def test_productive_use_cases_keep_costs_without_optimistic_uptake(result):
    r=productive_sensitivity(result)
    assert len(r['rows'])==9
    mill=[x for x in r['rows'] if x['option']=='One mill']
    assert mill[0]['extra_demand_kwh_month']==0
    assert mill[0]['grid_contribution_amount_month']==-1200
    assert mill[1]['extra_demand_kwh_month']==mill[2]['extra_demand_kwh_month']/2
    source=next(x for x in result['feasibility']['productive_options'] if x['key']=='mill')
    assert mill[2]['grid_contribution_amount_month']==pytest.approx(source['extra_contribution_amount_month'])


def test_api_packs_exports_and_escaped_report(client,result):
    p=project();p['financial_evidence']=packet(result)
    p['financial_evidence']['records'][0]['source_reference']='<script>alert(1)</script>'
    html=client.post('/api/feasibility-report',json=p).text
    assert '&lt;script&gt;' in html and '<script>alert(1)</script>' not in html
    assert 'Measured capital savings: not established' in html
    response=client.post('/api/export',json=p)
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert 'financial_evidence.json' in z.namelist() and 'productive_use_stress.csv' in z.namelist()
        assert json.loads(z.read('financial_evidence.json'))['source_attached']==1
    with zipfile.ZipFile(io.BytesIO(client.post('/api/financial-evidence-template',json=project()).data)) as z:
        assert json.loads(z.read('evidence.json'))['permission_confirmed'] is False
        assert 'detailed.equipment.mills.hours_per_day' in json.loads(z.read('applied_input_guide.json'))
    assert client.get('/api/financial-benchmarks').json['version']=='2026-11-01'
    assert client.post('/api/benchmark-check',json={'project':project(),'comparison':comparison()}).status_code==200


def test_update_template_fails_closed_and_http_cannot_freeze_or_write_registry(client):
    with zipfile.ZipFile(io.BytesIO(client.get('/api/update-template').data)) as z:
        spec=json.loads(z.read('release_spec.json'))
        assert all(v is None for v in spec['policy'].values())
        assert 'READ_ME.md' in z.namelist()
    p=update_fixture()
    response=client.post('/api/evaluate-update',json=p)
    assert response.status_code==200,response.json
    assert not response.json['predeclared_in_registry'] and not response.json['review_eligible']
    assert not response.json['serving_model_changed']
    assert 'actual_kwh' not in response.text
    assert client.post('/api/evaluate-update',json={**p,'preparation':{}}).status_code==400
    assert client.post('/api/evaluate-update',json={**p,'csv':''}).status_code==400
    assert client.post('/api/evaluate-update',json={**p,'csv':'x'*300000}).status_code==413


def test_new_static_scripts_served_and_legacy_mode_still_works(client):
    for name in ('financial-evidence','maintenance'):
        assert client.get('/static/'+name+'.js').status_code==200
        assert '/static/'+name+'.js' in client.get('/').text
    assert client.post('/api/analyze',json={**project(),'detailed':{'enabled':False}}).status_code==200
