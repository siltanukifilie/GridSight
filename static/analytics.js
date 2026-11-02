/* Presentation-only exploration of the Python feasibility output.
   Filters never change project assumptions, calibration, saved data or exports. */
const analyticsFilters = {scenario:'expected', year:1, period:'month', month:1};
const ANALYTICS_PERIODS = {day:['Daily',365], week:['Weekly',365/7], month:['Monthly',12], year:['Yearly',1]};

function analyticsSelection(result, filters={}) {
  const cases=result.feasibility.scenarios;
  const scenario=cases.find(c=>c.key===filters.scenario)||cases.find(c=>c.key==='expected');
  const year=[1,2,3].includes(Number(filters.year))?Number(filters.year):1;
  const period=Object.hasOwn(ANALYTICS_PERIODS,filters.period)?filters.period:'month';
  const annual=scenario.years.find(y=>y.year===year);
  const candidate=Number(filters.month);
  const month=Number.isInteger(candidate)&&candidate>=(year-1)*12+1&&candidate<=year*12?candidate:(year-1)*12+1;
  const selectedMonth=scenario.months[month-1];
  return {scenario,year,period,annual,month,selectedMonth,
    energy:annual.demand_kwh/ANALYTICS_PERIODS[period][1],
    unit:'kWh/'+period,
    low:cases.find(c=>c.key==='low').years.find(y=>y.year===year).demand_kwh/ANALYTICS_PERIODS[period][1],
    high:cases.find(c=>c.key==='high').years.find(y=>y.year===year).demand_kwh/ANALYTICS_PERIODS[period][1]};
}

function analyticsMonthlyLabel(month, index) {
  return month.calendar_month||'M'+(month.service_month||month.month||index+1);
}

function analyticsCurveHtml(r, selected) {
  const cases=r.feasibility.scenarios, expected=cases.find(c=>c.key==='expected').months;
  const low=cases.find(c=>c.key==='low').months, high=cases.find(c=>c.key==='high').months;
  const points=selected.scenario.months;
  const w=790,h=268,left=59,right=15,top=24,bottom=34;
  const max=Math.max(1,...high.map(m=>m.demand_kwh))*1.12;
  const x=i=>left+i*(w-left-right)/Math.max(1,points.length-1);
  const y=v=>h-bottom-v*(h-top-bottom)/max;
  const path=months=>months.map((m,i)=>`${x(i)},${y(m.demand_kwh)}`).join(' ');
  const band=path(high)+' '+low.map((m,i)=>`${x(i)},${y(m.demand_kwh)}`).reverse().join(' ');
  const start=(selected.year-1)*12, end=selected.year*12-1;
  const line=(months,cls)=>`<polyline class="${cls}" points="${path(months)}" fill="none"/>`;
  return `<svg class="analytics-curve" viewBox="0 0 ${w} ${h}" role="group" aria-label="36-month demand scenarios. Select a month to inspect it.">
    <text class="axis-unit" x="${left}" y="12">kWh / month</text>
    <rect class="year-highlight" x="${x(start)-4}" y="${top}" width="${x(end)-x(start)+8}" height="${h-top-bottom}" rx="6"/>
    ${Array.from({length:5},(_,i)=>{const v=max*i/4;return `<line class="gridline" x1="${left}" x2="${w-right}" y1="${y(v)}" y2="${y(v)}"/><text x="${left-10}" y="${y(v)+4}" text-anchor="end">${number(v)}</text>`;}).join('')}
    <polygon class="range-fill" points="${band}"/>
    ${line(low,'curve-bound')}${line(high,'curve-bound')}${line(expected,'curve-reference')}${line(points,'curve-selected')}
    ${points.map((m,i)=>`<circle class="curve-point ${i===selected.month-1?'selected':''}" cx="${x(i)}" cy="${y(m.demand_kwh)}" r="${i===selected.month-1?6:3}"/>`).join('')}
    ${points.map((m,i)=>`<circle class="curve-target" role="button" tabindex="${i===selected.month-1?'0':'-1'}" data-analytics-month="${i+1}" aria-pressed="${i===selected.month-1}" aria-label="${esc(analyticsMonthlyLabel(m,i))}: ${number(m.demand_kwh,1)} kWh, ${esc(selected.scenario.label)}. Inspect month ${i+1}" cx="${x(i)}" cy="${y(m.demand_kwh)}" r="12"><title>${esc(analyticsMonthlyLabel(m,i))} · ${number(m.demand_kwh,1)} kWh · click for cash and supply</title></circle>`).join('')}
    ${[0,5,11,17,23,29,35].filter(i=>i<points.length).map(i=>`<text x="${x(i)}" y="${h-9}" text-anchor="middle">${esc(analyticsMonthlyLabel(points[i],i))}</text>`).join('')}
  </svg>`;
}

