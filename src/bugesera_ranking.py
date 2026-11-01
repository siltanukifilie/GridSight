"""Expose the existing screening ranking, checking it against pinned source data.

No sector totals enter demand or finance. Preserve the prototype's ranking and
make its neutral missing-data assumptions and grid direction explicit.
"""
import csv
import hashlib
import io
import json
import math
from .domain import ROOT
from .prepared_evidence import _sector_data, _match

RANKING = ROOT / 'data/processed/bugesera_site_priority_ranking.csv'
COMPONENTS = [
    ('access_gap_score', '2022 grid-access gap', .30),
    ('settlement_density_score', 'Building and population density', .25),
    ('economic_activity_score', 'Lights and mapped commerce', .20),
    ('productive_use_score', 'Agriculture and assumed equipment scores', .15),
    ('grid_proximity_score', 'Closer to historical grid reference', .10),
]
NOTICE = ('Public-data screening of 15 administrative sectors, not surveyed mini-grid service areas. '
          'Scores are relative to this shortlist, not demand, probability, investment suitability or verified off-grid status. '
          'Selection never changes customer counts or demand inputs.')
LIMITATIONS = [
    'Grid proximity rewards shorter distance to a historical reference point, NOT distance from a surveyed service boundary to a current utility line. Near-grid locations may be unsuitable for isolated mini-grids. Verify utility coverage and expansion plans.',
    'Mills and farming generators are missing for all sectors. The existing formula assigns each a neutral 0.5 score, adding the same 3.75 points to every total. These are scoring assumptions, not zero equipment counts or measured productive demand.',
    'Census: 2022. Buildings: 2023 over 2012 administrative boundaries. GridFinder: 2019 study / 2020 archive. Nighttime lights: indirect GEP proxy with exact VIIRS vintage unverified. OSM counts are incomplete mapped inventories.',
    'No matched metered consumption labels exist for these sectors. No score threshold establishes feasibility. Do not compare these normalized scores across countries or future refreshed cohorts.',
]
SOURCE_FIELDS = ['population_2022', 'households_2022', 'not_grid_connected_households_percent_2022',
                 'building_density_per_km2', 'nighttime_light_radiance_gep_mean_nw_cm2_sr',
                 'gridfinder_reference_point_distance_km']


def summary(location=None):
    base = {'status': 'unavailable', 'notice': NOTICE, 'limitations': LIMITATIONS,
            'rows': [], 'selected_site_id': None, 'match_basis': None,
            'used_in_forecast': False, 'method_version': 'existing-public-screening-v1',
            'components': [dict(key=k, label=l, weight=w) for k, l, w in COMPONENTS]}
    try:
        data = _sector_data()
        if data is None:
            raise ValueError('Pinned public sources unavailable')
        raw = RANKING.read_bytes()
        table = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
        source = {r['sector'].casefold(): r for r in data['rows']}
        if len(table) != 15 or len({r['site_name'].casefold() for r in table}) != 15:
            raise ValueError('Invalid sector coverage')
        def scaled(row, field, inverse=False):
            values = [r[field] for r in source.values()]
            if any(v is None for v in values):
                raise ValueError('Required scoring feature missing')
            low, high = min(values), max(values)
            score = .5 if high == low else (row[field] - low) / (high - low)
            return 1 - score if inverse else score
        rows = []
        for stored in table:
            key = stored['site_name'].casefold()
            s = source[key]
            if stored['site_id'] != 'RW-Bugesera-' + key or stored['district'] != 'Bugesera' or stored['label_status'] != 'NO_MATCHED_METER_LABELS':
                raise ValueError('Invalid identity or label')
            # The published v1 uses neutral equipment scores for all sectors.
            # Fail closed if those inputs change: a new reviewed method is needed.
            if s['milling_places_total'] is not None or s['farming_generators_total'] is not None:
                raise ValueError('Equipment inputs changed; review ranking method')
            expected = {
                'access_gap_score': scaled(s, SOURCE_FIELDS[2]),
                'settlement_density_score': .6*scaled(s, 'building_density_per_km2') + .4*scaled(s, 'population_density_per_km2'),
                'economic_activity_score': .55*scaled(s, SOURCE_FIELDS[4]) + .25*scaled(s, 'shop_count_osm') + .2*scaled(s, 'market_count_osm'),
                'productive_use_score': .5*scaled(s, 'agricultural_households_percent_2022') + .25,
                'grid_proximity_score': scaled(s, SOURCE_FIELDS[5], inverse=True),
            }
            expected['priority_score'] = 100*sum(expected[k]*w for k, _, w in COMPONENTS)
            expected.update({f: s[f] for f in SOURCE_FIELDS})
            for field, value in expected.items():
                if not math.isclose(float(stored[field]), value, rel_tol=1e-9, abs_tol=1e-8):
                    raise ValueError('Ranking is stale or changed')
            rows.append({**stored, **expected, 'priority_rank': int(stored['priority_rank']),
                         'milling_places_total': None, 'farming_generators_total': None,
                         'contributions': [dict(key=k, label=l, points=100*w*expected[k]) for k, l, w in COMPONENTS]})
        rows.sort(key=lambda r: (-r['priority_score'], r['site_name']))
        for row in rows:
            if row['priority_rank'] != 1 + sum(r['priority_score'] > row['priority_score'] for r in rows):
                raise ValueError('Rank does not match score')
        match = _match(location)
        selected = next((r for r in rows if match and r['site_name'].casefold() == match[0]), None)
        return {**base, 'status': 'available', 'rows': rows, 'source_version': data['version'],
                'ranking_sha256': hashlib.sha256(raw).hexdigest(),
                'selected_site_id': selected['site_id'] if selected else None,
                'match_basis': match[1] if selected else None,
                'sources': data['sources'],
                'method': 'Min-max normalize each feature across the 15 sectors. Density = 60% buildings + 40% population. Commerce = 55% lights + 25% shops + 20% markets. Productive-use proxy = 50% agriculture + 25% neutral mills + 25% neutral generators. Constant features score 0.5. Weighted sum × 100; tied scores share the minimum rank.'}
    except (OSError, ValueError, KeyError, TypeError, csv.Error):
        return {**base, 'reason': 'Ranking or public sources are missing, changed or inconsistent. No substitute ranking is shown.'}


def write_archive(z, packet):
    z.writestr('bugesera_ranking/method_and_sources.json', json.dumps(packet, indent=2))
    if packet['status'] != 'available':
        return
    # Serialize the verified snapshot, not an unchecked later re-read.
    out = io.StringIO()
    fields = [k for k in packet['rows'][0] if k != 'contributions']
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(packet['rows'])
    z.writestr('bugesera_ranking/sector_ranking.csv', out.getvalue())
