/* Evidence follows the exact applied project; benchmarks never replace inputs. */
let benchmarkResult = null;

function financialEvidenceHtml() {
  const e=state.result.financial_evidence;if(!e)return '';
  const c=e.benchmarks, money=esc(state.result.context.currency);
  const labels={missing:'Missing',assumption:'Assumption',source_attached:'Source attached',review_due:'Review date'};
  return `<article class="card financial-evidence-card"><div class="card-head"><div><h2>Can we trust the budget?</h2><p>${esc(e.status)}</p></div><span class="tag">${e.source_attached} / ${e.input_count} sourced</span></div>
    ${e.stale_project?'<p class="demo-notice">Inputs changed. Previous evidence was detached; review and attach it to the updated project.</p>':''}
    <p class="subtle-note">Sources attached ≠ independently verified. Potential spare capacity ≠ proven savings.</p>
    <details><summary>Check the inputs & missing evidence</summary><div class="table-wrap"><table><thead><tr><th>Input</th><th>Applied value</th><th>Evidence</th><th>Reference / date</th></tr></thead><tbody>${e.rows.map(x=>`<tr><td>${esc(x.field.replaceAll('_',' '))}</td><td>${x.value==null?'Not supplied':number(x.value,2)} ${esc(x.unit)}</td><td>${labels[x.status]}</td><td>${x.evidence?esc(x.evidence.source_reference)+' · '+esc(x.evidence.observed_on):'Needed'}</td></tr>`).join('')}</tbody></table></div><p class="subtle-note">${esc(e.notice)}</p></details>
    <div class="form-actions"><button id="financial-template" class="button secondary">Get survey & evidence pack ↓</button><button id="clear-financial-evidence" class="text-button">Clear attached evidence</button></div>
    <form id="financial-evidence-form"><div class="field"><label for="financial-evidence-file">Attach completed evidence.json · no personal data</label><input id="financial-evidence-file" name="evidence" type="file" accept=".json,application/json" required></div><button class="button secondary" type="submit">Check & attach sources</button></form><p id="financial-evidence-error" role="alert"></p>
    <details><summary>Regional benchmarks · not site quotations</summary><p>${esc(c.notice)}</p><div class="table-wrap"><table><thead><tr><th>Reference</th><th>Historical average</th><th>Scope</th></tr></thead><tbody>${c.benchmarks.map(b=>`<tr><td><a href="${esc(b.url)}" target="_blank" rel="noopener">${esc(b.label)} ↗</a><br><small>${esc(b.source)} · ${esc(b.locator)}</small></td><td>${number(b.value)} ${esc(b.unit)}</td><td>${esc(b.scope)}<br><small>${esc(b.limitation)}</small></td></tr>`).join('')}</tbody></table></div>
    ${c.local_context.map(x=>`<p><a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.label)} ↗</a> · ${esc(x.date)}<br><small>${esc(x.finding)} ${esc(x.limitation)}</small></p>`).join('')}
    <form id="benchmark-form"><h3>Compare your budget</h3><p class="subtle-note">Enter total metered connections, not service-area households. Currency conversion is only for this comparison.</p><div class="compact-grid">
    <div class="field"><label for="benchmark-connections">Metered connections · Year 1 basis</label><input id="benchmark-connections" name="connections" type="number" min="1" max="1000000" step="1" required></div>
    <div class="field"><label for="benchmark-fx">${money} per 1 USD</label><input id="benchmark-fx" name="fx" type="number" min="0.000000001" max="1000000000" step="any" required></div>
    <div class="field"><label for="benchmark-date">Exchange-rate date</label><input id="benchmark-date" name="date" type="date" required></div>
    <div class="field"><label for="benchmark-reference">Exchange-rate source reference</label><input id="benchmark-reference" name="reference" maxlength="240" required></div></div>
    <label><input name="confirmed" type="checkbox" required> I checked the cost scope and connection definition.</label><p><button class="button secondary" type="submit">Compare · do not change budget</button></p></form><div id="benchmark-result" aria-live="polite"></div></details>
  </article>`;
}

