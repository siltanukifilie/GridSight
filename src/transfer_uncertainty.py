"""Read verified retrospective operational error evidence without model loading."""
import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data/transfer_uncertainty'
FILES = ('summary.json', 'held_out_predictions.csv', 'site_metrics.csv', 'split_audit.csv')


def summary():
    try:
        inventory = json.loads((DATA/'inventory.json').read_text())
        for name in FILES:
            if hashlib.sha256((DATA/name).read_bytes()).hexdigest() != inventory[name]:
                raise ValueError('Changed error study')
        result = json.loads((DATA/'summary.json').read_text())
        if result['schema'] != 'kenya-nigeria-transfer-errors-v1':
            raise ValueError('Unsupported error study')
        return result
    except (OSError, ValueError, KeyError, TypeError):
        return {'status': 'unavailable', 'horizons': [], 'site_metrics': [],
                'notice': 'Measured error study unavailable or changed; rebuild the verified study.'}


def write_archive(archive, evidence):
    archive.writestr('kenya_nigeria_uncertainty/ATTRIBUTION.txt',
        'Source: Nicholas Selby / Renewvia Solar Africa, High-Frequency, Multi-Domain '
        'Operational Dataset for Community Solar Mini-Grids in Kenya and Nigeria.\n'
        'https://doi.org/10.5281/zenodo.22149102\n'
        'Source and derived data: CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/\n'
        'GridSight transformations: qualified monthly aggregates, site-held-out predictions, '
        'error ranges and split diagnostics. Targets can include reconstructed intervals. '
        'Preserve attribution and share-alike obligations. No source-author endorsement.\n'
        'Operational history is required; this is not pre-build Rwanda validation.\n')
    archive.writestr('kenya_nigeria_uncertainty/summary.json', json.dumps(evidence, indent=2, allow_nan=False))
    if summary()['status'] != 'unavailable':
        for name in FILES[1:] + ('inventory.json',):
            archive.write(DATA/name, 'kenya_nigeria_uncertainty/'+name)
