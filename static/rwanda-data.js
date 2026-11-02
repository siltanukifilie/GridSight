/* Public evidence initializes a preliminary screen; it does not validate demand. */
async function openLocationDashboard(location,{projectMode='auto'}={}){
  if(discovery.opening||!contextReady())return;
  discovery.opening=true;const token=discovery.epoch,previousView=state.view;
  discoveryLock(true);$('#finder-status').textContent='Preparing this location’s evidence and dashboard…';
  try{
    const {financial_evidence,...project}=await(await api('/api/location-project',{location,project_mode:projectMode})).json();
    if(token!==discovery.epoch)return;
    const juruDemo=project.site?.id==='RW-JURU-SYNTHETIC-01';
    state.view=juruDemo?'overview':'community';
    if(await updateProjectContext({...project,financialEvidence:financial_evidence||null})){
      discovery.location=location;discoveryMode(false);ensureCustomOption();render();
      toast(juruDemo?'Juru demo loaded · 20 inputs. Public data stays separate.':'Location ready. Review the 20 inputs and financial assumptions.');
    }else{
      state.view=previousView;$('#finder-status').textContent=$('#error-box').textContent||'Dashboard could not be prepared. Your previous project is unchanged.';
    }
  }catch(e){
    state.view=previousView;$('#finder-status').textContent=e.message;
    $('#site-setup').innerHTML='<p class="subtle-note">Automatic data preparation is unavailable. Your previous project is unchanged.</p><button class="button secondary" id="manual-candidate">Choose administrative names instead</button>';
    $('#manual-candidate').addEventListener('click',openDiscovery);
  }finally{discovery.opening=false;discoveryLock(false);}
}

function publicProfileSummaryHtml(){
  const p=state.result?.location_profile;if(!p)return '';
  const f=p.mapped_facilities;
  return `<article class="card local-evidence"><div class="card-head"><div><h2>A first look at this place</h2><p>500 m around the selected point · not a surveyed service area</p></div><span class="tag">Preliminary</span></div><div class="public-stats"><div class="public-stat"><span>Building detections</span><strong>${p.building_detections==null?'Unknown':number(p.building_detections)}</strong><small>Google · 2023 inference</small></div><div class="public-stat"><span>Mapped shops</span><strong>${f==null?'Unknown':number(f.shops)}</strong><small>OSM objects · not a census</small></div><div class="public-stat"><span>Schools / health facilities</span><strong>${f==null?'Unknown':number(f.schools)+' / '+number(f.clinics)}</strong><small>Mapped objects · verify operation</small></div><div class="public-stat"><span>Financial inputs</span><strong class="evidence-word">Illustrative</strong><small>Replace with your project budget</small></div></div><p class="subtle-note">${esc(p.historical_grid.status)}. ${p.historical_grid.on_grid_records?'Check existing grid service before treating this as an opportunity.':'Current grid coverage is unverified.'} Demand uses public-data proxies and editable assumptions, not measured consumption.</p><div class="form-actions"><button class="button secondary" data-go="community">Review demand inputs</button><button class="text-button" data-go="locations">See data & sources ↗</button></div></article>`;
}

function rwandaDataHtml(){
  if(state.result?.context.country_code!=='RW')return '';
  const p=state.result?.location_profile,pack=p?.data_pack||state.bootstrap?.public_sources;
  if(!pack)return '';
  return `<article class="card"><div class="card-head"><div><h2>Rwanda data pack</h2><p>Collected evidence. Visible gaps.</p></div><a class="button secondary" href="/api/rwanda-data/download">Download source pack ↓</a></div>${p?`<p class="subtle-note">${esc(p.notice)}</p><details class="more-details"><summary>How this place’s inputs were prepared</summary><div class="table-wrap"><table><thead><tr><th>Input</th><th>Starting value</th><th>Current value</th><th>Basis</th></tr></thead><tbody>${p.input_basis.map(b=>`<tr><td>${esc(siteInputLabels[b.field]||b.field)}</td><td>${number(b.value,Number.isInteger(b.value)?0:2)}</td><td>${number(state.site[b.field],Number.isInteger(state.site[b.field])?0:2)}</td><td><b>${esc(b.kind)}</b><small class="block-note">${esc(b.basis)}</small></td></tr>`).join('')}</tbody></table></div><p class="subtle-note">Original suggestions remain separate from your edits. All counts require field verification. No meter data was used.</p></details>`:''}<p class="subtle-note"><a href="/api/rwanda-data/buildings">Download building points · NumPy dataset ↓</a> · Coordinates, area and confidence; column definitions and licence in the source pack.</p><div class="table-wrap"><table class="source-table"><thead><tr><th>Layer</th><th>Status</th><th>Coverage / use</th></tr></thead><tbody>${pack.layers.map(s=>`<tr><td><b>${esc(s.name)}</b><small class="block-note">${s.url?`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.provider)} ↗</a>`:esc(s.provider)}</small></td><td>${esc(s.status)}${s.records!=null?`<small class="block-note">${number(s.records)} records</small>`:''}</td><td>${esc(s.use)}<small class="block-note">${esc(s.date||'Date not available')} · ${esc(s.license)}</small></td></tr>`).join('')}</tbody></table></div><p class="subtle-note">${esc(pack.notice)}</p></article>`;
}
