/* Backend-owned connection growth. Saved/exported inputs retain this scenario. */
function connectionOverviewHtml(r){
  if(r.detailed?.enabled)return detailedCurveHtml(r);
  const c=r.connection;if(!c)return '';
  if(!c.enabled)return `<article class="card"><div class="card-head"><div><h2>Demand after connection</h2><p>Post-connection growth is off for this saved reference scenario.</p></div><button class="button secondary" data-go="feasibility">Set connection growth ↗</button></div></article>`;
  const months=r.feasibility.monthly_growth,[low,expected,high]=r.feasibility.scenarios;
  const first=months[0],last=months[35];
  return `<article class="card connection-growth"><div class="card-head"><div><h2>Demand after connection</h2><p>First 36 service months${c.connection_month?' · starts '+esc(c.connection_month):' · connection month not set'}</p></div><button class="text-button" data-go="feasibility">Edit growth ↗</button></div><div class="legend"><span><i></i>Expected</span><span><i class="band"></i>Low / high scenarios</span></div>${chart({central:expected.months.map(m=>m.demand_kwh),lower:low.months.map(m=>m.demand_kwh),upper:high.months.map(m=>m.demand_kwh)},months.map(m=>m.calendar_month||'M'+m.month),{unit:'kWh/month',height:220,tickStep:6})}<div class="mini-grid"><div class="mini-stat"><small>Month 1 demand</small><strong>${number(first.central)} <span>kWh</span></strong></div><div class="mini-stat"><small>Month 36 demand</small><strong>${number(last.central)} <span>kWh</span></strong></div><div class="mini-stat"><small>Adoption reaches target</small><strong>Month ${c.ramp_months}</strong></div></div><p class="subtle-note">Gradual connections, appliance use and non-household use. Assumption-based, not a metered growth forecast. The low/high band shows scenarios, not calibrated probability.</p></article>`;
}

function connectionControlsHtml(r){
  if(r.detailed?.enabled)return '<article class="card"><h2>Growth inputs</h2><p>Connections, appliance adoption, time since connection and agricultural seasonality are set in the 20-feature inputs.</p><button class="button secondary" data-go="community">Review growth inputs ↗</button></article>';
  const c=r.connection;if(!c)return '';
  if(state.role!=='developer')return `<article class="card"><div class="card-head"><h2>Connection-growth assumptions</h2><span class="tag">${c.enabled?'Active':'Off'}</span></div><p>Start: ${esc(c.connection_month||'Not set')} · adoption reaches target in Month ${c.ramp_months}.</p><p class="subtle-note">Initial households: ${number(c.start_household_fraction*100)}% of target connections. Appliance use: ${number(c.start_appliance_fraction*100)}% of the target basket. Non-household use: ${number(c.start_business_fraction*100)}% of target.</p><button class="button secondary" data-role="developer">Review in developer view</button></article>`;
  const input=(key,label,min,max,value,step='1')=>`<div class="field"><label for="connection-${key}">${label}</label><input id="connection-${key}" name="${key}" type="number" min="${min}" max="${max}" step="${step}" value="${value}" required></div>`;
  return `<article class="card"><div class="card-head"><div><h2>Start from connection</h2><p>Your assumptions · not measured adoption rates</p></div></div><form id="connection-form"><label class="check-line"><input type="checkbox" name="enabled" ${c.enabled?'checked':''}> Model gradual demand after connection</label><div class="compact-grid"><div class="field"><label for="connection-month">Connection month (optional)</label><input id="connection-month" name="connection_month" type="month" min="1900-01" max="2100-12" value="${esc(c.connection_month||'')}"></div>${input('ramp_months','Reach target in service month',1,60,c.ramp_months)}${input('start_household_fraction','Initial share of target connections (%)',0,100,c.start_household_fraction*100,'any')}${input('start_appliance_fraction','Initial share of target appliance use (%)',0,100,c.start_appliance_fraction*100,'any')}${input('start_business_fraction','Initial non-household use (%)',0,100,c.start_business_fraction*100,'any')}</div>${detailsHtml('How the curve works',`<p class="subtle-note">Community uptake and appliance index define the mature target. For example, 35% initial connections × 75% target uptake = 26.25% of households initially connected. Month 1 maturity means immediate full use. Annual growth in Scenarios adds underlying expansion; do not count adoption twice.</p><p class="subtle-note">The curve starts with service Month 1, not an observed reading. A blank date keeps relative months. Energy uses standard 365/12-day months, not exact billing-calendar totals. Changing these inputs recalculates Year 1 cards, growth, cash and reports.</p>`)}<button type="submit" class="button primary run-button">Update connection curve</button></form></article>`;
}

