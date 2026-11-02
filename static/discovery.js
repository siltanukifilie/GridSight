/* East Africa administrative selection; no map, device location or coordinate entry. */
const discovery={active:false,busy:false,opening:false,epoch:0,country:'RW',area:'',local:'',location:null,areas:[],locals:[],places:[],next:null,query:'',assumed:[],provenance:null};
const gridLabels={unknown:'Needs verification',reported_unserved:'Reported unserved',planned:'Grid expansion reported',connected:'Main grid connected'};
const siteInputLabels={households:'Households',shops:'Businesses',schools:'Schools',clinics:'Clinics',mills:'Mills',pumps:'Irrigation pumps',cold_rooms:'Cold rooms',uptake:'Household connection rate',appliance_index:'Legacy appliance index'};
function discoveryMode(active){
  discovery.active=active;document.body?.classList.toggle('discovery-mode',active);
  $('#discovery-panel').hidden=!active;$('#role-select').disabled=state.busy;
  document.querySelectorAll('.nav-item').forEach(b=>{b.disabled=active&&b.dataset.view!=='locations';if(active){b.classList.toggle('active',b.dataset.view==='locations');}});
}
function discoveryLock(value){
  discovery.busy=value;$('#discovery-panel').querySelectorAll('button,input,select').forEach(e=>e.disabled=value);
  if(!value){$('#discover-area').disabled=!discovery.areas.length;$('#discover-local').disabled=!discovery.area||!discovery.locals.length;$('#discover-place').disabled=!discovery.local||!discovery.places.length;}
}
function optionsHtml(rows,placeholder,value=''){return '<option value="">'+esc(placeholder)+'</option>'+rows.map(r=>'<option value="'+esc(r.id)+'" '+(r.id===value?'selected':'')+'>'+esc(r.name)+'</option>').join('');}
function clearDiscoverySite(){discovery.location=null;discovery.assumed=[];$('#site-setup').innerHTML='';$('#place-preview').innerHTML='';}
async function openDiscovery(){
  if(!contextReady()||discovery.busy)return;
  discoveryMode(true);applyWorkspace();error('');
  discovery.country=state.context?.country_code||'RW';
  const countries=Object.fromEntries(state.contextSettings.active_countries.map(code=>[code,state.contextSettings.countries[code]]));
  $('#crumb').textContent='Choose location';$('#footer-context').textContent='East Africa · estimates need field validation';
  $('#discovery-panel').innerHTML=`<div class="input-workspace"><aside class="input-panel location-panel"><h2>Site</h2><p class="panel-intro">East Africa · eight EAC countries</p><div class="field"><label for="discover-country">Country</label><select id="discover-country">${Object.entries(countries).map(([code,c])=>`<option value="${code}" ${code===discovery.country?'selected':''}>${esc(c.name)}</option>`).join('')}</select></div><div class="field"><label id="area-label" for="discover-area">District</label><select id="discover-area" disabled></select></div><div class="field"><label id="local-label" for="discover-local">Sector</label><select id="discover-local" disabled></select></div><div class="field"><label id="cell-label" for="discover-place">Cell</label><select id="discover-place" disabled></select></div><div id="finder-status" role="status" aria-live="polite"></div><p id="coverage-note" class="panel-note"></p><div id="place-preview"></div>
  <details class="input-group"><summary>Missing from the list?</summary><p class="panel-note">Enter local administrative names. These remain unverified.</p><form id="named-location"><div class="field"><label for="named-area">District / local equivalent</label><input id="named-area" name="area" maxlength="100" required></div><div class="field"><label for="named-local">Sector / local equivalent</label><input id="named-local" name="local" maxlength="100" required></div><div class="field"><label for="named-cell">Cell / local equivalent</label><input id="named-cell" name="cell" maxlength="100" required></div><button class="button primary" type="submit">Use these names</button></form></details>
  <details class="input-group"><summary>Location data & coverage</summary><p id="location-attribution" class="panel-note"></p><p class="panel-note">Rwanda uses district, sector and cell; other countries use local equivalents. Rwanda has building/facility proxies; elsewhere inputs begin as assumptions. Verify utility coverage and local records.</p></details></aside>
  <div class="input-content"><div class="location-welcome"><h1>Choose a location</h1><p>Estimate demand and review the project.</p><div class="workflow-steps"><div class="workflow-step"><span>1</span><strong>Choose a location</strong></div><div class="workflow-step"><span>2</span><strong>Check the inputs</strong></div><div class="workflow-step"><span>3</span><strong>Review demand & finance</strong></div></div></div><div id="site-setup"></div><article class="card"><h2>Continue a project</h2><div class="form-actions">${state.result?'<button class="button secondary" id="return-project">Back to current project</button>':''}<button class="button secondary" id="restore-project">Restore saved project</button><button class="text-button" id="open-demo">Explore synthetic demo ↗</button></div></article></div></div>`;
  if(typeof juruDemoCardHtml==='function'){
    $('#discovery-panel').querySelector('.location-welcome').insertAdjacentHTML('afterend',juruDemoCardHtml());
    bindJuruDemoButtons($('#discovery-panel'));
  }
  if(typeof bugeseraRankingHtml==='function'){
    const content=$('#discovery-panel').querySelector('.input-content');
    content.insertAdjacentHTML('beforeend','<details class="more-details"><summary>Compare Bugesera sectors</summary>'+bugeseraRankingHtml(state.bootstrap.bugesera_ranking)+'</details>');
    bindRankingButtons(content,state.bootstrap.bugesera_ranking);
  }
  $('#discover-country').addEventListener('change',()=>loadDiscoveryCountry($('#discover-country').value));
  $('#discover-area').addEventListener('change',chooseDiscoveryArea);
  $('#discover-local').addEventListener('change',async()=>{++discovery.epoch;discovery.local=$('#discover-local').value;discovery.places=[];clearDiscoverySite();await loadDiscoveryPlaces();});
  $('#discover-place').addEventListener('change',()=>{if($('#discover-place').value)chooseDiscoveryPlace($('#discover-place').value);});
  $('#named-location').addEventListener('submit',e=>{e.preventDefault();const f=e.target.elements;openLocationDashboard({country_code:discovery.country,source:'user_entered_administration',label:f.cell.value,administrative_path:[f.area.value,f.local.value,f.cell.value]});});
  if(state.result)$('#return-project').addEventListener('click',()=>{discoveryMode(false);render();});
  $('#restore-project').addEventListener('click',restoreDiscoveryProject);
  $('#open-demo').addEventListener('click',async()=>{if(discovery.busy)return;state.view='overview';await selectSite('RW-DEMO-02');if(!state.dirty){discoveryMode(false);render();}});
  await loadDiscoveryCountry(discovery.country);
}
async function loadDiscoveryCountry(code){
  if(!state.contextSettings.active_countries.includes(code))return;
  const token=++discovery.epoch;Object.assign(discovery,{country:code,area:'',local:'',areas:[],locals:[],places:[],query:''});clearDiscoverySite();
  const c=state.contextSettings.countries[code];
  $('#country-badge').textContent=code;$('#country-workspace').textContent=c.name+' workspace';
  $('#area-label').textContent=code==='RW'?'District':'District / '+c.area_label;
  $('#local-label').textContent=code==='RW'?'Sector':'Sector / '+c.local_label;
  $('#cell-label').textContent=code==='RW'?'Cell':'Cell / mapped lower area';
  $('#coverage-note').textContent=c.coverage_note;
  $('#discover-area').innerHTML=optionsHtml([],'Loading…');$('#discover-local').innerHTML=optionsHtml([],'Choose district first');$('#discover-place').innerHTML=optionsHtml([],'Choose sector first');
  for(const id of ['named-area','named-local','named-cell'])$('#'+id).value='';
  discoveryLock(true);$('#finder-status').textContent='Loading administrative areas…';
  try{const data=await(await api('/api/geography?country='+code)).json();if(token!==discovery.epoch)return;discovery.areas=data.items;discovery.provenance=data.provenance;
    $('#discover-area').innerHTML=optionsHtml(data.items,'Choose district / area');$('#finder-status').textContent='Choose your district, sector and cell.';
    $('#location-attribution').textContent='GeoNames · CC BY 4.0 · fetched '+data.provenance.fetched_at.slice(0,10)+'. '+data.notice;
  }catch(e){if(token===discovery.epoch)$('#finder-status').textContent=e.message;}finally{if(token===discovery.epoch)discoveryLock(false);}
}
async function chooseDiscoveryArea(){
  const token=++discovery.epoch;discovery.area=$('#discover-area').value;discovery.local='';discovery.locals=[];discovery.places=[];clearDiscoverySite();
  $('#discover-local').innerHTML=optionsHtml([],'Choose sector / local area');$('#discover-place').innerHTML=optionsHtml([],'Choose sector first');
  $('#named-area').value=discovery.areas.find(x=>x.id===discovery.area)?.name||'';$('#named-local').value='';$('#named-cell').value='';
  if(!discovery.area){discoveryLock(false);return;}
  discoveryLock(true);
  try{const data=await(await api('/api/geography?country='+discovery.country+'&kind=local&parent='+discovery.area)).json();if(token!==discovery.epoch)return;discovery.locals=data.items;
    $('#discover-local').innerHTML=optionsHtml(data.items,data.items.length?'Choose sector / local area':'No linked sectors in source');$('#finder-status').textContent=data.items.length?'Choose a sector or local equivalent.':'No linked subdivisions available. Enter the local names below.';
  }catch(e){if(token===discovery.epoch)$('#finder-status').textContent=e.message;}finally{if(token===discovery.epoch)discoveryLock(false);}
}
async function loadDiscoveryPlaces(){
  const token=discovery.epoch;discovery.places=[];$('#discover-place').innerHTML=optionsHtml([],'Choose sector first');
  $('#named-local').value=discovery.locals.find(x=>x.id===discovery.local)?.name||'';$('#named-cell').value='';
  if(!discovery.local){discoveryLock(false);return;}
  discoveryLock(true);
  try{const data=await(await api('/api/geography?country='+discovery.country+'&kind=cells&parent='+discovery.local)).json();if(token!==discovery.epoch)return;discovery.places=data.items;
    $('#discover-place').innerHTML=optionsHtml(data.items,data.items.length?'Choose cell / local area':'No linked cells in source');
    $('#finder-status').textContent=data.items.length?'Select a cell to prepare your dashboard.':'Cell-level records are unavailable here. Enter the local names below; no substitute coordinates are used.';
  }catch(e){if(token===discovery.epoch)$('#finder-status').textContent=e.message;}finally{if(token===discovery.epoch)discoveryLock(false);}
}
async function chooseDiscoveryPlace(id){
  const token=discovery.epoch;discoveryLock(true);
  try{const place=await(await api('/api/geography/location?country='+discovery.country+'&id='+id)).json();if(token===discovery.epoch)await openLocationDashboard(place);}catch(e){if(token===discovery.epoch)$('#finder-status').textContent=e.message;}finally{if(token===discovery.epoch)discoveryLock(false);}
}
function gridFields(grid={status:'unknown',source:'',checked_on:null},prefix='new'){
  return `<div class="input-grid"><div class="field"><label for="${prefix}-grid-status">Main-grid access</label><select id="${prefix}-grid-status" name="grid_status">${Object.entries(gridLabels).map(([k,v])=>`<option value="${k}" ${k===grid.status?'selected':''}>${v}</option>`).join('')}</select></div><div class="field"><label for="${prefix}-grid-date">Checked on</label><input id="${prefix}-grid-date" name="grid_date" type="date" value="${esc(grid.checked_on||'')}"></div></div><div class="field"><label for="${prefix}-grid-source">Source / field note</label><input id="${prefix}-grid-source" name="grid_source" maxlength="240" value="${esc(grid.source||'')}" placeholder="Utility map, field visit or other evidence"></div><p class="subtle-note">A reported status needs a source and date. Claims remain unverified. Connected sites are outside the unserved-site shortlist.</p>`;
}
function gridFromForm(form){return {status:form.elements.grid_status.value,source:form.elements.grid_source.value,checked_on:form.elements.grid_date.value||null};}
async function restoreDiscoveryProject(){
  if(discovery.busy)return;
  try{const saved=JSON.parse(localStorage.getItem('gridsight-scenario-v1'));if(!saved?.site||!saved?.assumptions){toast('No saved project in this browser yet.');return;}
    discoveryLock(true);if(await updateProjectContext({financialEvidence:saved.financial_evidence||null,site:saved.site,detailed:saved.detailed||{enabled:false},connection:saved.connection||{enabled:false},assumptions:saved.assumptions,context:saved.context||emptyContext(),planning:{...state.planningSettings.defaults,...saved.planning}})){discoveryMode(false);ensureCustomOption();state.view='overview';render();}
  }catch(e){error('Could not restore the saved project: '+e.message);}finally{discoveryLock(false);}
}
function siteScreeningHtml(){
  const c=state.result.context,g=c.grid||{status:'unknown'},connected=g.status==='connected',loc=c.location;
  const incomplete=!state.result.assumptions.tariff||!state.result.assumptions.capacity_kwh||!state.result.assumptions.firm_power_kw;
  return `<div class="project-ribbon"><div><span class="eyebrow">${esc(c.country)} · ${esc(c.currency)}</span><h2>${esc(state.site.name)}</h2><p>${esc(loc?.administrative_path?.join(' → ')||state.site.district)}</p></div><span class="screening-badge ${connected?'excluded':''}">${esc(gridLabels[g.status]||gridLabels.unknown)}</span><button class="button secondary" data-go="locations">Site details ↗</button></div><div class="project-next"><b>${connected?'Not an unserved-site candidate':g.status==='planned'?'Review grid-arrival risk':incomplete?'Supply & finances not set':'Next: verify the site'}</b><span>${connected?'Main-grid access is reported. No off-grid development recommendation.':incomplete?'Enter capacity, tariff, costs and financing in Scenarios before interpreting cash or repayment.':'Confirm utility coverage, customer counts and the project budget before committing.'}</span></div>`;
}
