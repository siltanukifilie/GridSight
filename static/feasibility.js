/* Shared decision-support view; backend owns every calculation. */
function planningField(key, label, {percent=false, optional=false}={}) {
  const factor = percent ? 100 : 1;
  const limits = state.planningSettings.limits[key];
  const value = state.planning[key];
  return `<div class="field"><label for="planning-${key}">${label}</label><input id="planning-${key}" name="${key}" type="number" data-percent="${percent}" data-optional="${optional}" min="${limits[0]*factor}" max="${limits[1]*factor}" step="any" value="${value == null ? '' : Number((value*factor).toFixed(6))}" ${optional ? 'placeholder="Not provided"' : 'required'}></div>`;
}

function planningFormValues(form) {
  return Object.fromEntries(Object.keys(state.planningSettings.defaults).map(key => {
    const input = form.elements[key];
    return [key, input.value.trim() === '' && input.dataset.optional === 'true' ? null : Number(input.value)/(input.dataset.percent === 'true' ? 100 : 1)];
  }));
}

function moneyOrMissing(value) { return value == null ? 'Not assessed' : number(value); }
function measuredRangesHtml(r) {
  const u=r.transfer_uncertainty;
  if(!u||u.status==='unavailable')return `<article class="card"><h2>Measured-site error ranges</h2><p>${esc(u?.notice||'Study unavailable.')}</p></article>`;
  return `<article class="card"><div class="card-head"><div><h2>Measured-site error ranges</h2><p>Kenya / Nigeria · existing-site forecasts with meter history</p></div><a class="button secondary" href="/api/transfer-uncertainty/download">Download study ↓</a></div><div class="table-wrap"><table><thead><tr><th>Horizon</th><th>Sites / months</th><th>Reference radius · kWh per origin meter</th><th>Held-out coverage · equal site weight</th><th>Model / last-month MAE · kWh</th></tr></thead><tbody>${u.horizons.map(h=>`<tr><td>${h.horizon_months} months</td><td>${h.sites} / ${h.rows}</td><td>± ${number(h.radius_kwh_per_origin_meter,2)}</td><td>${number(h.nested_equal_site_coverage*100,1)}%</td><td>${number(h.equal_site_mae_kwh,1)} / ${number(h.equal_site_persistence_mae_kwh,1)}</td></tr>`).join('')}</tbody></table></div><p class="subtle-note">A reference range is prediction ± radius × observed meters, with the lower end clipped at zero. Coverage above tests independently calibrated ranges on each excluded site. The table's pooled radii are for subsequent experiments. The last-month baseline currently has lower average error.</p><details><summary>Scope and calibration</summary><p>${esc(u.method)}</p><p>${esc(u.temporal_scope)}</p><p>${esc(u.notice)}</p><p>${esc(u.source)} · ${esc(u.license)}</p></details></article>`;
}

function affordabilityHtml(r) {
  if(!r.planning_scenarios)return '';
  const a=r.planning_scenarios.affordability;
  return `<article class="card"><h2>Can households afford the basket?</h2><p>Flat-tariff sensitivity · ${esc(r.context.currency)} per household per month</p><div class="table-wrap"><table><thead><tr><th>Tariff case</th><th>Tariff / kWh</th><th>Monthly bill</th><th>Income share</th><th>Budget gap</th><th>Income screen</th></tr></thead><tbody>${a.rows.map(x=>`<tr><td>${esc(x.case)}</td><td>${number(x.tariff_per_kwh,2)}</td><td>${moneyOrMissing(x.bill_monthly)}</td><td>${x.income_share==null?'Not assessed':number(100*x.income_share,1)+'%'}</td><td>${moneyOrMissing(x.budget_gap_monthly)}</td><td>${x.income_screen_exceeded==null?'Not assessed':x.income_screen_exceeded?'Above entered threshold':'Within entered threshold'}</td></tr>`).join('')}</tbody></table></div><p class="subtle-note">Income-share screen: ${number(a.income_threshold*100,1)}%. Add a household basket and income or budget in the assumptions form. Blank inputs remain unassessed.</p><details><summary>How this comparison works</summary><p>${esc(a.notice)}</p></details></article>`;
}

function productiveGrowthHtml(r) {
  if(!r.planning_scenarios)return '';
  const s=r.planning_scenarios.productive_growth;
  return `<details><summary>Productive-use alternatives over Years 1–3</summary><p>${esc(s.notice)}</p><div class="table-wrap"><table><thead><tr><th>Added unit / use / year</th><th>Extra demand / served · kWh/year</th><th>Grid contribution / year</th><th>Cash after support / year</th></tr></thead><tbody>${s.years.map(x=>`<tr><td>${esc(x.option)} · ${esc(x.case)} · Y${x.year}</td><td>${number(x.extra_demand_kwh)} / ${number(x.extra_served_kwh)}</td><td>${number(x.extra_operating_contribution)} ${esc(r.context.currency)}</td><td>${moneyOrMissing(x.cash_after_support)} ${esc(r.context.currency)}</td></tr>`).join('')}</tbody></table></div></details>`;
}
function caseSummaryHtml(r) {
  const cases = r.feasibility.scenarios;
  return `<article class="card scenario-summary"><div class="card-head"><div><h2>Low / expected / high range</h2><p>Scenario range · Year 1 averages</p></div><button class="text-button" data-go="feasibility">View range ↗</button></div><div class="case-cards">${cases.map(c => {
    const y=c.years[0];
    return `<div class="case-card case-${c.key}"><span>${c.label} · ${number(c.factor*100)}%</span><strong>${number(y.average_monthly_kwh)} <small>kWh/mo</small></strong><p>Cash after debt <b>${number(y.cash_after_debt/12)} ${moneyUnit()}/mo</b></p></div>`;
  }).join('')}</div><p class="subtle-note">${r.detailed?.enabled?'Same low/high factors as the displayed scenario range.':'Separate from the prediction range.'} Cash uses monthly supply limits.</p></article>`;
}

