"""Affordability and staged productive use, with no inferred tariff elasticity."""
from .domain import finance


def affordability(assumptions, planning, currency):
    energy = planning['household_basket_kwh']
    income = planning['household_income_monthly']
    budget = planning['household_energy_budget_monthly']
    fee = planning['household_fixed_fee_monthly']
    threshold = planning['affordability_income_share']
    rows = []
    for label, multiplier in [('Lower tariff', .8), ('Entered tariff', 1), ('Higher tariff', 1.2)]:
        tariff = assumptions['tariff'] * multiplier
        bill = energy * tariff + fee if energy is not None else None
        share = bill / income if bill is not None and income is not None and income > 0 else None
        exceeds_income = bill > income * threshold if bill is not None and income is not None else None
        rows.append({'case': label, 'tariff_multiplier': multiplier, 'tariff_per_kwh': tariff,
                     'basket_kwh': energy, 'fixed_fee_monthly': fee, 'bill_monthly': bill,
                     'income_share': share, 'income_screen_exceeded': exceeds_income,
                     'budget_gap_monthly': max(0, bill-budget) if bill is not None and budget is not None else None,
                     'within_entered_budget': bill <= budget if bill is not None and budget is not None else None,
                     'currency': currency})
    return {'rows': rows, 'status': 'needs_household_basket' if energy is None else
            'needs_income_or_budget' if income is None and budget is None else 'scenario_comparison',
            'income_threshold': threshold,
            'notice': 'One household energy basket at 80%, 100% and 120% of the entered flat tariff. Bills include the entered monthly fixed fee; collection rate does not reduce the household bill. Income and budget are user inputs. The editable income-share threshold is a screening assumption, not an official affordability standard. Demand is held fixed; no willingness-to-pay or tariff response is inferred.'}


def productive_growth(result):
    a, p = result['assumptions'], result['planning']
    months = result['feasibility']['monthly_growth']
    start = (a['adoption_year']-1)*12+1
    rows, annual = [], []
    # The unit's monthly energy comes from the active engineering/legacy engine.
    for option in result['feasibility']['productive_options']:
        key = option['key']
        for label, usage in [('No uptake', 0), ('Half assumed use', .5), ('Assumed full use', 1)]:
            for index, month in enumerate(months, 1):
                active = index >= start
                extra = option['extra_demand_kwh_month']*usage*(1+a['business_growth'])**((index-start)/12) if active else 0
                base = finance(month['central'], a)['base']
                changed = finance(month['central']+extra, a)['base']
                served = changed['served_kwh']-base['served_kwh']
                fixed = p[key+'_monthly_cost'] if active else 0
                revenue = served*a['tariff']*a['collection_rate']
                contribution = revenue-served*a['variable_cost']-fixed
                support = p[key+'_support_cost'] if index == start else 0
                rows.append({'option': key, 'case': label, 'usage_factor': usage, 'month': index,
                             'year': (index-1)//12+1, 'calendar_month': month.get('calendar_month'),
                             'start_month': start, 'baseline_demand_kwh': month['central'],
                             'extra_demand_kwh': extra, 'total_demand_kwh': month['central']+extra,
                             'extra_served_kwh': served, 'extra_unserved_kwh': max(0,extra-served),
                             'extra_revenue': revenue, 'extra_fixed_cost': fixed,
                             'extra_operating_contribution': contribution, 'support_capex': support,
                             'cash_after_support': contribution-support if support is not None else None,
                             'currency': result['context']['currency']})
            for year in (1, 2, 3):
                group = [r for r in rows if r['option']==key and r['case']==label and r['year']==year]
                cash_known = all(r['cash_after_support'] is not None for r in group)
                annual.append({'option': key, 'case': label, 'year': year,
                               'extra_demand_kwh': sum(r['extra_demand_kwh'] for r in group),
                               'extra_served_kwh': sum(r['extra_served_kwh'] for r in group),
                               'extra_unserved_kwh': sum(r['extra_unserved_kwh'] for r in group),
                               'extra_operating_contribution': sum(r['extra_operating_contribution'] for r in group),
                               'cash_after_support': sum(r['cash_after_support'] for r in group) if cash_known else None,
                               'currency': result['context']['currency']})
    return {'months': rows, 'years': annual, 'start_month': start,
            'notice': 'Separate one-unit alternatives added to the existing 36-month plan, starting in the chosen adoption year. Each tests no uptake, half use and full assumed use. Extra energy follows the entered business-growth rate. Fixed support costs persist after launch even at zero use; support capital is deducted once. Unknown support capital leaves launch-year cash unknown. Monthly energy caps apply; hourly power/dispatch and extra generation capital are not modeled. These are additional units beyond any additions already in the plan.'}


def build(result):
    f = result['feasibility']
    return {'affordability': affordability(result['assumptions'], result['planning'], result['context']['currency']),
            'productive_growth': productive_growth(result),
            'growth': {'months': [{'month': i+1, 'year': (i//12)+1, 'calendar_month': month.get('calendar_month'),
                                  'low_kwh': f['scenarios'][0]['months'][i]['demand_kwh'],
                                  'base_kwh': f['scenarios'][1]['months'][i]['demand_kwh'],
                                  'high_kwh': f['scenarios'][2]['months'][i]['demand_kwh']}
                                 for i, month in enumerate(f['monthly_growth'])],
                       'years': [{'case': c['key'], 'year': y['year'], 'total_kwh': y['demand_kwh'],
                                  'mean_monthly_kwh': y['average_monthly_kwh']} for c in f['scenarios'] for y in c['years']],
                       'basis': f['methods']['growth'], 'empirical_interval_applied': False}}
