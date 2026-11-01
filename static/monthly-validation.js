/* Separate batch evidence: never promote an upload to selected-project validation. */
let monthlyComparison = null;
let monthlySources = null;
let monthlyRequestBusy = false;

function monthlyValidationHtml() {
  return `<article class="card validation-card" id="meter-validation" tabindex="-1"><div class="card-head"><div><h2>Test the current forecast</h2><p>East Africa · 20-input model · first 36 months</p></div><span class="tag">Real validation pending</span></div>
    <p>Compare the forecast with measured electricity use from independent mini-grids.</p>
    <p class="subtle-note">A separate test batch—not a validation of your selected location. Needs documented pre-connection inputs and complete monthly customer-meter totals. No fitting or automatic pass.</p>
    <a class="button secondary" href="/api/monthly-validation-template">1. Download starter pack ↓</a>
    <form id="monthly-validation-form">
      <div class="input-grid">
        <div class="field"><label for="monthly-inputs">2. Frozen site inputs · JSON</label><input id="monthly-inputs" name="inputs" type="file" accept=".json,application/json" required></div>
        <div class="field"><label for="monthly-readings">3. Measured monthly totals · CSV</label><input id="monthly-readings" name="readings" type="file" accept=".csv,text/csv" required></div>
      </div>
      <p class="subtle-note">30 sites maximum. No customer names or account numbers. Missing values are not zero. Processed locally in memory; not stored or sent to data providers. Download results before refreshing.</p>
      <button class="button primary" type="submit" id="monthly-compare">4. Compare forecast & actual</button>
    </form>
    <p id="monthly-error" role="alert"></p><div id="monthly-results" aria-live="polite"></div>
    <details><summary>Public data: what is available?</summary><div id="monthly-sources"><p class="subtle-note">Loading the source review…</p></div></details>
  </article>`;
}

function monthlyMetric(value, suffix='') { return value == null ? 'N/A' : number(value,1)+suffix; }

function monthlyChart(rows) {
  if (!rows.length) return '<p>No eligible measured months for this site.</p>';
  const maximum=Math.max(1,...rows.flatMap(r=>[r.actual_kwh,r.predicted_kwh]));
  const x=m=>55+(m-1)*685/35, y=v=>215-175*v/maximum;
  const line=key=>{
    let previous=0;
    return rows.map(r=>{const move=r.service_month!==previous+1;previous=r.service_month;return (move?'M':'L')+x(r.service_month).toFixed(2)+' '+y(r[key]).toFixed(2);}).join(' ').replace(/^L/,'M');
  };
  return `<svg viewBox="0 0 770 260" role="img" aria-label="Expected versus measured monthly energy. Missing months are not connected." style="width:100%;height:auto">
    <text x="55" y="18" fill="#45645b" font-size="12">kWh / calendar month · green = expected · orange = measured</text>
    ${[0,.5,1].map(t=>`<line x1="55" y1="${y(t*maximum)}" x2="740" y2="${y(t*maximum)}" stroke="#e4eae5"/><text x="48" y="${y(t*maximum)+4}" text-anchor="end" font-size="10" fill="#63746b">${number(t*maximum)}</text>`).join('')}
    <path d="${line('predicted_kwh')}" stroke="#28684f" fill="none" stroke-width="2.5"/>
    <path d="${line('actual_kwh')}" stroke="#b85c21" fill="none" stroke-width="2.5"/>
    ${rows.map(r=>`<circle cx="${x(r.service_month)}" cy="${y(r.actual_kwh)}" r="3" fill="#b85c21"/><circle cx="${x(r.service_month)}" cy="${y(r.predicted_kwh)}" r="3" fill="#28684f"/>`).join('')}
    ${[1,12,24,36].map(m=>`<text x="${x(m)}" y="239" text-anchor="middle" font-size="11" fill="#63746b">Month ${m}</text>`).join('')}
  </svg>`;
}

function renderMonthlySite() {
  const r=monthlyComparison, id=$('#monthly-site').value;
  const rows=r.monthly_comparisons.filter(row=>row.site_id===id), site=r.by_site[id];
  const growth=r.growth_comparisons.filter(row=>row.site_id===id);
  $('#monthly-site-results').innerHTML=`${monthlyChart(rows)}
    <p class="subtle-note">${rows.length} / 36 eligible months. MAE ${monthlyMetric(site.mae_kwh)} kWh/month · WAPE ${monthlyMetric(site.wape_pct,'%')}. Missing/excluded service months: ${site.missing_or_excluded_service_months.join(', ')||'None'}.</p>
    <div class="table-wrap"><table><caption>Predicted vs actual · ${esc(id)}</caption><thead><tr><th>Month</th><th>Service month</th><th>Expected kWh</th><th>Measured kWh</th><th>Error kWh</th></tr></thead><tbody>${rows.map(row=>`<tr><td>${esc(row.month)}</td><td>${row.service_month}</td><td>${number(row.predicted_kwh,1)}</td><td>${number(row.actual_kwh,1)}</td><td>${number(row.error_kwh,1)}</td></tr>`).join('')}</tbody></table></div>
    <h4>Is growth accurate?</h4>${growth.length?`<div class="table-wrap"><table><thead><tr><th>Service years</th><th>Expected growth</th><th>Measured growth</th><th>Error · percentage points</th></tr></thead><tbody>${growth.map(g=>`<tr><td>${g.from_year} → ${g.to_year}</td><td>${monthlyMetric(g.predicted_growth_pct,'%')}</td><td>${monthlyMetric(g.actual_growth_pct,'%')}</td><td>${monthlyMetric(g.error_percentage_points)}</td></tr>`).join('')}</tbody></table></div>`:'<p class="subtle-note">Not enough complete years. Each growth comparison needs two consecutive full service years.</p>'}`;
}