function renderFeasibility() {
  const r=state.result, f=r.feasibility, p=state.planning;
  const [low,expected,high]=f.scenarios;
  const yearly=f.scenarios.flatMap(c=>c.years);
  const card=(title,subtitle,body)=>`<article class="card"><div class="card-head"><div><h2>${title}</h2><p>${subtitle}</p></div></div>${body}</article>`;
  const table=(head,rows)=>`<div class="table-wrap"><table><thead><tr>${head.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>`;
  const casesTable=table(['Case / year','Demand · kWh/year',moneyText('Cash after debt · RWF/year'),'Debt coverage','Cash-gap months'],yearly.map(y=>`<tr class="${y.scenario==='expected'?'highlight':''}"><td>${y.label} · Y${y.year}</td><td>${number(y.demand_kwh)}</td><td class="${y.cash_after_debt<0?'negative':''}">${number(y.cash_after_debt)}</td><td>${y.dscr==null?'N/A':number(y.dscr,2)+'×'}</td><td>${y.cash_shortfall_months} / 12</td></tr>`).join(''));
  const sizingTable=table(['Case / year','Energy used','Unused capacity · kWh/year','Unserved · kWh/year','Peak gap · kW','Spare power · kW',moneyText('Idle capital exposure · RWF')],yearly.map(y=>`<tr><td>${y.label} · Y${y.year}</td><td>${y.energy_utilization==null?'N/A':number(y.energy_utilization*100,1)+'%'}</td><td>${number(y.unused_capacity_kwh)}</td><td class="${y.unserved_kwh>0?'negative':''}">${number(y.unserved_kwh)}</td><td class="${y.peak_shortfall_kw>0?'negative':''}">${number(y.peak_shortfall_kw,1)}</td><td>${number(y.spare_power_kw,1)}</td><td>${moneyOrMissing(y.idle_capital_exposure_amount)}</td></tr>`).join(''));
  const productiveTable=table(['Option','Extra demand / served · kWh/mo',moneyText('Extra revenue · RWF/mo'),moneyText('Grid contribution · RWF/mo'),'Support payback','Supply check'],f.productive_options.map(o=>`<tr><td>${o.rank}. ${o.label}</td><td>${number(o.extra_demand_kwh_month)} / ${number(o.extra_served_kwh_month)}</td><td>${number(o.extra_revenue_amount_month)}</td><td class="${o.extra_contribution_amount_month<=0?'negative':''}">${number(o.extra_contribution_amount_month)}</td><td>${o.simple_payback_years==null?(o.developer_support_cost_amount==null?'Enter support cost':'No positive payback'):number(o.simple_payback_years,1)+' yr'+(o.supply_gap?' · provisional':'')}</td><td>${o.screen}</td></tr>`).join(''));
  const npvTable=table(['Case',moneyText('3-year cash after debt · RWF'),moneyText('3-year NPV before financing · RWF')],f.scenarios.map(c=>`<tr><td>${c.label}</td><td>${number(c.three_year_cash_after_debt)}</td><td>${moneyOrMissing(c.three_year_npv_before_financing)}</td></tr>`).join(''));
  const fields=planningField('low_factor','Low demand · % of expected',{percent:true})+planningField('high_factor','High demand · % of expected',{percent:true});
  const costs=planningField('project_capex',moneyText('Total project capital cost · RWF'),{optional:true})+planningField('capacity_capex',moneyText('Capacity-linked part · RWF'),{optional:true})+planningField('discount_rate','Annual discount rate · %',{percent:true});
  const support=[['mill','Mill'],['pump','Pump'],['cold_room','Cold room']].map(([key,label])=>planningField(`${key}_support_cost`,`${label}: support cost · ${moneyUnit()}`,{optional:true})+planningField(`${key}_monthly_cost`,`${label}: extra operating cost · ${moneyUnit()}/mo`)).join('');
  const household=state.planningSettings.limits.household_basket_kwh?planningField('household_basket_kwh','Household basket · kWh/month',{optional:true})+planningField('household_income_monthly',`Household income · ${moneyUnit()}/month`,{optional:true})+planningField('household_energy_budget_monthly',`Energy budget · ${moneyUnit()}/month`,{optional:true})+planningField('household_fixed_fee_monthly',`Fixed electricity fee · ${moneyUnit()}/month`)+planningField('affordability_income_share','Income-share screen · % (assumption)',{percent:true}):'<p>Recalculate the saved project to load the affordability inputs.</p>';
  const form=`<form id="planning-form"><h3>Set the range</h3><div class="compact-grid">${fields}</div><div class="form-section"><h3>Capital budget</h3><p class="subtle-note">Use verified quotes. Leave unknown costs blank.</p><div class="compact-grid">${costs}</div></div><div class="form-section"><h3>Productive-use support</h3><p class="subtle-note">Developer costs, not business profit. Zero operating costs are assumptions.</p><div class="compact-grid">${support}</div></div><div class="form-section"><h3>Household affordability</h3><p class="subtle-note">Monthly household values. Leave unknown income or budget blank.</p><div class="compact-grid">${household}</div></div><div class="form-actions"><button class="button primary run-button" type="submit">Update feasibility</button></div></form>`;
  const findings=f.findings.map(x=>`<div class="insight-card"><span class="insight-symbol">!</span><div><h3>${esc(x.title)}</h3><p>${esc(x.detail)}</p><p>${esc(x.action)}</p></div></div>`).join('');
  const growthChart=chart({central:expected.months.map(m=>m.demand_kwh),lower:low.months.map(m=>m.demand_kwh),upper:high.months.map(m=>m.demand_kwh)},expected.months.map(m=>m.calendar_month||'M'+m.month),{unit:'kWh/month',tickStep:6,height:230});
  $('#view-feasibility').innerHTML=countryMarkup(`<p class="demo-notice">Planning screen · not engineering sign-off or lending approval.</p>
    <div class="feasibility-actions"><button class="button primary" id="download-feasibility">${icon('download')}Download report</button><button class="button secondary" id="preview-feasibility">Print / PDF</button><span class="subtle-note">HTML / PDF · full export includes CSV + JSON.</span></div>
    <div class="feasibility-layout"><div class="feasibility-controls">${connectionControlsHtml(r)}${card('Set the assumptions','Shared between both roles',form)}</div><div class="feasibility-results">
    ${affordabilityHtml(r)}
    ${typeof financialEvidenceHtml==='function'?financialEvidenceHtml():''}
    ${card('Project checks','Demand, supply and cash',findings)}
    ${card('Low / expected / high range','3 years · expected line with low–high band',growthChart+casesTable+detailsHtml('How it works',`<p>${f.methods.scenarios}</p><p>${f.methods.growth}</p>`))}
    ${card('Too much—or too little?','Potential over-sizing and supply gaps',sizingTable+detailsHtml('How it works',`<p>${f.methods.sizing}</p>`))}
    ${card('Productive-use opportunities','One added unit at a time · ranked by grid contribution',productiveTable+(typeof productiveStressHtml==='function'?productiveStressHtml():'')+productiveGrowthHtml(r)+detailsHtml('How it works',`<p>${f.methods.productive}</p><p>Before commitment: check local customers, activity volumes, operating schedules and willingness to pay.</p>`))}
    <details class="more-details"><summary>Uncertainty methods & measured-site study</summary>${typeof uncertaintyHtml==='function'?uncertaintyHtml():''}${measuredRangesHtml(r)}</details>
    ${card('Capital & cash','Limited 36-month screen · not whole-life project returns',npvTable+`<p class="subtle-note">${p.project_capex==null?'Enter capital cost to calculate NPV.':'Capital cost: '+number(p.project_capex)+moneyText(' RWF.')} Discount rate: ${number(p.discount_rate*100)}%/year.</p>`+detailsHtml('Financial scope',`<p>${f.methods.finance}</p>`))}
    ${card('Before you commit','Real evidence still needed',`<ul class="evidence-checklist">${f.evidence_gaps.map(g=>`<li>${esc(g)}</li>`).join('')}</ul>`)}
    </div></div>`);
  bindConnectionControls();
  if(typeof bindFinancialEvidence==='function')bindFinancialEvidence();
  if(typeof bindUncertainty==='function')bindUncertainty();
  $('#planning-form').addEventListener('input',markDirty);
  $('#planning-form').addEventListener('submit',async event=>{
    event.preventDefault(); await applyFeasibilityForms();
  });
  $('#download-feasibility').addEventListener('click',downloadFeasibility);
  $('#preview-feasibility').addEventListener('click',printReport);
}

async function downloadFeasibility() {
  if(!state.result)return;
  if(state.dirty){toast('Run the analysis before downloading its report.');return;}
  try {
    const res=await api('/api/feasibility-report',{role:state.role,site:state.result.site,assumptions:state.result.assumptions,planning:state.result.planning,detailed:state.result.detailed,connection:state.result.connection,context:state.result.context,financial_evidence:state.result.financial_evidence?.packet||null});
    const url=URL.createObjectURL(await res.blob()), a=document.createElement('a');
    a.href=url; a.download='gridsight-feasibility-report.html'; a.click();
    setTimeout(()=>URL.revokeObjectURL(url),30000);
    toast('Feasibility report downloaded. Open it to review or print.');
  } catch(e){error(e.message);}
}
