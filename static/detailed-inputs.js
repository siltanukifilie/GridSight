/* Compact, labelled inputs. All calculations remain server-owned. */
const DETAILED_SITE_FIELDS=['households','uptake','shops','mills','pumps','cold_rooms','schools','clinics'];
const DETAILED_LABELS={lighting:'LED lights',phone:'Phone charging',radio:'Radio',television:'Television',refrigerator:'Refrigerator',fan:'Fan',iron:'Iron',other:'Other appliance'};
function detailedDefaults(){return structuredClone(state.planningSettings.detailed_defaults);}
function stepInput(name,label,value,{min=0,max=1e12,step=1,integer=false,optional=false,help='',unit=''}={}){
  const id='detail-'+name;
  return `<div class="field"><label for="${id}">${esc(label)}${unit?' <small>('+esc(unit)+')</small>':''}</label><div class="stepper"><input id="${id}" name="${name}" type="number" min="${min}" max="${max}" step="${integer?1:'any'}" data-increment="${step}" value="${value??''}" ${optional?'placeholder="Unknown"':'required'}><button type="button" data-step="-1" data-input="${id}" aria-label="Decrease ${esc(label)}">−</button><button type="button" data-step="1" data-input="${id}" aria-label="Increase ${esc(label)}">+</button></div>${help?'<small class="panel-note">'+esc(help)+'</small>':''}</div>`;
}
function stepControl(input,direction){
  const min=Number(input.min||0),max=Number(input.max||1e12),step=Number(input.dataset?.increment||input.step)||1;
  const value=input.value===''?0:Number(input.value);
  input.value=String(Number(Math.min(max,Math.max(min,value+direction*step)).toFixed(8)));
  input.dispatchEvent(new Event('input',{bubbles:true}));
}
function bindSteppers(container){
  container.querySelectorAll('[data-step]').forEach(button=>button.addEventListener('click',()=>stepControl(document.getElementById(button.dataset.input),Number(button.dataset.step))));
}
function detailedInputReviewHtml(r){
  const d=r.detailed;if(!d?.enabled)return '';
  const rows=[['Households',r.site.households],['Starting connection rate',number(r.site.uptake*100)+'%'],
    ['Months since connection',d.months_since_connection],['Household income / month',d.household_income_monthly==null?'Unknown':number(d.household_income_monthly)+' '+r.context.currency],
    ['Tariff / kWh',number(r.assumptions.tariff)+' '+r.context.currency],['Connection fee',d.connection_fee==null?'Unknown':number(d.connection_fee)+' '+r.context.currency],
    ['Businesses / mills / pumps',r.site.shops+' / '+r.site.mills+' / '+r.site.pumps],['Schools / clinics',r.site.schools+' / '+r.site.clinics],
    ['New connections / year',d.new_connections_yearly],['Appliance adoption / year',number(d.appliance_adoption_rate*100)+'%'],['Business growth / year',number(r.assumptions.business_growth*100)+'%']];
  return `<article class="card"><div class="card-head"><h2>Applied inputs</h2><span class="tag">20-feature screen</span></div>${rows.map(([label,value])=>`<div class="data-stat-row"><span>${label}</span><b>${esc(value)}</b></div>`).join('')}${detailsHtml('Appliances, equipment & agricultural cycle',`<div class="table-wrap"><table><thead><tr><th>Appliance</th><th>Units / household</th><th>Watts</th><th>Hours/day</th></tr></thead><tbody>${Object.entries(d.appliances).map(([k,v])=>`<tr><td>${DETAILED_LABELS[k]}</td><td>${number(v.units_per_household,2)}</td><td>${number(v.power_w)}</td><td>${number(v.hours_per_day,2)}</td></tr>`).join('')}</tbody></table><table><thead><tr><th>Equipment / site</th><th>kW/unit</th><th>Hours/day</th></tr></thead><tbody>${Object.entries(d.equipment).map(([k,v])=>`<tr><td>${esc(siteInputLabels[k])}</td><td>${number(v.power_kw,2)}</td><td>${number(v.hours_per_day,2)}</td></tr>`).join('')}</tbody></table></div><p>Service-month factors (M1–M12): ${d.agricultural_seasonality.map(v=>number(v,2)).join(', ')}.</p><p>Mills and pumps only. These are assumptions, not measured seasonality.</p>`)} </article>`;
}
function affordabilityHtml(r){
  const a=r.affordability;if(!a)return '';
  return `<article class="card"><div class="card-head"><h2>Household affordability</h2><span class="tag">Screening only</span></div><div class="data-stat-row"><span>Monthly bill / connected household</span><b>${number(a.monthly_bill_per_connected_household)} ${esc(a.currency)}</b></div><div class="data-stat-row"><span>Bill / gross income</span><b>${a.bill_share_of_income==null?'Income needed':number(a.bill_share_of_income*100,1)+'%'}</b></div><div class="data-stat-row"><span>Connection fee / monthly income</span><b>${a.connection_fee_income_months==null?'Inputs needed':number(a.connection_fee_income_months,2)+' months'}</b></div>${detailsHtml('What these numbers mean','<p>'+esc(a.basis)+'</p>')}</article>`;
}
function detailedOverviewHtml(r){
  if(!r.detailed?.enabled)return '';
  return `<article class="card detailed-note"><div class="card-head"><div><h2>Your inputs → your estimate</h2><p>36-month outlook · service Months ${r.horizon.first_service_month}–${r.horizon.last_service_month}</p></div><button class="button secondary" data-go="community">${state.role==='developer'?'Edit 20 inputs':'Review 20 inputs'} ↗</button></div><p class="subtle-note">Counts × power × operating hours. Growth and farm seasonality are assumptions. Low / expected / high is a scenario range, not a calibrated confidence interval.</p></article>`;
}
function detailedCurveHtml(r){
  const m=r.feasibility.monthly_growth;
  return `<article class="card connection-growth"><div class="card-head"><div><h2>Demand after connection</h2><p>Next 36 months · service M${m[0].service_month}–M${m[35].service_month}</p></div><span class="tag">Low / expected / high</span></div>${chart({central:m.map(x=>x.central),lower:m.map(x=>x.lower),upper:m.map(x=>x.upper)},m.map(x=>x.calendar_month||'M'+x.service_month),{unit:'kWh/month',height:230,tickStep:6})}<p class="subtle-note">Connections, appliance adoption, businesses and agricultural cycle. Assumptions—not observed growth.</p></article>`;
}
function renderDetailedCommunity(){
  const r=state.result,d=r.detailed||detailedDefaults(),s=state.site,a=state.assumptions;
  if(state.role==='investor'){
    $('#view-community').innerHTML='<p class="role-notice">Read-only review of the shared project. Switch to developer to change demand inputs.</p>'+detailedInputReviewHtml(r)+affordabilityHtml(r)+lenderExplanationHtml(r);
    return;
  }
  const field=(key,label,options={})=>stepInput('site_'+key,label,key==='uptake'?s[key]*100:s[key],{max:key==='uptake'?100:state.bootstrap.site_limits[key][1],integer:key!=='uptake',...options});
  const group=(title,content,open=false)=>`<details class="input-group" ${open?'open':''}><summary>${title}</summary><div class="group-content">${content}</div></details>`;
  const appliances=Object.entries(d.appliances).map(([key,v])=>group(DETAILED_LABELS[key],stepInput('app_'+key+'_units', 'Units per connected household',v.units_per_household,{max:20,step:.05,help:'Average ownership; 0.25 means one unit per four connected households.'})+stepInput('app_'+key+'_power','Power rating',v.power_w,{max:10000,step:1,unit:'W'})+stepInput('app_'+key+'_hours','Daily running hours',v.hours_per_day,{max:24,step:.25,unit:'hours/day'}))).join('');
  const equipment=Object.entries(d.equipment).map(([key,v])=>group(siteInputLabels[key],stepInput('eq_'+key+'_power','Power per unit',v.power_kw,{max:5000,step:.1,unit:'kW'})+stepInput('eq_'+key+'_hours','Daily running hours',v.hours_per_day,{max:24,step:.25,unit:'hours/day'}))).join('');
  const season=d.agricultural_seasonality.map((v,i)=>stepInput('season_'+i,'Service month '+(i+1),v,{max:2,step:.1})).join('');
  const currentLocation=r.context.location?.administrative_path?.join(' → ')||r.context.country;
  $('#view-community').innerHTML=`<div class="input-workspace"><aside class="input-panel"><div class="panel-title"><h2>Site & inputs</h2><span>20 features</span></div><p class="panel-note">${esc(currentLocation)}</p><button class="button secondary panel-location" type="button" id="detail-change-location">Change country / district / sector / cell</button><p class="panel-note">Illustrative defaults. Replace with your survey. Applied only when you update.</p><form id="detailed-form">
    ${group('Households & connections',field('households','Households in the service area',{help:'The maximum available households, not building detections.'})+field('uptake','Expected household connection rate',{unit:'%',help:'Starting share in service Month 1. New connections are added below.'})+stepInput('months_since_connection','Time since electricity connection',d.months_since_connection,{max:120,integer:true,unit:'months'})+`<label class="slider-label" for="detail-month-slider">Forecast starts in service Month <output id="detail-design-month">${d.months_since_connection+1}</output></label><input type="range" id="detail-month-slider" min="0" max="120" step="1" value="${d.months_since_connection}" aria-label="Months since electricity connection">`,true)}
    ${group('Income & prices',stepInput('household_income_monthly','Monthly household income',d.household_income_monthly,{optional:true,unit:moneyUnit()})+stepInput('tariff','Electricity tariff',a.tariff,{max:1000000,step:.01,unit:moneyUnit()+'/kWh'})+stepInput('connection_fee','Connection fee per household',d.connection_fee,{optional:true,max:1e10,unit:moneyUnit(),help:'One-time affordability cost; not recurring operating revenue.'}),true)}
    ${group('Appliance ownership & use','<p class="panel-note">Units × watts × effective running hours. For cycling appliances, enter equivalent running hours—not 24 hours of standby.</p>'+appliances)}
    ${group('Businesses & public services',field('shops','Number of businesses',{help:'Exclude separately listed mills, pumps and cold rooms.'})+field('mills','Number of milling facilities')+field('pumps','Number of irrigation pumps')+field('cold_rooms','Number of cold rooms')+field('schools','Number of schools')+field('clinics','Number of clinics'))}
    ${group('Equipment power & hours',equipment)}
    ${group('Growth',stepInput('new_connections_yearly','Expected new connections per year',d.new_connections_yearly,{max:1500,help:'Household additions; capped by households in the service area.'})+stepInput('appliance_adoption_rate','Appliance adoption rate',d.appliance_adoption_rate*100,{max:100,step:1,unit:'%/year',help:'Proportional growth in the ownership quantities entered above.'})+stepInput('business_growth','Business growth rate',a.business_growth*100,{min:-20,max:50,step:1,unit:'%/year'}))}
    ${group('Agricultural seasonality','<p class="panel-note">Mills and pumps only. 1 = normal use, 0 = no use, 2 = twice normal. Cycle starts at connection and repeats every 12 service months.</p>'+season)}
    <div class="panel-apply"><button class="button primary run-button" type="submit">Update dashboard ↗</button><small>Demand, growth, finances and report update together.</small></div></form></aside><div class="input-content">${detailedOverviewHtml(r)}${demandPeriodsHtml(r)}${affordabilityHtml(r)}${lenderExplanationHtml(r)}${publicProfileSummaryHtml()}<article class="card"><h2>How the 20 features are used</h2>${detailsHtml('Open feature checklist',`<ol class="feature-list">${r.feature_inventory.map(f=>'<li><b>'+esc(f.name)+'</b><p>'+esc(f.use)+'</p></li>').join('')}</ol>`)}<p class="subtle-note">The earlier synthetic-trained model has nine inputs. This detailed screen uses transparent engineering calculations; it has not been retrained or field-validated on these 20 features.</p></article></div></div>`;
  const form=$('#detailed-form');bindSteppers(form);form.addEventListener('input',markDirty);
  $('#detail-change-location').addEventListener('click',openDiscovery);
  const slider=$('#detail-month-slider'),months=$('#detail-months_since_connection');
  slider.addEventListener('input',()=>{months.value=slider.value;$('#detail-design-month').textContent=Number(slider.value)+1;});
  months.addEventListener('input',()=>{slider.value=months.value;$('#detail-design-month').textContent=Number(months.value)+1;});
  form.addEventListener('submit',async e=>{e.preventDefault();if(state.busy)return;try{Object.assign(state,detailedFormValues(form));await calculate();if(!state.dirty)toast('All 20 inputs applied to the dashboard and reports.');}catch(err){error(err.message);}});
}
function detailedFormValues(form){
  const e=form.elements;
  const value=(name,optional=false)=>{const raw=e[name].value.trim();if(raw===''){if(optional)return null;throw Error('Complete '+name.replaceAll('_',' ')+'.');}const n=Number(raw);if(!Number.isFinite(n))throw Error('Enter a valid number.');return n;};
  const d=structuredClone(state.result.detailed||detailedDefaults());d.enabled=true;
  const site={...state.site};
  for(const key of DETAILED_SITE_FIELDS)site[key]=value('site_'+key)/(key==='uptake'?100:1);
  for(const key of ['months_since_connection','household_income_monthly','connection_fee','new_connections_yearly'])d[key]=value(key,key==='household_income_monthly'||key==='connection_fee');
  d.appliance_adoption_rate=value('appliance_adoption_rate')/100;
  for(const key of Object.keys(d.appliances))d.appliances[key]={units_per_household:value('app_'+key+'_units'),power_w:value('app_'+key+'_power'),hours_per_day:value('app_'+key+'_hours')};
  for(const key of Object.keys(d.equipment))d.equipment[key]={power_kw:value('eq_'+key+'_power'),hours_per_day:value('eq_'+key+'_hours')};
  d.agricultural_seasonality=Array.from({length:12},(_,i)=>value('season_'+i));
  return {site,detailed:d,assumptions:{...state.assumptions,tariff:value('tariff'),business_growth:value('business_growth')/100}};
}
async function enableDetailedInputs(){
  if(!contextReady())return;
  state.detailed={...detailedDefaults(),enabled:true};await calculate();
  if(!state.dirty){state.view='community';render();toast('Detailed engineering mode enabled. Review the new assumptions.');}
}
function legacyDetailedButton(){return '<article class="card detailed-note"><h2>Use the 20-feature inputs</h2><p class="subtle-note">Switch this saved project to the detailed engineering estimate. Review appliance, growth and affordability assumptions before relying on the result.</p><button class="button primary" id="enable-detailed" type="button">Open detailed inputs ↗</button></article>';}
