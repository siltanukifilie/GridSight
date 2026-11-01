"""Produce public-only offline review artifacts through the same app endpoints."""
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app
from src.domain import DEMOS


def main():
    client = create_app().test_client()
    output = ROOT / 'reports/screening_review'
    output.mkdir(parents=True, exist_ok=True)
    # Explicit synthetic demand fixture; public ranking remains separate.
    body = {'site': {**DEMOS[2], 'name': 'Illustrative review — synthetic demand inputs'},
            'context': {'country_code': 'RW', 'input_origin': 'synthetic'},
            'connection': {'enabled': True}}
    for route, filename in [('/api/operator-pilot', 'operator-proposal.html'),
                            ('/api/operator-pilot/download', 'operator-pilot.zip'),
                            ('/api/bugesera-ranking/download', 'bugesera-ranking.zip')]:
        response = client.get(route)
        if response.status_code != 200:
            raise RuntimeError(response.text)
        (output / filename).write_bytes(response.data)
    response = client.post('/api/deliverables-pack', json=body)
    if response.status_code != 200:
        raise RuntimeError(response.text)
    (output / 'screening-deliverables.zip').write_bytes(response.data)
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        if z.testzip() is not None:
            raise RuntimeError('Invalid output archive')
        # Only HTML is copied for a convenient preview; all linked attachments
        # live in the complete ZIP, not an automatically extracted user archive.
        (output / 'review.html').write_bytes(z.read('report.html'))
        assessment = json.loads(z.read('assessment_checklist.json'))
        print(json.dumps({'output': str(output), 'criteria': [c['criterion'] for c in assessment['criteria']],
                          'archive_entries': len(z.namelist()), 'demand_inputs': 'synthetic'}, indent=2))


if __name__ == '__main__':
    main()
