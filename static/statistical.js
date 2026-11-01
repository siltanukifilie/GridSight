/* Scenario uncertainty and measured-data studies stay separate from finance. */
let uncertaintyResult = null, uncertaintyProjectKey = null, confidenceResult = null;
let statisticalBusy = false;

function statisticalProjectKey() {
  const r=state.result;
  return JSON.stringify([r.site,r.assumptions,r.detailed,r.connection,r.context]);
}

function uncertaintyHtml() {
  if(!state.result.detailed?.enabled)return '';
  const defaults=uncertaintyResult&&uncertaintyProjectKey===statisticalProjectKey()?uncertaintyResult.settings:state.planningSettings?.statistical_defaults;
  if(!defaults)return '<article class="card"><h2>Input uncertainty</h2><p>Refresh to load the new uncertainty settings.</p></article>';
  return `<article class="card"><div class="card-head"><div><h2>How uncertain are the inputs?</h2><p>Explore assumptions · separate from low / expected / high</p></div><span class="tag">Not calibrated</span></div>
    <p>Let counts, appliance use and growth vary. See how much the forecast moves.</p>
    <form id="uncertainty-form">
      <div class="field"><label for="uncertainty-mass">Simulation band—not confidence</label><select id="uncertainty-mass" name="coverage">${[.8,.9,.95].map(v=>`<option value="${v}" ${defaults.coverage===v?'selected':''}>Middle ${v*100}% of simulations</option>`).join('')}</select></div>
      <details><summary>Review uncertain inputs</summary><p class="subtle-note">Illustrative triangular ranges, not survey evidence. Percentage-point widths add to rates; other widths multiply inputs. Zero is treated as known, not missing.</p><div class="input-grid">
      ${Object.entries(defaults.widths).map(([key,value])=>`<div class="field"><label for="uq-${key}">${esc(state.planningSettings.uncertainty_labels[key])}</label><input id="uq-${key}" name="${key}" type="number" min="0" max="${key.endsWith('_points')?50:80}" step="any" required value="${value*100}"></div>`).join('')}
      </div></details><button class="button secondary" type="submit">Explore input uncertainty</button>
    </form><p class="subtle-note">This excludes unmeasured forecast errors. For a calibrated prediction band, use the measured-history study in Evidence. Neither output changes the financial scenarios.</p>
    <p id="uncertainty-error" role="alert"></p><div id="uncertainty-results" aria-live="polite"></div></article>`;
}

function uncertaintyFormValues(form) {
  const opts=structuredClone(state.planningSettings.statistical_defaults);
  opts.coverage=Number(form.elements.coverage.value);
  for(const key of Object.keys(opts.widths)){
    const value=form.elements[key].value;
    if(value.trim()==='')throw new Error('Enter every uncertainty width; unknown is not zero.');
    opts.widths[key]=Number(value)/100;
  }
  return opts;
}

function renderUncertaintyResult() {
  if(!uncertaintyResult||uncertaintyProjectKey!==statisticalProjectKey())return;
  const r=uncertaintyResult;
  $('#uncertainty-results').innerHTML=`<h3>${esc(r.status)}</h3>
    <p class="subtle-note">Middle ${number(r.simulation_mass*100)}% of ${r.settings.draws} simulations. This is not a measured coverage rate. Forecast error is not included.</p>
    ${chart({central:r.months.map(m=>m.expected_kwh),lower:r.months.map(m=>m.lower_kwh),upper:r.months.map(m=>m.upper_kwh)},r.months.map(m=>'M'+m.service_month),{unit:'kWh / standard month',tickStep:6,height:230})}
    <div class="table-wrap"><table><caption>Annual input uncertainty · simulated totals</caption><thead><tr><th>Forecast year</th><th>Lower kWh</th><th>Expected kWh</th><th>Upper kWh</th></tr></thead><tbody>${r.years.map(y=>`<tr><td>${y.forecast_year}</td><td>${number(y.lower_kwh)}</td><td>${number(y.expected_kwh)}</td><td>${number(y.upper_kwh)}</td></tr>`).join('')}</tbody></table></div>
    <details><summary>Assumptions & limits</summary><ul>${r.limitations.map(t=>`<li>${esc(t)}</li>`).join('')}</ul></details>
    <button class="button secondary" id="uncertainty-download">Download uncertainty analysis</button>`;
  $('#uncertainty-download').addEventListener('click',()=>{if(contextReady())downloadJson(uncertaintyResult,'gridsight-input-uncertainty.json');});
}

