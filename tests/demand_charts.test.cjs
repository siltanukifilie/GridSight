/* Logic and markup checks only; these do not substitute for browser QA. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {DEMAND_VIEWS, demandChartData} = require('../static/demand-charts.js');
const script = fs.readFileSync(path.join(__dirname, '../static/demand-charts.js'), 'utf8');

function fixture(monthly=3650) {
  const daily = monthly * 12 / 365;
  return {
    forecast:{central:monthly, lower:monthly*.8, upper:monthly*1.2},
    demand_periods:{estimates:[['day',daily,1],['week',daily*7,7],['month',monthly,365/12],['year',monthly*12,365]].map(([period,central,days_per_period]) => ({period,central,days_per_period}))},
    profile:{hours:Array.from({length:24}, (_,i)=>i), kw:Array.from({length:24}, (_,i)=>daily*(i+1)/300), load_factor:.52}
  };
}
function close(actual, expected) {
  assert.ok(Math.abs(actual-expected) <= Math.max(1,Math.abs(expected))*1e-10, `${actual} differs from ${expected}`);
}

test('four periods are available and unknown periods safely use daily', () => {
  assert.deepEqual(Object.keys(DEMAND_VIEWS), ['day','week','month','year']);
  for (const value of [undefined, null, 'unknown', '__proto__', 'constructor']) assert.equal(demandChartData(fixture(), value).period, 'day');
});

test('daily preserves the hourly power profile and scales the monthly band', () => {
  const result = fixture(), view = demandChartData(result, 'day');
  assert.equal(view.unit, 'kW');
  assert.equal(view.labels[0], '00:00');
  assert.equal(view.labels.at(-1), '23:00');
  assert.deepEqual(view.series.central, result.profile.kw);
  assert.notEqual(view.series.central, result.profile.kw);
  view.series.central.forEach((v,i) => {close(view.series.lower[i],v*.8);close(view.series.upper[i],v*1.2);});
  close(view.total, 120);
});

test('weekly displays seven average daily energy values', () => {
  const view = demandChartData(fixture(), 'week');
  assert.equal(view.unit, 'kWh/day');
  assert.equal(view.labels.length, 7);
  assert.equal(view.labels.at(-1), 'Day 7');
  view.series.central.forEach(v => close(v,120));
  close(view.total, 840);
  assert.match(view.note, /No seasonal pattern modeled/);
});

test('monthly uses an explicit partial final day without inventing a demand drop', () => {
  const view = demandChartData(fixture(), 'month');
  assert.equal(view.unit, 'kWh/day');
  assert.equal(view.labels.length, 31);
  assert.equal(view.labels.at(-1), 'Day 31*');
  assert.equal(view.durations.slice(0,30).every(v=>v===1), true);
  close(view.durations.at(-1), 5/12);
  view.series.central.forEach(v => close(v,120));
  close(view.total, 3650);
  assert.match(view.note, /Final day: 0.42 day/);
});

test('yearly displays twelve first-year monthly averages, not growth or seasonality', () => {
  const view = demandChartData(fixture(), 'year');
  assert.equal(view.unit, 'kWh/month');
  assert.deepEqual(view.labels, Array.from({length:12}, (_,i)=>`M${i+1}`));
  view.series.central.forEach(v => close(v,3650));
  view.series.lower.forEach(v => close(v,2920));
  view.series.upper.forEach(v => close(v,4380));
  close(view.total, 43800);
  assert.match(view.subtitle, /Year 1/);
});

for (const monthly of [0, .125, 3650]) {
  test(`all period totals conserve energy and match estimate cards: monthly ${monthly}`, () => {
    const result = fixture(monthly), before = JSON.stringify(result);
    for (const period of Object.keys(DEMAND_VIEWS)) {
      const view = demandChartData(result, period);
      close(view.series.central.reduce((sum,v,i)=>sum+v*view.durations[i],0), view.total);
      close(view.total, result.demand_periods.estimates.find(p=>p.period===period).central);
      assert.equal(view.series.central.length, view.labels.length);
      view.series.central.forEach((v,i) => {
        assert.ok(Number.isFinite(v));
        assert.ok(Number.isFinite(view.series.lower[i]));
        assert.ok(Number.isFinite(view.series.upper[i]));
        assert.ok(view.series.lower[i] <= v && v <= view.series.upper[i]);
      });
    }
    assert.equal(JSON.stringify(result), before);
  });
}

for (const id of ['01','02','03']) {
  test(`all chart horizons agree with the stored model analysis for RW-DEMO-${id}`, () => {
    const result = JSON.parse(fs.readFileSync(path.join(__dirname, `fixtures/rw-demo-${id}.json`), 'utf8'));
    for (const period of Object.keys(DEMAND_VIEWS)) {
      const view = demandChartData(result, period);
      close(view.series.central.reduce((sum,v,i)=>sum+v*view.durations[i],0), view.total);
    }
  });
}

function harness() {
  const state = {demandPeriod:'day', result:fixture(), dirty:true, site:{households:99}, assumptions:{tariff:410}};
  let html='', buttons=[], focused=null;
  const container = {
    get innerHTML(){return html;},
    set innerHTML(value){
      html=value;
      buttons=Object.keys(DEMAND_VIEWS).map(period=>({dataset:{demandPeriod:period}, handlers:{}, addEventListener(event,handler){this.handlers[event]=handler;}, focus(){focused=period;}}));
    },
    querySelectorAll(){return buttons;},
    querySelector(selector){return buttons.find(b=>selector.includes(`"${b.dataset.demandPeriod}"`));}
  };
  const chartCalls=[];
  const context = vm.createContext({state, $:selector=>selector==='#demand-chart-card'?container:null,
    number:(n,digits=0)=>n.toFixed(digits), detailsHtml:(label,content)=>`<details><summary>${label}</summary>${content}</details>`,
    chart:(series,labels,options)=>{chartCalls.push({series,labels,options});return '<svg></svg>';}});
  vm.runInContext(script, context);
  container.innerHTML=context.demandChartContents(state.result, 'day');
  context.bindDemandChart();
  return {state,context,container,chartCalls,button:period=>buttons.find(b=>b.dataset.demandPeriod===period),focused:()=>focused};
}

test('all views render four accessible tabs and one corresponding panel', () => {
  const h=harness();
  for (const period of Object.keys(DEMAND_VIEWS)) {
    h.context.selectDemandPeriod(period);
    const html=h.container.innerHTML;
    assert.equal((html.match(/role="tab"/g)||[]).length, 4);
    assert.equal((html.match(/aria-selected="true"/g)||[]).length, 1);
    assert.equal((html.match(/role="tabpanel"/g)||[]).length, 1);
    assert.match(html, new RegExp(`aria-labelledby="demand-tab-${period}"`));
    assert.ok(html.includes(demandChartData(h.state.result,period).total.toFixed(1)+' kWh'));
    assert.equal(h.chartCalls.at(-1).options.unit, period==='day'?'kW':period==='year'?'kWh/month':'kWh/day');
    assert.equal(html.includes('Load factor'), period==='day');
  }
  assert.equal(h.chartCalls.at(-1).options.tickStep, 1);
});

test('click changes only the chart and preserves result, scenario and unfinished input state', () => {
  const h=harness(), {result,site,assumptions}=h.state;
  h.button('week').handlers.click();
  assert.equal(h.state.demandPeriod,'week');
  assert.equal(h.focused(),'week');
  assert.equal(h.state.dirty,true);
  assert.equal(h.state.result,result);
  assert.equal(h.state.site,site);
  assert.equal(h.state.assumptions,assumptions);
  const html=h.container.innerHTML;
  h.context.selectDemandPeriod('invalid');
  assert.equal(h.container.innerHTML,html);
});

test('arrow, Home and End keys navigate with focus; unrelated keys are ignored', () => {
  const h=harness();
  for (const [from,key,to] of [['day','ArrowLeft','year'],['year','ArrowRight','day'],['day','End','year'],['year','Home','day'],['day','ArrowRight','week']]) {
    let prevented=false;
    h.button(from).handlers.keydown({key,preventDefault(){prevented=true;}});
    assert.equal(prevented,true);
    assert.equal(h.state.demandPeriod,to);
    assert.equal(h.focused(),to);
  }
  h.button('week').handlers.keydown({key:'Tab',preventDefault(){throw new Error('Tab must remain native');}});
  assert.equal(h.state.demandPeriod,'week');
});
