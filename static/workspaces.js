/* Role-specific presentation. The role switch is deliberately NOT access control. */
const FINANCIAL_FIELDS = ['tariff', 'collection_rate', 'variable_cost', 'fixed_cost', 'debt_payment'];
const WORKSPACES = {
  developer: {
    label: 'Mini-grid developer',
    nav: {overview: 'Overview', community: 'Community', scenarios: 'Scenarios', feasibility: 'Feasibility', evidence: 'Evidence', locations: 'Locations'},
    titles: {
      overview: ['Demand overview', 'Demand, capacity and cash.'],
      community: ['Site data', 'Customers, connections and equipment.'],
      scenarios: ['Scenarios', 'Growth, capacity and costs.'],
      feasibility: ['Feasibility', 'Supply, costs and repayment.'],
      evidence: ['Evidence', 'Sources, methods and validation status.'],
      locations: ['Location', 'Grid access and public data.']
    }
  },
  investor: {
    label: 'Investor / lender',
    nav: {overview: 'Overview', community: 'Project', scenarios: 'Finance', feasibility: 'Feasibility', evidence: 'Evidence', locations: 'Locations'},
    titles: {
      overview: ['Investment overview', 'Demand and financial risk.'],
      community: ['Project profile', 'Customers, equipment and growth.'],
      scenarios: ['Financial scenarios', 'Costs, revenue and repayment.'],
      feasibility: ['Feasibility', 'Scenarios and financial checks.'],
      evidence: ['Evidence', 'Sources, methods and validation status.'],
      locations: ['Location', 'Site and public data.']
    }
  }
};

function normalizedRole(value) { return Object.hasOwn(WORKSPACES, value) ? value : 'developer'; }
function mergeFinancialInputs(current, values) {
  return {...current, ...Object.fromEntries(FINANCIAL_FIELDS.map(key => [key, values[key]]))};
}
function canSwitchWorkspace({busy, dirty, result}) { return !busy && !dirty && Boolean(result); }

function applyWorkspace() {
  const role = WORKSPACES[state.role];
  $('#role-select').value = state.role;
  $('#role-label').textContent = role.label;
  $('#workspace-label').textContent = state.role === 'developer' ? 'DEVELOPER WORKSPACE' : 'INVESTOR / LENDER WORKSPACE';
  document.querySelectorAll('.nav-item').forEach(button => {
    button.querySelector('.nav-label').textContent = role.nav[button.dataset.view];
  });
  $('#edit-button').textContent = state.role === 'developer' ? 'Edit project ↗' : 'Review project ↗';
  $('#export-button').innerHTML = icon('download') + 'Export report';
}

function switchWorkspace(role) {
  if (!canSwitchWorkspace(state)) {
    $('#role-select').value = state.role;
    toast(state.busy ? 'Wait for the analysis to finish.' : 'Apply changes before switching roles. Project values have been kept.');
    return;
  }
  state.role = normalizedRole(role);
  state.view = 'overview';
  try { localStorage.setItem('gridsight-role-v1', state.role); } catch {}
  render();
  toast(WORKSPACES[state.role].label + ' workspace · same community and scenario.');
}

function workflowSteps() {
  const investor = state.role === 'investor';
  const steps = investor
    ? [['community', 'Review project'], ['scenarios', 'Test finances'], ['evidence', 'View evidence']]
    : [['community', 'Check customers'], ['scenarios', 'Set supply & costs'], ['feasibility', 'Review the case']];
  return `<div class="workflow-steps" aria-label="${investor ? 'Investment review' : 'Development'} workflow">${steps.map(([view, title], i) => `<button class="workflow-step" data-go="${view}"><span>${i + 1}</span><strong>${title}</strong>${icon('arrow')}</button>`).join('')}</div>`;
}

function detailsHtml(label, content) {
  return `<details class="more-details"><summary>${esc(label)}</summary><div class="details-body">${content}</div></details>`;
}

