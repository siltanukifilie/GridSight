"""Actual snapshot integration checks; no invented observations or model training."""
import csv
import hashlib
import io
import json
import shutil
import zipfile

import pytest
from app import create_app
from src import operational_evidence as oe
from src.domain import DEMOS


@pytest.fixture(scope='module')
def client():
    return create_app().test_client()


def test_actual_model_results_and_separate_scope():
    o = oe.summary()
    assert o['status']=='trained_exploratory'
    assert o['counts']=={'train':1013,'validation':267,'test':260}
    assert o['data_rows']==1540 and o['candidate_fits']==66 and o['families_per_site']==8
    assert len(o['test_metrics'])==len(o['validation_metrics'])==24
    assert len(o['feature_dictionary'])==20
    assert not o['used_in_planning_forecast'] and not o['live_inference']
    assert 'not Bugesera' in o['notice'] and 'outside East Africa' in o['notice']
    expected={'RW_ECOS':('ridge',0.03951708295567686,1.2456768167003152),
              'CD_IDJWI':('persistence',0.19983531163695567,6.67474096021704),
              'HT_BEAUMONT':('extra_trees',0.04007829464990664,28.31278277862899)}
    for s in o['sites']:
        family,mae,wape=expected[s['site_id']]
        assert s['selected']['family']==family
        assert s['selected']['mae_kw']==pytest.approx(mae)
        assert s['selected']['wape_pct']==pytest.approx(wape)
        assert len(s['test_preview'])==8
        assert all(r['forecast_origin_utc']<r['target_end_utc'] for r in s['test_preview'])
    assert o['source']['license']=='CC BY 4.0'


def test_actual_rf_and_gradient_boosting_scores():
    scores={(m['site_id'],m['family']):m for m in oe.summary()['test_metrics']}
    assert scores['RW_ECOS','random_forest']['wape_pct']==pytest.approx(1.7053401399249395)
    assert scores['RW_ECOS','gradient_boosting']['wape_pct']==pytest.approx(1.8476903212401103)
    for site in oe.SITES:
        assert scores[site,'random_forest']['mae_kw']<scores[site,'gradient_boosting']['mae_kw']


def test_actual_readings_match_feature_rows_and_not_predictions():
    features={r['row_id']:r for r in csv.DictReader((oe.DATA/'operational_features.csv').open())}
    predictions=list(csv.DictReader((oe.DATA/'predictions.csv').open()))
    for row in predictions:
        assert float(row['actual_power_kw'])==float(features[row['row_id']]['target_power_kw'])
        assert row['split']==features[row['row_id']]['split']
    assert any(float(r['actual_power_kw'])!=float(r['prediction_kw']) for r in predictions)


def test_api_and_download_are_public_results_not_live_inference(client):
    response=client.get('/api/operational-models')
    assert response.status_code==200 and response.json['status']=='trained_exploratory'
    response=client.get('/api/operational-models/download')
    assert response.status_code==200
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.testzip() is None
        features=list(csv.DictReader(io.StringIO(z.read('operational_models/operational_features.csv').decode())))
        assert len(features)==1540 and all(r['target_power_kw']!='' for r in features)
        assert any(r['power_lag_24h_kw']=='' for r in features)
        assert not any(name.endswith(('.joblib','.pkl')) for name in z.namelist())
        assert 'CC BY 4.0' in z.read('operational_models/README.txt').decode()
        inv=json.loads(z.read('operational_models/inventory.json'))
        for row in inv['files']:
            assert hashlib.sha256(z.read('operational_models/'+row['bundled'])).hexdigest()==row['sha256']
    assert client.post('/api/operational-models',json={}).status_code==405


@pytest.mark.parametrize('role',['developer','investor'])
def test_planning_remains_separate_and_exports_include_data(client,role,monkeypatch):
    body={'role':role,'site':DEMOS[0],'detailed':{'enabled':True}}
    a=client.post('/api/analyze',json=body).json
    assert a['prepared_evidence']['operational_models']['status']=='trained_exploratory'
    assert a['delivery']['validation']['field_validated'] is False
    assert a['forecast']['interval_level'] is None
    assert a['forecast']['method']=='detailed_bottom_up'
    monkeypatch.setattr(oe,'_bundle',lambda:(None,None))
    b=client.post('/api/analyze',json=body).json
    for key in ('forecast','finance','growth','site','feasibility','profile'):
        assert a[key]==b[key]
    assert b['prepared_evidence']['operational_models']['status']=='unavailable'


@pytest.mark.parametrize('route',['/api/export','/api/deliverables-pack'])
def test_reports_and_project_zip_retain_model_context(client,route):
    response=client.post(route,json={'site':DEMOS[0],'detailed':{'enabled':True}})
    assert response.status_code==200
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.testzip() is None
        assert 'operational_models/operational_features.csv' in z.namelist()
        assert 'operational_models/predictions.csv' in z.namelist()
        html=z.read('report.html').decode()
        for value in ('Completed real-data hourly model comparison','Ridge regression','Random Forest','Gradient Boosting',
                      '0.0395','1.25','not whole sites','monthly pre-construction','CC BY 4.0'):
            assert value in html


@pytest.mark.parametrize('damage',['missing','tampered','malformed_with_new_hash'])
def test_fail_closed_when_snapshot_changes(client,tmp_path,monkeypatch,damage):
    copied=tmp_path/'data';shutil.copytree(oe.DATA,copied)
    target=copied/'metrics.csv'
    if damage=='missing':target.unlink()
    else:target.write_text('site_id,mae_kw\nRW_ECOS,NaN\n')
    if damage=='malformed_with_new_hash':
        inv=json.loads((copied/'inventory.json').read_text())
        next(r for r in inv['files'] if r['bundled']=='metrics.csv')['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        (copied/'inventory.json').write_text(json.dumps(inv))
    monkeypatch.setattr(oe,'DATA',copied)
    assert oe.summary()['status']=='unavailable'
    assert client.get('/api/operational-models/download').status_code==503


def test_public_upload_guards_unchanged(client):
    original=client.application.config['PUBLIC_DEMO'];client.application.config['PUBLIC_DEMO']=True
    try:
        for name in ('validate-consumption','validate-monthly','confidence-study','evaluate-update'):
            assert client.post('/api/'+name,json={}).status_code==403
        assert client.get('/api/operational-models/download').status_code==200
    finally:client.application.config['PUBLIC_DEMO']=original