function renderMonthlyResult() {
  const r=monthlyComparison;if(!r)return;
  const m=r.metrics,c=r.coverage;
  $('#monthly-results').innerHTML=`<h3>${esc(r.status)}</h3><p>${esc(r.source_name)}</p>
    <p class="subtle-note">${c.evaluated_sites} / ${c.submitted_sites} sites scored · ${c.eligible_months} eligible months · ${c.excluded_months} excluded · ${c.sites_with_complete_36_months} sites with all 36 months. Evidence is user-attested, not independently verified.</p>
    <div class="public-stats">
      <div class="public-stat"><span>Mean absolute error</span><strong>${monthlyMetric(m.mae_kwh)}</strong><small>kWh/month</small></div>
      <div class="public-stat"><span>Weighted error</span><strong>${monthlyMetric(m.wape_pct,'%')}</strong><small>N/A when measured total is zero</small></div>
      <div class="public-stat"><span>Bias</span><strong>${monthlyMetric(m.bias_pct,'%')}</strong><small>Positive = overprediction</small></div>
    </div>
    <p class="subtle-note">RMSE: ${monthlyMetric(m.rmse_kwh)} kWh/month. Overall scores pool months; months are not independent sites. No regional accuracy claim.</p>
    <div class="table-wrap"><table><caption>Country-level results</caption><thead><tr><th>Country</th><th>Sites</th><th>Months</th><th>MAE · kWh/month</th><th>WAPE</th></tr></thead><tbody>${Object.entries(r.by_country).map(([code,g])=>`<tr><td>${esc(code)}</td><td>${g.n_sites}</td><td>${g.n_months}</td><td>${monthlyMetric(g.mae_kwh)}</td><td>${monthlyMetric(g.wape_pct,'%')}</td></tr>`).join('')}</tbody></table></div>
    <div class="field"><label for="monthly-site">Review a test site</label><select id="monthly-site">${Object.keys(r.by_site).map(id=>`<option value="${esc(id)}">${esc(id)}</option>`).join('')}</select></div><div id="monthly-site-results"></div>
    <details><summary>Excluded records (${r.excluded_rows.length})</summary><ul>${r.excluded_rows.map(row=>`<li>${esc(row.site_id)} · ${esc(row.month)}: ${esc(row.reasons.join('; '))}</li>`).join('')||'<li>None</li>'}</ul></details>
    <details><summary>Methods & limits</summary><ul>${r.limitations.map(s=>`<li>${esc(s)}</li>`).join('')}</ul><p class="subtle-note">Calculation: ${esc(r.model.method)} · ${esc(r.model.calculation_version)}. Fingerprint: ${esc(r.model.sha256)}</p></details>
    <div class="form-actions"><button class="button secondary" id="monthly-report">Download full comparison</button><button class="button secondary" id="monthly-csv">Download results CSV</button></div>`;
  $('#monthly-site').value=Object.keys(r.by_site)[0];
  $('#monthly-site').addEventListener('change',renderMonthlySite);
  $('#monthly-report').addEventListener('click',()=>downloadJson(monthlyComparison,'gridsight-current-model-comparison.json'));
  $('#monthly-csv').addEventListener('click',()=>{
    const url=URL.createObjectURL(new Blob([monthlyComparison.comparisons_csv],{type:'text/csv'}));
    const a=document.createElement('a');a.href=url;a.download='gridsight-predicted-vs-actual.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
  });
  renderMonthlySite();
}

function renderMonthlySources() {
  if(!monthlySources||!$('#monthly-sources'))return;
  $('#monthly-sources').innerHTML=`<p><strong>${esc(monthlySources.status)}</strong></p>
    <p class="subtle-note">Reviewed ${esc(monthlySources.reviewed_on)}. ${esc(monthlySources.note)}</p>
    <ul>${monthlySources.sources.map(s=>`<li><a href="${esc(s.url.startsWith('https://')?s.url:'#')}" target="_blank" rel="noopener">${esc(s.name)}</a> · ${esc(s.countries.join(', '))}<br><strong>${esc(s.status)}</strong><p class="subtle-note">${esc(s.evidence)} ${esc(s.remaining)}</p></li>`).join('')}</ul>`;
}

function bindMonthlyValidation() {
  $('#monthly-validation-form').addEventListener('submit',async event=>{
    event.preventDefault();if(monthlyRequestBusy||!contextReady())return;
    const f=event.target.elements,inputs=f.inputs.files[0],readings=f.readings.files[0];
    $('#monthly-error').textContent='';
    monthlyComparison=null;$('#monthly-results').innerHTML='';
    if(!inputs||!readings||inputs.size>140000||readings.size>90000){$('#monthly-error').textContent='Choose site inputs up to 140 KB and readings up to 90 KB.';return;}
    monthlyRequestBusy=true;setBusy(true);
    // A failed new attempt must never leave an older score looking current.
    try{
      const manifest=JSON.parse(await inputs.text()), csv=await readings.text();
      monthlyComparison=await(await api('/api/validate-monthly',{manifest,csv})).json();
      renderMonthlyResult();
    }catch(error){$('#monthly-error').textContent=error.message;}
    finally{monthlyRequestBusy=false;setBusy(false);}
  });
  renderMonthlyResult();
  if(monthlySources)renderMonthlySources();
  else api('/api/validation-sources').then(r=>r.json()).then(r=>{monthlySources=r;renderMonthlySources();})
    .catch(()=>{if($('#monthly-sources'))$('#monthly-sources').textContent='Source review unavailable. It is also included in the starter pack.';});
}
