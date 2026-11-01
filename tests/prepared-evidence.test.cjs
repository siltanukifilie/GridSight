/* UI rendering checks with invented fixtures; not field-accuracy evidence. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const read=f=>fs.readFileSync(path.join(__dirname,'..',f),'utf8');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function harness(role='developer'){
  const state={role,site:{households:42},result:{prepared_evidence:{
    sector_context:{status:'available',sector:'Gashora',sector_key:'RW-Bugesera-Gashora',scope:'Sector only',match_basis:'Names unverified',notice:'Not measured demand',sources:[],features:[
      {field:'households_2022',value:8393,unit:'households',evidence_type:'census_observation',reference_period:'2022',source_ids:'NISR',limitation:'Not project customers'},
      {field:'metered_monthly_consumption_kwh',value:null,unit:'kWh/month',evidence_type:'missing_target',reference_period:'not received',source_ids:'Partner',limitation:'No labels'},
      {field:'school_count_osm',value:0,unit:'mapped objects',evidence_type:'map',reference_period:'2026',source_ids:'OSM',limitation:'None mapped is not absence'}]},
    sector_catalog:{status:'available',sectors:Array(15).fill({})},model_status:{range:'Low / expected / high scenarios, not calibrated confidence intervals',growth:'No observed multi-year labels'},
    categories:[{name:'Synthetic demos',meaning:'Fictional'}],
    benchmark:{status:'available',qualified_hours:1620,calendar_hours:2035,notice:'Rwanda ECOS is not Bugesera; Haiti is outside East Africa',target:'Delivered power, not billed kWh',interpretation:'WAPE is error; poor transfer',metrics:[{country:'Haiti',test_site:'HT_BEAMONT',model:'equal_site_local_hour',test_hours:745,mae_kw:3.192,rmse_kw:3.21,bias_kw:3.192,wape_percent:2503.9}],quality:[],sites:[],limitations:['Not a blinded test'],source:{url:'https://doi.org/10.35097/1305',attribution:'Luh et al.',license:'CC BY 4.0',accessed_on:'2026-11-01'}},
    preparation:{status:'prepared_not_trained',notice:'No model trained',sites:[{site_id:'CD_IDJWI',train_rows:'215',validation_rows:'90',test_rows:'86',retained_features:'16',model_input_columns:'27'}],feature_coverage:[{requested_feature:'Households',status:'PARTIAL',limitation_or_next_step:'Sector only'}]}
  }}};
  const ctx=vm.createContext({state,esc,number:(n,d=0)=>Number(n).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d})});
  vm.runInContext(read('static/prepared-evidence.js'),ctx);
  return {state,ctx};
}
for(const role of ['developer','investor'])test(role+' sees sector context without input mutation',()=>{
  const {state,ctx}=harness(role),before=JSON.stringify(state);
  const html=ctx.sectorContextHtml();
  assert.match(html,/8,393/);assert.match(html,/not the selected cell/);assert.match(html,/Not used in forecast/);
  assert.match(html,/Unavailable/);assert.match(html,/>0<\/td>/);assert.match(html,/2022/);assert.match(html,/kWh\/month/);
  assert.match(html,/indirect GEP/);assert.match(html,/not device counts/);
  assert.equal(JSON.stringify(state),before);
});
test('benchmark displays both model context and errors, never an accuracy conversion',()=>{
  const {ctx}=harness(),html=ctx.preparedEvidenceHtml();
  for(const value of ['2,503.9','MAE · kW','WAPE · %','not Bugesera','outside East Africa','Current monthly model: validation pending','not calibrated confidence intervals','CC BY 4.0'])assert.ok(html.includes(value),value);
  assert.ok(!html.includes('accuracy:'));assert.match(html,/other two sites/);
});
test('training preparation shows separate per-site counts and missingness columns',()=>{
  const {ctx}=harness(),html=ctx.preparedEvidenceHtml();
  for(const value of ['Model training pending','215','90','86','16 + 11','four 24-hour rolling features','Original 20 inputs'])assert.ok(html.includes(value),value);
});
test('unmatched and unavailable evidence show no substitute scores',()=>{
  const {ctx,state}=harness();state.result.prepared_evidence.sector_context={status:'unavailable',reason:'Files unavailable'};
  state.result.prepared_evidence.benchmark={status:'unavailable',reason:'No scores substituted'};
  assert.match(ctx.sectorContextHtml(),/Data unavailable/);assert.ok(!ctx.sectorContextHtml().includes('8,393'));
  assert.match(ctx.preparedEvidenceHtml(),/No scores substituted/);assert.ok(!ctx.preparedEvidenceHtml().includes('2,503.9'));
});
test('all displayed source values and labels are escaped',()=>{
  const {ctx,state}=harness();state.result.prepared_evidence.sector_context.sector='<img onerror=x>';
  state.result.prepared_evidence.sector_context.features[0].value='<script>x</script>';
  const html=ctx.sectorContextHtml();assert.ok(!html.includes('<img'));assert.ok(!html.includes('<script>'));assert.match(html,/&lt;script&gt;/);
});
test('old saved examples without prepared evidence still render',()=>{
  const {ctx,state}=harness();delete state.result.prepared_evidence;
  assert.equal(ctx.sectorContextHtml(),'');assert.equal(ctx.preparedEvidenceHtml(),'');
});
test('evidence and location sections are wired to existing workspaces and exports',()=>{
  assert.match(read('static/app.js'),/preparedEvidenceHtml\(\)/);
  assert.match(read('static/context.js'),/sectorContextHtml\(\)/);
  assert.match(read('templates/index.html'),/prepared-evidence.js/);
  assert.match(read('templates/report.html'),/prepared_evidence_sections.html/);
  assert.match(read('templates/deliverables_report.html'),/prepared_evidence_sections.html/);
});

function operationalFixture(){
  const metrics=['ridge','random_forest','gradient_boosting'].map((family,i)=>({site_id:'RW_ECOS',family,
    model_name:['Ridge regression','Random Forest','Gradient Boosting'][i],n_rows:64,mae_kw:.04+i*.01,
    rmse_kw:.05,wape_pct:1.25+i*.5,r2:.77,selected_on_validation:i===0,mae_improvement_vs_persistence_pct:3.9}));
  return {status:'trained_exploratory',notice:'Later hours, not whole sites. Rwanda ECOS is not Bugesera.',data_rows:1540,
    counts:{train:1013,validation:267,test:260},families_per_site:8,candidate_fits:66,selection:'Validation MAE before test.',
    sites:[{site_id:'RW_ECOS',label:'Rwanda ECOS',selected:metrics[0],counts:{train:280,validation:64,test:64},
      test_start_utc:'2021-12-06 09:00 UTC',test_end_utc:'2021-12-09 01:00 UTC',
      test_preview:[{forecast_origin_utc:'2021-12-09 00:00 UTC',previous_hour_kw:3,actual_kw:3.1,prediction_kw:3.08}]}],
    test_metrics:metrics,target:'Next-hour mean power, kW',feature_dictionary:[{feature:'power_lag_1h_kw',unit:'kW',definition:'Previous clock hour'}],
    limitations:['Not monthly kWh or growth'],source:{url:'https://doi.org/10.35097/1305',attribution:'Luh et al.',license:'CC BY 4.0',accessed_on:'2026-11-01'}};
}
for(const role of ['developer','investor'])test(role+' sees trained data without changing monthly assumptions',()=>{
  const {ctx,state}=harness(role);state.result.prepared_evidence.operational_models=operationalFixture();
  const before=JSON.stringify(state),html=ctx.preparedEvidenceHtml();
  for(const word of ['Real-data model comparison','1,540','1,013','Random Forest','Gradient Boosting','Ridge regression',
                    'Actual · kW','Predicted · kW','not an accuracy percentage','not whole sites','power_lag_1h_kw',
                    '/api/operational-models/download','Current monthly model: validation pending'])assert.ok(html.includes(word),word);
  assert.ok(!html.includes('Model training pending'));
  assert.equal(JSON.stringify(state),before);
});
test('trained preview escapes labels and has no live-model activation control',()=>{
  const {ctx}=harness(),o=operationalFixture();o.sites[0].label='<img onerror=x>';
  o.sites[0].test_preview[0].forecast_origin_utc='<script>x</script>';
  const html=ctx.operationalModelsHtml(o);
  assert.ok(!html.includes('<img'));assert.ok(!html.includes('<script>'));assert.match(html,/&lt;script&gt;/);
  assert.ok(!html.includes('Apply model'));assert.match(html,/No model weights have replaced/);
});
test('missing trained files show unavailable rather than prototype scores',()=>{
  const {ctx}=harness(),html=ctx.operationalModelsHtml({status:'unavailable',reason:'Files changed'});
  assert.match(html,/Files changed/);assert.ok(!html.includes('1.25'));assert.ok(!html.includes('/api/operational-models/download'));
  assert.equal(ctx.operationalModelsHtml(null),'');
});
