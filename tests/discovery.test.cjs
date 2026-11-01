/* DOM doubles verify state/handlers only; these are not browser or visual tests. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.join(__dirname,'..'),read=f=>fs.readFileSync(path.join(root,f),'utf8');
const example=JSON.parse(read('tests/fixtures/rw-demo-02.json'));
const configs=JSON.parse(read('config/countries.json'));
function harness(){
  const nodes=new Map(),requests=[],saved={};
  const node=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',hidden:false,value:'',disabled:false,events:{},dataset:{},classList:{add(){},remove(){},toggle(){}},elements:{},addEventListener(k,fn){this.events[k]=fn;},querySelectorAll(){return [];},querySelector(){return null;},append(){},setAttribute(){},removeAttribute(){},replaceChildren(child){this.child=child;}});return nodes.get(id);};
  const context=vm.createContext({structuredClone,Event,document:{body:{classList:{toggle(){}}},querySelector:node,querySelectorAll:()=>[],createElement:()=>({click(){}})},localStorage:{getItem:k=>saved[k]||null,setItem:(k,v)=>saved[k]=v},setTimeout:()=>1,clearTimeout(){}});
  for(const file of ['workspaces','demand-charts','feasibility','context','discovery','rwanda-data','connection','detailed-inputs'])vm.runInContext(read('static/'+file+'.js'),context);
  vm.runInContext(read('static/app.js').split("document.querySelectorAll('.nav-item').forEach(b=>b.addEventListener")[0],context);
  const state=vm.runInContext('state',context),discovery=vm.runInContext('discovery',context);
  Object.assign(state,{site:structuredClone(example.site),result:structuredClone(example),context:structuredClone(example.context),assumptions:structuredClone(example.assumptions),planning:structuredClone(example.planning),planningSettings:{defaults:{...example.planning,capacity_capex:null,project_capex:null}},contextSettings:{active_countries:Object.keys(configs),countries:configs,defaults:Object.fromEntries(Object.keys(configs).map(c=>[c,{...example.assumptions}]))},bootstrap:{demos:[example.site],defaults:example.assumptions,site_limits:{households:[0,1500],shops:[0,150],schools:[0,10],clinics:[0,5],mills:[0,10],pumps:[0,15],cold_rooms:[0,10],uptake:[0,1],appliance_index:[.5,2]}}});
  context.api=async(url,body)=>{requests.push({url,body});return {json:async()=>({items:[{id:'10',name:'Public district',feature:'ADM2'}],total:1,next_offset:null,provenance:{fetched_at:'2026-10-31T00:00:00Z'},notice:'Not grid evidence.'})};};
  return {context,state,discovery,node,requests,saved};
}

test('landing offers eight East African countries and only administrative selectors',async()=>{
  const h=harness();h.state.result=null;await h.context.openDiscovery();
  const html=h.node('#discovery-panel').innerHTML;
  for(const code of Object.keys(configs))assert.ok(html.includes('value="'+code+'"'));
  for(const label of ['Country','District','Sector','Cell'])assert.ok(html.includes(label));
  assert.ok(!/<iframe|latitude|longitude|device-location|coordinate-form/.test(html));
  assert.equal(h.state.result,null);assert.equal(h.requests.length,1);
  assert.equal(h.discovery.active,true);assert.ok(h.node('#named-location').events.submit);
});
test('country switch clears descendants and manual drafts, retaining analyzed project',async()=>{
  const h=harness(),previous=h.state.site;
  Object.assign(h.discovery,{area:'a',local:'b',location:{label:'Old'},places:[{id:'c'}]});
  h.node('#named-cell').value='Old';
  await h.context.loadDiscoveryCountry('TZ');
  assert.equal(h.discovery.country,'TZ');assert.equal(h.discovery.area,'');assert.equal(h.discovery.local,'');
  assert.equal(h.discovery.location,null);assert.equal(h.node('#named-cell').value,'');assert.equal(h.state.site,previous);
  assert.match(h.node('#local-label').textContent,/Sector \/ Ward/);
});
test('non-EAC country makes no geographic request',async()=>{
  const h=harness();await h.context.loadDiscoveryCountry('US');assert.equal(h.requests.length,0);
});
test('district loads sectors but never settlement candidates',async()=>{
  const h=harness();h.node('#discover-area').value='123';await h.context.chooseDiscoveryArea();
  assert.equal(h.requests.length,1);assert.match(h.requests[0].url,/kind=local&parent=123/);
  assert.equal(h.discovery.local,'');assert.equal(h.discovery.places.length,0);
});
test('sector loads cells under precisely that parent',async()=>{
  const h=harness();h.discovery.local='456';await h.context.loadDiscoveryPlaces();
  assert.equal(h.requests.length,1);assert.match(h.requests[0].url,/kind=cells&parent=456/);
});
test('empty sector does not fetch unrelated cells',async()=>{
  const h=harness();await h.context.loadDiscoveryPlaces();assert.equal(h.requests.length,0);
});
test('late country response cannot replace newer country',async()=>{
  const h=harness();let resolveRW;
  h.context.api=async url=>({json:()=>url.includes('country=RW')?new Promise(resolve=>resolveRW=resolve):Promise.resolve({items:[{id:'ug',name:'Uganda area'}],provenance:{fetched_at:'2026-10-31'},notice:'UG'})});
  const first=h.context.loadDiscoveryCountry('RW');await new Promise(r=>setImmediate(r));
  await h.context.loadDiscoveryCountry('UG');resolveRW({items:[{id:'rw',name:'Rwanda area'}],provenance:{fetched_at:'2026-10-31'},notice:'RW'});await first;
  assert.equal(h.discovery.country,'UG');assert.equal(h.discovery.areas[0].id,'ug');assert.equal(h.discovery.busy,false);
});
test('late cell response cannot repopulate cleared country selection',async()=>{
  const h=harness();let resolve;
  h.discovery.local='456';h.context.api=async()=>({json:()=>new Promise(r=>resolve=r)});
  const pending=h.context.loadDiscoveryPlaces();await new Promise(r=>setImmediate(r));
  h.discovery.epoch++;h.discovery.places=[];resolve({items:[{id:'old'}]});await pending;
  assert.equal(h.discovery.places.length,0);
});
test('missing cells stay unavailable and do not fall back to settlements',async()=>{
  const h=harness();h.discovery.local='456';h.context.api=async()=>({json:async()=>({items:[]})});
  await h.context.loadDiscoveryPlaces();assert.equal(h.discovery.places.length,0);
  assert.equal(h.node('#discover-place').disabled,true);assert.match(h.node('#finder-status').textContent,/no substitute coordinates/);
});
test('source failure permits manual names without inventing data',async()=>{
  const h=harness();h.context.api=async()=>{throw Error('Index unavailable');};
  await h.context.openDiscovery();assert.equal(h.discovery.areas.length,0);assert.equal(h.discovery.busy,false);
  assert.match(h.node('#finder-status').textContent,/unavailable/);assert.ok(h.node('#named-location').events.submit);
});
test('manual names submit the selected country and no coordinates',async()=>{
  const h=harness();await h.context.openDiscovery();let selected;
  h.context.openLocationDashboard=loc=>selected=loc;
  h.discovery.country='KE';
  h.node('#named-location').events.submit({preventDefault(){},target:{elements:{area:{value:'District'},local:{value:'Ward'},cell:{value:'Cell'}}}});
  assert.equal(selected.country_code,'KE');assert.equal(selected.source,'user_entered_administration');
  assert.equal(JSON.stringify(selected.administrative_path),'["District","Ward","Cell"]');
  assert.ok(!('latitude' in selected));assert.ok(!('longitude' in selected));
});
test('choosing a canonical cell opens the detailed input review',async()=>{
  const h=harness();let applied;
  const location={id:'123',country_code:'RW',label:'Cell',source:'GeoNames'};
  h.context.api=async(url,body)=>{assert.equal(url,'/api/location-project');assert.equal(body.location,location);return {json:async()=>({site:{households:99},context:{input_origin:'public_proxy'},detailed:{enabled:true}})};};
  h.context.updateProjectContext=async p=>{applied=p;return true;};h.context.render=()=>{};h.context.ensureCustomOption=()=>{};
  await h.context.openLocationDashboard(location);
  assert.equal(applied.site.households,99);assert.equal(applied.detailed.enabled,true);
  assert.equal(h.state.view,'community');assert.equal(h.discovery.active,false);assert.equal(h.discovery.busy,false);
});
test('failed location preparation preserves project and offers administrative fallback',async()=>{
  const h=harness(),oldSite=h.state.site;h.context.api=async()=>{throw Error('Source unavailable');};
  await h.context.openLocationDashboard({country_code:'RW',label:'Cell'});
  assert.equal(h.state.site,oldSite);assert.match(h.node('#finder-status').textContent,/unavailable/);
  assert.ok(h.node('#manual-candidate').events.click);assert.equal(h.discovery.busy,false);
});
test('dirty edits block starting a new location',async()=>{
  const h=harness();h.state.dirty=true;await h.context.openDiscovery();
  assert.equal(h.requests.length,0);assert.equal(h.discovery.active,false);
});
test('connected/planned grid claims remain visible, never approved as unserved',()=>{
  const h=harness();h.state.result.context.grid={status:'connected'};
  assert.match(h.context.siteScreeningHtml(),/Not an unserved-site candidate/);
  h.state.result.context.grid={status:'planned'};assert.match(h.context.siteScreeningHtml(),/Review grid-arrival risk/);
});
test('malicious place names are escaped',()=>{
  const h=harness();h.state.result.context.location={label:'<script>',administrative_path:['<img onerror=bad>']};
  const html=h.context.siteScreeningHtml();assert.match(html,/&lt;img/);assert.ok(!html.includes('<img'));
});
test('saved financial evidence travels through landing-page restore',async()=>{
  const h=harness();let changes;
  h.saved['gridsight-scenario-v1']=JSON.stringify({site:h.state.site,assumptions:h.state.assumptions,financial_evidence:{schema:'invented-test-packet'}});
  h.context.updateProjectContext=async c=>{changes=c;return false;};
  await h.context.restoreDiscoveryProject();
  assert.equal(changes.financialEvidence.schema,'invented-test-packet');
});
test('failed context update restores the previous evidence packet',async()=>{
  const h=harness();h.state.financialEvidence={keep:true};
  h.context.calculate=async()=>{h.state.financialEvidence=null;h.state.dirty=true;};
  const ok=await h.context.updateProjectContext({financialEvidence:{new:true}});
  assert.equal(ok,false);assert.equal(h.state.financialEvidence.keep,true);
});
