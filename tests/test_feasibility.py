"""Independent checks for complete scenario coverage and honest evidence limits."""
import copy
import csv
import io
import json
import zipfile
import pytest
from app import create_app
from src.domain import CONFIG, DEMOS, SECTORS, growth
from src.feasibility import PLANNING_DEFAULTS, validate_planning, monthly_outlook, build_feasibility, productive_options


def assumptions(**changes):
    return {**CONFIG['default_scenario'], 'household_growth': 0, 'business_growth': 0,
            'tariff': 100, 'collection_rate': .9, 'variable_cost': 10, 'fixed_cost': 1000,
            'debt_payment': 1000, 'capacity_kwh': 1200, 'firm_power_kw': 10000, **changes}


FORECAST = {'central': 1000, 'lower': 700, 'upper': 1500}


@pytest.mark.parametrize('hg,bg', [(0,0),(.08,.12),(-.2,-.1),(.5,.5),(-.1,.3)])
@pytest.mark.parametrize('adoption', [2,3])
def test_monthly_growth_conserves_each_annual_projection(hg,bg,adoption):
    a=assumptions(household_growth=hg,business_growth=bg,additional_mills=1,additional_pumps=2,additional_cold_rooms=1,adoption_year=adoption)
    rows=monthly_outlook(DEMOS[1], FORECAST, a)
    assert [m['month'] for m in rows] == list(range(1,37))
    annual=growth(DEMOS[1],FORECAST,a)
    for year in annual:
        group=[m for m in rows if m['year']==year['year']]
        for key in ['central','lower','upper','added_productive_kwh']:
            assert sum(m[key] for m in group)/12 == pytest.approx(year[key])
        assert all(m['lower']<=m['central']<=m['upper'] for m in group)
    assert sum(m['central'] for m in rows[:12]) == pytest.approx(12000)
    assert all(m['added_productive_kwh']==0 for m in rows if m['year']<adoption)


@pytest.mark.parametrize('rate', [-.2,0,.12])
def test_growth_direction_and_compounding_are_not_forced_up(rate):
    rows=monthly_outlook(DEMOS[0],FORECAST,assumptions(household_growth=rate,business_growth=rate))
    for before,after in zip(rows,rows[1:]):
        assert after['central']/before['central'] == pytest.approx((1+rate)**(1/12))


def test_three_cases_are_distinct_from_prediction_bounds():
    f=build_feasibility(DEMOS[0],FORECAST,assumptions(),validate_planning())
    assert [c['key'] for c in f['scenarios']] == ['low','expected','high']
    assert [c['years'][0]['average_monthly_kwh'] for c in f['scenarios']] == pytest.approx([800,1000,1300])
    assert f['scenarios'][0]['years'][0]['average_monthly_kwh'] != FORECAST['lower']
    assert f['scenarios'][2]['years'][0]['average_monthly_kwh'] != FORECAST['upper']
    for case in f['scenarios']:
        assert len(case['months'])==36 and len(case['years'])==3
        for row in case['months']:
            assert row['demand_kwh']==pytest.approx(1000*case['factor'])


def test_hand_worked_sizing_cash_and_npv():
    p=validate_planning({'project_capex':100000,'capacity_capex':60000,'discount_rate':0})
    f=build_feasibility(DEMOS[0],FORECAST,assumptions(),p)
    low,expected,high=[c['years'][0] for c in f['scenarios']]
    assert low['unused_capacity_kwh']==pytest.approx(4800)
    assert low['energy_utilization']==pytest.approx(2/3)
    assert low['idle_capital_exposure_amount']==pytest.approx(20000)
    assert expected['cash_after_debt']==pytest.approx(78000*12)
    assert high['served_kwh']==14400
    assert high['unserved_kwh']==pytest.approx(1200)
    assert high['lost_sales_amount']==pytest.approx(108000)
    assert high['cash_after_debt']==94000*12
    assert f['scenarios'][1]['three_year_npv_before_financing']==pytest.approx(79000*36-100000)
    changed=build_feasibility(DEMOS[0],FORECAST,assumptions(debt_payment=5000),p)
    assert changed['scenarios'][1]['three_year_npv_before_financing']==f['scenarios'][1]['three_year_npv_before_financing']


