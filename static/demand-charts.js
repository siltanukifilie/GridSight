/* Present the existing forecast at different horizons. No new demand model. */
const DEMAND_VIEWS = {day:'Daily', week:'Weekly', month:'Monthly', year:'Yearly'};

function demandChartData(result, requestedPeriod='day') {
  const period = Object.hasOwn(DEMAND_VIEWS, requestedPeriod) ? requestedPeriod : 'day';
  const periods = Object.fromEntries(result.demand_periods.estimates.map(p => [p.period, p]));
  const forecast = result.forecast;
  const daysPerMonth = periods.month.days_per_period;
  const total = periods[period].central;
  if (period === 'year' && result.feasibility?.monthly_growth) {
    const months = result.feasibility.monthly_growth.slice(0,12);
    return {
      period, title:'Yearly demand', subtitle:result.detailed?.enabled?'Next 12 months · from service M'+result.horizon.first_service_month:result.connection?.enabled?'First year after connection':'Monthly growth · Year 1', tag:'Growth scenario',
      unit:'kWh/month', labels:months.map(m=>m.calendar_month||'M'+(m.service_month||m.month)),
      series:{central:months.map(m=>m.central), lower:months.map(m=>m.lower), upper:months.map(m=>m.upper)},
      durations:Array(12).fill(1), total, totalLabel:'Yearly energy',
      note:result.detailed?.enabled?'Assumed agricultural cycle':'Assumption-based · No seasonality modeled',
      detail:result.detailed?.enabled?'Connections, appliance use, business growth and agricultural factors shape the next 12 months. Low/high values use editable demand multipliers, not calibrated probability. The twelve standard energy months sum to the yearly card.':result.connection?.enabled?'Monthly demand follows the connection, appliance and non-household adoption assumptions. The first 12 service months sum to the yearly card. Reference bounds are propagated, not calibrated for this growth curve. Date labels locate standard 365/12-day energy months, not billing-calendar totals.':'Monthly growth follows the household and business assumptions. The 12 months average to the Year 1 model estimate, so their total matches the yearly card. Positive growth rises; zero growth stays flat; negative growth can fall. Shading propagates the initial monthly prediction range, not independently validated monthly uncertainty. See Feasibility for the 36-month Low / expected / high range, based on separate scenarios.'
    };
  }
  if (period === 'day') {
    return {
      period, title:'Daily demand', subtitle:'Illustrative 24-hour profile', tag:'Illustrative profile',
      unit:'kW', labels:result.profile.hours.map(h => String(h).padStart(2,'0') + ':00'),
      series:{central:[...result.profile.kw], lower:result.profile.kw.map(v => forecast.central ? v * forecast.lower / forecast.central : 0), upper:result.profile.kw.map(v => forecast.central ? v * forecast.upper / forecast.central : 0)},
      durations:Array(24).fill(1), total, totalLabel:'Daily energy',
      note:'Local time · '+(result.context?.country||'Rwanda'),
      detail:result.detailed?.enabled?'Illustrative sector timing scaled to the entered daily energy. Low/high are scenarios; power ratings and daily hours do not specify an actual hourly operating schedule.':'Hourly power follows the illustrative RAMP shape. The shaded band scales the monthly prediction range; it is not an independently calibrated hourly interval.'
    };
  }
  const wholeDays = Math.floor(daysPerMonth);
  const remainder = daysPerMonth - wholeDays;
  const labels = period === 'week' ? Array.from({length:7}, (_,i) => `Day ${i+1}`)
    : period === 'year' ? Array.from({length:12}, (_,i) => `M${i+1}`)
    : [...Array.from({length:wholeDays}, (_,i) => `Day ${i+1}`), ...(remainder > 1e-9 ? [`Day ${wholeDays+1}*`] : [])];
  const factor = period === 'year' ? 1 : 1 / daysPerMonth;
  const values = period === 'year' ? forecast.central : periods.day.central;
  const durations = period === 'month' ? [...Array(wholeDays).fill(1), ...(remainder > 1e-9 ? [remainder] : [])] : Array(labels.length).fill(1);
  return {
    period, title:DEMAND_VIEWS[period] + ' demand',
    subtitle:period === 'year' ? 'Average monthly energy · Year 1' : period === 'week' ? 'Average daily energy · 7 days' : `Average daily energy · ${daysPerMonth.toFixed(1)} days`,
    tag:'Average-based', unit:period === 'year' ? 'kWh/month' : 'kWh/day', labels,
    series:{central:Array(labels.length).fill(values), lower:Array(labels.length).fill(forecast.lower * factor), upper:Array(labels.length).fill(forecast.upper * factor)},
    durations, total, totalLabel:DEMAND_VIEWS[period] + ' energy',
    note:result.detailed?.enabled?'Average daily use · seasonality is shown in Yearly':period === 'month' && remainder > 1e-9 ? `*Final day: ${remainder.toFixed(2)} day. No seasonal pattern modeled.` : 'Uniform average · No seasonal pattern modeled',
    detail:'Weekly and monthly views repeat average daily use; yearly repeats the first-year monthly estimate. These are not date-specific forecasts. An average month is 365/12 days, including a partial final day. Totals match the central-estimate cards. Shading shows the monthly range scaled to the displayed units, not separately validated daily or yearly uncertainty. Future growth is shown separately below.'
  };
}

