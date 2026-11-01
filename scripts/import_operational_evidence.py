"""Import reviewed public hourly experiment snapshots; never train or deploy models."""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'metrics.csv': 'results/metrics.csv',
    'selected_models_test.csv': 'results/selected_models_test.csv',
    'split_summary.csv': 'results/split_summary.csv',
    'operational_features.csv': 'inputs/features/operational_forecasting.csv',
    'predictions.csv': 'results/predictions.csv',
    'protocol.json': 'protocol.json',
    'run_summary.json': 'run_summary.json',
    'selection_lock.json': 'selection_lock.json',
    'verification.json': 'verification.json',
    'feature_dictionary.csv': 'inputs/metadata/operational_feature_dictionary.csv',
    'source_manifest.csv': 'inputs/metadata/meter_source_manifest.csv',
    'source_notes.txt': 'inputs/metadata/KIT_source_notes.txt',
    'RESULTS.txt': 'RESULTS.txt',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(source):
    inventory = {row['file']: row for row in csv.DictReader((source / 'file_inventory.csv').open())}
    # Validate every source before writing any snapshot. The upstream pack is read-only.
    for rel in FILES.values():
        if sha(source / rel) != inventory[rel]['sha256']:
            raise ValueError(f'Changed experiment source: {rel}')
    out = ROOT / 'data/operational'
    out.mkdir(exist_ok=True)
    files = []
    for name, rel in FILES.items():
        shutil.copyfile(source / rel, out / name)
        files.append({'bundled': name, 'original': f'{source.name}/{rel}',
                      'sha256': sha(out / name), 'transformation': 'Unmodified public experiment snapshot'})
    (out / 'inventory.json').write_text(json.dumps({'version':'2026-11-01.1',
        'scope':'Existing-site hourly delivered power; no monthly or growth validation',
        'files':files}, indent=2)+'\n')
    print(f'Imported {len(files)} verified snapshots; no model fitting or source modification.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    main(parser.parse_args().source)