def test_npv_uses_end_of_month_effective_annual_discounting():
    p=validate_planning({'project_capex':100000,'discount_rate':.12})
    f=build_feasibility(DEMOS[0],FORECAST,assumptions(),p)
    expected=sum(79000/(1.12**(month/12)) for month in range(1,37))-100000
    assert f['scenarios'][1]['three_year_npv_before_financing']==pytest.approx(expected)


def test_unknown_costs_do_not_create_fake_financial_outputs():
    f=build_feasibility(DEMOS[0],FORECAST,assumptions(),validate_planning())
    assert all(c['three_year_npv_before_financing'] is None for c in f['scenarios'])
    assert all(y['idle_capital_exposure_amount'] is None for c in f['scenarios'] for y in c['years'])
    assert all(o['simple_payback_years'] is None for o in f['productive_options'])


def test_spare_energy_and_power_shortfall_can_coexist():
    f=build_feasibility(DEMOS[0],FORECAST,assumptions(capacity_kwh=100000,firm_power_kw=0),validate_planning())
    y=f['scenarios'][1]['years'][0]
    assert y['unused_capacity_kwh']>0 and y['unserved_kwh']==0
    assert y['peak_shortfall_kw']>0 and y['supply_gap']


def test_zero_capacity_zero_debt_and_zero_demand_stay_finite():
    site={**DEMOS[0],**{key:0 for key in SECTORS}}
    f=build_feasibility(site,{'central':0,'lower':0,'upper':0},assumptions(capacity_kwh=0,firm_power_kw=0,debt_payment=0),validate_planning())
    json.dumps(f,allow_nan=False)
    for case in f['scenarios']:
        for y in case['years']:
            assert y['energy_utilization'] is None and y['dscr'] is None
            assert y['unserved_kwh']==0 and y['peak_kw']==0


def test_cold_room_adoption_adds_energy_once_and_creates_peak_from_zero_site():
    site={**DEMOS[0],**{key:0 for key in SECTORS}}
    a=assumptions(additional_cold_rooms=1,adoption_year=2)
    rows=monthly_outlook(site,{'central':0,'lower':0,'upper':0},a)
    assert all(row['central']==0 for row in rows[:12])
    assert all(row['central']==500 and row['peak_kw']>0 for row in rows[12:])


def test_productive_option_cash_payback_and_capacity_are_independent():
    p=validate_planning({'mill_support_cost':360000,'mill_monthly_cost':1000})
    site=copy.deepcopy(DEMOS[0]); before=copy.deepcopy(site)
    options=productive_options(site,FORECAST,assumptions(),p)
    mill=next(o for o in options if o['key']=='mill')
    assert mill['extra_demand_kwh_month']==800
    assert mill['extra_served_kwh_month']==200
    assert mill['extra_unserved_kwh_month']==600
    assert mill['extra_revenue_amount_month']==18000
    assert mill['extra_contribution_amount_month']==15000
    assert mill['simple_payback_years']==2
    assert mill['supply_gap']
    assert [o['extra_contribution_amount_month'] for o in options]==sorted([o['extra_contribution_amount_month'] for o in options],reverse=True)
    assert site==before


@pytest.mark.parametrize('overrides',[{'capacity_kwh':0},{'tariff':0},{'collection_rate':0}])
def test_unprofitable_productive_options_have_no_payback(overrides):
    p=validate_planning({'mill_support_cost':100,'pump_support_cost':100,'cold_room_support_cost':100})
    options=productive_options(DEMOS[0],FORECAST,assumptions(**overrides),p)
    assert all(o['extra_contribution_amount_month']<=0 and o['simple_payback_years'] is None for o in options)