function analyticsKpi(title,value,unit,note,symbol,extra='') {
  return `<article class="kpi analytics-kpi ${extra}"><div class="kpi-label">${title}<span class="kpi-icon">${icon(symbol)}</span></div><div class="kpi-value">${value}<span>${unit}</span></div><p class="kpi-foot">${note}</p></article>`;
}

function analyticsMixHtml(r) {
  const rows=r.components.filter(c=>c.kwh>0).sort((a,b)=>b.kwh-a.kwh);
  return `<article class="card mix-card"><div class="card-head"><div><span class="section-kicker">DEMAND DRIVERS</span><h2>Demand by customer</h2></div><span class="tag">Expected · Year 1</span></div>
    <div class="mix-bars">${rows.map((c,i)=>`<div class="mix-row"><div><span><i style="background:${colors[i%colors.length]}"></i>${esc(c.label)}</span><strong>${number(c.share*100,1)}<small>%</small></strong></div><div class="mix-track"><span style="width:${Math.min(100,c.share*100)}%;background:${colors[i%colors.length]}"></span></div></div>`).join('')||'<p>No demand inputs yet.</p>'}</div>
    <p class="subtle-note">${r.detailed?.enabled?'Calculated contributions from your inputs.':'Baseline shares, not an exact model decomposition.'} Not measured consumption.</p><button class="inline-link" data-go="community">Review customers & equipment ↗</button></article>`;
}

