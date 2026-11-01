/* Public context is opt-in. It never becomes synthetic model training evidence. */
function emptyContext(){return {country_code:'RW',location:null,assumed_fields:[],input_origin:'synthetic',public_data_id:null};}
function countryDefaults(){const defaults=state.contextSettings?.defaults[state.context?.country_code||'RW'] || state.bootstrap.defaults;return state.context?.input_origin==='user_entered'?{...defaults,tariff:0,variable_cost:0,fixed_cost:0,debt_payment:0,capacity_kwh:0,firm_power_kw:0}:defaults;}
function moneyUnit(){return state.result?.context?.currency || 'RWF';}
function moneyText(label){return label.replaceAll('RWF',moneyUnit());}
function countryMarkup(html){return html;}
function contextReady(){if(state.busy||state.dirty){toast('Apply your current changes first.');return false;}return true;}
async function updateProjectContext(changes){
  const previous={financialEvidence:state.financialEvidence,context:state.context,site:state.site,assumptions:state.assumptions,planning:state.planning,detailed:state.detailed,connection:state.connection,result:state.result};
  Object.assign(state,changes);await calculate();
  if(state.dirty){Object.assign(state,previous);state.dirty=false;state.dirtyView=null;setBusy(false);return false;}
  return true;
}
function downloadJson(value,name){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
function publicDataHtml(data){
  if(!data)return '<p class="subtle-note">No public statistics loaded. Fetch national context when you need it.</p>';
  return `<div class="public-stats">${data.indicators.map(i=>`<div class="public-stat"><span>${esc(i.label)}</span><strong>${number(i.value,i.unit==='people'?0:1)}</strong><small>${esc(i.unit)} · ${i.year}</small><a href="${esc(i.source_url)}" target="_blank" rel="noopener">World Bank · CC BY 4.0 ↗</a></div>`).join('')}</div><p class="subtle-note">Fetched ${esc(data.fetched_at)}. ${esc(data.transformation)} ${data.missing_indicators.length?'Some indicators are unavailable.':''}</p>`;
}
function renderLocations(){
  if(!state.contextSettings)return;
  const c=state.result.context,loc=c.location,g=c.grid,dev=state.role==='developer';
  $('#view-locations').innerHTML=`<div class="dashboard-grid"><div><article class="card"><div class="card-head"><h2>Country → District → Sector → Cell</h2><button class="button secondary" id="find-new-site">Choose another location ↗</button></div><h3>${esc(c.country)}</h3><p>${esc(loc?.administrative_path?.join(' → ')||state.site.district)}</p><p class="subtle-note">${esc(loc?.label||'No selected location')} · ${esc(loc?.source||'Synthetic demo')}. Administrative records are not a surveyed service area.</p><p class="subtle-note">Rwanda locations can use public building/facility proxies. Other countries and manually entered names use labelled assumptions. No existing project data is reused.</p></article><article class="card"><div class="card-head"><h2>Grid-access check</h2><span class="tag">${esc(gridLabels[g.status])}</span></div>${dev?`<form id="grid-form">${gridFields(g,'edit')}<button class="button secondary" type="submit">Save grid check</button></form>`:`<p>${esc(g.source||'No evidence supplied')} · ${esc(g.checked_on||'No date')}</p>`}<p class="subtle-note">Verify main-grid access and expansion plans. Selection is not proof of an unserved community.</p></article></div><div><article class="card"><h2>Public country context</h2>${publicDataHtml(state.result.public_data)}<div class="form-actions"><button class="button secondary" id="fetch-public">Fetch public context</button>${state.result.public_data?'<button class="text-button" id="download-public">Download snapshot</button>':''}</div><p class="subtle-note">Only the country code is sent to the World Bank. National data does not estimate village demand.</p></article><article class="card"><h2>Coverage</h2><p>${esc(state.contextSettings.countries[c.country_code].coverage_note)}</p><p class="subtle-note">No real metered-site validation. Manually entered administrative names are unverified and have no inferred coordinates.</p></article></div></div>`+rwandaDataHtml();
  $('#find-new-site').addEventListener('click',openDiscovery);
  if(dev){$('#grid-form').addEventListener('input',markDirty);$('#grid-form').addEventListener('submit',async e=>{e.preventDefault();if(state.busy)return;state.context={...state.context,grid:gridFromForm(e.target)};await calculate();if(!state.dirty)toast('Grid check saved as user-reported evidence.');});}
  $('#fetch-public').addEventListener('click',fetchPublicContext);
  if(state.result.public_data)$('#download-public').addEventListener('click',()=>downloadJson(state.result.public_data,'gridsight-public-context.json'));
}
async function applyLocation(location){if(!contextReady())return;if(await updateProjectContext({context:{...state.context,location,grid:{status:'unknown',source:'',checked_on:null}}}))toast(location?'Planning location saved. Demand inputs are unchanged.':'Location cleared.');}
async function fetchPublicContext(){
  if(!contextReady())return;setBusy(true);let snapshot;
  try{snapshot=await(await api('/api/public-data?country='+state.context.country_code)).json();}catch(e){error(e.message);}finally{setBusy(false);}
  if(snapshot&&await updateProjectContext({context:{...state.context,public_data_id:snapshot.id}}))toast('Public context loaded. Demand forecast unchanged.');
}
function contextChrome(){
  const c=state.result.context;if(!c)return;
  $('#district-tag').textContent=state.site.district+' · '+c.country_code;
  $('#country-badge').textContent=c.country_code;$('#country-workspace').textContent=c.country+' workspace';
  $('#footer-context').textContent=(state.result.detailed?.enabled?'Engineering scenario · ':'Synthetic model · ')+c.currency;
  $('#input-origin').textContent=c.input_origin==='synthetic'?'Synthetic inputs':c.input_origin==='public_proxy'?'Public proxies + assumptions':'Planning inputs';
}

function thinDataIntro(){return `<div class="thin-intro"><label class="check-line"><input type="checkbox" id="thin-mode"> I don’t know every input yet.</label><p class="subtle-note">Keep the household count. Leave other unknown values blank, review suggestions, then apply. Zero means you know there are none.</p><div id="thin-proposals" aria-live="polite"></div></div>`;}
function bindThinMode(){
  $('#thin-mode').addEventListener('change',e=>{document.querySelectorAll('#community-form input[data-kind="site"]').forEach(input=>{if(input.name!=='households')input.required=!e.target.checked;});$('#thin-proposals').innerHTML='';markDirty();});
}
async function submitCommunity(event){
  event.preventDefault();const form=event.target;
  const values={...state.site,id:'CUSTOM',archetype:'Custom',name:form.elements.name.value,district:form.elements.district.value};
  const unknown=[];
  Object.keys(state.bootstrap.site_limits).forEach(key=>{const input=form.elements[key];if(input.value.trim()===''){unknown.push(key);values[key]=null;}else values[key]=Number(input.value)/(input.dataset.percent==='true'?100:1);});
  if(unknown.length){
    if(!$('#thin-mode').checked){error('Complete the inputs or enable the missing-input guide.');return;}
    setBusy(true);
    try{const prepared=await(await api('/api/prepare-inputs',{site:values})).json();$('#thin-proposals').innerHTML=`<h3>Review these assumptions</h3><div class="table-wrap"><table><thead><tr><th>Unknown input</th><th>Proposed value</th></tr></thead><tbody>${prepared.assumptions.map(a=>`<tr><td>${esc(a.field.replaceAll('_',' '))}<small class="block-note">${esc(a.reason)}</small></td><td>${a.value}</td></tr>`).join('')}</tbody></table></div><p class="subtle-note">${esc(prepared.notice)}</p><button class="button secondary" type="button" id="accept-thin">Fill suggested values for review</button>`;$('#accept-thin').addEventListener('click',()=>{for(const a of prepared.assumptions){const input=form.elements[a.field];input.value=a.value*(input.dataset.percent==='true'?100:1);}state.context.assumed_fields=[...new Set([...state.context.assumed_fields,...prepared.assumed_fields])];$('#thin-proposals').innerHTML='<p class="subtle-note">Suggestions filled and marked as assumptions. Review, edit if needed, then Estimate demand.</p>';markDirty();});}catch(e){error(e.message);}finally{setBusy(false);}return;
  }
  state.site=values;state.context={...state.context,input_origin:'user_entered'};await calculate();
  if(!state.dirty){ensureCustomOption();toast('Community analysis updated.');navigate('overview');}
}

function validationHtml(){return `<article class="card validation-card"><div class="card-head"><div><h2>Legacy reference-model comparison</h2><p>Held-out sites · frozen reference model · annual averages</p></div><span class="tag">Your data needed</span></div><p class="subtle-note">One row per independent site: 12 complete historical months of customer-side energy, plus the nine community inputs. Do not upload names, account numbers or household-level records. Maximum 100 sites / 50 KB. Processed by this local app; not saved to disk or sent to public providers.</p><a class="source-link" href="/api/validation-template">Download blank CSV template ↓</a>${detailsHtml('CSV instructions','<p>Use anonymous site_id, country_code RW, UG, KE, TZ, BI, SS, SO or CD, inclusive period_start and period_end (YYYY-MM-DD), and actual_kwh as the total over exactly 12 full calendar months. Enter customer counts, uptake (0–1) and appliance_index (0.5–2) with matching definitions. Counts must represent the period; document changes in your source. Consumption is normalized to a 365/12-day month. Incomplete or unknown inputs are rejected.</p>')}<form id="validation-form"><div class="input-grid"><div class="field"><label for="meter-source">Dataset or study name</label><input id="meter-source" name="source" minlength="3" maxlength="160" required placeholder="Anonymous site aggregates · source/version"></div><div class="field"><label for="meter-file">Measured aggregates · CSV</label><input id="meter-file" name="file" type="file" accept=".csv,text/csv" required></div></div><label class="check-line"><input type="checkbox" name="attestation" required> I have permission to use these measured, anonymized aggregates. Sites are independent of model development; coverage is complete and inputs use the stated definitions.</label><button class="button primary" type="submit">Compare consumption</button></form><div id="validation-results" aria-live="polite"></div></article><article class="card commercial-card"><div class="card-head"><div><h2>Who pays—and for what?</h2><p>Commercial hypothesis · not confirmed revenue</p></div></div><div class="data-stat-row"><span>Primary buyer</span><b>Mini-grid developer</b></div><div class="data-stat-row"><span>Starting offer</span><b>Per-project demand & feasibility assessment</b></div><div class="data-stat-row"><span>Repeat use</span><b>Portfolio subscription; lender review licence</b></div><div class="data-stat-row"><span>Paid customer / pricing</span><b>Unconfirmed / not validated</b></div><p class="subtle-note">Next evidence: authorized developer pilot, willingness to pay, and an actual payment or contract. A target buyer is not a paying customer.</p></article>`;}
function renderValidationResult(){
  const r=state.validation;if(!r)return;const m=r.metrics;
  $('#validation-results').innerHTML=`<h3>${esc(r.status)}</h3><p class="subtle-note">${esc(r.source_name)} · ${m.n_sites} sites · model ${esc(r.model_version)}</p><div class="public-stats"><div class="public-stat"><span>Mean absolute error</span><strong>${number(m.mae_kwh)}</strong><small>kWh/month</small></div><div class="public-stat"><span>Weighted error</span><strong>${m.wape_pct==null?'N/A':number(m.wape_pct,1)+'%'}</strong><small>Undefined when total actual energy is zero</small></div><div class="public-stat"><span>Range coverage</span><strong>${number(m.coverage_pct,1)}%</strong><small>Observed in your sample only</small></div></div><p class="subtle-note">Baseline MAE: ${number(m.baseline_mae_kwh)} kWh/month. Bias: ${number(m.bias_kwh)} kWh/month (positive = overprediction). This is an annual-average batch diagnostic, not validation of the selected project or the post-connection curve.</p><ul class="subtle-note">${r.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><button class="button secondary" id="download-validation">Download comparison</button>`;
  $('#download-validation').addEventListener('click',()=>downloadJson(state.validation,'gridsight-consumption-comparison.json'));
}
function bindValidation(){
  $('#validation-form').addEventListener('submit',async e=>{e.preventDefault();if(!contextReady())return;const f=e.target.elements,file=f.file.files[0];if(!file||file.size>50000){error('Choose a CSV file of at most 50 KB.');return;}setBusy(true);try{state.validation=await(await api('/api/validate-consumption',{csv:await file.text(),source_name:f.source.value,attestation:f.attestation.checked})).json();renderValidationResult();}catch(e){error(e.message);}finally{setBusy(false);}});
  renderValidationResult();
}
if(typeof module!=='undefined')module.exports={emptyContext};