function diligenceHtml() {
  const items = [
    ['Demand', 'Meter data or independent surveys.'],
    ['Technical design', 'Resource, engineering and battery studies.'],
    ['Financial case', 'Capital budget, tariff basis and financing terms.'],
    ['Delivery', 'Track record, site rights and approvals.']
  ];
  return `<ul class="diligence-list">${items.map(([title, detail]) => `<li><span class="evidence-status">Missing</span><div><strong>${title}</strong><p>${detail}</p></div></li>`).join('')}</ul><p class="subtle-note">Illustrative checklist only. No documents verified or credit rating assigned.</p>`;
}

function demandPeriodsHtml(r) {
  return `<article class="card demand-period-card" aria-label="Central demand estimate by period"><div class="card-head"><h2>Central demand estimate</h2><span class="tag">Year 1 averages</span></div><div class="demand-period-grid">${r.demand_periods.estimates.map(p => `<div class="demand-period ${p.period === 'month' ? 'source-period' : ''}"><span>${esc(p.label)}</span><strong>${number(p.central,1)}</strong><small>${esc(p.unit)}</small></div>`).join('')}</div><p class="period-range">${r.detailed?.enabled?'Scenario range':r.connection?.enabled?'Propagated reference range':'80% nominal range'}: <b>${number(r.forecast.lower)}–${number(r.forecast.upper)} kWh/month</b></p>${detailsHtml('How it works', `<p>${esc(r.demand_periods.basis)}</p><p>${r.detailed?.enabled?'Low/high are editable demand scenarios, not a confidence interval.':'The original range is evaluated for the reference model on synthetic monthly targets, not individual days or weeks. Propagating it through adoption does not validate the new curve.'}</p>`)}</article>`;
}

function fasterDemandHtml(r) {
  const faster = r.finance.scenarios.find(s => s.factor === 1.3);
  return `<div class="insight-card"><span class="insight-symbol">${icon('growth')}</span><div><h3>Demand +30%</h3><p>Cash after debt: <b>${number(faster.cash_after_debt)} ${moneyUnit()}/mo</b><br>Unserved: ${number(faster.unserved_kwh)} kWh/mo<br>Typical-peak gap: ${number(faster.peak_shortfall_kw,1)} kW</p><p>Stress case, not a growth forecast. Revenue is capped by supply.</p></div></div>`;
}

function renderInvestorOverview() {
  const r = state.result, base = r.finance.base;
  const downside = r.finance.scenarios.find(s => s.factor === 0.8);
  const severe = r.finance.scenarios.find(s => s.factor === 0.6);
  $('#view-overview').innerHTML = countryMarkup(`${alertHtml()}
    <p class="demo-notice">${r.detailed?.enabled?'Detailed engineering estimate':'Synthetic-trained planning screen'} · Not a funding recommendation.</p>
    ${workflowSteps()}${detailedOverviewHtml(r)}${demandPeriodsHtml(r)}${caseSummaryHtml(r)}${typeof connectionOverviewHtml==='function'?connectionOverviewHtml(r):''}
    <div class="kpi-grid">
      ${metric('Collected revenue', compact(base.revenue), moneyText('RWF/mo'), 'Served energy × tariff × collection', 'money')}
      ${metric('Cash after debt', compact(base.cash_after_debt), moneyText('RWF/mo'), 'After costs & debt', 'money')}
      ${metric('Debt coverage', base.dscr == null ? 'N/A' : number(base.dscr, 2), base.dscr == null ? '' : '×', base.dscr == null ? 'No debt payment entered' : 'Operating surplus / stated debt payment', 'report')}
      ${metric('20% lower demand', compact(downside.cash_after_debt), moneyText('RWF/mo'), 'Downside cash after debt', 'growth')}
    </div>
    ${demandChartHtml(r)}${typeof lenderExplanationHtml==='function'?lenderExplanationHtml(r):''}${typeof affordabilityHtml==='function'?affordabilityHtml(r):''}
    <div class="dashboard-grid"><article class="card"><div class="card-head"><div><h2>Cash under pressure</h2><p>Monthly · illustrative ${moneyUnit()}</p></div></div>${scenarioTable()}<div class="insight-card"><span class="insight-symbol">${icon('info')}</span><div><h3>${severe.cash_after_debt < 0 ? 'Demand −40%: cash shortfall' : 'Demand −40%: no cash shortfall'}</h3><p>${number(severe.cash_after_debt)} ${moneyUnit()}/mo after debt. Positive cash is not proof of viability.</p></div></div><div class="section-bottom"><p>Scenarios, not probabilities.</p><button class="inline-link" data-go="scenarios">Test finances ↗</button></div></article>
    <article class="card"><div class="card-head"><div><h2>Demand & break-even</h2><p>Shared developer forecast</p></div></div>
      <div class="data-stat-row"><span>Monthly customer demand</span><b>${number(r.forecast.central)} kWh</b></div>
      <div class="data-stat-row"><span>${r.detailed?.enabled?'Scenario range':r.connection?.enabled?'Propagated reference range':'80% nominal range'}</span><b>${number(r.forecast.lower)}–${number(r.forecast.upper)} kWh</b></div>
      <div class="data-stat-row"><span>Energy served</span><b>${number(base.served_kwh)} kWh/mo</b></div>
      <div class="data-stat-row"><span>Break-even served energy</span><b>${r.finance.break_even_kwh == null ? 'No finite break-even' : number(r.finance.break_even_kwh) + ' kWh/mo'}</b></div>
      <p class="subtle-note">${r.finance.break_even_kwh == null ? 'Nonpositive margin.' : r.finance.break_even_within_capacity ? 'Break-even fits the supply limit.' : 'Break-even exceeds supply.'} Revenue is capped by supply. Reliability is not modeled.</p>
      ${fasterDemandHtml(r)}<div class="section-bottom"><button class="inline-link" data-go="community">View project ↗</button></div></article></div>
    <article class="card review-evidence"><div class="card-head"><div><h2>Before funding</h2><p>Real data and project documents still needed.</p></div><span class="tag">Unverified</span></div>${detailsHtml('Missing evidence', diligenceHtml())}<button class="inline-link" data-go="evidence">View evidence ↗</button></article>`);
}

