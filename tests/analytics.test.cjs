/* Pure display logic and event regression checks. Browser QA is separate. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const {analyticsSelection,analyticsMonthlyLabel}=require('../static/analytics.js');
const read=file=>fs.readFileSync(path.join(__dirname,'..',file),'utf8');
const example=JSON.parse(read('reports/examples/rw-demo-02.json'));
const script=read('static/analytics.js');
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} vs ${b}`);

for(const scenario of ['low','expected','high'])for(const year of [1,2,3]) {
  test(`${scenario} Y${year}: all four energy periods conserve the Python annual total`,()=>{
    const before=JSON.stringify(example);
    const a=example.feasibility.scenarios.find(c=>c.key===scenario).years[year-1];
    for(const [period,divisor]of [['day',365],['week',365/7],['month',12],['year',1]]){
      const s=analyticsSelection(example,{scenario,year,period});
      close(s.energy*divisor,a.demand_kwh);
      assert.equal(s.annual,a);
      assert.ok(s.low<=s.energy&&s.energy<=s.high);
      assert.equal(s.unit,'kWh/'+period);
    }
    assert.equal(JSON.stringify(example),before);
  });
}

test('unknown and prototype-like filter keys fall back to expected monthly Year 1',()=>{
  for(const bad of ['__proto__','constructor',null,undefined,'bogus']){
    const s=analyticsSelection(example,{scenario:bad,period:bad,year:bad,month:bad});
    assert.equal(s.scenario.key,'expected');assert.equal(s.period,'month');assert.equal(s.year,1);assert.equal(s.month,1);
  }
});

test('year/month alignment keeps drill-down inside the chosen year',()=>{
  assert.equal(analyticsSelection(example,{year:2,month:2}).month,13);
  assert.equal(analyticsSelection(example,{year:3,month:36}).selectedMonth.month,36);
  for(const month of [0,-1,37,1.5,Infinity,NaN])assert.equal(analyticsSelection(example,{year:3,month}).month,25);
});

test('zero demand and missing debt stay zero and N/A, not fabricated ratios',()=>{
  const r=structuredClone(example);
  for(const c of r.feasibility.scenarios){c.years[0].demand_kwh=0;c.years[0].dscr=null;}
  const s=analyticsSelection(r);assert.equal(s.energy,0);assert.equal(s.low,0);assert.equal(s.high,0);assert.equal(s.annual.dscr,null);
});

test('labels preserve calendar/service age rather than calling every case newly connected',()=>{
  assert.equal(analyticsMonthlyLabel({calendar_month:'2027-01',service_month:18},0),'2027-01');
  assert.equal(analyticsMonthlyLabel({service_month:18,month:1},0),'M18');
  assert.equal(analyticsMonthlyLabel({month:3},2),'M3');
});

function harness(role='developer'){
  const nodes=new Map();let focused=null;
  const node=selector=>{if(!nodes.has(selector))nodes.set(selector,{innerHTML:'',value:'',dataset:{},events:{},addEventListener(event,cb){this.events[event]=cb;},focus(){focused=selector;},querySelector:node,querySelectorAll(){return [];}});return nodes.get(selector);};
  const state={role,result:structuredClone(example),dirty:true,site:{households:99},assumptions:{tariff:123},view:'overview'};
  const context=vm.createContext({state,$:node,number:(n,d=0)=>n==null?'—':Number(n).toFixed(d),compact:n=>String(Math.round(n)),
    esc:s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
    icon:()=>'<svg></svg>',colors:['#66ddc3'],gridLabels:{unknown:'Needs verification'},
    demandChartHtml:()=>'<div>Daily demand</div>',publicProfileSummaryHtml:()=>'',alertHtml:()=>'',
    lenderExplanationHtml:()=>'',affordabilityHtml:()=>''});
  vm.runInContext(script,context);
  return {context,state,node,focused:()=>focused,filters:()=>vm.runInContext('analyticsFilters',context)};
}

for(const role of ['developer','investor'])test(role+' overview renders complete data without missing values',()=>{
  const h=harness(role);h.context.renderAnalyticsOverview();const html=h.node('#view-overview').innerHTML;
  for(const label of ['Demand scenario','Low / expected / high range','Monthly','36 months','MONTH IN FOCUS','Debt coverage','Explore feasibility','NOT LINKED TO FILTERS','Scenarios, not confidence bounds'])assert.ok(html.includes(label),label);
  assert.equal((html.match(/data-analytics-month=/g)||[]).length,36);
  assert.equal((html.match(/class="curve-target" role="button" tabindex="0"/g)||[]).length,1);
  assert.ok(!/NaN|undefined|\$\{/.test(html));
  assert.ok(html.includes(role==='investor'?'Collected revenue':'Typical peak'));
});

test('month click/keyboard selection preserves dirty forms and applied result identity',()=>{
  const h=harness(),{result,site,assumptions}=h.state;
  h.context.selectAnalyticsMonth(17,true);
  assert.equal(h.filters().year,2);assert.equal(h.filters().month,17);
  assert.equal(h.focused(),'[data-analytics-month="17"]');
  assert.equal(h.state.result,result);assert.equal(h.state.site,site);assert.equal(h.state.assumptions,assumptions);assert.equal(h.state.dirty,true);
  const html=h.node('#analytics-explorer').innerHTML;
  h.context.selectAnalyticsMonth(37);assert.equal(h.node('#analytics-explorer').innerHTML,html);
});

test('year and slider handlers align the linked KPIs; reset changes only display',()=>{
  const h=harness();h.context.bindAnalytics();
  h.node('#analytics-year').events.change({target:{value:'3'}});
  assert.equal(h.filters().month,25);assert.equal(h.filters().year,3);
  h.node('#analytics-month').events.change({target:{value:'12'}});
  assert.equal(h.filters().year,1);assert.equal(h.filters().month,12);
  h.node('#analytics-reset').events.click();
  assert.equal(h.filters().month,1);assert.equal(h.filters().scenario,'expected');assert.equal(h.state.dirty,true);
});

test('negative cash is explicit and grid-connected sites keep their status',()=>{
  const h=harness();h.state.result.feasibility.scenarios[1].months[0].cash_after_debt=-100;
  assert.match(h.context.analyticsExplorerContents(h.state.result),/Cash gap: review costs/);
  h.state.result.context.grid={status:'connected'};
  h.context.renderAnalyticsOverview();
  assert.match(h.node('#view-overview').innerHTML,/Not an unserved-site candidate/);
  h.state.result.horizon={first_service_month:19,last_service_month:54};
  assert.match(h.context.analyticsExplorerContents(h.state.result),/service M19–M54/);
});

test('site and calendar strings are escaped',()=>{
  const h=harness();h.state.result.site.name='<img src=x onerror=alert(1)>';
  for(const c of h.state.result.feasibility.scenarios)c.months[0].calendar_month='<script>x</script>';
  h.context.renderAnalyticsOverview();const html=h.node('#view-overview').innerHTML;
  assert.ok(!html.includes('<script>'));assert.ok(!html.includes('<img src=x'));
  assert.ok(html.includes('&lt;script&gt;'));assert.ok(html.includes('&lt;img'));
});

test('template loads theme last and explorer before app; no Microsoft integration is claimed',()=>{
  const html=read('templates/index.html');
  assert.ok(html.indexOf('/static/dashboard.css')>html.indexOf('/static/detailed-inputs.css'));
  assert.ok(html.indexOf('/static/analytics.js')<html.indexOf('/static/app.js'));
  assert.ok(!html.includes('app.powerbi.com'));assert.ok(!script.includes('fetch('));
});
