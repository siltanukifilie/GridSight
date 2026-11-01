"""Public trained-experiment evidence, not a new forecasting service or model registry."""
import csv
import hashlib
import io
import json
import math

from .domain import ROOT

DATA = ROOT / 'data/operational'
FILES = ('metrics.csv', 'selected_models_test.csv', 'split_summary.csv', 'operational_features.csv',
         'predictions.csv', 'protocol.json', 'run_summary.json', 'selection_lock.json', 'verification.json',
         'feature_dictionary.csv', 'source_manifest.csv', 'source_notes.txt', 'RESULTS.txt')
SITES = {'RW_ECOS':'Rwanda ECOS', 'CD_IDJWI':'Congo Idjwi', 'HT_BEAUMONT':'Haiti Beaumont'}
FAMILIES = ('persistence','training_median','seasonal_24h','ridge','random_forest','extra_trees','gradient_boosting','svr')
NOTICE = ('Real measured-power experiment at existing sites. Later hours are held out, not whole sites. '
          'Rwanda ECOS is not Bugesera and Haiti is outside East Africa. These scores do not validate '
          'the monthly pre-construction estimate, future growth, capacity sizing or confidence intervals.')
SOURCE = {'attribution':'Luh et al., KIT / RADAR4KIT, High-Resolution Real-World Electricity Data from Three Microgrids in the Global South',
          'url':'https://doi.org/10.35097/1305', 'license':'CC BY 4.0', 'accessed_on':'2026-11-01'}