function demandChartContents(result, period) {
  const view = demandChartData(result, period);
  return `<div class="card-head profile-heading"><div><h2 id="demand-chart-heading">${view.title}</h2><p>${view.subtitle}</p></div><span class="tag">${view.tag}</span></div>
    <div class="chart-period-tabs" role="tablist" aria-label="Demand chart period">${Object.entries(DEMAND_VIEWS).map(([key,label]) => `<button type="button" role="tab" id="demand-tab-${key}" data-demand-period="${key}" aria-selected="${key === view.period}" aria-controls="demand-chart-panel" tabindex="${key === view.period ? '0' : '-1'}">${label}</button>`).join('')}</div>
    <div id="demand-chart-panel" role="tabpanel" aria-labelledby="demand-tab-${view.period}" tabindex="0"><div class="legend"><span><i></i>Central estimate</span><span><i class="band"></i>${result.detailed?.enabled?'Low / high scenario':'Scaled monthly range'}</span></div>
    ${chart(view.series, view.labels, {unit:view.unit, tickStep:view.period === 'year' ? 1 : undefined})}
    <div class="chart-caption"><span>${view.totalLabel} <b>${number(view.total,1)} kWh</b></span>${view.period === 'day' ? `<span>Load factor <b>${number(result.profile.load_factor*100)}%</b></span>` : ''}<span>${view.note}</span></div>
    ${detailsHtml('How it works', `<p>${view.detail}</p>`)}</div>`;
}

function demandChartHtml(result) {
  return `<article class="card demand-chart-card" id="demand-chart-card">${demandChartContents(result, state.demandPeriod)}</article>`;
}

function selectDemandPeriod(period, moveFocus=false) {
  if (!Object.hasOwn(DEMAND_VIEWS, period) || !state.result) return;
  const container = $('#demand-chart-card');
  if (!container) return;
  state.demandPeriod = period;
  // Only replace this chart. Preserve unapplied inputs in the other views.
  container.innerHTML = demandChartContents(state.result, period);
  bindDemandChart();
  if (moveFocus) container.querySelector(`[data-demand-period="${period}"]`).focus();
}

function bindDemandChart() {
  const container = $('#demand-chart-card');
  if (!container) return;
  const keys = Object.keys(DEMAND_VIEWS);
  container.querySelectorAll('[data-demand-period]').forEach(button => {
    button.addEventListener('click', () => selectDemandPeriod(button.dataset.demandPeriod, true));
    button.addEventListener('keydown', event => {
      const index = keys.indexOf(button.dataset.demandPeriod);
      const next = event.key === 'ArrowRight' ? keys[(index+1)%keys.length]
        : event.key === 'ArrowLeft' ? keys[(index+keys.length-1)%keys.length]
        : event.key === 'Home' ? keys[0] : event.key === 'End' ? keys.at(-1) : null;
      if (next) { event.preventDefault(); selectDemandPeriod(next, true); }
    });
  });
}

if (typeof module !== 'undefined') module.exports = {DEMAND_VIEWS, demandChartData};
