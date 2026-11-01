const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../static/screening.js'),'utf8');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const make=extra=>{const c=vm.createContext({esc,number:(x,d=0)=>Number(x).toFixed(d),...extra});vm.runInContext(source,c);return c;};
const packet=()=>({status:'available',notice:'Public context',limitations:['Historical grid only','Unknown equipment'],
  selected_site_id:null,source_version:'v1',method_version:'v1',method:'Minmax',components:[],
  rows:[{priority_rank:1,site_id:'RW-Bugesera-juru',site_name:'Juru',priority_score:62.77,
    contributions:[{label:'<img src=x>',points:30}],households_2022:8508,milling_places_total:null,farming_generators_total:null,
    building_density_per_km2:203.5,nighttime_light_radiance_gep_mean_nw_cm2_sr:.1017,gridfinder_reference_point_distance_km:.98}]});

test('ranking exposes assumptions, units, missing counts and escaped source strings',()=>{
  const html=make().bugeseraRankingHtml(packet());
  for(const text of ['Score / 100','nW/cm²/sr','Historical grid','Unavailable','not project customers','data-review-sector','&lt;img'])assert.ok(html.includes(text),text);
  assert.ok(!html.includes('<img'));assert.ok(!html.includes('NaN'));
});
test('absent ranking has no selectable fallback',()=>{
  const c=make();assert.match(c.bugeseraRankingHtml(),/unavailable/);
  assert.ok(!c.bugeseraRankingHtml({status:'unavailable',reason:'Changed'}).includes('data-review-sector'));
  assert.equal(c.operatorPilotHtml(null),'');assert.equal(c.assessmentHtml(null),'');
});
test('sector review prepares real hierarchy but never replaces project inputs',async()=>{
  const nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',focus(){}});return nodes.get(id);};
  const state={busy:false,site:{households:25},assumptions:{tariff:100}};
  const before=JSON.stringify(state),discovery={busy:false,active:false,country:'RW',areas:[{id:'b',name:'Bugesera District'}],locals:[]};
  let handler;
  const button={dataset:{reviewSector:'RW-Bugesera-juru'},addEventListener:(type,fn)=>handler=fn};
  const c=make({state,discovery,$:node,contextReady:()=>true,openDiscovery:async()=>{discovery.active=true;},
    chooseDiscoveryArea:async()=>{discovery.locals=[{id:'j',name:'Juru'}];},loadDiscoveryPlaces:async()=>{},error:assert.fail});
  c.bindRankingButtons({querySelectorAll:()=>[button]},packet());await handler();
  assert.equal(node('#discover-area').value,'b');assert.equal(node('#discover-local').value,'j');
  assert.equal(node('#named-area').value,'Bugesera');assert.equal(node('#named-cell').value,'');
  assert.equal(JSON.stringify(state),before);assert.match(node('#finder-status').textContent,/existing project is unchanged/);
});
test('dirty and busy project states block ranking navigation',async()=>{
  for(const [busy,ready] of [[true,true],[false,false]]){
    let handler,opened=false;
    const c=make({state:{busy},discovery:{busy:false},contextReady:()=>ready,openDiscovery:async()=>{opened=true;}});
    c.bindRankingButtons({querySelectorAll:()=>[{dataset:{reviewSector:'RW-Bugesera-juru'},addEventListener:(_,fn)=>handler=fn}]},packet());
    await handler();assert.equal(opened,false);
  }
});
