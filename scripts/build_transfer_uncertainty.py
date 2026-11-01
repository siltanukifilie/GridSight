"""Reproducible, retrospective Kenya/Nigeria site-transfer error study.

The outer site is excluded from BOTH fitting and inner residual calibration.
Rows are correlated months; the 90th percentile is an empirical reference,
not a distribution-free confidence or coverage guarantee.
"""
import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
NUM = ['origin_kwh_per_meter', 'prior_kwh_per_meter', 'origin_observed_meter_count']
CAT = ['site_id', 'country']
SITES = ['KEN_lomekwi', 'KEN_lorengelup', 'KEN_kalobeyei_settlement_village_3a', 'NGA_akipelai']


def equal_site_quantile(rows, level=.9):
    """Inverse weighted empirical CDF: each site contributes equal total mass."""
    data = rows.sort_values('absolute_error_per_origin_meter').copy()
    counts = data.groupby('site_id').site_id.transform('size')
    weights = 1 / counts / data.site_id.nunique()
    index = np.searchsorted(weights.cumsum().to_numpy(), level, side='left')
    return float(data.iloc[min(index, len(data)-1)].absolute_error_per_origin_meter)


def predict(train, test):
    assert set(train.site_id).isdisjoint(test.site_id)
    pre = ColumnTransformer([
        ('num', SimpleImputer(strategy='median'), NUM),
        ('cat', OneHotEncoder(handle_unknown='ignore'), CAT),
    ])
    # Preserve Step 4's fixed model; no tuning or choice on this test set.
    model = make_pipeline(pre, Ridge(alpha=1.0))
    model.fit(train[NUM + CAT], train.target_consumption_kwh / train.origin_observed_meter_count)
    return np.maximum(0, model.predict(test[NUM + CAT])) * test.origin_observed_meter_count.to_numpy()


def residuals(train, test):
    out = test[['site_id', 'country', 'forecast_origin_month', 'target_month',
                'horizon_months', 'origin_observed_meter_count', 'origin_month_kwh',
                'target_consumption_kwh']].copy()
    out['prediction_kwh'] = predict(train, test)
    out['absolute_error_kwh'] = abs(out.prediction_kwh - out.target_consumption_kwh)
    out['absolute_error_per_origin_meter'] = out.absolute_error_kwh / out.origin_observed_meter_count
    out['persistence_error_kwh'] = abs(out.origin_month_kwh - out.target_consumption_kwh)
    return out


def load_data(source):
    db = duckdb.connect()
    df = db.execute('SELECT * FROM read_parquet(?)', [str(source/'operational_forecasting.parquet')]).df()
    panel = db.execute('SELECT * FROM read_parquet(?)', [str(source/'site_month_panel.parquet')]).df()
    db.close()
    assert not df.duplicated(['site_id','forecast_origin_month','horizon_months']).any()
    assert not panel.duplicated(['site_id','month']).any()
    qualified = panel.set_index(['site_id','month'])
    for row in df.itertuples():
        origin = qualified.loc[(row.site_id, row.forecast_origin_month)]
        target = qualified.loc[(row.site_id, row.target_month)]
        assert origin.data_quality_status == target.data_quality_status == 'QUALIFIED_MEASURED'
        assert np.isclose(row.target_consumption_kwh, target.total_consumption_kwh)
        assert np.isclose(row.origin_month_kwh, origin.total_consumption_kwh)
        assert row.origin_observed_meter_count == origin.observed_meter_count
        assert (row.target_month.year-row.forecast_origin_month.year)*12+row.target_month.month-row.forecast_origin_month.month == row.horizon_months
        if pd.notna(row.prior_month_kwh):
            prior = qualified.loc[(row.site_id, row.forecast_origin_month-pd.DateOffset(months=1))]
            assert prior.data_quality_status == 'QUALIFIED_MEASURED'
            assert np.isclose(row.prior_month_kwh, prior.total_consumption_kwh)
    df = df[df.site_id.isin(SITES)].copy()
    assert (df.origin_observed_meter_count > 0).all()
    df['origin_kwh_per_meter'] = df.origin_month_kwh / df.origin_observed_meter_count
    df['prior_kwh_per_meter'] = df.prior_month_kwh / df.origin_observed_meter_count
    return df