function analyticsExplorerContents(r) {
  const s=analyticsSelection(r,analyticsFilters),a=s.annual,m=s.selectedMonth,currency=esc(r.context.currency);
  const periodButtons=Object.entries(ANALYTICS_PERIODS).map(([key,[label]])=>`<button type="button" data-analytics-period="${key}" aria-pressed="${key===s.period}">${label}</button>`).join('');
  const caseButtons=r.feasibility.scenarios.map(c=>`<button type="button" data-analytics-scenario="${c.key}" aria-pressed="${c.key===s.scenario.key}">${esc(c.label)}</button>`).join('');
  const first=s.scenario.years[0].demand_kwh,growth=first?(a.demand_kwh/first-1)*100:null;
  return `<div class="analytics-filters" aria-label="Dashboard display filters"><div class="filter-group"><span>Demand scenario</span><div class="segmented" role="group" aria-label="Demand scenario">${caseButtons}</div></div>
    <div class="filter-group"><label for="analytics-year">Forecast year</label><select id="analytics-year">${[1,2,3].map(y=>`<option value="${y}" ${s.year===y?'selected':''}>Year ${y}</option>`).join('')}</select></div>
    <div class="filter-group period-filter"><span>Energy view</span><div class="segmented" role="group" aria-label="Energy view">${periodButtons}</div></div><button type="button" class="text-button" id="analytics-reset">Reset view ↺</button></div>
    <div class="analytics-scope" role="status"><span><i class="live-dot"></i>${esc(s.scenario.label)} scenario · Year ${s.year}</span><span>View only · inputs unchanged</span></div>
    <div class="kpi-grid analytics-kpis">
      ${analyticsKpi('Demand · '+ANALYTICS_PERIODS[s.period][0].toLowerCase(),number(s.energy,1),s.unit,`Low ${number(s.low,1)} — High ${number(s.high,1)}`,'energy','demand-kpi')}
      ${state.role==='investor'?analyticsKpi('Collected revenue',compact(a.revenue/12),currency+'/mo','Monthly average · supply-limited','money'):analyticsKpi('Typical peak',number(a.peak_kw,1),'kW','Highest illustrative peak in this year','clock')}
      ${analyticsKpi('Cash after debt',compact(a.cash_after_debt/12),currency+'/mo',`${a.cash_shortfall_months} of 12 months with a cash gap`,'money',a.cash_after_debt<0?'risk-kpi':'')}
      ${analyticsKpi('Debt coverage',a.dscr==null?'N/A':number(a.dscr,2),a.dscr==null?'':'×',a.dscr==null?'No debt payment entered':'Operating surplus ÷ stated debt payment','report')}
    </div>
    <div class="analytics-primary-grid"><article class="card growth-explorer"><div class="card-head"><div><span class="section-kicker">DEMAND OUTLOOK</span><h2>3-year demand</h2><p>36 months${r.horizon?' · service M'+r.horizon.first_service_month+'–M'+r.horizon.last_service_month:''} · Year ${s.year} highlighted</p></div><span class="growth-chip">${s.year===1?'Year 1 baseline':growth==null?'No baseline':(growth>=0?'+':'')+number(growth,1)+'% vs Year 1'}</span></div>
      <div class="analytics-legend"><span><i class="legend-line"></i>${esc(s.scenario.label)}</span><span><i class="legend-band"></i>Low / expected / high range</span><small>Scenarios, not confidence bounds</small></div>
      <div class="curve-viewport" tabindex="0" aria-label="Demand chart. Scroll horizontally on small screens.">${analyticsCurveHtml(r,s)}</div>
      <div class="curve-controls"><label for="analytics-month">Inspect month <b>${esc(analyticsMonthlyLabel(m,s.month-1))}</b></label><input id="analytics-month" aria-label="Inspect forecast month" type="range" min="1" max="36" step="1" value="${s.month}"><span>Select a month</span></div>
      <details class="more-details"><summary>View monthly data & method</summary><div class="details-body"><p>Growth follows the entered connection, appliance and business assumptions. Standard energy months use 365/12 days, not billing-calendar totals. Low/high use the feasibility scenario factors; these are not calibrated probabilities. Daily/weekly cards are annual averages; cash cards always show monthly averages. Exports retain all scenarios.</p><div class="table-wrap"><table><caption>Year ${s.year} · ${esc(s.scenario.label)}</caption><thead><tr><th>Month</th><th>Demand · kWh</th><th>Cash after debt · ${currency}</th><th>Debt coverage</th></tr></thead><tbody>${s.scenario.months.filter(v=>v.year===s.year).map((v,i)=>`<tr><td>${esc(analyticsMonthlyLabel(v,(s.year-1)*12+i))}</td><td>${number(v.demand_kwh,1)}</td><td>${number(v.cash_after_debt)}</td><td>${v.dscr==null?'N/A':number(v.dscr,2)+'×'}</td></tr>`).join('')}</tbody></table></div></div></details>
    </article><article class="card month-detail" aria-label="Selected month detail"><span class="section-kicker">MONTH IN FOCUS</span><div class="month-focus-title"><h2>${esc(analyticsMonthlyLabel(m,s.month-1))}</h2><span class="tag">${esc(s.scenario.label)}</span></div><strong class="focus-energy">${number(m.demand_kwh,1)}<small>kWh / month</small></strong><p class="subtle-note">Forecast month ${s.month}</p>
      <div class="data-stat-row"><span>Revenue</span><b>${compact(m.revenue)} ${currency}</b></div><div class="data-stat-row"><span>Cash after debt</span><b class="${m.cash_after_debt<0?'negative':''}">${compact(m.cash_after_debt)} ${currency}</b></div><div class="data-stat-row"><span>Debt coverage</span><b>${m.dscr==null?'N/A':number(m.dscr,2)+'×'}</b></div><div class="data-stat-row"><span>Unserved demand</span><b>${number(m.unserved_kwh,1)} kWh</b></div><div class="data-stat-row"><span>Peak power gap</span><b>${number(m.peak_shortfall_kw,1)} kW</b></div>
      <div class="focus-note ${m.cash_after_debt<0||m.unserved_kwh>0||m.peak_shortfall_kw>0?'attention':''}">${m.cash_after_debt<0?'Cash gap: review costs and financing.':m.unserved_kwh>0||m.peak_shortfall_kw>0?'Supply gap: review capacity.':'No modeled cash or supply gap.'}<small>Planning screen, not investment approval.</small></div></article></div>
    <div class="analytics-checks"><div><span>Energy capacity used · Y${s.year}</span><b>${a.energy_utilization==null?'Not set':number(a.energy_utilization*100,1)+'%'}</b></div><div><span>Unused energy capacity · Y${s.year}</span><b>${number(a.unused_capacity_kwh)} kWh</b></div><div><span>Unserved demand · Y${s.year}</span><b>${number(a.unserved_kwh)} kWh</b></div><p>Capacity exposure ≠ proven wasted capital. Check local demand and design.</p></div>`;
}