function renderInvestorCommunity() {
  const r = state.result, s = r.site, a = r.assumptions;
  const rows = [
    ['Community', s.name], ['District context', s.district], ['Households', number(s.households)],
    ['Expected household uptake', number(s.uptake * 100) + '%'], ['Household appliance index', number(s.appliance_index, 2)],
    ['Shops', number(s.shops)], ['Schools', number(s.schools)], ['Clinics', number(s.clinics)],
    ['Mills', number(s.mills)], ['Pumps', number(s.pumps)], ['Cold rooms', number(s.cold_rooms)]
  ];
  $('#view-community').innerHTML = countryMarkup(`<div class="role-notice">Read-only project. Edit costs in Finance. Both roles share this scenario.</div>
    <div class="dashboard-grid"><article class="card"><div class="card-head"><div><h2>Community profile</h2><p>Planning inputs · check provenance</p></div><span class="tag">Read-only view</span></div>${rows.map(([label, value]) => `<div class="data-stat-row"><span>${label}</span><b>${esc(value)}</b></div>`).join('')}<div class="section-bottom"><p>Change project inputs?</p><button class="inline-link" data-role="developer">Switch to developer ↗</button></div></article>
    <article class="card"><div class="card-head"><div><h2>Growth & supply</h2><p>Developer inputs</p></div></div>
      <div class="data-stat-row"><span>Household growth</span><b>${number(a.household_growth * 100)}% / year</b></div>
      <div class="data-stat-row"><span>Business growth</span><b>${number(a.business_growth * 100)}% / year</b></div>
      <div class="data-stat-row"><span>New equipment in Year ${a.adoption_year}</span><b>${a.additional_mills} mills · ${a.additional_pumps} pumps · ${a.additional_cold_rooms} cold rooms</b></div>
      <div class="data-stat-row"><span>Deliverable customer energy</span><b>${number(a.capacity_kwh)} kWh/mo</b></div>
      <div class="data-stat-row"><span>Firm power</span><b>${number(a.firm_power_kw, 1)} kW</b></div>
      <div class="data-stat-row"><span>Distribution losses</span><b>${number(a.loss_rate * 100)}%</b></div>
      ${chart({central:r.growth.map(x=>x.central),lower:r.growth.map(x=>x.lower),upper:r.growth.map(x=>x.upper)},r.growth.map(x=>`Year ${x.year}`),{unit:'kWh / month',height:185})}
      <p class="subtle-note">Assumption-based growth. Firm power ≠ solar nameplate capacity. No live consumption data.</p></article></div>`);
}

