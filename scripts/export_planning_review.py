"""Export a reproducible illustrative review of all three new capabilities."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app
from src.domain import DEMOS


def main():
    project = {
        'site': {**DEMOS[2], 'name': 'Bugesera illustrative planning review'},
        'context': {'country_code': 'RW', 'input_origin': 'synthetic'},
        'connection': {'enabled': True, 'connection_month': '2026-11'},
        'assumptions': {'additional_mills': 0, 'additional_pumps': 0, 'additional_cold_rooms': 0, 'adoption_year': 2},
        'planning': {'household_basket_kwh': 15, 'household_income_monthly': 100000,
                     'household_energy_budget_monthly': 7500, 'household_fixed_fee_monthly': 0,
                     'affordability_income_share': .05, 'mill_support_cost': 1000000,
                     'mill_monthly_cost': 10000, 'pump_support_cost': None, 'cold_room_support_cost': None},
    }
    client = create_app().test_client()
    output = ROOT/'reports/planning_review'
    output.mkdir(parents=True, exist_ok=True)
    (output/'illustrative_inputs.json').write_text(json.dumps(project, indent=2)+'\n')
    for route, filename in [('/api/report','review.html'),('/api/export','planning_review.zip'),('/api/analyze','analysis.json')]:
        response = client.post(route, json=project)
        if response.status_code != 200:
            raise RuntimeError(response.get_data(as_text=True))
        (output/filename).write_bytes(response.data)
    analysis = json.loads((output/'analysis.json').read_text())
    print(json.dumps({'directory':str(output), 'annual_growth':analysis['planning_scenarios']['growth']['years'],
                      'affordability':analysis['planning_scenarios']['affordability']['rows']}, indent=2))


if __name__ == '__main__':
    main()