function bindUncertainty() {
  const form=$('#uncertainty-form');if(!form)return;
  if(uncertaintyProjectKey!==statisticalProjectKey()){uncertaintyResult=null;uncertaintyProjectKey=null;}
  form.addEventListener('input',()=>{uncertaintyResult=null;$('#uncertainty-results').innerHTML='';});
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(statisticalBusy||!contextReady())return;
    uncertaintyResult=null;$('#uncertainty-results').innerHTML='';$('#uncertainty-error').textContent='';
    statisticalBusy=true;setBusy(true);
    try{
      const opts=uncertaintyFormValues(event.target),key=statisticalProjectKey();
      const result=await(await api('/api/forecast-uncertainty',{project:payload(),settings:opts})).json();
      if(key===statisticalProjectKey()){uncertaintyResult=result;uncertaintyProjectKey=key;renderUncertaintyResult();}
    }catch(e){$('#uncertainty-error').textContent=e.message;}
    finally{statisticalBusy=false;setBusy(false);}
  });
  renderUncertaintyResult();
}

function confidenceStudyHtml() {
  return `<article class="card validation-card"><div class="card-head"><div><h2>Calibrate confidence & growth</h2><p>Observed histories → fit → calibrate → untouched test</p></div><span class="tag">Measured histories needed</span></div>
    <p>Learn the early demand curve, then test how often actual use falls inside the range.</p>
    <p class="subtle-note">First 24 months by default; 36 months for a three-year study. A 90% target needs at least 3 fitting sites, 9 calibration sites and 2 test sites, with complete histories. These minimums do not prove broad accuracy.</p>
    <a class="button secondary" href="/api/confidence-study-template">Download study starter pack ↓</a>
    <form id="confidence-study-form"><div class="input-grid">
      <div class="field"><label for="confidence-inputs">Frozen site inputs · JSON</label><input id="confidence-inputs" name="inputs" type="file" accept=".json,application/json" required></div>
      <div class="field"><label for="confidence-meters">Monthly measured kWh · CSV</label><input id="confidence-meters" name="meters" type="file" accept=".csv,text/csv" required></div>
      <div class="field"><label for="confidence-plan">Predeclared site split & settings · JSON</label><input id="confidence-plan" name="plan" type="file" accept=".json,application/json" required></div>
    </div><button class="button primary" type="submit">Fit, calibrate & test</button></form>
    <p class="subtle-note">No built-in measured dataset. Upload only approved anonymous site aggregates. In-memory processing; no server storage or outside transfer. Results stay separate from your selected project.</p>
    <details><summary>What the growth fit can explain</summary><p>It learns the overall energy trajectory, not separate connection, appliance or business effects. Those need dated customer counts, appliance surveys and business records. A 24-month fit cannot validate Year 3. Real growth can fall as well as rise.</p></details>
    <p id="confidence-error" role="alert"></p><div id="confidence-results" aria-live="polite"></div></article>`;
}

