"""Build one canonical Bugesera sector-level feature table.

This is a public-context table, not a metered-demand table. Missing values are
preserved and source/status fields are retained for model and UI transparency.
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/prepared/bugesera_sectors.csv'
OUT_DIR = ROOT / 'data/processed'
OUT = OUT_DIR / 'bugesera_site_features.csv'
META = OUT_DIR / 'bugesera_site_features_metadata.json'

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SOURCE)
    df = df.rename(columns={'sector': 'site_name'})
    df.insert(0, 'site_id', 'RW-Bugesera-' + df['site_name'].str.strip().str.lower().str.replace(' ', '_', regex=False))
    df.insert(1, 'country', 'Rwanda')
    df.insert(2, 'district', 'Bugesera')
    df['data_origin'] = 'public_context'
    df['is_metered_demand'] = False
    df['demand_status'] = 'not_available'
    df['feature_status'] = df['label_status'].fillna('unverified')
    df.to_csv(OUT, index=False)
    metadata = {
        'table': OUT.name,
        'grain': 'one row per Bugesera sector/site candidate',
        'rows': int(len(df)),
        'columns': int(len(df.columns)),
        'source_table': str(SOURCE),
        'measured_demand_rows': 0,
        'public_context_only': True,
        'missing_value_policy': 'preserve missing values; do not replace with zero',
        'notes': [
            'OSM counts are mapped-object proxies, not complete inventories.',
            'GridFinder distance is a dated reference-point context variable.',
            'Nighttime-light values are indirect/unverified where indicated by status.',
            'Operator demand and peak-demand fields remain unavailable.',
        ],
    }
    META.write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Wrote {OUT} ({len(df)} rows, {len(df.columns)} columns)')
    print(f'Wrote {META}')

if __name__ == '__main__':
    main()
