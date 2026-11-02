/* UI state tests, not browser/visual verification. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.join(__dirname,'..');
const source=fs.readFileSync(path.join(root,'static/demo-cases.js'),'utf8');
const preset=JSON.parse(fs.readFileSync(path.join(root,'data/examples/juru_synthetic_project.json'),'utf8'));
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function harness(active=true){
  const messages=[],errors=[],requests=[];
  const state={role:'investor',busy:false,dirty:false,view:'locations',site:{id:'OLD'}};
  const discovery={active,busy:false,opening:false};
  const c=vm.createContext({state,discovery,esc,URLSearchParams,number:n=>String(n),
    contextReady:()=>!state.busy&&!state.dirty,
    discoveryLock:value=>{discovery.busy=value;},setBusy:value=>{state.busy=value;},
    api:async url=>{requests.push(url);return {json:async()=>structuredClone(preset)};},
    updateProjectContext:async project=>{assert.equal(state.busy,false);Object.assign(state,project);return true;},
    discoveryMode:value=>{discovery.active=value;},openDiscovery:async()=>{discovery.active=true;},ensureCustomOption(){},render(){},
    toast:s=>messages.push(s),error:s=>errors.push(s)});
  vm.runInContext(source,c);return {c,state,discovery,messages,errors,requests};
}

test('test card is clearly labelled with details collapsed and download distinct',()=>{
  const h=harness(),html=h.c.juruDemoCardHtml();
  for(const text of ['Load Juru test case','Demo data','300 households','Data notes','/api/demo-cases/juru/download','Open public-data screen','data-open-juru-public'])assert.ok(html.includes(text));
  assert.ok(!/<details[^>]*\bopen\b/.test(html));
  assert.ok(!/fictional/i.test(html));
});

test('explicit Juru startup link loads the complete preset and retains the chosen role',async()=>{
  const h=harness(false);h.state.site=null;h.state.result=null;
  await h.c.openInitialWorkspace('?demo=juru');
  assert.equal(h.state.site.id,'RW-JURU-SYNTHETIC-01');
  assert.equal(h.state.role,'investor');assert.equal(h.state.view,'overview');
  assert.equal(h.discovery.active,false);assert.equal(h.requests.length,1);
  assert.equal(h.state.assumptions.debt_payment,500000);
  assert.equal(h.state.site.mills,2);assert.equal(h.state.site.pumps,3);
  assert.equal(h.state.site.households,300);assert.equal(h.state.context.input_origin,'synthetic');
});

test('ordinary and unknown startup links keep the normal location screen',async()=>{
  for(const query of ['', '?demo=other', '?demo=https://example.com', '?country=RW']){
    const h=harness(false);await h.c.openInitialWorkspace(query);
    assert.equal(h.discovery.active,true);assert.equal(h.requests.length,0);
    assert.equal(h.state.site.id,'OLD');
  }
});

test('failed Juru startup leaves the location screen usable and shows the error',async()=>{
  const h=harness(false);h.c.api=async()=>{throw new Error('Service unavailable');};
  await h.c.openInitialWorkspace('?demo=juru');
  assert.equal(h.discovery.active,true);assert.equal(h.state.busy,false);
  assert.equal(h.discovery.busy,false);assert.deepEqual(h.errors,['Service unavailable']);
  assert.equal(h.state.site.id,'OLD');
});

test('startup uses the opt-in loader and never saves or overwrites a project',()=>{
  assert.match(fs.readFileSync(path.join(root,'static/app.js'),'utf8'),/openInitialWorkspace\(window.location.search\)/);
  assert.ok(!source.includes('localStorage.setItem'));
  assert.ok(!source.includes('saveScenario('));
});

for(const active of [true,false])test('preset loads from '+(active?'location screen':'current dashboard')+' without changing role',async()=>{
  const h=harness(active);await h.c.loadJuruDemo();
  assert.equal(h.state.site.id,'RW-JURU-SYNTHETIC-01');
  assert.equal(h.state.role,'investor');assert.equal(h.state.view,'overview');
  assert.equal(h.state.context.input_origin,'synthetic');
  assert.equal(h.state.financialEvidence,null);
  assert.equal(h.state.busy,false);assert.equal(h.discovery.busy,false);assert.equal(h.discovery.active,false);
  assert.equal(h.requests.length,1);assert.equal(h.errors.length,0);
});

test('busy or unapplied edits do not get overwritten',async()=>{
  for(const flag of ['busy','dirty']){
    const h=harness();h.state[flag]=true;await h.c.loadJuruDemo();
    assert.equal(h.requests.length,0);assert.equal(h.state.site.id,'OLD');
  }
});

test('failed load preserves project and shows real error',async()=>{
  const h=harness();h.c.api=async()=>{throw new Error('Service unavailable');};
  await h.c.loadJuruDemo();
  assert.equal(h.state.site.id,'OLD');assert.equal(h.state.view,'locations');
  assert.equal(h.discovery.active,true);assert.equal(h.state.busy,false);
  assert.equal(h.discovery.busy,false);assert.deepEqual(h.errors,['Service unavailable']);
});

test('public-data action explicitly opts out of the Juru demo and releases the busy lock',async()=>{
  const h=harness(false),location={id:'11186926',country_code:'RW',source:'GeoNames',label:'Juru'};
  let opened;
  h.c.api=async url=>{assert.equal(url,'/api/geography/location?country=RW&id=11186926');return {json:async()=>location};};
  h.c.openLocationDashboard=async(loc,options)=>{assert.equal(h.state.busy,false);opened={loc,mode:options.projectMode};};
  await h.c.openJuruPublicScreen();
  assert.equal(opened.loc,location);assert.equal(opened.mode,'public_proxy');
  assert.equal(h.state.busy,false);assert.equal(h.state.role,'investor');
});

test('public-data action preserves the current project when the lookup fails',async()=>{
  const h=harness(false);h.c.api=async()=>{throw Error('Lookup unavailable');};
  h.c.openLocationDashboard=()=>assert.fail('Must not replace the current project');
  await h.c.openJuruPublicScreen();
  assert.deepEqual(h.errors,['Lookup unavailable']);
  assert.equal(h.state.site.id,'OLD');assert.equal(h.state.busy,false);
});

test('public-data action does not discard unapplied inputs',async()=>{
  const h=harness(false);h.state.dirty=true;
  h.c.openLocationDashboard=()=>assert.fail('Must not discard edits');
  await h.c.openJuruPublicScreen();
  assert.equal(h.requests.length,0);assert.equal(h.state.site.id,'OLD');
});

test('repeated clicks send only one request',async()=>{
  const h=harness(false);let finish;
  h.c.api=async url=>{h.requests.push(url);return new Promise(resolve=>{finish=()=>resolve({json:async()=>structuredClone(preset)});});};
  const first=h.c.loadJuruDemo();await h.c.loadJuruDemo();
  finish();await first;assert.equal(h.requests.length,1);
});

test('case notes escape data and do not appear on other projects',()=>{
  const h=harness();assert.equal(h.c.juruCaseSummaryHtml({}),'');
  const html=h.c.juruCaseSummaryHtml({site:{households:300},context:{currency:'RWF'},demo_case:{notice:'<img src=x>',scope:'demo',features:[{feature_number:1,feature:'Households',value:'<script>',unit:'households'}]}});
  assert.ok(html.includes('&lt;script&gt;'));assert.ok(html.includes('&lt;img'));
  assert.ok(!html.includes('<script>'));assert.ok(html.includes('Demo data'));
});

test('preset is connected to discovery, locations, report and analysis',()=>{
  for(const [file,pattern] of [
    ['static/discovery.js',/bindJuruDemoButtons/],
    ['static/screening.js',/renderJuruCasePanels/],
    ['templates/report.html',/r.demo_case.features/],
    ['src/analysis.py',/annotate\(result\)/],
  ])assert.match(fs.readFileSync(path.join(root,file),'utf8'),pattern);
});

test('cleared optional inputs are not counted as complete and zero remains supplied',()=>{
  const h=harness();
  const html=h.c.juruCaseSummaryHtml({site:{households:300},context:{currency:'RWF'},demo_case:{notice:'Demo data',scope:'test',features:[
    {feature_number:1,feature:'Income',value:null,unit:'RWF/month'},
    {feature_number:2,feature:'Elapsed months',value:0,unit:'months'}]}});
  assert.ok(html.includes('1/20 features supplied'));assert.ok(html.includes('Not supplied'));
});

test('compact notes retain provenance without duplicating the input table',()=>{
  const h=harness();
  const html=h.c.juruCaseSummaryHtml({site:{households:300},context:{currency:'RWF'},demo_case:{notice:'Generated test inputs, not measured consumption.',scope:'Public sector data stays separate.',features:[{feature_number:1,feature:'Households',value:300,unit:'households'}]}},true);
  assert.match(html,/^<details/);
  assert.ok(!/<details[^>]*\bopen\b/.test(html));
  for(const text of ['1/20 inputs','not measured consumption','not calibrated confidence limits','Public sector data stays separate','/api/demo-cases/juru/download'])assert.ok(html.includes(text),text);
  assert.ok(!html.includes('<table>'));
});

test('demo notes appear below Community and in Evidence, never duplicate Overview',()=>{
  const h=harness(),insertions=[];
  h.state.result={site:{households:300},context:{currency:'RWF'},demo_case:{notice:'Generated test inputs',scope:'Demo area',features:[]}};
  h.c.$=id=>({insertAdjacentHTML:(position,html)=>insertions.push({id,position,html})});
  h.c.renderJuruCasePanels();
  assert.deepEqual(insertions.map(x=>[x.id,x.position]),[['#view-community','beforeend'],['#view-evidence','afterbegin']]);
  assert.ok(insertions[0].html.startsWith('<details'));
  assert.ok(insertions[1].html.includes('<table>'));
});