function productiveStressHtml() {
  const s=state.result.productive_sensitivity;if(!s)return '';
  return `<details><summary>What if productive use is lower?</summary><p class="subtle-note">${esc(s.notice)}</p><div class="table-wrap"><table><thead><tr><th>Option / use</th><th>Extra kWh/month</th><th>Grid contribution · ${esc(moneyUnit())}/month</th></tr></thead><tbody>${s.rows.map(x=>`<tr><td>${esc(x.option)} · ${esc(x.case)}</td><td>${number(x.extra_demand_kwh_month)}</td><td>${number(x.grid_contribution_amount_month)}</td></tr>`).join('')}</tbody></table></div></details>`;
}

function benchmarkValues(form) {
  for(const key of ['connections','fx','date','reference'])if(!form.elements[key].value.trim())throw new Error('Complete every comparison field.');
  return {connections:Number(form.elements.connections.value),local_currency_per_usd:Number(form.elements.fx.value),fx_date:form.elements.date.value,fx_reference:form.elements.reference.value,scope_confirmed:form.elements.confirmed.checked};
}

function bindFinancialEvidence() {
  if(!state.result.financial_evidence)return;
  // A rerender clears comparison results rather than retaining a stale currency/budget comparison.
  benchmarkResult=null;
  $('#financial-template').addEventListener('click',async()=>{
    if(!contextReady())return;
    try{const response=await api('/api/financial-evidence-template',payload());const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='gridsight-financial-evidence-starter.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}catch(e){error(e.message);}
  });
  $('#clear-financial-evidence').addEventListener('click',async()=>{if(!contextReady())return;state.financialEvidence=null;await calculate();});
  $('#financial-evidence-form').addEventListener('submit',async event=>{
    event.preventDefault();if(!contextReady())return;
    const previous=state.financialEvidence;setBusy(true);
    try{
      const file=event.target.elements.evidence.files[0];if(!file||file.size>24000)throw new Error('Choose an evidence JSON file under 24 KB.');
      const packet=JSON.parse(await file.text());
      const r=await(await api('/api/analyze',{...payload(),financial_evidence:packet})).json();
      state.financialEvidence=r.financial_evidence.packet;state.result=r;render();
    }catch(e){state.financialEvidence=previous;$('#financial-evidence-error').textContent=e.message;}
    finally{setBusy(false);}
  });
  $('#benchmark-form').addEventListener('input',()=>{benchmarkResult=null;$('#benchmark-result').innerHTML='';});
  $('#benchmark-form').addEventListener('submit',async event=>{
    event.preventDefault();if(!contextReady())return;
    benchmarkResult=null;$('#benchmark-result').innerHTML='';setBusy(true);
    try{const values=benchmarkValues(event.target);const b=await(await api('/api/benchmark-check',{project:payload(),comparison:values})).json();benchmarkResult=b;
      $('#benchmark-result').innerHTML=`<p>Your capital cost: <b>${b.capex_usd_per_connection==null?'Enter project capital cost first':number(b.capex_usd_per_connection,2)+' USD/connection'}</b> · regional reference ${number(b.benchmark_capex_usd_per_connection)}.</p><p>Your annual operating cost: <b>${number(b.opex_usd_per_connection_year,2)} USD/connection</b> · regional reference ${number(b.benchmark_opex_usd_per_connection_year)}.</p><p class="subtle-note">${esc(b.notice)}${b.fx_review_due?' Exchange-rate date is over 90 days old; review it.':''}</p><button id="benchmark-download" class="button secondary">Download comparison</button>`;
      $('#benchmark-download').addEventListener('click',()=>{if(contextReady()&&benchmarkResult)downloadJson(benchmarkResult,'gridsight-benchmark-comparison.json');});
    }catch(e){$('#benchmark-result').textContent=e.message;}finally{setBusy(false);}
  });
}