function renderInvestorScenarios() {
  const r = state.result, a = state.assumptions;
  const sf = (key, label, options={}) => field(key, label, a[key], {kind:'scenario', ...options});
  $('#view-scenarios').innerHTML = countryMarkup(`${alertHtml()}<div class="role-notice">Shared financial scenario. Community and capacity stay unchanged.</div>
    <div class="scenario-layout"><article class="card"><div class="card-head"><div><h2>Financial assumptions</h2><p>Monthly · illustrative ${moneyUnit()}</p></div></div><form id="investor-finance-form"><div class="compact-grid">
      ${sf('tariff', moneyText('Tariff · RWF / kWh'))}${sf('collection_rate', 'Bill collection (%)', {percent:true})}
      ${sf('variable_cost', moneyText('Variable cost · RWF / kWh'))}${sf('fixed_cost', moneyText('Fixed cost · RWF / month'), {step:'1000'})}
      ${sf('debt_payment', moneyText('Debt payment · RWF / month'), {step:'1000'})}</div><div class="form-actions"><button class="button primary run-button" type="submit">${icon('money')}Run stress test</button><button class="text-button" type="button" id="reset-finance">Reset finances</button></div></form>
      <p class="subtle-note">No debt → coverage N/A. Tariff changes do not change demand.</p></article>
    <div><article class="card"><div class="card-head"><div><h2>Demand vs. cash</h2><p>Collection and supply limits included.</p></div></div>${scenarioTable()}
      <div class="data-stat-row"><span>Contribution per served kWh</span><b>${number(r.finance.contribution_margin)} ${moneyUnit()}</b></div>
      <div class="data-stat-row"><span>Break-even served energy</span><b>${r.finance.break_even_kwh == null ? 'No finite break-even' : number(r.finance.break_even_kwh) + ' kWh/mo'}</b></div>
      ${detailsHtml('How it works', '<p class="subtle-note">Cash after debt = collected revenue − variable and fixed operating costs − stated debt payment. Debt coverage = operating surplus / stated debt payment. These are monthly screening calculations, not a lender-specific covenant calculation.</p>')}
      <div class="insight-card"><span class="insight-symbol">${icon('money')}</span><div><h3>Can it cover debt?</h3><p>${r.finance.base.dscr == null ? 'Enter a debt payment to assess coverage.' : r.finance.base.dscr >= 1 ? 'Base-case surplus covers the entered payment.' : 'Base-case surplus falls short of the entered payment.'} Check the downside too. This is not a loan-term repayment assessment.</p></div></div>${fasterDemandHtml(r)}</article>
    <article class="card"><div class="card-head"><div><h2>Screening, not approval</h2><p>Real-site validation still needed.</p></div></div><p>Optional capital inputs and a limited NPV screen are in Feasibility. No whole-life appraisal, IRR or lending decision.</p><p class="subtle-note">Synthetic evidence. Stress cases are not probabilities.</p><button class="inline-link" data-go="evidence">View evidence ↗</button></article></div></div>`);
  $('#investor-finance-form').addEventListener('input', markDirty);
  $('#investor-finance-form').addEventListener('submit', async event => {
    event.preventDefault();
    const values = Object.fromEntries(FINANCIAL_FIELDS.map(key => {
      const input = event.target.elements[key];
      return [key, Number(input.value) / (input.dataset.percent === 'true' ? 100 : 1)];
    }));
    state.assumptions = mergeFinancialInputs(state.assumptions, values);
    await calculate();
    if (!state.dirty) toast('Finances updated. Technical inputs unchanged.');
  });
  $('#reset-finance').addEventListener('click', async () => {
    state.assumptions = mergeFinancialInputs(state.assumptions, countryDefaults());
    await calculate();
    if (!state.dirty) toast('Finances reset. Technical inputs unchanged.');
  });
}

// Pure helpers can be tested without a browser. This is not visual or interaction QA.
if (typeof module !== 'undefined') module.exports = {WORKSPACES, FINANCIAL_FIELDS, normalizedRole, mergeFinancialInputs, canSwitchWorkspace};
