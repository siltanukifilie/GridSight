"""Independent checks of measured residuals, scenario arithmetic and exports."""
import csv
import io
import json
import zipfile

import pytest
from app import create_app
from src.domain import DEMOS
from src.feasibility import validate_planning
from src.planning_scenarios import affordability
from src.transfer_uncertainty import DATA, summary


def test_independent_outer_sites_and_measured_coverage():
    study = summary()
    assert study['status'] == 'empirical_reference'
    with (DATA/'split_audit.csv').open() as f:
        for row in csv.DictReader(f):
            fit = set(row['fit_sites'].split('|'))
            assert row['outer_test_site'] not in fit
            assert row['calibration_site'] not in fit
            assert row['outer_test_site'] != row['calibration_site']
    with (DATA/'held_out_predictions.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 237
    assert all(r['country'] in ('KEN','NGA') for r in rows)
    for row in rows:
        actual, pred, count = [float(row[k]) for k in ('target_consumption_kwh','prediction_kwh','origin_observed_meter_count')]
        assert float(row['absolute_error_per_origin_meter']) == pytest.approx(abs(actual-pred)/count)
        assert (row['covered']=='True') == (float(row['lower_kwh'])<=actual<=float(row['upper_kwh']))
    for h in study['horizons']:
        selected = [r for r in rows if int(r['horizon_months'])==h['horizon_months']]
        sites = {r['site_id'] for r in selected}
        rate = sum(sum(r['covered']=='True' for r in selected if r['site_id']==s)/sum(r['site_id']==s for r in selected) for s in sites)/len(sites)
        assert rate == pytest.approx(h['nested_equal_site_coverage'])


def test_household_bill_uses_tariff_and_fee_without_collection_discount():
    p = validate_planning({'household_basket_kwh': 20, 'household_income_monthly': 100000,
                          'household_energy_budget_monthly': 9000, 'household_fixed_fee_monthly': 1000})
    result = affordability({'tariff':500, 'collection_rate':.5}, p, 'RWF')
    row = result['rows'][1]
    assert row['bill_monthly'] == 11000
    assert row['income_share'] == .11
    assert row['budget_gap_monthly'] == 2000
    assert row['income_screen_exceeded'] is True
    assert row['within_entered_budget'] is False
    assert result['rows'][0]['bill_monthly'] == 9000


def test_blank_and_zero_affordability_inputs():
    a = {'tariff': 0}
    assert affordability(a, validate_planning(), 'RWF')['rows'][0]['bill_monthly'] is None
    p = validate_planning({'household_basket_kwh':0, 'household_income_monthly':0, 'household_energy_budget_monthly':0})
    row = affordability(a,p,'RWF')['rows'][1]
    assert row['income_share'] is None
    assert row['within_entered_budget'] is True
    json.dumps(row,allow_nan=False)


@pytest.mark.parametrize('values',[{'household_basket_kwh':-1},{'household_income_monthly':float('nan')},
                                    {'affordability_income_share':1.1},{'household_fixed_fee_monthly':True}])
def test_invalid_inputs(values):
    with pytest.raises(ValueError): validate_planning(values)


@pytest.fixture(scope='module')
def client():
    return create_app().test_client()


def project(detailed=False):
    return {'site':DEMOS[1], 'detailed':{'enabled':detailed},
            'connection':{'enabled':True,'connection_month':'2026-11'},
            'assumptions':{'business_growth':0,'additional_mills':0,'additional_pumps':0,'additional_cold_rooms':0,
                           'capacity_kwh':1e6,'adoption_year':2},
            'planning':{'mill_monthly_cost':100, 'mill_support_cost':1000,
                        'household_basket_kwh':15,'household_energy_budget_monthly':5000}}


@pytest.mark.parametrize('detailed',[False,True])
def test_growth_and_staged_equipment_arithmetic(client,detailed):
    response = client.post('/api/analyze',json=project(detailed))
    assert response.status_code==200,response.json
    r = response.json; s = r['planning_scenarios']
    assert len(s['growth']['months'])==36
    assert len(s['growth']['years'])==9
    for y in s['growth']['years']:
        field = {'low':'low_kwh','expected':'base_kwh','high':'high_kwh'}[y['case']]
        assert y['total_kwh']==pytest.approx(sum(m[field] for m in s['growth']['months'] if m['year']==y['year']))
    assert s['growth']['empirical_interval_applied'] is False
    assert len(s['productive_growth']['months'])==324
    no_use = [m for m in s['productive_growth']['months'] if m['option']=='mill' and m['case']=='No uptake']
    assert no_use[11]['cash_after_support']==0
    assert no_use[12]['cash_after_support']==-1100
    assert no_use[13]['cash_after_support']==-100
    assert no_use[12]['extra_demand_kwh']==0
    for y in s['productive_growth']['years']:
        rows = [m for m in s['productive_growth']['months'] if m['option']==y['option'] and m['case']==y['case'] and m['year']==y['year']]
        assert y['extra_served_kwh']==pytest.approx(sum(m['extra_served_kwh'] for m in rows))
    json.dumps(r,allow_nan=False)


def test_supply_cap_and_missing_capital(client):
    p = project();p['assumptions']['capacity_kwh']=0;p['planning']['mill_support_cost']=None
    r=client.post('/api/analyze',json=p).json
    rows=r['planning_scenarios']['productive_growth']['months']
    assert all(m['extra_served_kwh']==0 for m in rows)
    assert next(m for m in rows if m['month']==13 and m['option']=='mill')['cash_after_support'] is None


def test_reports_exports_and_persistence(client):
    p = project()
    response = client.post('/api/report',json=p)
    assert response.status_code==200
    assert 'Household affordability scenarios' in response.text
    assert 'Kenya/Nigeria measured-site error ranges' in response.text
    assert client.get('/api/transfer-uncertainty').json['synthetic_rows']==0
    with zipfile.ZipFile(io.BytesIO(client.post('/api/export',json=p).data)) as z:
        assert len(list(csv.DictReader(io.StringIO(z.read('growth_36_months.csv').decode()))))==36
        assert len(list(csv.DictReader(io.StringIO(z.read('productive_growth_monthly.csv').decode()))))==324
        assert 'kenya_nigeria_uncertainty/split_audit.csv' in z.namelist()
        saved=json.loads(z.read('analysis.json'))
        assert saved['planning']['household_basket_kwh']==15
    recreated=client.post('/api/analyze',json={k:saved[k] for k in ('site','planning','context','connection','detailed','assumptions')}).json
    assert recreated['planning_scenarios']==saved['planning_scenarios']
