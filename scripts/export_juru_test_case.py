"""Export the public synthetic examination preset using the application itself."""
import argparse
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'exports/juru-examination')
    args = parser.parse_args()
    client = create_app().test_client()
    response = client.get('/api/demo-cases/juru/download')
    if response.status_code != 200:
        raise RuntimeError(response.text)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Test dataset archive failed its integrity check.')
        # Only known, app-generated outputs. Never extract arbitrary uploaded ZIPs.
        for name in ('features_20.csv', 'all_inputs.csv', 'synthetic_monthly_36.csv',
                     'daily_weekly_monthly_yearly.csv', 'synthetic_hourly_profile.csv',
                     'financial_stress.csv', 'project.json', 'metadata.json', 'report.html',
                     'public_sector_context.csv', 'public_sector_context.json', 'README.txt'):
            if name in archive.namelist():
                (output / name).write_bytes(archive.read(name))
    target = output / 'gridsight-juru-synthetic-test-data.zip'
    target.write_bytes(response.data)
    print(json.dumps({'dataset': str(target), 'output': str(output),
                      'input_features': 20, 'scenario_months': 36,
                      'data_origin': 'synthetic', 'is_metered': False}, indent=2))


if __name__ == '__main__':
    main()