function confidencePlot(rows) {
  if(!rows.length)return '';
  const W=720,H=255,L=55,R=20,T=25,B=35,max=Math.max(1,...rows.flatMap(r=>[r.upper_kwh,r.actual_kwh,r.original_kwh]))*1.05;
  const x=i=>L+i*(W-L-R)/Math.max(1,rows.length-1),y=v=>H-B-v*(H-T-B)/max;
  const pts=key=>rows.map((r,i)=>x(i).toFixed(2)+','+y(r[key]).toFixed(2)).join(' ');
  const band=pts('upper_kwh')+' '+rows.map((r,i)=>x(i)+','+y(r.lower_kwh)).reverse().join(' ');
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Actual versus original and growth-adjusted monthly energy, with calibrated prediction band." style="width:100%;height:auto">
    <text x="${L}" y="15" font-size="11" fill="#45645b">kWh / calendar month</text>
    ${[0,.5,1].map(t=>`<line x1="${L}" x2="${W-R}" y1="${y(max*t)}" y2="${y(max*t)}" stroke="#e3e9e2"/><text x="${L-8}" y="${y(max*t)+4}" text-anchor="end" font-size="10" fill="#63746b">${number(max*t)}</text>`).join('')}
    <polygon points="${band}" fill="#dfebd4"/>
    <polyline points="${pts('original_kwh')}" fill="none" stroke="#81918a" stroke-dasharray="5 4" stroke-width="2"/>
    <polyline points="${pts('predicted_kwh')}" fill="none" stroke="#28684f" stroke-width="2.5"/>
    <polyline points="${pts('actual_kwh')}" fill="none" stroke="#b85c21" stroke-width="2.5"/>
    ${rows.map((r,i)=>i%6===0||i===rows.length-1?`<text x="${x(i)}" y="${H-12}" text-anchor="middle" font-size="10" fill="#63746b">M${r.service_month}</text>`:'').join('')}
  </svg><p class="subtle-note">Orange: measured · Green: fitted growth · Dashed: original estimate · Shaded: calibrated prediction band</p>`;
}

function statValue(value,suffix='') {return value==null?'N/A':number(value,1)+suffix;}

function renderConfidenceSite() {
  const id=$('#confidence-site').value,r=confidenceResult,rows=r.monthly_comparisons.filter(v=>v.site_id===id);
  const growth=r.growth_comparisons.filter(v=>v.site_id===id);
  $('#confidence-site-results').innerHTML=confidencePlot(rows)+`
    <div class="table-wrap"><table><caption>Early growth · ${esc(id)}</caption><thead><tr><th>Years</th><th>Measured</th><th>Original forecast</th><th>Fitted forecast</th></tr></thead><tbody>${growth.map(g=>`<tr><td>${g.from_year} → ${g.to_year}</td><td>${statValue(g.actual_growth_pct,'%')}</td><td>${statValue(g.original_growth_pct,'%')}</td><td>${statValue(g.fitted_growth_pct,'%')}</td></tr>`).join('')}</tbody></table></div>
    <details><summary>Monthly readings, bounds & misses</summary><div class="table-wrap"><table><thead><tr><th>Month</th><th>Actual kWh</th><th>Fitted kWh</th><th>Lower</th><th>Upper</th><th>Inside?</th></tr></thead><tbody>${rows.map(m=>`<tr><td>${esc(m.month)}</td><td>${number(m.actual_kwh)}</td><td>${number(m.predicted_kwh)}</td><td>${number(m.lower_kwh)}</td><td>${number(m.upper_kwh)}</td><td>${m.covered?'Yes':'No'}</td></tr>`).join('')}</tbody></table></div></details>`;
}

function renderConfidenceResult() {
  const r=confidenceResult;if(!r)return;const t=r.test,c=r.calibration;
  $('#confidence-results').innerHTML=`<h3>${esc(r.status)}</h3><p>${esc(r.source_name)}</p><p class="subtle-note">${esc(r.scope)}. Source, split and population comparability are user-attested.</p>
    ${(r.transfer_warnings||[]).map(w=>`<p class="subtle-note">${esc(w)}</p>`).join('')}
    <div class="public-stats">
      <div class="public-stat"><span>Whole-path target</span><strong>${number(c.target_coverage*100)}%</strong><small>${r.plan.horizon_months} months · ${c.n_sites} calibration sites</small></div>
      <div class="public-stat"><span>Observed test coverage</span><strong>${statValue(t.site_path_coverage_pct,'%')}</strong><small>${t.covered_site_paths} / ${t.n_sites} complete site paths</small></div>
      <div class="public-stat"><span>95% coverage confidence interval</span><strong>${statValue(t.site_coverage_ci95_pct[0])}–${statValue(t.site_coverage_ci95_pct[1])}%</strong><small>Across test sites—not months</small></div>
    </div>
    <p class="subtle-note">Monthly coverage: ${statValue(t.monthly_coverage_pct,'%')} · Mean band width: ${statValue(t.mean_width_kwh)} kWh. A small sample or wide band does not establish useful accuracy.</p>
    <h4>Did the growth fit help?</h4><p>Original MAE: ${statValue(t.original.mae_kwh)} → fitted MAE: ${statValue(t.growth_adjusted.mae_kwh)} kWh/month. Lower is better; improvement is not guaranteed.</p>
    <div class="table-wrap"><table><caption>Untouched test histories</caption><thead><tr><th>Stage</th><th>Sites</th><th>Original MAE</th><th>Fitted MAE</th><th>Monthly coverage</th></tr></thead><tbody>${Object.entries(r.by_stage).map(([label,g])=>`<tr><td>${esc(label)}</td><td>${g.growth_adjusted.n_sites}</td><td>${statValue(g.original.mae_kwh)}</td><td>${statValue(g.growth_adjusted.mae_kwh)}</td><td>${statValue(g.monthly_coverage_pct,'%')}</td></tr>`).join('')}</tbody></table></div>
    <div class="table-wrap"><table><caption>Country checks—not country-wide guarantees</caption><thead><tr><th>Country</th><th>Test sites</th><th>Fitted MAE</th><th>Monthly coverage</th></tr></thead><tbody>${Object.entries(r.by_country).map(([code,g])=>`<tr><td>${esc(code)}</td><td>${g.growth_adjusted.n_sites}</td><td>${statValue(g.growth_adjusted.mae_kwh)}</td><td>${statValue(g.monthly_coverage_pct,'%')}</td></tr>`).join('')}</tbody></table></div>
    <div class="field"><label for="confidence-site">Review an untouched test site</label><select id="confidence-site">${Object.keys(r.by_site).map(id=>`<option value="${esc(id)}">${esc(id)}</option>`).join('')}</select></div><div id="confidence-site-results"></div>
    <details><summary>Evidence limits & reproducibility</summary><ul>${r.limitations.map(v=>`<li>${esc(v)}</li>`).join('')}</ul><p class="subtle-note">No automatic validation pass. Calibration rank ${c.rank}; ${c.n_sites} site scores. Download includes exact settings, coefficients and hashes.</p></details>
    <div class="form-actions"><button class="button secondary" id="confidence-json">Download full study</button><button class="button secondary" id="confidence-csv">Download test results CSV</button></div>`;
  $('#confidence-site').value=Object.keys(r.by_site)[0];
  $('#confidence-site').addEventListener('change',renderConfidenceSite);
  $('#confidence-json').addEventListener('click',()=>downloadJson(confidenceResult,'gridsight-confidence-growth-study.json'));
  $('#confidence-csv').addEventListener('click',()=>{
    const url=URL.createObjectURL(new Blob([confidenceResult.comparisons_csv],{type:'text/csv'})),a=document.createElement('a');
    a.href=url;a.download='gridsight-confidence-growth-test.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
  });
  renderConfidenceSite();
}

function bindConfidenceStudy() {
  $('#confidence-study-form').addEventListener('submit',async event=>{
    event.preventDefault();if(statisticalBusy||!contextReady())return;
    confidenceResult=null;$('#confidence-results').innerHTML='';$('#confidence-error').textContent='';
    const f=event.target.elements,inputs=f.inputs.files[0],meters=f.meters.files[0],plan=f.plan.files[0];
    if(!inputs||!meters||!plan||inputs.size>140000||meters.size>90000||plan.size>10000){
      $('#confidence-error').textContent='Choose inputs up to 140 KB, readings up to 90 KB and a study plan up to 10 KB.';return;
    }
    statisticalBusy=true;setBusy(true);
    try{
      confidenceResult=await(await api('/api/confidence-study',{manifest:JSON.parse(await inputs.text()),csv:await meters.text(),plan:JSON.parse(await plan.text())})).json();
      renderConfidenceResult();
    }catch(e){$('#confidence-error').textContent=e.message;}
    finally{statisticalBusy=false;setBusy(false);}
  });
  renderConfidenceResult();
}