@pytest.mark.parametrize('bad',[[],True,{'low_factor':1.1},{'high_factor':.9},{'discount_rate':-1},{'project_capex':-1},{'project_capex':True},{'project_capex':float('nan')},{'mill_support_cost':float('inf')},{'pump_monthly_cost':None},{'discount_rate':None},{'project_capex':1,'capacity_capex':2},{'unexpected':42}])
def test_planning_input_validation(bad):
    with pytest.raises(ValueError): validate_planning(bad)


@pytest.fixture(scope='module')
def client():
    app=create_app(); app.config['TESTING']=True
    return app.test_client()


def test_settings_and_new_assets_available(client):
    assert client.get('/api/planning-settings').json['defaults']==PLANNING_DEFAULTS
    for path in ['/static/feasibility.js','/static/feasibility.css']:
        assert client.get(path).status_code==200
    page=client.get('/').text
    assert 'id="view-feasibility"' in page and 'data-view="feasibility"' in page


@pytest.mark.parametrize('role',['developer','investor'])
def test_downloadable_report_and_zip_cover_every_feature(client,role):
    body={'role':role,'site':DEMOS[1],'planning':{'project_capex':45000000,'capacity_capex':30000000,'low_factor':.6,'high_factor':1.5,'mill_support_cost':750000},'assumptions':{'additional_cold_rooms':2}}
    r=client.post('/api/analyze',json=body).json
    response=client.post('/api/feasibility-report',json=body)
    assert response.status_code==200
    assert 'attachment' in response.headers['Content-Disposition']
    html=response.text
    for heading in ['Central demand estimate','Low / expected / high range','Conditional growth','Productive-use opportunities','Over-sizing and under-sizing','Monthly financial scenarios','Reasons behind the forecast','36-month expected-demand','Evidence needed before commitment']:
        assert heading in html
    assert 'Synthetic evidence only' in html and 'not a whole-life' in html
    assert '45000000.0' in html and '750000.0' in html
    with zipfile.ZipFile(io.BytesIO(client.post('/api/export',json=body).data)) as z:
        exported=json.loads(z.read('analysis.json'))
        assert exported['planning']==r['planning'] and exported['feasibility']==r['feasibility']
        assert z.read('report.html').decode().count('Low / expected / high range')>=1
        for filename,expected_count in [('demand_scenarios.csv',9),('monthly_scenarios.csv',108),('monthly_growth.csv',36),('productive_options.csv',3)]:
            rows=list(csv.DictReader(io.StringIO(z.read(filename).decode())))
            assert len(rows)==expected_count
        monthly=list(csv.DictReader(io.StringIO(z.read('monthly_scenarios.csv').decode())))
        for row,actual in zip(monthly,[m for c in r['feasibility']['scenarios'] for m in c['months']],strict=True):
            assert float(row['cash_after_debt'])==actual['cash_after_debt']


def test_roles_share_all_new_outputs_and_legacy_payload_defaults(client):
    a=client.post('/api/analyze',json={'site':DEMOS[2]}).json
    b=client.post('/api/analyze',json={'site':DEMOS[2],'role':'investor'}).json
    assert a['planning']==PLANNING_DEFAULTS
    assert a['feasibility']==b['feasibility']


@pytest.mark.parametrize('route',['analyze','report','export','feasibility-report'])
def test_invalid_planning_rejected_on_all_output_routes(client,route):
    response=client.post('/api/'+route,json={'site':DEMOS[0],'planning':{'high_factor':float('inf')}})
    assert response.status_code==400 and response.json['error']


def test_report_download_escapes_site_text(client):
    response=client.post('/api/feasibility-report',json={'site':{**DEMOS[0],'name':'<script>attack()</script>'}})
    assert response.status_code==200
    assert '<script>attack()' not in response.text and '&lt;script&gt;' in response.text
