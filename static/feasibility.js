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
  const form=`<form id="planning-form"><h3>Set the range</h3><div class="compact-grid">${fields}</div><div class="form-section"><h3>Capital budget</h3><p class="subtle-note">Your estimates, not verified quotations. Leave unknown costs blank.</p><div class="compact-grid">${costs}</div></div><div class="form-section"><h3>Productive-use support</h3><p class="subtle-note">Developer connection/support costs—not the customer's business profit. Zero extra running costs are assumptions.</p><div class="compact-grid">${support}</div></div><div class="form-actions"><button class="button primary run-button" type="submit">Update feasibility</button></div></form>`;
  const findings=f.findings.map(x=>`<div class="insight-card"><span class="insight-symbol">!</span><div><h3>${esc(x.title)}</h3><p>${esc(x.detail)}</p><p>${esc(x.action)}</p></div></div>`).join('');
  const growthChart=chart({central:expected.months.map(m=>m.demand_kwh),lower:low.months.map(m=>m.demand_kwh),upper:high.months.map(m=>m.demand_kwh)},expected.months.map(m=>m.calendar_month||'M'+m.month),{unit:'kWh/month',tickStep:6,height:230});
  $('#view-feasibility').innerHTML=countryMarkup(`<p class="demo-notice">Synthetic feasibility screen · Not engineering sign-off or lending approval.</p>
    <div class="feasibility-actions"><button class="button primary" id="download-feasibility">${icon('download')}Download report</button><button class="button secondary" id="preview-feasibility">Print / PDF</button><span class="subtle-note">HTML report · Export report also includes CSV + JSON.</span></div>
    <div class="feasibility-layout"><div class="feasibility-controls">${connectionControlsHtml(r)}${card('Set the assumptions','Shared between both roles',form)}</div><div class="feasibility-results">
    ${typeof uncertaintyHtml==='function'?uncertaintyHtml():''}
    ${typeof financialEvidenceHtml==='function'?financialEvidenceHtml():''}
    ${card('What needs attention?','Model-based checks',findings)}
    ${card('Low / expected / high range','3 years · expected line with low–high band',growthChart+casesTable+detailsHtml('How it works',`<p>${f.methods.scenarios}</p><p>${f.methods.growth}</p>`))}
    ${card('Too much—or too little?','Potential over-sizing and supply gaps',sizingTable+detailsHtml('How it works',`<p>${f.methods.sizing}</p>`))}
    ${card('Productive-use opportunities','One added unit at a time · ranked by grid contribution',productiveTable+(typeof productiveStressHtml==='function'?productiveStressHtml():'')+detailsHtml('How it works',`<p>${f.methods.productive}</p><p>Before commitment: check local customers, activity volumes, operating schedules and willingness to pay.</p>`))}
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
