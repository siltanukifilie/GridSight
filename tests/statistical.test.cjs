/* UI logic checks with invented study results; not visual or field validation. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const script=fs.readFileSync(path.join(__dirname,'../static/statistical.js'),'utf8');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const summary=()=>({original:{mae_kwh:100},growth_adjusted:{mae_kwh:80,n_sites:2},monthly_coverage_pct:95,mean_width_kwh:150});
function study(){
  const rows=Array.from({length:24},(_,i)=>({site_id:'TEST001',month:'2022-'+String(i%12+1).padStart(2,'0'),service_month:i+1,
    actual_kwh:100+i,predicted_kwh:105+i,original_kwh:150,lower_kwh:80,upper_kwh:140,covered:true}));
  return {status:'Supplied-history study — not independently verified',source_name:'<img src=x onerror=alert(1)>',
    scope:'Separate batch, not the selected project',plan:{horizon_months:24},calibration:{target_coverage:.9,n_sites:9,rank:9},
    test:{...summary(),n_sites:2,covered_site_paths:2,site_path_coverage_pct:100,site_coverage_ci95_pct:[15.8,100]},
    by_stage:{'Months 1–6':summary(),'Months 13–24':summary()},by_country:{KE:summary()},by_site:{TEST001:summary()},
    growth_comparisons:[{site_id:'TEST001',from_year:1,to_year:2,actual_growth_pct:20,original_growth_pct:10,fitted_growth_pct:18}],
    monthly_comparisons:rows,limitations:['No automatic pass','User-attested inputs'],transfer_warnings:['Country-transfer diagnostic'],
    comparisons_csv:'site_id,covered\nTEST001,true\n'};
}
function uncertainty(){
  return {status:'Input-assumption band — not calibrated',simulation_mass:.9,
    settings:{coverage:.9,draws:256,seed:1729,widths:{household_count_fraction:.1,connection_rate_points:.1}},
    months:[{service_month:1,expected_kwh:100,lower_kwh:80,upper_kwh:130}],
    years:[{forecast_year:1,expected_kwh:1200,lower_kwh:900,upper_kwh:1500}],limitations:['Not a confidence interval']};
}
function harness(){
  const nodes=new Map(),requests=[],downloads=[],busy=[];
  const node=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',value:'',events:{},
    addEventListener(event,handler){this.events[event]=handler;}});return nodes.get(id);};
  const state={result:{detailed:{enabled:true},site:{households:100},assumptions:{},connection:{},context:{country_code:'KE'}},
    planningSettings:{statistical_defaults:uncertainty().settings,
      uncertainty_labels:{household_count_fraction:'Households ± %',connection_rate_points:'Connection rate ± percentage points'}}};
  const c=vm.createContext({state,structuredClone,esc,number:(v,d=0)=>Number(v).toFixed(d),$:node,
    contextReady:()=>true,setBusy:v=>busy.push(v),payload:()=>structuredClone(state.result),
    chart:()=>'<svg role="img"></svg>',downloadJson:(value,name)=>downloads.push({value,name}),
    URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},Blob,setTimeout:()=>1,
    document:{createElement:()=>({click(){}})},api:async(url,data)=>{
      requests.push({url,data});return {json:async()=>url==='/api/forecast-uncertainty'?uncertainty():study()};
    }});
  vm.runInContext(script,c);return {c,state,node,requests,downloads,busy};
}
function form(){return {elements:{coverage:{value:'0.9'},household_count_fraction:{value:'20'},connection_rate_points:{value:'5'}}};}
function files(plan='{"schema":"fixture"}'){return {elements:{
  inputs:{files:[{size:100,text:async()=> '{"schema":"inputs"}'}]},
  meters:{files:[{size:50,text:async()=> 'meter CSV fixture'}]},
  plan:{files:[{size:100,text:async()=>plan}]}}};}

test('uncertainty labels distinguish simulation mass from confidence',()=>{
  const h=harness(),html=h.c.uncertaintyHtml();
  for(const text of ['Not calibrated','Simulation band—not confidence','percentage points','not survey evidence'])assert.ok(html.includes(text));
  h.state.result.detailed.enabled=false;assert.equal(h.c.uncertaintyHtml(),'');
});
test('uncertainty percentages converted correctly, blanks rejected, defaults unchanged',()=>{
  const h=harness(),f=form(),opts=h.c.uncertaintyFormValues(f);
  assert.equal(opts.widths.household_count_fraction,.2);assert.equal(opts.widths.connection_rate_points,.05);
  assert.equal(h.state.planningSettings.statistical_defaults.widths.household_count_fraction,.1);
  f.elements.household_count_fraction.value='';assert.throws(()=>h.c.uncertaintyFormValues(f),/unknown is not zero/);
});
test('uncertainty request uses applied project, no study results or finance mutation',async()=>{
  const h=harness(),before=JSON.stringify(h.state.result);h.c.bindUncertainty();
  await h.node('#uncertainty-form').events.submit({preventDefault(){},target:form()});
  assert.equal(h.requests[0].url,'/api/forecast-uncertainty');
  assert.equal(h.requests[0].data.project.site.households,100);
  assert.deepEqual(h.busy,[true,false]);assert.equal(JSON.stringify(h.state.result),before);
  assert.match(h.node('#uncertainty-results').innerHTML,/not a measured coverage rate/);
  h.node('#uncertainty-download').events.click();assert.equal(h.downloads.length,1);
});
test('preview invalidated when current project changes',async()=>{
  const h=harness();h.c.bindUncertainty();
  await h.node('#uncertainty-form').events.submit({preventDefault(){},target:form()});
  h.state.result.site.households=200;
  h.c.bindUncertainty();
  assert.equal(vm.runInContext('uncertaintyResult',h.c),null);
});
test('editing uncertainty settings removes stale preview',async()=>{
  const h=harness();h.c.bindUncertainty();
  await h.node('#uncertainty-form').events.submit({preventDefault(){},target:form()});
  h.node('#uncertainty-form').events.input();
  assert.equal(h.node('#uncertainty-results').innerHTML,'');
  assert.equal(vm.runInContext('uncertaintyResult',h.c),null);
});
test('rendered controls retain the settings behind a cached result',()=>{
  const h=harness();h.c.fixture=uncertainty();h.c.fixture.settings.coverage=.95;h.c.fixture.settings.widths.household_count_fraction=.3;
  vm.runInContext('uncertaintyResult=fixture;uncertaintyProjectKey=statisticalProjectKey()',h.c);
  const html=h.c.uncertaintyHtml();
  assert.match(html,/value="0.95" selected/);assert.match(html,/value="30"/);
});
test('study starter describes separate splits and first-two-year restriction',()=>{
  const h=harness(),html=h.c.confidenceStudyHtml();
  for(const text of ['9 calibration sites','2 test sites','First 24 months','cannot validate Year 3','No built-in measured monthly-history dataset','study starter pack'])assert.ok(html.includes(text));
});
test('study rendering escapes data, reports actual coverage and small-sample interval',()=>{
  const h=harness();h.c.fixture=study();vm.runInContext('confidenceResult=fixture;renderConfidenceResult()',h.c);
  const html=h.node('#confidence-results').innerHTML;
  assert.ok(!html.includes('<img src=x'));assert.ok(html.includes('&lt;img'));
  for(const text of ['15.8–100.0%','2 / 2 complete site paths','Original MAE','Months 13–24','Country-transfer diagnostic','No automatic validation pass'])assert.ok(html.includes(text));
  assert.match(h.node('#confidence-site-results').innerHTML,/18.0%/);
  h.node('#confidence-json').events.click();assert.equal(h.downloads.length,1);
});
test('plot distinguishes original, fitted, observed and calibrated band',()=>{
  const h=harness(),html=h.c.confidencePlot(study().monthly_comparisons);
  for(const text of ['role="img"','<polygon','stroke-dasharray','Orange: measured','Shaded: calibrated'])assert.ok(html.includes(text));
  assert.ok(!html.includes('NaN'));assert.equal(h.c.confidencePlot([]),'');
});
test('zero and unknown growth/coverage metrics are not confused',()=>{
  const h=harness();assert.equal(h.c.statValue(null,'%'),'N/A');assert.equal(h.c.statValue(0,'%'),'0.0%');
});
test('study submits separate plan and paired data to local endpoint only',async()=>{
  const h=harness();h.c.bindConfidenceStudy();
  await h.node('#confidence-study-form').events.submit({preventDefault(){},target:files()});
  assert.equal(h.requests[0].url,'/api/confidence-study');
  assert.equal(h.requests[0].data.manifest.schema,'inputs');assert.equal(h.requests[0].data.plan.schema,'fixture');
  assert.equal(h.requests[0].data.csv,'meter CSV fixture');assert.deepEqual(h.busy,[true,false]);
});
test('bad plan JSON clears old study and restores controls',async()=>{
  const h=harness();h.c.fixture=study();vm.runInContext('confidenceResult=fixture',h.c);
  h.c.bindConfidenceStudy();
  await h.node('#confidence-study-form').events.submit({preventDefault(){},target:files('{broken')});
  assert.ok(h.node('#confidence-error').textContent);assert.equal(h.node('#confidence-results').innerHTML,'');
  assert.equal(h.requests.length,0);assert.deepEqual(h.busy,[true,false]);
});
test('oversized plan rejected without a request',async()=>{
  const h=harness();h.c.bindConfidenceStudy();const f=files();f.elements.plan.files[0].size=10001;
  await h.node('#confidence-study-form').events.submit({preventDefault(){},target:f});
  assert.match(h.node('#confidence-error').textContent,/10 KB/);assert.equal(h.requests.length,0);
});
test('server-side failed study cannot leave an old apparent success',async()=>{
  const h=harness();h.c.api=async()=>{throw new Error('Not enough calibration sites');};h.c.bindConfidenceStudy();
  h.node('#confidence-results').innerHTML='old result';
  await h.node('#confidence-study-form').events.submit({preventDefault(){},target:files()});
  assert.equal(h.node('#confidence-results').innerHTML,'');
  assert.match(h.node('#confidence-error').textContent,/Not enough calibration/);
  assert.deepEqual(h.busy,[true,false]);
});