function connectionFormValues(form){
  const e=form.elements;
  return {enabled:e.enabled.checked,connection_month:e.connection_month.value||null,ramp_months:Number(e.ramp_months.value),start_household_fraction:Number(e.start_household_fraction.value)/100,start_appliance_fraction:Number(e.start_appliance_fraction.value)/100,start_business_fraction:Number(e.start_business_fraction.value)/100};
}

function bindConnectionControls(){
  const form=$('#connection-form');if(!form||state.role!=='developer'||state.result.detailed?.enabled)return;
  form.addEventListener('input',markDirty);
  form.addEventListener('submit',async e=>{e.preventDefault();await applyFeasibilityForms();});
}

async function applyFeasibilityForms(){
  if(state.busy)return;
  const planning=$('#planning-form');
  const connection=state.role==='developer'&&!state.result.detailed?.enabled?$('#connection-form'):null;
  const forms=[planning,connection].filter(Boolean);
  if(forms.some(form=>!form.reportValidity()))return;
  // Both forms share one page and dirty state; never discard an unapplied edit.
  state.planning=planningFormValues(planning);
  if(connection)state.connection=connectionFormValues(connection);
  await calculate();
  if(!state.dirty)toast('Connection curve, demand and finances updated.');
}

function lenderExplanationHtml(r, anchor=false){
  if(!r.lender_explanation)return '';
  return `<article class="card" ${anchor?'id="lender-deliverable" tabindex="-1"':''}><div class="card-head"><h2>Why this forecast?</h2><span class="tag">Lender review</span></div>${r.lender_explanation.slice(0,2).map(x=>`<p>${esc(x)}</p>`).join('')}${detailsHtml('Growth, risks and evidence',r.lender_explanation.slice(2).map(x=>`<p>${esc(x)}</p>`).join(''))}</article>`;
}

function deliverablesHtml(r){
  if(!r.deliverables)return '';
  const p=r.sharing_proposal;
  const actions=[
    '<button class="text-button" data-go="overview">View demand ↗</button>',
    '<button class="text-button" data-go="feasibility">Review growth ↗</button>',
    '<a class="text-button" href="#meter-validation">Test with meter data ↓</a>',
    '<a class="text-button" href="#lender-deliverable">Read explanation ↓</a>',
    '<a class="text-button" href="#sharing-deliverable">Read proposal ↓</a>'
  ];
  return `<article class="card deliverables-hub" aria-labelledby="deliverables-heading">
    <div class="card-head"><div><span class="section-kicker">PROJECT DELIVERABLES</span><h2 id="deliverables-heading">Five deliverables. One clear review.</h2><p>Tools ready. Real-world evidence still needed.</p></div><button class="button primary" id="deliverables-download">Download deliverables ↓</button></div>
    <p class="deliverables-notice">Metered-site validation is pending. Scenario ranges are not calibrated confidence bounds; growth assumptions are not measured histories.</p>
    <ol class="deliverable-list">${r.deliverables.map((d,i)=>`<li><span class="deliverable-number">${i+1}</span><div><h3>${esc(d.name)}</h3><span class="deliverable-state ${['available','partial','blocked'].includes(d.state)?d.state:'partial'}">${esc(d.status)}</span><details><summary>Scope & next action</summary><p>${esc(d.detail)}</p>${d.next_action?`<p><b>Next:</b> ${esc(d.next_action)}</p>`:''}</details></div><div class="deliverable-action">${actions[i]||''}</div></li>`).join('')}</ol>
    <p class="subtle-note">The ZIP includes an offline review, demand/growth CSVs, lender explanation, sharing proposal and blank validation templates. Existing analysis, inputs and finance are included. Separate uploaded studies are not attached or certified.</p>
  </article>${lenderExplanationHtml(r,true)}<article class="card" id="sharing-deliverable" tabindex="-1"><div class="card-head"><div><h2>${esc(p.title)}</h2><p>${esc(p.status)}</p></div><a class="button secondary" href="/api/meter-sharing-proposal">Download proposal ↓</a></div><p class="subtle-note">Keep raw customer readings with the operator. Share only approved, disclosure-reviewed site aggregates. The deliverables pack also includes a blank handover worksheet.</p>${detailsHtml('Read the sharing and holdout plan',`<ol>${p.steps.map(s=>`<li><b>${esc(s.title)}</b><p>${esc(s.detail)}</p></li>`).join('')}</ol><p>${esc(p.minimum_data)}</p><p>${esc(p.future_curve_study)}</p><p>${p.references.map(ref=>`<a href="${esc(ref.url)}" target="_blank" rel="noopener">${esc(ref.title)}</a>`).join(' · ')}</p>`)}</article>`;
}
