/* Explicit test presets. Public Juru observations are never overwritten. */
let loadingJuruDemo=false;

// Explicit demo links start a fresh examination case; saved projects stay untouched.
async function openInitialWorkspace(search=''){
  await openDiscovery();
  if(new URLSearchParams(search).get('demo')==='juru')await loadJuruDemo();
}

function juruDemoCardHtml(){
  return `<article class="card"><div class="card-head"><div><h2>Juru demo</h2><p>300 households · 20 inputs · 3-year forecast</p></div><span class="tag">Demo data</span></div><div class="form-actions"><button type="button" class="button primary" data-load-juru-demo>Load Juru test case</button><a class="button secondary" href="/api/demo-cases/juru/download">Download test dataset</a><button type="button" class="text-button" data-open-juru-public>Open public-data screen</button></div><details class="more-details"><summary>Data notes</summary><p>Generated test inputs, not meter readings or surveyed customers. Public sector data stays separate. This is not all of Juru or a verified cell.</p><p>Download gives the original preset. Export report includes your edits.</p></details></article>`;
}

async function loadJuruDemo(){
  if(loadingJuruDemo||discovery.busy||discovery.opening||!contextReady())return;
  loadingJuruDemo=true;
  const wasDiscovering=discovery.active,previousView=state.view;
  if(wasDiscovering)discoveryLock(true);
  else setBusy(true);
  try{
    const packet=await(await api('/api/demo-cases/juru')).json();
    const {financial_evidence,...project}=packet.project;
    state.view='overview';
    // calculate() owns its own busy lock; release the download lock first.
    setBusy(false);
    if(await updateProjectContext({...project,financialEvidence:financial_evidence||null})){
      if(wasDiscovering)discoveryMode(false);
      ensureCustomOption();render();
      toast('Juru demo ready.');
    }else state.view=previousView;
  }catch(e){state.view=previousView;error(e.message);}
  finally{
    loadingJuruDemo=false;
    if(wasDiscovering)discoveryLock(false);
    setBusy(false);
  }
}

function bindJuruDemoButtons(root){
  root.querySelectorAll('[data-load-juru-demo]').forEach(b=>b.addEventListener('click',loadJuruDemo));
  root.querySelectorAll('[data-open-juru-public]').forEach(b=>b.addEventListener('click',openJuruPublicScreen));
}

async function openJuruPublicScreen(){
  if(loadingJuruDemo||discovery.busy||discovery.opening||!contextReady())return;
  setBusy(true);
  try{
    const location=await(await api('/api/geography/location?country=RW&id=11186926')).json();
    setBusy(false);
    await openLocationDashboard(location,{projectMode:'public_proxy'});
  }catch(e){error(e.message);}
  finally{setBusy(false);}
}

function juruCaseSummaryHtml(r,compact=false){
  const c=r.demo_case;if(!c)return '';
  const rows=c.features||[];
  const complete=rows.filter(row=>row.value!=null&&row.value!=='').length;
  const notes=`<p>${esc(c.notice)}</p><p>${esc(c.scope)}</p><p>${esc(r.context.currency)} · Low / expected / high are scenarios, not calibrated confidence limits. Growth and seasonality are assumptions.</p><p>Export report includes your edits.</p><a class="button secondary" href="/api/demo-cases/juru/download">Download original test dataset</a>`;
  if(compact)return `<details class="card more-details"><summary>Juru demo · ${complete}/20 inputs · data notes</summary>${notes}</details>`;
  return `<article class="card"><div class="card-head"><div><h2>Juru demo data</h2><p>${number(r.site.households)} households · ${complete}/20 features supplied</p></div><span class="tag">Demo data</span></div>${notes}<details class="more-details"><summary>All 20 input values</summary><div class="table-wrap"><table><thead><tr><th>Feature</th><th>Current demo value</th><th>Unit</th></tr></thead><tbody>${rows.map(row=>`<tr><th scope="row">${number(row.feature_number)}. ${esc(row.feature)}</th><td>${row.value==null?'Not supplied':esc(row.value)}</td><td>${esc(row.unit)}</td></tr>`).join('')}</tbody></table></div></details></article>`;
}

function renderJuruCasePanels(){
  if(!state.result?.demo_case)return;
  $('#view-community').insertAdjacentHTML('beforeend',juruCaseSummaryHtml(state.result,true));
  $('#view-evidence').insertAdjacentHTML('afterbegin',juruCaseSummaryHtml(state.result));
}
