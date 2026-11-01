const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const c=vm.createContext({esc:s=>String(s).replaceAll('<','&lt;').replaceAll('>','&gt;'),
  number:(x,d=0)=>x==null?'—':Number(x).toFixed(d)});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/feasibility.js'),'utf8'),c);

test('older projects render without the new scenario packet',()=>{
  assert.equal(c.affordabilityHtml({}),'');
  assert.equal(c.productiveGrowthHtml({}),'');
  assert.match(c.measuredRangesHtml({}),/Study unavailable/);
});

test('income and budget remain unassessed and currency is escaped',()=>{
  const r={context:{currency:'<RWF>'},planning_scenarios:{affordability:{income_threshold:.05,
    notice:'Assumption',rows:[{case:'Entered tariff',tariff_per_kwh:500,bill_monthly:7500,income_share:null,
      budget_gap_monthly:null,income_screen_exceeded:null}]}}};
  const html=c.affordabilityHtml(r);
  assert.match(html,/Not assessed/);assert.match(html,/&lt;RWF&gt;/);
  assert.ok(!html.includes('NaN')&&!html.includes('undefined'));
  assert.match(html,/7500/);
});

test('empirical panel distinguishes tested coverage and reference radii',()=>{
  const html=c.measuredRangesHtml({transfer_uncertainty:{status:'empirical_reference',horizons:[{
    horizon_months:1,sites:4,rows:94,radius_kwh_per_origin_meter:6.34,nested_equal_site_coverage:.85,
    equal_site_mae_kwh:513,equal_site_persistence_mae_kwh:319}],method:'nested',temporal_scope:'retrospective',notice:'operational only',source:'Renewvia',license:'CC-BY-SA-4.0'}});
  for(const text of ['85.0%','6.34','Download study','last-month baseline','subsequent experiments'])assert.ok(html.includes(text),text);
});
