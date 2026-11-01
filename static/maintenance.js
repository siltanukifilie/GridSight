/* Exploratory batch diagnostics only. Registry approval stays an explicit local workflow. */
let updateResult = null;

function maintenanceHtml() {
  return `<article class="card"><div class="card-head"><div><h2>Keep the model accountable</h2><p>New data → candidate → quality checks → review</p></div><span class="tag">No automatic deployment</span></div>
    <p>Version real-data updates. Catch worse forecasts before approving a candidate.</p>
    <p class="subtle-note">Recalibrates growth and prediction ranges—not a new 20-input ML model. No genuine operator dataset is bundled. This browser check is exploratory; formal updates must freeze the protocol in the private local registry before outcomes are reviewed.</p>
    <a class="button secondary" href="/api/update-template">Get update & review pack ↓</a>
    <details><summary>Check an update candidate</summary><p>Use fresh whole-site fit, calibration and test groups. Choose acceptance thresholds before inspecting outcomes. Reusing test results for tuning invalidates an independent test.</p>
    <form id="update-form"><div class="compact-grid">
    <div class="field"><label for="update-sites">Pre-connection site inputs · JSON</label><input type="file" id="update-sites" name="sites" accept=".json" required></div>
    <div class="field"><label for="update-csv">Monthly meter totals · CSV</label><input type="file" id="update-csv" name="csv" accept=".csv" required></div>
    <div class="field"><label for="update-spec">Release specification · JSON</label><input type="file" id="update-spec" name="spec" accept=".json" required></div></div>
    <button type="submit" class="button secondary">Check candidate · do not deploy</button></form><p id="update-error" role="alert"></p><div id="update-results" aria-live="polite"></div></details>
    <details><summary>Review cycle & safe rollback</summary><ol><li>Monthly: check missing data, outages, permissions and local surveys.</li><li>Quarterly, if enough complete histories exist: freeze a new protocol and evaluate an immutable candidate.</li><li>Review errors, coverage, country and age-group checks. Record a separate review decision.</li><li>Select or roll back an approved registry version explicitly. The live dashboard is unchanged.</li></ol><p class="subtle-note">This is a manual workflow, not an active scheduled job. Detailed instructions are in the update pack.</p></details>
  </article>`;
}

function updateResultsHtml(r) {
  const m=r.metrics, adjusted=m.growth_adjusted;
  return `<h3>${esc(r.release.version_id)} · ${r.performance_gates_passed?'Numerical checks passed':'Quality checks failed'}</h3>
    <p class="demo-notice">Exploratory only. Not predeclared in a registry, not approved, and not deployed. Source authenticity is unverified.</p>
    <div class="data-stat-row"><span>Weighted forecast error</span><b>${adjusted.wape_pct==null?'Undefined':number(adjusted.wape_pct,1)+'%'}</b></div>
    <div class="data-stat-row"><span>Whole-site paths covered</span><b>${number(m.site_path_coverage_pct,1)}% · ${m.n_sites} test sites</b></div>
    <p class="subtle-note">Coverage 95% interval: ${m.site_coverage_ci95_pct.map(v=>number(v,1)+'%').join(' – ')}. ${esc(r.method)}.</p>
    <details><summary>Quality gates · including country and service age</summary><div class="table-wrap"><table><thead><tr><th>Check</th><th>Observed</th><th>Required</th><th>Result</th></tr></thead><tbody>${r.gates.map(g=>`<tr><td>${esc(g.name)}</td><td>${g.value==null?'Undefined':number(g.value,2)}</td><td>${esc(g.operator)} ${number(g.threshold,2)}</td><td>${esc(g.status)}</td></tr>`).join('')}</tbody></table></div></details>
    <p class="subtle-note">Versioned data and code fingerprints are included in the download. No raw monthly meter rows are retained in this result. Small-cohort aggregates may still be sensitive.</p><button id="update-download" class="button secondary">Download candidate diagnostics</button>`;
}

function bindMaintenance() {
  const form=$('#update-form');if(!form)return;
  const show=()=>{if(!updateResult)return;$('#update-results').innerHTML=updateResultsHtml(updateResult);$('#update-download').addEventListener('click',()=>{if(contextReady()&&updateResult)downloadJson(updateResult,'gridsight-update-'+updateResult.release.version_id+'.json');});};
  form.addEventListener('input',()=>{updateResult=null;$('#update-results').innerHTML='';});
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(!contextReady())return;
    updateResult=null;$('#update-results').innerHTML='';$('#update-error').textContent='';setBusy(true);
    try{
      const read=async(name,limit)=>{const f=form.elements[name].files[0];if(!f||f.size>limit)throw new Error('Choose all update files within the size limits (site inputs 140 KB, CSV 90 KB, specification 15 KB).');return f.text();};
      const [sites,csv,specText]=await Promise.all([read('sites',140000),read('csv',90000),read('spec',15000)]);
      const spec=JSON.parse(specText);if(!spec||Array.isArray(spec)||Object.keys(spec).sort().join(',')!=='plan,policy,release')throw new Error('Release specification must contain only plan, policy and release.');
      updateResult=await(await api('/api/evaluate-update',{manifest:JSON.parse(sites),csv,...spec})).json();show();
    }catch(e){$('#update-error').textContent=e.message;}finally{setBusy(false);}
  });
  show();
}
