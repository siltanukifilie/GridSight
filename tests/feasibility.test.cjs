/* Real rendering functions with DOM test doubles; no visual/browser claims. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.join(__dirname,'..');
const read=file=>fs.readFileSync(path.join(root,file),'utf8');
const example=JSON.parse(read('tests/fixtures/rw-demo-02.json'));
const app=read('static/app.js').split("document.querySelectorAll('.nav-item').forEach(b=>b.addEventListener")[0];

function harness(role='developer', modern=false) {
  const nodes=new Map(), saved={}, requests=[];
  const node=selector=>{
    if(!nodes.has(selector))nodes.set(selector,{innerHTML:'',value:'',textContent:'',dataset:{},events:{},
      classList:{add(){},remove(){},toggle(){}},addEventListener(event,handler){this.events[event]=handler;},
      querySelectorAll(){return [];},querySelector(selector){return node(selector);},focus(){},setAttribute(){},removeAttribute(){}});
    return nodes.get(selector);
  };
  const result=structuredClone(example);
  result.planning.project_capex=123456;
  const inputs={context:result.context,contextSettings:{countries:JSON.parse(read('config/countries.json')),defaults:{RW:result.assumptions,UG:{...result.assumptions,tariff:0,variable_cost:0,fixed_cost:0,debt_payment:0}}},role,view:'feasibility',result,site:result.site,assumptions:result.assumptions,planning:result.planning,
    planningSettings:{defaults:structuredClone(result.planning),limits:Object.fromEntries(Object.keys(result.planning).map(k=>[k,[0,1e12]]))},
    bootstrap:{data:JSON.parse(read('data/metadata.json')),site_limits:Object.fromEntries(Object.keys(result.site).map(k=>[k,[0,1e12]])),scenario_limits:Object.fromEntries(Object.keys(result.assumptions).map(k=>[k,[0,1e12]]))}};
  const context=vm.createContext({inputs,structuredClone,Event,document:{querySelector:node,querySelectorAll:()=>[],createElement:()=>({click(){}})},
    localStorage:{getItem:key=>saved[key]||null,setItem:(key,value)=>saved[key]=value},
    setTimeout:()=>1,clearTimeout(){},URL:{createObjectURL:()=> 'blob:unit-test',revokeObjectURL(){}},
    window:{open:()=>({document:{write(){},close(){}},close(){}})},fetch:async(url,options)=>{
      requests.push({url,body:JSON.parse(options.body)});return {ok:true,blob:async()=>({}),text:async()=>'<html></html>'};
    }});
  for(const script of ['static/workspaces.js','static/demand-charts.js','static/feasibility.js','static/context.js','static/discovery.js','static/rwanda-data.js','static/connection.js','static/detailed-inputs.js','static/monthly-validation.js','static/statistical.js','static/financial-evidence.js','static/maintenance.js'])vm.runInContext(read(script),context);
  if(modern)vm.runInContext(read('static/analytics.js'),context);
  vm.runInContext(app,context);
  vm.runInContext('Object.assign(state,inputs)',context);
  return {context,node,saved,requests,state:()=>vm.runInContext('state',context)};
}

for(const role of ['developer','investor']) {
  test('redesigned overview integrates with all existing workspaces: '+role,()=>{
    const h=harness(role,true);h.context.render();
    const html=h.node('#view-overview').innerHTML;
    for(const label of ['analytics-explorer','Low / expected / high range','Who uses the power?','Daily demand','Site evidence & forecast explanation'])assert.ok(html.includes(label),label);
    assert.ok(!/NaN|undefined|\$\{/.test(html));
    assert.ok(h.node('#analytics-year').events.change);
    assert.ok(h.node('#planning-form').events.submit);
    assert.ok(h.node('#view-evidence').innerHTML.includes('Keep the model accountable'));
  });
  test('all real view renderers integrate with new feasibility data: '+role,()=>{
    const h=harness(role);
    h.context.render();
    const html=h.node('#view-feasibility').innerHTML;
    for(const text of ['Low / expected / high range','Too much—or too little?','Productive-use opportunities','Capital & cash','Download report','id="planning-form"'])assert.ok(html.includes(text),text);
    assert.ok(h.node('#view-overview').innerHTML.includes('Low / expected / high range'));
    assert.ok(!html.includes('NaN')&&!html.includes('undefined'));
    assert.ok(!html.includes('${'), 'all currency labels are rendered');
    assert.ok(h.node('#planning-form').events.submit);
    assert.ok(h.node('#download-feasibility').events.click);
    if(role==='investor')assert.ok(!h.node('#view-community').innerHTML.includes('<input'));
  });
}

test('blank optional budgets remain unknown; a supplied zero remains zero',()=>{
  const h=harness(), form={elements:{}};
  for(const key of Object.keys(h.state().planningSettings.defaults))form.elements[key]={value:'0',dataset:{optional:'false',percent:'false'}};
  form.elements.project_capex={value:'',dataset:{optional:'true'}};
  form.elements.mill_support_cost={value:'0',dataset:{optional:'true'}};
  form.elements.low_factor={value:'80',dataset:{percent:'true'}};
  form.elements.high_factor={value:'130',dataset:{percent:'true'}};
  const values=h.context.planningFormValues(form);
  assert.equal(values.project_capex,null);
  assert.equal(values.mill_support_cost,0);
  assert.equal(values.low_factor,.8);
  assert.equal(values.high_factor,1.3);
});

test('planning controls show labels and retain optional budget values',()=>{
  const h=harness();
  const blank=h.context.planningField('pump_support_cost','Pump cost',{optional:true});
  assert.match(blank,/value=""/);
  assert.match(blank,/placeholder="Not provided"/);
  assert.ok(!blank.includes(' required'));
  assert.match(h.context.planningField('project_capex','Capital',{optional:true}),/value="123456"/);
});

test('analysis payload and saved scenario retain planning inputs',()=>{
  const h=harness();
  assert.equal(h.context.payload().planning.project_capex,123456);
  h.context.saveScenario();
  assert.equal(JSON.parse(h.saved['gridsight-scenario-v1']).planning.project_capex,123456);
});

test('legacy saved scenario restores new planning defaults',async()=>{
  const h=harness();
  h.saved['gridsight-scenario-v1']=JSON.stringify({site:example.site,assumptions:example.assumptions});
  h.context.renderCommunity();
  vm.runInContext('calculate=async()=>{};ensureCustomOption=()=>{};navigate=()=>{}',h.context);
  await h.node('#restore-button').events.click();
  assert.equal(h.state().planning.project_capex,123456);
  assert.equal(h.state().planning.low_factor,.8);
});

test('report, ZIP and print actions submit the exact analyzed planning inputs',async()=>{
  const h=harness('investor');
  h.state().planning={...h.state().planning,project_capex:999}; // unapplied draft must not leak into export
  await h.context.downloadFeasibility();
  await h.context.downloadExport();
  await h.context.printReport();
  assert.deepEqual(h.requests.map(r=>r.url),['/api/feasibility-report','/api/export','/api/report']);
  for(const r of h.requests){assert.equal(r.body.planning.project_capex,123456);assert.equal(r.body.role,'investor');}
});

test('dirty inputs block report downloads and printing',async()=>{
  const h=harness(); h.state().dirty=true;
  await h.context.downloadFeasibility(); await h.context.downloadExport(); await h.context.printReport();
  assert.equal(h.requests.length,0);
});

test('unapplied inputs cannot be silently lost by navigating to another form',()=>{
  const h=harness();
  h.context.markDirty();
  h.context.navigate('scenarios');
  assert.equal(h.state().view,'feasibility');
  assert.equal(h.state().dirtyView,'feasibility');
  assert.match(h.node('#toast').textContent,/Apply your input changes/);
  h.state().dirty=false;h.state().dirtyView=null;
  h.context.navigate('scenarios');
  assert.equal(h.state().view,'scenarios');
});

test('yearly chart uses monthly growth while preserving the annual estimate',()=>{
  const h=harness();
  const view=h.context.demandChartData(example,'year');
  assert.equal(view.tag,'Growth scenario');
  assert.ok(view.series.central.at(-1)>view.series.central[0]);
  const sum=view.series.central.reduce((a,b)=>a+b,0);
  assert.ok(Math.abs(sum-view.total)<1e-7);
  assert.match(view.detail,/negative growth can fall/);
  const html=h.context.demandChartContents(example,'year');
  assert.match(html,/Monthly growth · Year 1/);
});

test('case cards distinguish scenario factors from prediction bounds',()=>{
  const h=harness(), html=h.context.caseSummaryHtml(example);
  for(const label of ['Low · 80%','Expected · 100%','High · 130%','Separate from the prediction range'])assert.ok(html.includes(label));
});

for(const role of ['developer','investor'])test('Uganda currency reaches every view: '+role,()=>{
  const h=harness(role),s=h.state();
  Object.assign(s.result.context,{country_code:'UG',country:'Uganda',currency:'UGX'});
  s.context=s.result.context;
  s.site.name='RWF Cooperative'; // arbitrary user text must not be relabelled
  h.context.render();
  for(const view of ['overview','community','scenarios','feasibility','evidence','locations']){
    const html=h.node('#view-'+view).innerHTML;
    assert.ok(html.length>50,view);
    assert.ok(!html.includes('${')&&!html.includes('NaN')&&!html.includes('undefined'),view);
    assert.ok(!/RWF\s*\//.test(html),view+' denomination');
  }
  assert.ok(h.node('#view-community').innerHTML.includes('RWF Cooperative'));
  assert.ok(h.node('#view-feasibility').innerHTML.includes('Capacity-linked part · UGX'));
  assert.equal(h.node('#footer-context').textContent,'Synthetic model · UGX');
});

test('location and input provenance are saved and passed to all report actions',async()=>{
  const h=harness(),s=h.state();
  s.context={...s.context,location:{latitude:-2,longitude:30,label:'Chosen site',source:'manual',country_code:'RW'},assumed_fields:['mills']};
  s.result.context=s.context;
  assert.equal(h.context.payload().context.location.latitude,-2);
  h.context.saveScenario();
  assert.deepEqual(JSON.parse(h.saved['gridsight-scenario-v1']).context.assumed_fields,['mills']);
  s.context={...s.context,location:null}; // draft must not alter the analyzed export
  await h.context.downloadFeasibility();await h.context.downloadExport();await h.context.printReport();
  for(const request of h.requests)assert.equal(request.body.context.location.label,'Chosen site');
});

test('locations use escaped administrative paths, no map or coordinate controls',()=>{
  const h=harness(),s=h.state();
  s.result.context.location={label:'A <script>site</script>',administrative_path:['District','Sector','Cell'],source:'user_entered_administration',country_code:'RW'};
  h.context.renderLocations();const html=h.node('#view-locations').innerHTML;
  assert.ok(html.includes('A &lt;script&gt;site&lt;/script&gt;'));assert.ok(html.includes('District → Sector → Cell'));
  assert.ok(!/<iframe|coordinate-form|load-map|device-location|<script>/.test(html));
  assert.equal(typeof h.context.fillDeviceLocation,'undefined');
});
test('legacy coordinate metadata never creates an interactive map',()=>{
  const h=harness();h.state().result.context.location={label:'Legacy',latitude:-2,longitude:30};
  h.context.renderLocations();assert.ok(!/iframe|load-map|coordinate-form/.test(h.node('#view-locations').innerHTML));
});

test('failed location update restores last valid scenario and permits correction',async()=>{
  const h=harness(),s=h.state(),previous=s.context;
  vm.runInContext('calculate=async()=>{state.dirty=true}',h.context);
  await h.context.applyLocation({latitude:90,longitude:0,label:'Invalid'});
  assert.equal(s.context,previous);
  assert.equal(s.dirty,false);
  assert.equal(s.dirtyView,null);
});

test('a different country starts a fresh location-first project, not a relabelled scenario',()=>{
  const h=harness();h.context.renderLocations();
  const html=h.node('#view-locations').innerHTML;
  assert.ok(!html.includes('id="country-form"'));
  assert.ok(html.includes('Rwanda locations can use public building/facility proxies'));
  assert.ok(h.node('#find-new-site').events.click);
});

test('dirty state prevents location requests and changes',async()=>{
  const h=harness(),s=h.state(),previous=s.context;
  s.dirty=true;
  await h.context.applyLocation({latitude:-2,longitude:30});
  await h.context.fetchPublicContext();
  assert.equal(s.context,previous);
  assert.equal(h.requests.length,0);
});

test('validation UI requests attestation and labels uploads as separate comparisons',()=>{
  const h=harness();h.context.renderEvidence();
  const html=h.node('#view-evidence').innerHTML;
  for(const text of ['Legacy reference-model comparison','Test the current forecast','name="attestation" required','/api/validation-template','not saved to disk','Unconfirmed / not validated'])assert.ok(html.includes(text),text);
  assert.ok(h.node('#validation-form').events.submit);
});

test('thin-data suggestions need explicit review and a second submit before analysis',async()=>{
  const h=harness(),s=h.state(),keys=['households','shops','schools','clinics','mills','pumps','cold_rooms','uptake','appliance_index'];
  s.bootstrap.site_limits=Object.fromEntries(keys.map(k=>[k,[0,1500]]));
  const form={elements:{name:{value:'Known community'},district:{value:'Kirehe'}}};
  for(const key of keys)form.elements[key]={value:String(example.site[key]),dataset:{percent:'false'}};
  form.elements.mills.value='';
  h.node('#thin-mode').checked=true;
  let prepareCalls=0,analyzeCalls=0;
  h.context.api=async(path,body)=>{assert.equal(path,'/api/prepare-inputs');assert.equal(body.site.mills,null);prepareCalls++;return {json:async()=>({site:{...example.site,mills:0},assumptions:[{field:'mills',value:0,reason:'Unknown, not observed zero'}],assumed_fields:['mills'],notice:'Review every proposed value.'})};};
  h.context.calculate=async()=>{analyzeCalls++;s.dirty=false;};h.context.ensureCustomOption=()=>{};h.context.navigate=()=>{};
  const event={preventDefault(){},target:form};
  await h.context.submitCommunity(event);
  assert.equal(prepareCalls,1);assert.equal(analyzeCalls,0);assert.equal(form.elements.mills.value,'');
  h.node('#accept-thin').events.click();
  assert.equal(Number(form.elements.mills.value),0);assert.ok(s.context.assumed_fields.includes('mills'));
  // Browser input.value coerces numbers to strings; mirror that DOM behavior here.
  form.elements.mills.value=String(form.elements.mills.value);
  await h.context.submitCommunity(event);
  assert.equal(analyzeCalls,1);assert.equal(s.site.mills,0);assert.equal(s.context.input_origin,'user_entered');
});
const rampExample=JSON.parse(read('tests/fixtures/connection-ramp.json'));
function connected(role='developer'){
  const h=harness(role),s=h.state(),r=structuredClone(rampExample);
  Object.assign(s,{result:r,site:r.site,assumptions:r.assumptions,planning:r.planning,
    connection:r.connection,context:r.context});
  return h;
}
function connectionForm(changes={}){
  const values={enabled:true,connection_month:'2026-11',ramp_months:'24',
    start_household_fraction:'35',start_appliance_fraction:'60',start_business_fraction:'50',...changes};
  return {reportValidity:()=>true,elements:Object.fromEntries(Object.entries(values).map(([key,value])=>[key,key==='enabled'?{checked:value}:{value}]))};
}
for(const role of ['developer','investor'])test('connection curve and five deliverables render for '+role,()=>{
  const h=connected(role);h.context.render();
  const overview=h.node('#view-overview').innerHTML,feasibility=h.node('#view-feasibility').innerHTML,evidence=h.node('#view-evidence').innerHTML;
  assert.match(overview,/Demand after connection/);
  assert.match(overview,/2026-11/);
  assert.match(overview,/Propagated reference range/);
  assert.match(overview,/Month 36 demand/);
  assert.equal(feasibility.includes('id="connection-form"'),role==='developer');
  for(const phrase of ['Five deliverables','Pending genuine operator data','Why this forecast?','Safe meter-data sharing proposal','/api/meter-sharing-proposal','not implemented'])
    assert.ok(evidence.includes(phrase),phrase);
  for(const html of [overview,feasibility,evidence])assert.ok(!/NaN|undefined|\$\{/.test(html));
  const year=h.context.demandChartData(h.state().result,'year');
  assert.equal(year.subtitle,'First year after connection');
  assert.equal(year.labels[0],'2026-11');
  assert.equal(year.labels[11],'2027-10');
  assert.ok(Math.abs(year.total-year.series.central.reduce((a,b)=>a+b,0))<1e-7);
});

test('connection zero percentages and blank date remain explicit',()=>{
  const h=connected(),value=h.context.connectionFormValues(connectionForm({connection_month:'',start_household_fraction:'0',start_appliance_fraction:'0',start_business_fraction:'0'}));
  assert.equal(value.connection_month,null);
  assert.equal(value.start_household_fraction,0);
  assert.equal(value.start_appliance_fraction,0);
  assert.equal(value.start_business_fraction,0);
});

test('saved and downloaded analyses use the applied connection settings',async()=>{
  const h=connected();
  assert.equal(h.context.payload().connection.connection_month,'2026-11');
  h.context.saveScenario();
  assert.equal(JSON.parse(h.saved['gridsight-scenario-v1']).connection.ramp_months,24);
  h.state().connection={...h.state().connection,ramp_months:60}; // draft is not exportable as applied result
  await h.context.downloadFeasibility();await h.context.downloadExport();await h.context.printReport();
  for(const r of h.requests){
    assert.equal(r.body.connection.ramp_months,24);
    assert.equal(r.body.connection.connection_month,'2026-11');
  }
});

test('restore retains connection inputs; failed replacement rolls back them too',async()=>{
  const h=connected(),s=h.state();
  h.context.saveScenario();
  s.connection={enabled:false};
  h.context.renderCommunity();
  h.context.calculate=async()=>{};
  h.context.ensureCustomOption=()=>{};h.context.navigate=()=>{};
  await h.node('#restore-button').events.click();
  assert.equal(s.connection.connection_month,'2026-11');
  const previous=s.connection;
  h.context.calculate=async()=>{s.dirty=true;};
  assert.equal(await h.context.updateProjectContext({connection:{enabled:true,ramp_months:60}}),false);
  assert.equal(s.connection,previous);
});

test('role switch retains the exact connection and curve',()=>{
  const h=connected(),s=h.state(),c=s.connection,r=s.result;
  h.context.switchWorkspace('investor');
  assert.equal(s.connection,c);assert.equal(s.result,r);
  assert.equal(s.role,'investor');
});

for(const formName of ['#connection-form','#planning-form'])test('either update applies both edited forms: '+formName,async()=>{
  const h=connected(),s=h.state();h.context.renderFeasibility();
  Object.assign(h.node('#connection-form'),connectionForm({ramp_months:'36'}));
  Object.assign(h.node('#planning-form'),{reportValidity:()=>true,elements:{project_capex:{value:'54321'}}});
  h.context.planningFormValues=form=>({project_capex:Number(form.elements.project_capex.value)});
  let calls=0;h.context.calculate=async()=>{calls++;s.dirty=false;};
  s.dirty=true;
  await h.node(formName).events.submit({preventDefault(){},target:h.node(formName)});
  assert.equal(calls,1);assert.equal(s.connection.ramp_months,36);assert.equal(s.planning.project_capex,54321);
});

test('invalid companion form prevents partial application and busy state prevents submit',async()=>{
  const h=connected(),s=h.state(),previous=s.connection;let calls=0;
  Object.assign(h.node('#connection-form'),connectionForm());
  h.node('#planning-form').reportValidity=()=>false;
  h.context.calculate=async()=>{calls++;};
  await h.context.applyFeasibilityForms();
  assert.equal(calls,0);assert.equal(s.connection,previous);
  s.busy=true;h.node('#planning-form').reportValidity=()=>{throw Error('must not run while busy');};
  await h.context.applyFeasibilityForms();
  assert.equal(calls,0);
});

test('investor financial edits leave connection assumptions unchanged',async()=>{
  const h=connected('investor'),s=h.state(),previous=s.connection;
  h.node('#planning-form').reportValidity=()=>true;
  h.context.planningFormValues=()=>({...s.planning,project_capex:1000});
  h.context.calculate=async()=>{s.dirty=false;};
  await h.context.applyFeasibilityForms();
  assert.equal(s.connection,previous);assert.equal(s.planning.project_capex,1000);
});

const detailedExample=JSON.parse(read('tests/fixtures/detailed-inputs.json'));
function detailedHarness(role='developer'){
  const h=harness(role),r=structuredClone(detailedExample),s=h.state();
  Object.assign(s,{result:r,site:r.site,context:r.context,detailed:r.detailed,connection:r.connection,assumptions:r.assumptions,planning:r.planning});
  s.planningSettings.detailed_defaults=structuredClone(r.detailed);return h;
}
for(const role of ['developer','investor'])test('detailed views integrate all 20 features for '+role,()=>{
  const h=detailedHarness(role);h.context.render();
  const html=h.node('#view-community').innerHTML;
  assert.ok(html.includes('Household affordability'));
  assert.ok(!/NaN|undefined|<iframe/.test(html));
  if(role==='developer'){
    assert.ok(html.includes('id="detailed-form"'));assert.ok(html.includes('Agricultural seasonality'));
    assert.ok(html.includes('data-step="-1"'));assert.ok(html.includes('id="detail-month-slider"'));
    assert.ok(!h.node('#view-scenarios').innerHTML.includes('name="household_growth"'));
  }else assert.ok(!html.includes('<input'));
  assert.ok(!h.node('#view-feasibility').innerHTML.includes('id="connection-form"'));
  assert.match(h.node('#view-overview').innerHTML,/service Months 19–54/);
});
function detailedForm(h){
  const r=h.state().result,d=r.detailed,values={};
  for(const key of ['households','uptake','shops','mills','pumps','cold_rooms','schools','clinics'])values['site_'+key]=r.site[key]*(key==='uptake'?100:1);
  for(const key of ['months_since_connection','household_income_monthly','connection_fee','new_connections_yearly'])values[key]=d[key]??'';
  values.appliance_adoption_rate=d.appliance_adoption_rate*100;values.business_growth=r.assumptions.business_growth*100;values.tariff=r.assumptions.tariff;
  for(const [k,v] of Object.entries(d.appliances))for(const [suffix,key] of [['units','units_per_household'],['power','power_w'],['hours','hours_per_day']])values['app_'+k+'_'+suffix]=v[key];
  for(const [k,v] of Object.entries(d.equipment))for(const [suffix,key] of [['power','power_kw'],['hours','hours_per_day']])values['eq_'+k+'_'+suffix]=v[key];
  d.agricultural_seasonality.forEach((v,i)=>values['season_'+i]=v);
  return {elements:Object.fromEntries(Object.entries(values).map(([k,v])=>[k,{value:String(v)}]))};
}
test('all detailed values round-trip without mutating applied analysis',()=>{
  const h=detailedHarness(),r=h.state().result,form=detailedForm(h);
  const v=h.context.detailedFormValues(form);
  assert.deepEqual(JSON.parse(JSON.stringify(v.detailed)),r.detailed);
  assert.equal(v.site.uptake,r.site.uptake);
  form.elements.app_lighting_power.value='20';form.elements.season_0.value='0.5';
  const edited=h.context.detailedFormValues(form);
  assert.equal(edited.detailed.appliances.lighting.power_w,20);assert.equal(edited.detailed.agricultural_seasonality[0],.5);
  assert.equal(r.detailed.appliances.lighting.power_w,7);assert.equal(r.detailed.agricultural_seasonality[0],1);
});
test('optional unknowns remain null, explicit zero stays zero and required blanks fail',()=>{
  const h=detailedHarness(),f=detailedForm(h);f.elements.household_income_monthly.value='';f.elements.connection_fee.value='0';
  const v=h.context.detailedFormValues(f);assert.equal(v.detailed.household_income_monthly,null);assert.equal(v.detailed.connection_fee,0);
  f.elements.site_households.value='';assert.throws(()=>h.context.detailedFormValues(f),/Complete/);
});
test('steppers clamp values and dispatch dirty input events',()=>{
  const h=detailedHarness(),events=[],input={min:'0',max:'1',step:'.1',value:'.95',dispatchEvent:e=>events.push(e)};
  h.context.stepControl(input,1);assert.equal(input.value,'1');
  input.value='0';h.context.stepControl(input,-1);assert.equal(input.value,'0');
  input.value='';h.context.stepControl(input,1);assert.equal(input.value,'0.1');
  assert.match(h.context.stepInput('test','Power',7.5,{step:1}),/step="any"/);
  assert.match(h.context.stepInput('count','Households',2,{integer:true}),/step="1"/);
  assert.equal(events.length,3);assert.equal(events[0].type,'input');assert.equal(events[0].bubbles,true);
});
test('month slider and numeric time stay synchronized',()=>{
  const h=detailedHarness();h.context.renderCommunity();
  h.node('#detail-month-slider').value='24';h.node('#detail-month-slider').events.input();
  assert.equal(h.node('#detail-months_since_connection').value,'24');assert.equal(h.node('#detail-design-month').textContent,25);
  h.node('#detail-months_since_connection').value='0';h.node('#detail-months_since_connection').events.input();
  assert.equal(h.node('#detail-month-slider').value,'0');assert.equal(h.node('#detail-design-month').textContent,1);
});
test('save and every report action retain applied detailed inputs, not draft',async()=>{
  const h=detailedHarness();h.context.saveScenario();assert.equal(JSON.parse(h.saved['gridsight-scenario-v1']).detailed.months_since_connection,18);
  h.state().detailed={...h.state().detailed,months_since_connection:99};
  await h.context.downloadFeasibility();await h.context.downloadExport();await h.context.printReport();
  for(const request of h.requests)assert.equal(request.body.detailed.months_since_connection,18);
});
test('failed project replacement restores detailed assumptions',async()=>{
  const h=detailedHarness(),prior=h.state().detailed;
  h.context.calculate=async()=>{h.state().dirty=true;};
  assert.equal(await h.context.updateProjectContext({detailed:{enabled:true,months_since_connection:99}}),false);
  assert.equal(h.state().detailed,prior);
});
test('detailed yearly curve and all period charts retain correct scenario semantics',()=>{
  const h=detailedHarness(),r=h.state().result;
  for(const period of ['day','week','month','year']){
    const html=h.context.demandChartContents(r,period);assert.match(html,/Low \/ high scenario/);assert.ok(!/NaN|undefined/.test(html));
  }
  const year=h.context.demandChartData(r,'year');assert.match(year.subtitle,/M19/);assert.equal(year.series.central.length,12);
});
test('legacy project has an explicit working opt-in to detailed mode',()=>{
  const h=harness();h.context.renderCommunity();assert.ok(h.node('#enable-detailed').events.click);
});
