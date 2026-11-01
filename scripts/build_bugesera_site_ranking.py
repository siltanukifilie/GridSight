"""Rank Bugesera sectors for mini-grid screening using public context only."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/bugesera_site_features.csv'
OUTPUT = ROOT / 'data/processed/bugesera_site_priority_ranking.csv'

def scale(s, inverse=False):
    s = pd.to_numeric(s, errors='coerce')
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or hi == lo:
        return pd.Series(0.5, index=s.index)
    out = (s - lo) / (hi - lo)
    return 1 - out if inverse else out

def main():
    df = pd.read_csv(INPUT)
    # Public-context screening score, not a demand forecast or investment verdict.
    df['access_gap_score'] = scale(df['not_grid_connected_households_percent_2022'])
    df['settlement_density_score'] = (
        0.6 * scale(df['building_density_per_km2']) +
        0.4 * scale(df['population_density_per_km2'])
    )
    df['economic_activity_score'] = (
        0.55 * scale(df['nighttime_light_radiance_gep_mean_nw_cm2_sr']) +
        0.25 * scale(df['shop_count_osm']) +
        0.20 * scale(df['market_count_osm'])
    )
    df['productive_use_score'] = (
        0.5 * scale(df['agricultural_households_percent_2022']) +
        0.25 * scale(df['milling_places_total'].fillna(0)) +
        0.25 * scale(df['farming_generators_total'].fillna(0))
    )
    df['grid_proximity_score'] = scale(df['gridfinder_reference_point_distance_km'], inverse=True)
    df['priority_score'] = 100 * (
        0.30 * df['access_gap_score'] +
        0.25 * df['settlement_density_score'] +
        0.20 * df['economic_activity_score'] +
        0.15 * df['productive_use_score'] +
        0.10 * df['grid_proximity_score']
    )
    df['priority_rank'] = df['priority_score'].rank(method='min', ascending=False).astype(int)
    cols = ['priority_rank', 'site_id', 'site_name', 'district', 'priority_score',
            'access_gap_score', 'settlement_density_score', 'economic_activity_score',
            'productive_use_score', 'grid_proximity_score',
            'population_2022', 'households_2022',
            'not_grid_connected_households_percent_2022',
            'building_density_per_km2', 'nighttime_light_radiance_gep_mean_nw_cm2_sr',
            'gridfinder_reference_point_distance_km', 'label_status']
    df[cols].sort_values(['priority_rank', 'site_name']).to_csv(OUTPUT, index=False)
    print(f'Wrote {OUTPUT}')
    print(df[cols].sort_values('priority_rank')[['priority_rank', 'site_name', 'priority_score']].to_string(index=False))

if __name__ == '__main__':
    main()