function renderAnalyticsOverview() {
  const r=state.result,c=r.context;
  const gridNotice=c.grid?.status==='connected'?'Main-grid access reported. Not an unserved-site candidate.':c.grid?.status==='planned'?'Grid expansion reported. Review grid-arrival risk before committing.':'';
  $('#view-overview').innerHTML=`<div class="analytics-site"><div><span class="section-kicker">${esc(c.country)} · ${esc(c.currency)}</span><h2>${esc(r.site.name)}</h2><p>${esc(c.location?.administrative_path?.join(' / ')||r.site.district)}</p></div><div><span class="screening-badge">${esc(gridLabels[c.grid?.status]||gridLabels.unknown)}</span><button class="text-button" data-go="locations">Site details ↗</button></div></div>
    ${gridNotice?`<p class="demo-notice">${gridNotice}</p>`:''}
    <div id="analytics-explorer">${analyticsExplorerContents(r)}</div>
    <div class="analytics-secondary-grid"><div class="profile-section"><p class="section-kicker fixed-scope">Expected · Year 1 · independent of filters</p>${demandChartHtml(r)}</div>${analyticsMixHtml(r)}</div>
    <div class="analytics-actions"><div><h2>Feasibility</h2><p>Costs, supply and repayment.</p></div><button class="button primary" data-go="feasibility">Explore feasibility ${icon('arrow')}</button></div>
    ${alertHtml()}<details class="more-details overview-evidence"><summary>Forecast drivers & data notes</summary><div class="details-body"><p>${c.input_origin==='synthetic'?'Demo data: generated test values, not measured consumption. ':''}Estimates use entered assumptions. Verify grid access and costs.</p><button class="inline-link" data-go="evidence">Data & methods ↗</button>${publicProfileSummaryHtml()}${typeof lenderExplanationHtml==='function'?lenderExplanationHtml(r):''}${typeof affordabilityHtml==='function'?affordabilityHtml(r):''}</div></details>`;
}

function refreshAnalytics(focusSelector) {
  const container=$('#analytics-explorer');
  if(!container||!state.result)return;
  container.innerHTML=analyticsExplorerContents(state.result);
  bindAnalytics();
  if(focusSelector)container.querySelector(focusSelector)?.focus();
}

function selectAnalyticsMonth(value, focus=false) {
  const month=Number(value);
  if(!Number.isInteger(month)||month<1||month>36)return;
  analyticsFilters.month=month;analyticsFilters.year=Math.ceil(month/12);
  refreshAnalytics(focus?`[data-analytics-month="${month}"]`:null);
}

function bindAnalytics() {
  const container=$('#analytics-explorer');if(!container)return;
  for(const dimension of ['scenario','period'])container.querySelectorAll(`[data-analytics-${dimension}]`).forEach(button=>button.addEventListener('click',()=>{
    analyticsFilters[dimension]=button.dataset[dimension==='scenario'?'analyticsScenario':'analyticsPeriod'];
    refreshAnalytics(`[data-analytics-${dimension}="${analyticsFilters[dimension]}"]`);
  }));
  container.querySelector('#analytics-year').addEventListener('change',event=>{analyticsFilters.year=Number(event.target.value);analyticsFilters.month=(analyticsFilters.year-1)*12+1;refreshAnalytics('#analytics-year');});
  container.querySelector('#analytics-month').addEventListener('change',event=>{selectAnalyticsMonth(event.target.value);$('#analytics-month')?.focus();});
  container.querySelector('#analytics-reset').addEventListener('click',()=>{Object.assign(analyticsFilters,{scenario:'expected',year:1,period:'month',month:1});refreshAnalytics('#analytics-reset');});
  container.querySelectorAll('[data-analytics-month]').forEach(point=>{
    point.addEventListener('click',()=>selectAnalyticsMonth(point.dataset.analyticsMonth,true));
    point.addEventListener('keydown',event=>{
      const current=Number(point.dataset.analyticsMonth);
      const month=event.key==='ArrowRight'?Math.min(36,current+1):event.key==='ArrowLeft'?Math.max(1,current-1):event.key==='Home'?1:event.key==='End'?36:['Enter',' '].includes(event.key)?current:null;
      if(month!==null){event.preventDefault();selectAnalyticsMonth(month,true);}
    });
  });
}

if(typeof module!=='undefined')module.exports={analyticsSelection,analyticsMonthlyLabel,ANALYTICS_PERIODS};
