/* UI logic tests with invented data and DOM doubles, not visual/browser tests. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const read=f=>fs.readFileSync(path.join(__dirname,'..',f),'utf8');
function harness(){
  const nodes=new Map(), requests=[], downloads=[];
  const node=s=>{if(!nodes.has(s))nodes.set(s,{innerHTML:'',textContent:'',events:{},addEventListener(k,v){this.events[k]=v;}});return nodes.get(s);};
  const state={result:{context:{currency:'RWF'},financial_evidence:{status:'Site inputs need evidence',source_attached:0,input_count:1,stale_project:false,notice:'Unverified',
    rows:[{field:'planning.project_capex',value:null,unit:'RWF',status:'missing',evidence:null}],benchmarks:JSON.parse(read('data/financial_benchmarks.json'))},
    productive_sensitivity:{notice:'Not probabilities',rows:[{option:'One mill',case:'No uptake',extra_demand_kwh_month:0,grid_contribution_amount_month:-10}]}},financialEvidence:null};
  const ctx=vm.createContext({state,$:node,esc:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;'),
    number:n=>String(n),moneyUnit:()=> 'RWF',contextReady:()=>true,setBusy:v=>state.busy=v,payload:()=>({site:{name:'fixture'}}),
    downloadJson:(...a)=>downloads.push(a),render(){},calculate:async()=>{},error(){},
    document:{createElement:()=>({click(){}})},URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},setTimeout(){},
    api:async(url,body)=>{requests.push({url,body});return {json:async()=>{throw new Error('Invented rejected fixture');},blob:async()=>({})};}});
  vm.runInContext(read('static/financial-evidence.js'),ctx);vm.runInContext(read('static/maintenance.js'),ctx);
  return {ctx,state,node,requests,downloads};
}
test('financial panel clearly separates assumed, sourced and proven',()=>{const h=harness();const html=h.ctx.financialEvidenceHtml();for(const s of ['Can we trust the budget?','Not supplied','Regional benchmarks','proven savings','Sources attached ≠ independently verified','1,948'.replace(',','')])assert.ok(html.includes(s),s);assert.ok(!html.includes('undefined'));});
test('untrusted evidence is escaped',()=>{const h=harness();h.state.result.financial_evidence.rows[0].evidence={source_reference:'<script>x</script>',observed_on:'2026-01-01'};assert.ok(h.ctx.financialEvidenceHtml().includes('&lt;script&gt;'));});
test('stale project evidence gets a visible detached warning',()=>{const h=harness();h.state.result.financial_evidence.stale_project=true;assert.match(h.ctx.financialEvidenceHtml(),/Previous evidence was detached/);});
test('legacy examples without evidence remain renderable',()=>{const h=harness();delete h.state.result.financial_evidence;assert.equal(h.ctx.financialEvidenceHtml(),'');});
test('productive use downside keeps negative operating contribution',()=>{const h=harness();const s=h.ctx.productiveStressHtml();assert.ok(s.includes('No uptake')&&s.includes('-10'));});
test('comparison field units use selected currency',()=>{const h=harness();h.state.result.context.currency='KES';assert.match(h.ctx.financialEvidenceHtml(),/KES per 1 USD/);});
test('blank comparison cannot silently become zero',()=>{const h=harness();assert.throws(()=>h.ctx.benchmarkValues({elements:{connections:{value:''}}}),/Complete/);});
test('comparison passes explicit FX/source/acknowledgement',()=>{const h=harness();const elements={connections:{value:'10'},fx:{value:'1300'},date:{value:'2026-01-01'},reference:{value:'test source'},confirmed:{checked:true}};const p=h.ctx.benchmarkValues({elements});assert.equal(p.local_currency_per_usd,1300);assert.equal(p.connections,10);assert.equal(p.scope_confirmed,true);});
test('evidence upload failure keeps prior packet and shows error',async()=>{const h=harness();h.state.financialEvidence={retained:true};h.ctx.bindFinancialEvidence();await h.node('#financial-evidence-form').events.submit({preventDefault(){},target:{elements:{evidence:{files:[{size:1,text:async()=>'{bad'}]}}}});assert.equal(h.state.financialEvidence.retained,true);assert.ok(h.node('#financial-evidence-error').textContent);assert.equal(h.state.busy,false);});
test('oversized evidence is rejected before request',async()=>{const h=harness();h.ctx.bindFinancialEvidence();await h.node('#financial-evidence-form').events.submit({preventDefault(){},target:{elements:{evidence:{files:[{size:25000}]}}}});assert.equal(h.requests.length,0);assert.match(h.node('#financial-evidence-error').textContent,/24 KB/);});
test('dirty project prevents benchmark submission',async()=>{const h=harness();h.ctx.contextReady=()=>false;h.ctx.bindFinancialEvidence();await h.node('#benchmark-form').events.submit({preventDefault(){}});assert.equal(h.requests.length,0);});
test('maintenance explains manual scope and no deployment',()=>{const h=harness();const s=h.ctx.maintenanceHtml();for(const t of ['No automatic deployment','manual workflow','not an active scheduled job','not a new 20-input ML model','private local registry'])assert.ok(s.includes(t),t);});
test('new update inputs clear previous diagnostics',()=>{const h=harness();h.ctx.bindMaintenance();h.node('#update-results').innerHTML='old';h.node('#update-form').events.input();assert.equal(h.node('#update-results').innerHTML,'');});
test('update rejects missing files and restores form after failure',async()=>{const h=harness();h.node('#update-form').elements={sites:{files:[]},csv:{files:[]},spec:{files:[]}};h.ctx.bindMaintenance();await h.node('#update-form').events.submit({preventDefault(){}});assert.match(h.node('#update-error').textContent,/Choose all update files/);assert.equal(h.state.busy,false);assert.equal(h.requests.length,0);});
test('candidate diagnostics do not claim review approval from passed checks',()=>{const h=harness();const s=h.ctx.updateResultsHtml({release:{version_id:'<img>'},performance_gates_passed:true,metrics:{growth_adjusted:{wape_pct:1},site_path_coverage_pct:100,n_sites:2,site_coverage_ci95_pct:[15,100]},method:'fixture',gates:[]});assert.ok(s.includes('&lt;img&gt;'));assert.match(s,/not approved, and not deployed/);assert.match(s,/Numerical checks passed/);});
