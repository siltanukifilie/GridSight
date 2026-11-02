/* Logic-only checks; these do not claim browser or visual verification. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '../static/workspaces.js'), 'utf8');
const {WORKSPACES, FINANCIAL_FIELDS, normalizedRole, mergeFinancialInputs, canSwitchWorkspace} = require('../static/workspaces.js');

test('two named audiences with distinct navigation and matching sections', () => {
  assert.deepEqual(Object.keys(WORKSPACES), ['developer', 'investor']);
  assert.equal(WORKSPACES.investor.label, 'Investor / lender');
  assert.notEqual(WORKSPACES.developer.nav.community, WORKSPACES.investor.nav.community);
  for (const role of Object.values(WORKSPACES)) assert.deepEqual(Object.keys(role.nav), Object.keys(role.titles));
});

test('unknown stored roles fall back safely', () => {
  for (const role of [null, '', 'admin', '__proto__', 'constructor']) assert.equal(normalizedRole(role), 'developer');
  assert.equal(normalizedRole('investor'), 'investor');
});

test('financial edits retain engineering inputs and do not mutate the original', () => {
  const current = {household_growth:.12, business_growth:.2, additional_mills:3, capacity_kwh:12000, firm_power_kw:70, tariff:500};
  const values = {tariff:410, collection_rate:.85, variable_cost:55, fixed_cost:400000, debt_payment:0, capacity_kwh:999, household_growth:.9};
  const merged = mergeFinancialInputs(current, values);
  for (const key of FINANCIAL_FIELDS) assert.equal(merged[key], values[key]);
  for (const key of ['household_growth','business_growth','additional_mills','capacity_kwh','firm_power_kw']) assert.equal(merged[key], current[key]);
  assert.equal(current.tariff, 500);
});

for (const [name, changes] of [['while calculating', {busy:true}], ['with unapplied inputs', {dirty:true}], ['before initial analysis', {result:null}]]) {
  test('role switch is blocked ' + name, () => {
    assert.equal(canSwitchWorkspace({busy:false, dirty:false, result:{}, ...changes}), false);
  });
}

function harness(changes={}) {
  const state = {role:'developer', view:'community', busy:false, dirty:false, site:{name:'Shared scenario'}, assumptions:{tariff:500}, result:{forecast:{central:1234}}, ...changes};
  const select = {value:'investor'}, messages = [], saved = {};
  let renderCount = 0;
  const context = vm.createContext({state, $:()=>select, toast:message=>messages.push(message), render:()=>renderCount++, localStorage:{setItem:(key,value)=>saved[key]=value}});
  vm.runInContext(script, context);
  return {state, select, messages, saved, context, renderCount:()=>renderCount};
}

test('real switch handler preserves scenario/result identity and remembers the role', () => {
  const h = harness();
  const {site, assumptions, result} = h.state;
  h.context.switchWorkspace('investor');
  assert.equal(h.state.role, 'investor');
  assert.equal(h.state.view, 'overview');
  assert.equal(h.state.site, site);
  assert.equal(h.state.assumptions, assumptions);
  assert.equal(h.state.result, result);
  assert.equal(h.saved['gridsight-role-v1'], 'investor');
  assert.equal(h.renderCount(), 1);
  h.context.switchWorkspace('developer');
  assert.equal(h.state.result, result);
});

test('real switch handler preserves dirty form view and resets role selector', () => {
  const h = harness({dirty:true});
  h.context.switchWorkspace('investor');
  assert.equal(h.state.role, 'developer');
  assert.equal(h.state.view, 'community');
  assert.equal(h.select.value, 'developer');
  assert.equal(h.renderCount(), 0);
  assert.match(h.messages[0], /Project values have been kept/);
});

test('role switch still works when browser storage is unavailable', () => {
  const h = harness();
  h.context.localStorage.setItem = () => { throw new Error('unavailable'); };
  h.context.switchWorkspace('investor');
  assert.equal(h.state.role, 'investor');
  assert.equal(h.renderCount(), 1);
});

for (const monthly of [3650, 0]) {
  test('central-estimate panel presents all four periods for monthly demand ' + monthly, () => {
    const h = harness();
    h.context.esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;');
    h.context.number = (value, digits=0) => value.toLocaleString('en-US', {minimumFractionDigits:digits, maximumFractionDigits:digits});
    const daily = monthly * 12 / 365;
    const r = {forecast:{lower:monthly * .8, upper:monthly * 1.2}, demand_periods:{basis:'365 days; 12 months; 7-day weeks. Not date-specific.', estimates:
      [['day',daily], ['week',daily*7], ['month',monthly], ['year',monthly*12]].map(([period, central]) => ({period, central, label:'Per '+period, unit:'kWh/'+period}))}};
    const html = h.context.demandPeriodsHtml(r);
    let lastIndex = -1;
    for (const period of ['day','week','month','year']) {
      const index = html.indexOf('Per '+period);
      assert.ok(index > lastIndex);
      lastIndex = index;
      assert.ok(html.includes('kWh/'+period));
    }
    assert.ok(html.includes(monthly ? '43,800.0' : '0.0'));
    assert.match(html, /Central demand estimate/);
    assert.match(html, /Year 1 averages/);
    assert.match(html, /reference model on synthetic monthly targets/);
    assert.match(html, /does not validate the new curve/);
    assert.match(html, /Not date-specific/);
  });
}

test('long explanations use closed, keyboard-accessible native disclosures', () => {
  const h = harness();
  h.context.esc = value => String(value).replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  const html = h.context.detailsHtml('How it works <test>', '<p>Synthetic evidence; not investment approval.</p>');
  assert.match(html, /^<details class="more-details">/);
  assert.ok(!html.includes(' open'));
  assert.match(html, /<summary>How it works &lt;test&gt;<\/summary>/);
  assert.match(html, /Synthetic evidence; not investment approval/);
});

test('workspace headings and workflow labels stay short', () => {
  for (const role of Object.values(WORKSPACES)) {
    for (const label of Object.values(role.nav)) assert.ok(label.split(/\s+/).length <= 2);
    for (const [title, subtitle] of Object.values(role.titles)) {
      assert.ok(title.split(/\s+/).length <= 7);
      assert.ok(subtitle.split(/\s+/).length <= 12);
    }
  }
  const h = harness();
  h.context.icon = () => '';
  for (const role of ['developer', 'investor']) {
    h.state.role = role;
    const html = h.context.workflowSteps();
    assert.equal((html.match(/data-go=/g) || []).length, 3);
    assert.ok(!html.includes('<small>'));
  }
});
