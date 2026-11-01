/* Invented UI fixtures. No measured-data accuracy or visual-browser assertion. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const script=fs.readFileSync(path.join(__dirname,'../static/monthly-validation.js'),'utf8');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const result=()=>({
  status:'Fixture comparison — not field evidence',source_name:'<img src=x onerror=alert(1)>',
  model:{method:'detailed_bottom_up',calculation_version:'1.6',sha256:'abc123'},
  coverage:{evaluated_sites:1,submitted_sites:1,eligible_months:2,excluded_months:1,sites_with_complete_36_months:0},
  metrics:{mae_kwh:20,rmse_kwh:22,wape_pct:10,bias_pct:-2},
  by_country:{KE:{n_sites:1,n_months:2,mae_kwh:20,wape_pct:10}},
  by_site:{CASE001:{mae_kwh:20,wape_pct:10,missing_or_excluded_service_months:[2,4]}},
  monthly_comparisons:[{site_id:'CASE001',month:'2022-01',service_month:1,actual_kwh:90,predicted_kwh:100,error_kwh:10},
    {site_id:'CASE001',month:'2022-03',service_month:3,actual_kwh:110,predicted_kwh:100,error_kwh:-10}],
  growth_comparisons:[],excluded_rows:[{site_id:'CASE001',month:'2022-02',reasons:['Incomplete coverage']}],
  limitations:['Fixture only','Not an automatic pass'],comparisons_csv:'site_id,month,actual_kwh,predicted_kwh\nCASE001,2022-01,90,100\n'
});
function harness(){
  const nodes=new Map(),requests=[],downloads=[],busy=[];
  const node=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',value:'',events:{},
    addEventListener(event,handler){this.events[event]=handler;}});return nodes.get(id);};
  const c=vm.createContext({console,esc,number:(v,d=0)=>Number(v).toFixed(d),$:node,
    contextReady:()=>true,setBusy:v=>busy.push(v),downloadJson:(value,name)=>downloads.push({value,name}),
    URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},Blob,setTimeout:()=>1,
    document:{createElement:()=>({click(){}})},api:async(url,data)=>{
      requests.push({url,data});
      return {json:async()=>url.includes('sources')?{status:'No imported data',reviewed_on:'2026-11-01',note:'Source review',sources:[]}:result()};
    }});
  vm.runInContext(script,c);return {c,node,requests,downloads,busy};
}
test('new current-model workflow is distinct and simple',()=>{
  const h=harness(),html=h.c.monthlyValidationHtml();
  for(const text of ['20-input model','Real validation pending','pre-connection','not stored','monthly-inputs','monthly-readings','starter pack'])assert.ok(html.includes(text),text);
  assert.ok(!html.includes('accuracy achieved'));
});
test('chart breaks across missing months and has accessible units',()=>{
  const h=harness(),html=h.c.monthlyChart(result().monthly_comparisons);
  assert.match(html,/role="img"/);assert.match(html,/kWh \/ calendar month/);
  const paths=[...html.matchAll(/<path d="([^"]+)"/g)];
  assert.equal(paths.length,2);
  for(const [,d] of paths)assert.equal((d.match(/M/g)||[]).length,2);
  assert.ok(!html.includes('NaN'));
  assert.match(h.c.monthlyChart([]),/No eligible/);
});
test('render escapes source, displays exclusions, groups and honest growth gate',()=>{
  const h=harness();h.c.fixture=result();vm.runInContext('monthlyComparison=fixture;renderMonthlyResult()',h.c);
  const html=h.node('#monthly-results').innerHTML,site=h.node('#monthly-site-results').innerHTML;
  assert.ok(!html.includes('<img src=x'));assert.ok(html.includes('&lt;img'));
  for(const text of ['RMSE','Country-level','Incomplete coverage','not independently verified','Download results CSV'])assert.ok(html.includes(text));
  assert.ok(site.includes('Not enough complete years'));assert.ok(site.includes('Predicted vs actual'));
  h.node('#monthly-report').events.click();assert.equal(h.downloads.length,1);
});
test('null scores never look like zero error',()=>{
  const h=harness(),r=result();r.metrics={mae_kwh:null,rmse_kwh:null,wape_pct:null,bias_pct:null};
  h.c.fixture=r;vm.runInContext('monthlyComparison=fixture;renderMonthlyResult()',h.c);
  assert.ok(h.node('#monthly-results').innerHTML.includes('N/A'));
  assert.ok(!h.node('#monthly-results').innerHTML.includes('NaN'));
});
test('complete growth comparisons show actual and expected separately',()=>{
  const h=harness(),r=result();
  r.growth_comparisons=[{site_id:'CASE001',from_year:1,to_year:2,actual_growth_pct:20,predicted_growth_pct:25,error_percentage_points:5}];
  h.c.fixture=r;vm.runInContext('monthlyComparison=fixture;renderMonthlyResult()',h.c);
  const html=h.node('#monthly-site-results').innerHTML;
  for(const text of ['20.0%','25.0%','5.0','percentage points'])assert.ok(html.includes(text));
});
test('submit sends matching inputs and readings only to local monthly endpoint',async()=>{
  const h=harness();h.c.bindMonthlyValidation();
  await h.node('#monthly-validation-form').events.submit({preventDefault(){},target:{elements:{
    inputs:{files:[{size:100,text:async()=> '{"schema":"fixture"}'}]},
    readings:{files:[{size:50,text:async()=> 'csv fixture'}]}
  }}});
  const req=h.requests.find(r=>r.url==='/api/validate-monthly');
  assert.equal(req.data.csv,'csv fixture');assert.equal(req.data.manifest.schema,'fixture');
  assert.deepEqual(h.busy,[true,false]);assert.ok(h.node('#monthly-results').innerHTML);
});
test('invalid JSON clears stale results and restores controls',async()=>{
  const h=harness();h.c.fixture=result();vm.runInContext('monthlyComparison=fixture',h.c);
  h.c.bindMonthlyValidation();
  await h.node('#monthly-validation-form').events.submit({preventDefault(){},target:{elements:{
    inputs:{files:[{size:100,text:async()=> '{broken'}]},readings:{files:[{size:1,text:async()=> 'x'}]}
  }}});
  assert.equal(h.node('#monthly-results').innerHTML,'');assert.ok(h.node('#monthly-error').textContent);
  assert.deepEqual(h.busy,[true,false]);assert.ok(!h.requests.some(r=>r.url==='/api/validate-monthly'));
});
test('oversized file rejected without sending data or leaving old results',async()=>{
  const h=harness();h.c.bindMonthlyValidation();h.node('#monthly-results').innerHTML='stale';
  await h.node('#monthly-validation-form').events.submit({preventDefault(){},target:{elements:{
    inputs:{files:[{size:150000}]},readings:{files:[{size:1}]}
  }}});
  assert.match(h.node('#monthly-error').textContent,/140 KB/);
  assert.equal(h.node('#monthly-results').innerHTML,'');
  assert.ok(!h.requests.some(r=>r.url==='/api/validate-monthly'));
});
test('source review escapes text and rejects non-HTTPS links',()=>{
  const h=harness();h.c.sources={status:'Pending',reviewed_on:'2026-11-01',note:'no data',sources:[
    {url:'javascript:alert(1)',name:'<script>bad</script>',countries:['KE'],status:'Pending',evidence:'Not imported',remaining:'No paired inputs'}]};
  vm.runInContext('monthlySources=sources;renderMonthlySources()',h.c);
  const html=h.node('#monthly-sources').innerHTML;
  assert.ok(!html.includes('javascript:'));assert.ok(!html.includes('<script>'));assert.match(html,/href="#"/);
});
