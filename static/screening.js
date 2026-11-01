/* Public screening and operator handover. Never writes demand/finance inputs. */
function bugeseraRankingHtml(packet, canChoose=true){
  if(!packet||packet.status!=='available')return `<article class="card"><h2>Bugesera sector screening</h2><p>${esc(packet?.reason||'Ranking unavailable. No substitute scores are shown.')}</p></article>`;
  const val=(x,d=1)=>x==null?'Unavailable':number(x,d);
  return `<article class="card bugesera-ranking"><div class="card-head"><div><h2>Bugesera sector screening</h2><p>15 sectors · public context · not measured demand</p></div><a class="button secondary" href="/api/bugesera-ranking/download">Download ranking & method</a></div><p>${esc(packet.notice)}</p>
    <p class="subtle-note">${esc(packet.limitations[0])}</p>
    ${packet.selected_site_id?`<p>Project sector context: <b>${esc(packet.rows.find(r=>r.site_id===packet.selected_site_id)?.site_name||'')}</b>. ${esc(packet.match_basis)}</p>`:''}
    <div class="table-wrap"><table><caption>Existing screening score, not an investment recommendation</caption><thead><tr><th>Rank</th><th>Sector</th><th>Score / 100</th><th>Buildings / km²</th><th>Nighttime lights<br>nW/cm²/sr</th><th>Historical grid<br>reference · km</th><th>Review</th></tr></thead><tbody>${packet.rows.map(row=>`<tr><td>${number(row.priority_rank)}</td><th scope="row">${esc(row.site_name)}${row.site_id===packet.selected_site_id?' · current':''}</th><td>${val(row.priority_score)}</td><td>${val(row.building_density_per_km2)}</td><td>${val(row.nighttime_light_radiance_gep_mean_nw_cm2_sr,3)}</td><td>${val(row.gridfinder_reference_point_distance_km,2)}</td><td><details><summary>Score drivers</summary><ul>${row.contributions.map(c=>`<li>${esc(c.label)}: ${val(c.points)} points</li>`).join('')}</ul><p>Not grid connected (2022): ${val(row.not_grid_connected_households_percent_2022)}%. Sector households: ${val(row.households_2022,0)}. These are not project customers.</p><p>Mills: ${val(row.milling_places_total)}. Farming generators: ${val(row.farming_generators_total)}.</p></details>${canChoose?`<button type="button" class="text-button" data-review-sector="${esc(row.site_id)}">Choose a cell in ${esc(row.site_name)}</button>`:''}</td></tr>`).join('')}</tbody></table></div>
    <details><summary>Method, weights and data limitations</summary><p>${esc(packet.method)}</p><ul>${packet.components.map(c=>`<li>${esc(c.label)}: ${number(c.weight*100)}%</li>`).join('')}</ul><ul>${packet.limitations.slice(1).map(s=>`<li>${esc(s)}</li>`).join('')}</ul><p>Source snapshot: ${esc(packet.source_version)}. Method: ${esc(packet.method_version)}. Source records and full precision scores are in the download.</p></details></article>`;
}

function operatorPilotHtml(p){
  if(!p)return '';
  return `<article class="card"><div class="card-head"><div><h2>${esc(p.title)}</h2><p>${esc(p.status)}</p></div><a class="button secondary" href="/api/operator-pilot/download">Download operator pilot pack</a></div><p>${esc(p.request)}</p><p>${esc(p.operator_value)}</p><details><summary>Permissions, minimum data and review gates</summary><p>${esc(p.scope)}</p><dl>${p.data_contract.map(d=>`<dt><b>${esc(d.item)}</b></dt><dd>${esc(d.detail)}</dd>`).join('')}</dl><ol>${p.gates.map(g=>`<li><b>${esc(g.stage)} · ${esc(g.owner)}</b><p>${esc(g.exit)}</p></li>`).join('')}</ol><p>${esc(p.stop_rules)}</p></details><a class="source-link" href="/api/operator-pilot" target="_blank" rel="noopener">Read / print full proposal</a><p class="subtle-note">Includes a draft request, blank handover worksheet and compatible monthly validation templates. No message is sent and no operator partnership is claimed.</p></article>`;
}

function assessmentHtml(a){
  if(!a)return '';
  return `<article class="card"><h2>Brief 03 assessment checklist</h2><p>${esc(a.notice)}</p><div class="table-wrap"><table><thead><tr><th>Criterion</th><th>Weight</th><th>Evidence to demonstrate</th><th>Remaining gap</th></tr></thead><tbody>${a.criteria.map(c=>`<tr><th scope="row">${esc(c.criterion)}</th><td>${number(c.weight_percent)}%</td><td>${esc(c.evidence)}<br><button class="text-button" data-go="${esc(c.view)}">Open evidence</button></td><td>${esc(c.gap)}</td></tr>`).join('')}</tbody></table></div><p>${esc(a.submission)}</p><p class="subtle-note">${esc(a.source)}</p></article>`;
}

function renderScreeningPanels(){
  const r=state.result;
  $('#view-locations').insertAdjacentHTML('afterbegin',bugeseraRankingHtml(r.bugesera_ranking));
  $('#view-evidence').insertAdjacentHTML('afterbegin',assessmentHtml(r.assessment)+operatorPilotHtml(r.operator_pilot));
  const packet=r.bugesera_ranking;
  if(packet?.status==='available'){
    const current=packet.rows.find(row=>row.site_id===packet.selected_site_id);
    $('#view-overview').insertAdjacentHTML('beforeend',`<article class="card"><div class="card-head"><div><h2>Bugesera screening shortlist</h2><p>${current?esc(current.site_name)+' · sector screening rank '+number(current.priority_rank)+' of 15':'15 administrative sectors available for review'}</p></div><button class="button secondary" data-go="locations">Review ranking</button></div><p>Public building, activity and access proxies. Not measured Rwanda demand or an investment recommendation. Sector totals do not change this project.</p><button class="text-button" data-go="evidence">Operator pilot & assessment checklist</button></article>`);
  }
  bindRankingButtons($('#view-locations'),packet);
}

function bindRankingButtons(root,packet){
  root.querySelectorAll('[data-review-sector]').forEach(button=>button.addEventListener('click',async()=>{
    const row=packet?.rows.find(r=>r.site_id===button.dataset.reviewSector);
    if(!row||state.busy||discovery.busy||!contextReady())return;
    button.disabled=true;
    try{
      await openDiscovery();
      if(!discovery.active)return;
      if(discovery.country!=='RW')await loadDiscoveryCountry('RW');
      const area=discovery.areas.find(a=>['bugesera','bugesera district'].includes(a.name.toLowerCase()));
      if(area){$('#discover-area').value=area.id;await chooseDiscoveryArea();
        const local=discovery.locals.find(a=>a.name.toLowerCase()===row.site_name.toLowerCase());
        if(local){$('#discover-local').value=local.id;discovery.local=local.id;await loadDiscoveryPlaces();}
      }
      $('#named-area').value='Bugesera';$('#named-local').value=row.site_name;$('#named-cell').value='';
      $('#finder-status').textContent='Screening '+row.site_name+'. Choose a real cell, or enter its names below if not listed. Your existing project is unchanged until you open a new location.';
      $('#discover-place').focus();
    }catch(e){error(e.message);}finally{button.disabled=false;}
  }));
}
