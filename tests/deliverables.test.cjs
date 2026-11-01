/* UI/package plumbing checks. No measured-site evidence is fabricated. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=file=>fs.readFileSync(path.join(__dirname,'..',file),'utf8');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fixture=()=>({
  deliverables:['demand','growth','validation','explanation','sharing'].map((id,i)=>({
    id,name:id,status:i===2?'Pending genuine operator data':'Available',state:i===2?'blocked':'available',
    detail:'Scope <script>bad()</script>',next_action:'Review <img src=x>'
  })),
  lender_explanation:['Counts × power × hours','Assumed growth','Not observed'],
  sharing_proposal:{title:'Safe meter-data sharing proposal',status:'Proposal only',steps:[],
    minimum_data:'Site totals',future_curve_study:'Independent sites',references:[]}
});
function ui(){
  const c=vm.createContext({esc,detailsHtml:(title,body)=>'<details><summary>'+title+'</summary>'+body+'</details>'});
  vm.runInContext(read('static/connection.js'),c);return c;
}
test('five actions and deliverables download are visible; evidence stays pending',()=>{
  const html=ui().deliverablesHtml(fixture());
  assert.equal((html.match(/class="deliverable-number"/g)||[]).length,5);
  for(const text of ['Download deliverables','Pending genuine operator data','#meter-validation','#lender-deliverable',
    '#sharing-deliverable','data-go="overview"','data-go="feasibility"','not calibrated','blank validation templates'])
    assert.ok(html.includes(text),text);
  assert.ok(!html.includes('<script>bad'));assert.ok(!html.includes('<img src=x>'));
  assert.ok(html.includes('&lt;script&gt;'));
});
test('empty and older result structures are safe',()=>{
  const c=ui();assert.equal(c.deliverablesHtml({}),'');
  const r=fixture();for(const item of r.deliverables){delete item.state;delete item.next_action;}
  assert.ok(c.deliverablesHtml(r).includes('Five deliverables'));
});
test('only the dedicated explanation has a jump target',()=>{
  const c=ui(),r=fixture();
  assert.ok(!c.lenderExplanationHtml(r).includes('id="lender-deliverable"'));
  assert.ok(c.lenderExplanationHtml(r,true).includes('id="lender-deliverable"'));
});
function exporter({dirty=false,busy=false}={}){
  const requests=[],downloads=[],messages=[];
  const result={site:{id:'DEMO'},assumptions:{tariff:1},detailed:{enabled:true},planning:{},connection:{},context:{},financial_evidence:null};
  const c=vm.createContext({state:{role:'developer',result,dirty,busy},toast:s=>messages.push(s),error:s=>messages.push(s),
    api:async(url,body)=>{requests.push({url,body});return {blob:async()=>new Blob(['fixture'])};},
    URL:{createObjectURL:()=> 'blob:fixture',revokeObjectURL(){}},setTimeout:()=>1,
    document:{createElement:()=>({click(){downloads.push(this.download);}})}});
  vm.runInContext(read('static/app.js').split('\n').find(l=>l.startsWith('async function downloadExport(')),c);
  return {c,requests,downloads,messages,result};
}
test('pack exports only applied project inputs and uses the new endpoint',async()=>{
  const h=exporter();await h.c.downloadExport(true);
  assert.equal(h.requests[0].url,'/api/deliverables-pack');
  assert.equal(h.requests[0].body.site,h.result.site);
  assert.ok(!('monthlyComparison' in h.requests[0].body));
  assert.equal(h.downloads[0],'gridsight-deliverables.zip');
  assert.match(h.messages[0],/START_HERE.html/);
});
test('normal button click remains the existing analysis export',async()=>{
  const h=exporter();await h.c.downloadExport({type:'click'});
  assert.equal(h.requests[0].url,'/api/export');
  assert.equal(h.downloads[0],'gridsight-planning-analysis.zip');
});
test('dirty or busy states block both packages',async()=>{
  for(const state of [{dirty:true},{busy:true}]){
    const h=exporter(state);await h.c.downloadExport(true);await h.c.downloadExport();
    assert.equal(h.requests.length,0);assert.equal(h.downloads.length,0);
  }
});
test('evidence hub precedes specialist tools and jump target exists',()=>{
  const app=read('static/app.js').split('\n').find(l=>l.startsWith('function renderEvidence'));
  assert.ok(app.indexOf('${deliverablesHtml(r)}')<app.indexOf('${typeof monthlyValidationHtml'));
  assert.match(app,/deliverables-download.*downloadExport\(true\)/);
  assert.match(read('static/monthly-validation.js'),/id="meter-validation" tabindex="-1"/);
});