def _bundle():
    try:
        inventory = json.loads((DATA / 'inventory.json').read_text())
        hashes = {f['bundled']:f['sha256'] for f in inventory['files']}
        files = {}
        for name in FILES:
            raw = (DATA / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != hashes[name]:
                return None, None
            files[name] = raw
        return files, inventory
    except (OSError, ValueError, KeyError, TypeError):
        return None, None


def _rows(files, name):
    return list(csv.DictReader(io.StringIO(files[name].decode('utf-8'))))


def _number(value):
    n = float(value)
    if not math.isfinite(n):
        raise ValueError('Invalid experiment score')
    return n


def summary():
    base = {'status':'unavailable', 'notice':NOTICE, 'source':SOURCE, 'sites':[], 'test_metrics':[],
            'used_in_planning_forecast':False, 'live_inference':False,
            'reason':'Trained experiment data unavailable or changed. No example scores substituted.'}
    files, inventory = _bundle()
    if files is None:
        return base
    try:
        run = json.loads(files['run_summary.json'])
        protocol = json.loads(files['protocol.json'])
        lock = json.loads(files['selection_lock.json'])
        checked = json.loads(files['verification.json'])
        if (run['status'] != 'TRAINED_EXPLORATORY_NOT_DEPLOYED' or checked['status'] != 'PASS'
                or run['ml_candidate_fits'] != 66 or lock['test_read_before_selection'] is not False
                or hashlib.sha256(files['selection_lock.json']).hexdigest() != run['selection_lock_sha256']
                or hashlib.sha256(files['protocol.json']).hexdigest() != lock['protocol_sha256']):
            return base
        raw_metrics = _rows(files, 'metrics.csv')
        splits = _rows(files, 'split_summary.csv')
        features = _rows(files, 'operational_features.csv')
        predictions = _rows(files, 'predictions.csv')
        if len(raw_metrics) != 48 or len(splits) != 9 or len(features) != 1540 or len(predictions) != 4216:
            return base
        if len({r['row_id'] for r in features}) != len(features):
            return base
        metrics = []
        for row in raw_metrics:
            if row['site_id'] not in SITES or row['family'] not in FAMILIES or row['split'] not in ('validation','test'):
                return base
            if row['selected_on_validation'] not in ('True','False'):
                return base
            metrics.append({**row, **{k:_number(row[k]) for k in ('n_rows','actual_mean_kw','mae_kw','rmse_kw',
                'wape_pct','bias_kw','r2','mae_improvement_vs_persistence_pct','seasonal_fallback_rows')},
                'selected_on_validation':row['selected_on_validation']=='True'})
        if len({(m['site_id'],m['family'],m['split']) for m in metrics}) != 48:
            return base
        sites = []
        for site, label in SITES.items():
            parts = {r['split']:r for r in splits if r['site_id']==site}
            counts = {p:int(parts[p]['rows']) for p in ('train','validation','test')}
            if any(sum(r['site_id']==site and r['split']==p for r in features) != n for p,n in counts.items()):
                return base
            choice = lock['sites'][site]['selected_family']
            scores = [m for m in metrics if m['site_id']==site and m['split']=='test']
            validations = [m for m in metrics if m['site_id']==site and m['split']=='validation']
            expected = min(FAMILIES, key=lambda f:next(m['mae_kw'] for m in validations if m['family']==f))
            if choice != expected or sum(m['selected_on_validation'] for m in scores)!=1:
                return base
            chosen = next(m for m in scores if m['family']==choice and m['selected_on_validation'])
            if any(m['n_rows']!=counts['test'] for m in scores):
                return base
            test_predictions = [r for r in predictions if r['site_id']==site and r['split']=='test' and r['family']==choice]
            test_features = {r['row_id']:r for r in features if r['site_id']==site and r['split']=='test'}
            if len(test_predictions)!=counts['test'] or {r['row_id'] for r in test_predictions} != set(test_features):
                return base
            sample = []
            for row in sorted(test_predictions,key=lambda r:r['forecast_origin_utc'])[-8:]:
                sample.append({'forecast_origin_utc':row['forecast_origin_utc'],'target_end_utc':row['target_end_utc'],
                               'previous_hour_kw':_number(test_features[row['row_id']]['power_lag_1h_kw']),
                               'actual_kw':_number(row['actual_power_kw']),'prediction_kw':_number(row['prediction_kw'])})
            sites.append({'site_id':site,'label':label, 'selected':chosen, 'counts':counts,
                          'input_columns':int(parts['train']['input_columns']),
                          'test_start_utc':parts['test']['start_utc'],'test_end_utc':parts['test']['last_target_end_utc'],
                          'test_preview':sample})
        return {**base, 'status':'trained_exploratory', 'reason':None, 'version':inventory['version'],
                'sites':sites, 'test_metrics':[m for m in metrics if m['split']=='test'],
                'validation_metrics':[m for m in metrics if m['split']=='validation'],
                'data_rows':len(features),'candidate_fits':run['ml_candidate_fits'], 'families_per_site':8,
                'counts':{p:sum(s['counts'][p] for s in sites) for p in ('train','validation','test')},
                'feature_dictionary':_rows(files,'feature_dictionary.csv'), 'protocol':protocol,
                'target':'Mean delivered active power during the forthcoming hour, kW',
                'selection':'Lowest validation MAE, frozen before test scoring. Each model is fitted on training rows only.',
                'limitations':['Short 2021–2022 campaigns with faults and gaps; delivered power may be supply-constrained.',
                               'Earlier observed test readings supply later lag features. This is sequential one-hour forecasting.',
                               'Small, correlated, previously inspected test campaigns; no fresh blinded external validation or significance claim.',
                               'No single winner across sites. WAPE is error, not accuracy. No calibrated prediction intervals.',
                               'The 20 calendar/past-power predictors are not the original 20 household/business pre-construction inputs.']}
    except (ValueError, KeyError, TypeError, StopIteration, csv.Error):
        return base


def write_archive(archive, evidence=None):
    """A fixed allowlist of public data/results only. Never export/load model pickles."""
    evidence = evidence if evidence is not None else summary()
    archive.writestr('operational_models/summary.json', json.dumps(evidence,indent=2,allow_nan=False))
    files, inventory = _bundle()
    if files is not None and evidence['status']=='trained_exploratory':
        for name, raw in files.items():
            archive.writestr('operational_models/'+name, raw)
        archive.writestr('operational_models/inventory.json',json.dumps(inventory,indent=2))
    archive.writestr('operational_models/README.txt', (DATA/'README.txt').read_text() if (DATA/'README.txt').exists() else NOTICE)