def run(source, output):
    df = load_data(source)
    outer, audits = [], []
    for horizon, part in df.groupby('horizon_months'):
        for held in sorted(part.site_id.unique()):
            train, test = part[part.site_id != held], part[part.site_id == held]
            inner = []
            for calibration_site in sorted(train.site_id.unique()):
                fit = train[train.site_id != calibration_site]
                cal = train[train.site_id == calibration_site]
                assert held not in set(fit.site_id) | set(cal.site_id)
                inner.append(residuals(fit, cal))
                audits.append({'horizon_months': int(horizon), 'outer_test_site': held,
                               'calibration_site': calibration_site, 'fit_sites': '|'.join(sorted(fit.site_id.unique())),
                               'fit_rows': len(fit), 'calibration_rows': len(cal)})
            cal = pd.concat(inner, ignore_index=True)
            q = equal_site_quantile(cal)
            out = residuals(train, test)
            out['calibration_sites'] = cal.site_id.nunique()
            out['calibration_rows'] = len(cal)
            out['radius_kwh_per_origin_meter'] = q
            out['lower_kwh'] = np.maximum(0, out.prediction_kwh - q*out.origin_observed_meter_count)
            out['upper_kwh'] = out.prediction_kwh + q*out.origin_observed_meter_count
            out['covered'] = out.target_consumption_kwh.between(out.lower_kwh, out.upper_kwh)
            outer.append(out)
    predictions = pd.concat(outer, ignore_index=True)
    metrics = []
    for (h, site), group in predictions.groupby(['horizon_months','site_id']):
        metrics.append({'horizon_months': int(h), 'site_id': site, 'test_rows': len(group),
                        'mae_kwh': float(group.absolute_error_kwh.mean()),
                        'persistence_mae_kwh': float(group.persistence_error_kwh.mean()),
                        'coverage': float(group.covered.mean()),
                        'mean_width_kwh': float((group.upper_kwh-group.lower_kwh).mean()),
                        'actual_mean_kwh': float(group.target_consumption_kwh.mean()),
                        'calibration_sites': int(group.calibration_sites.iloc[0])})
    horizons = []
    for h, group in predictions.groupby('horizon_months'):
        site_metrics = [m for m in metrics if m['horizon_months'] == h]
        horizons.append({'horizon_months': int(h), 'rows': len(group), 'sites': group.site_id.nunique(),
                         'radius_kwh_per_origin_meter': equal_site_quantile(group),
                         'nested_equal_site_coverage': float(np.mean([m['coverage'] for m in site_metrics])),
                         'nested_row_coverage': float(group.covered.mean()),
                         'equal_site_mae_kwh': float(np.mean([m['mae_kwh'] for m in site_metrics])),
                         'equal_site_persistence_mae_kwh': float(np.mean([m['persistence_mae_kwh'] for m in site_metrics]))})
    protocol = {
        'schema': 'kenya-nigeria-transfer-errors-v1', 'status': 'empirical_reference',
        'runtime_versions': {name: version(name) for name in ['duckdb','numpy','pandas','scikit-learn']},
        'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'nominal_error_quantile': .9, 'site_metrics': metrics, 'horizons': horizons,
        'source': 'Renewvia / Zenodo record 22149102; local qualified monthly aggregates',
        'license': 'CC-BY-SA-4.0 according to supplied source manifest; derived results attributed to Renewvia',
        'model': 'Fixed Step 4 normalized Ridge(alpha=1); predictions clipped at zero',
        'method': 'Nested leave-one-site-out; inner calibration excludes the outer test site. Equal total weight per calibration site; absolute error / origin observed-meter count.',
        'temporal_scope': 'Retrospective site transfer. Other-site records may postdate a test origin. Not a chronological deployment backtest.',
        'reference_radius_scope': 'Pooled outer residual quantile for subsequent operational experiments. Nested coverage tests separately fitted radii; no independent evaluation of pooled radii.',
        'notice': 'Empirical operational error ranges from Kenya/Nigeria. Requires observed consumption history and origin meter counts. Does not calibrate Bugesera greenfield demand or 24–36 month growth. Months are correlated; only 3–4 sites per horizon, and qualified totals can include reconstructed intervals. 90th-percentile errors do not guarantee 90% coverage.',
        'source_hashes': {name: hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ['operational_forecasting.parquet','site_month_panel.parquet']},
        'synthetic_rows': 0, 'rwanda_validation_sites': 0,
    }
    output.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output/'held_out_predictions.csv', index=False)
    pd.DataFrame(metrics).to_csv(output/'site_metrics.csv', index=False)
    pd.DataFrame(audits).to_csv(output/'split_audit.csv', index=False)
    (output/'summary.json').write_text(json.dumps(protocol, indent=2, allow_nan=False)+'\n')
    names = ['summary.json','held_out_predictions.csv','site_metrics.csv','split_audit.csv']
    (output/'inventory.json').write_text(json.dumps({n:hashlib.sha256((output/n).read_bytes()).hexdigest() for n in names}, indent=2)+'\n')
    print(json.dumps(horizons, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'data/transfer_uncertainty')
    args = parser.parse_args()
    run(args.source, args.output)
