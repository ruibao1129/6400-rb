/* Plotly explorer. Data are additive counts, never averages of percentages. */
(() => {
  'use strict';
  const payload = window.BLOG7_DATA;
  const fields = payload.columns;
  const rows = payload.rows.map(row => Object.fromEntries(fields.map((k, i) => [k, row[i]])));
  const counts = ['n', 'on_time', 'late', 'cancelled', 'diverted', 'unknown', 'dep_observed', 'dep_late'];
  const byId = id => document.getElementById(id);
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const metricLabels = {
    disruption: 'Arrival delay ≥15 min, cancellation or diversion',
    arrival: 'Arrival delay ≥15 min among reported non-diverted arrivals',
    cancel: 'Cancellation among all scheduled records',
    departure: 'Departure delay ≥15 min among reported departures'
  };
  const colors = {disruption: '#2A9D8F', arrival: '#355C7D', cancel: '#d88739', departure: '#355C7D'};
  const config = {responsive: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d']};
  const baseLayout = {
    font: {family: 'Arial, sans-serif', size: 13, color: '#243746'},
    paper_bgcolor: 'white', plot_bgcolor: 'white',
    margin: {l: 62, r: 22, t: 30, b: 58},
    hoverlabel: {namelength: -1},
    xaxis: {fixedrange: false}, yaxis: {rangemode: 'tozero', gridcolor: '#edf0f2'}
  };
  function sum(items) {
    const v = Object.fromEntries(counts.map(k => [k, 0]));
    items.forEach(r => counts.forEach(k => {v[k] += r[k];}));
    return v;
  }
  function metric(v, key) {
    if (key === 'arrival') return [v.late, v.on_time + v.late];
    if (key === 'cancel') return [v.cancelled, v.n];
    if (key === 'departure') return [v.dep_late, v.dep_observed];
    return [v.late + v.cancelled + v.diverted, v.n - v.unknown];
  }
  function option(select, value, text) {
    const o = document.createElement('option'); o.value = value; o.textContent = text; select.append(o);
  }
  function carrierOptions() {
    const airport = byId('b7-airport').value;
    const previous = byId('b7-carrier').value;
    const available = [...new Set(rows.filter(r => airport === 'ALL' || r.airport === airport).map(r => r.carrier))].sort();
    const select = byId('b7-carrier'); select.replaceChildren();
    option(select, 'ALL', 'All reporting airlines');
    available.forEach(c => option(select, c, payload.carrier_names[c] ? `${c} — ${payload.carrier_names[c]}` : c));
    select.value = available.includes(previous) ? previous : 'ALL';
  }
  function titleContext(airport, carrier, month) {
    return `${airport === 'ALL' ? 'All three airports' : airport} · ${carrier === 'ALL' ? 'all reporting airlines' : carrier} · ${month === 'ALL' ? 'all months' : monthNames[Number(month)-1]} 2025`;
  }
  async function update() {
    const airport = byId('b7-airport').value;
    const carrier = byId('b7-carrier').value;
    const month = byId('b7-month').value;
    const key = byId('b7-metric').value;
    const allMonths = rows.filter(r => (airport === 'ALL' || r.airport === airport) && (carrier === 'ALL' || r.carrier === carrier));
    const selected = allMonths.filter(r => month === 'ALL' || r.month === Number(month));
    const total = sum(selected);
    const [num, den] = metric(total, key);
    const fmt = n => n.toLocaleString('en-US');
    byId('b7-context').textContent = titleContext(airport, carrier, month);
    byId('b7-summary').textContent = total.n ? `${fmt(total.n)} scheduled records · ${den ? (100*num/den).toFixed(1)+'%' : 'n.a.'} selected outcome (${fmt(num)} / ${fmt(den)} eligible records) · ${fmt(total.unknown)} unclassified outcome${total.unknown === 1 ? '' : 's'}` : 'No records for this selection. Broaden the filters.';
    byId('b7-definition').textContent = metricLabels[key] + '. Hours with fewer than 100 eligible records are blank, not zero. All times are scheduled local departure hours.';
    const hours = Array.from({length: 24}, (_, i) => i);
    const perHour = hours.map(h => sum(selected.filter(r => r.hour === h)));
    const pairs = perHour.map(v => metric(v, key));
    const y = pairs.map(([n, d]) => d >= 100 ? n/d : null);
    const custom = pairs.map(([n, d], i) => [n, d, perHour[i].n]);
    const trace = {type: 'scatter', mode: 'lines+markers', x: hours, y, customdata: custom,
      connectgaps: false, name: 'Selected outcome', marker: {color: colors[key], size: 6},
      line: {color: colors[key], width: 3},
      hovertemplate: '%{x}:00–%{x}:59<Br>Rate: %{y:.1%}<br>Outcome count: %{customdata[0]:,}<br>Eligible records: %{customdata[1]:,}<br>Scheduled records: %{customdata[2]:,}<extra></extra>'};
    const lineLayout = {...baseLayout, height: 350,
      xaxis: {title: {text: 'Scheduled departure hour (local)'}, tickmode: 'linear', dtick: 3, range: [-.4, 23.4]},
      yaxis: {title: {text: 'Historical rate'}, tickformat: '.0%', rangemode: 'tozero', gridcolor: '#edf0f2'},
      annotations: y.every(v => v === null) ? [{text: 'No hourly groups meet the 100-record threshold. Broaden filters.', x:.5,y:.5,xref:'paper',yref:'paper',showarrow:false}] : []};
    if (y.every(v => v === null)) lineLayout.yaxis.range = [0, 1];
    const z = [], hc = [];
    for (let m = 1; m <= 12; m++) {
      const monthRows = allMonths.filter(r => r.month === m);
      const cells = hours.map(h => metric(sum(monthRows.filter(r => r.hour === h)), key));
      z.push(cells.map(([n,d]) => d >= 100 ? n/d : null));
      hc.push(cells.map(([n,d]) => [n,d]));
    }
    byId('b7-heat-context').textContent = `${airport === 'ALL' ? 'All three airports' : airport} · ${carrier === 'ALL' ? 'all reporting airlines' : carrier} · full year 2025. This view ignores the month selector so you can compare seasons.`;
    const heatTrace = {type: 'heatmap', x: hours, y: monthNames, z, customdata: hc, zmin: 0, zmax: 1,
      colorscale: [[0,'#f2faf8'],[.3,'#2A9D8F'],[.65,'#355C7D'],[1,'#142f46']],
      colorbar: {title: {text:'Rate'}, tickformat:'.0%', thickness:14}, hoverongaps:false,
      hovertemplate:'%{y}, %{x}:00–%{x}:59<br>Rate: %{z:.1%}<br>Outcome count: %{customdata[0]:,}<br>Eligible records: %{customdata[1]:,}<extra></extra>'};
    const heatLayout = {...baseLayout, height: 410,
      xaxis:{title:{text:'Scheduled departure hour (local)'}, tickmode:'linear',dtick:3},
      yaxis:{autorange:'reversed', type:'category'}, margin:{l:62,r:60,t:20,b:58}};
    if (z.every(row => row.every(v => v === null))) {
      heatLayout.annotations = [{text:'No monthly/hourly cells meet the 100-record threshold.',
        x:.5,y:.5,xref:'paper',yref:'paper',showarrow:false}];
    }
    const bands = [[0,4,'00–04'],[5,8,'05–08'],[9,11,'09–11'],[12,14,'12–14'],[15,17,'15–17'],[18,23,'18–23']];
    const bandCounts = bands.map(([lo,hi]) => sum(selected.filter(r => r.hour >= lo && r.hour <= hi)));
    const outcomes = [['on_time','Arrival <15 min late','#2A9D8F'],['late','Arrival ≥15 min late','#355C7D'],
      ['cancelled','Cancelled','#d88739'],['diverted','Diverted','#6a737a'],['unknown','Unclassified','#c3cbd0']];
    const bars = outcomes.map(([field,name,color]) => ({type:'bar',name,
      x:bands.map(b=>b[2]),y:bandCounts.map(v=>v.n>=100?v[field]/v.n:null),
      customdata:bandCounts.map(v=>[v[field],v.n]),marker:{color},
      hovertemplate:'%{x} scheduled hour band<br>'+name+': %{y:.1%}<br>Count: %{customdata[0]:,} / %{customdata[1]:,}<extra></extra>'}));
    const narrow = window.matchMedia('(max-width:540px)').matches;
    const barLayout = {...baseLayout,height:narrow?520:420,barmode:'stack',
      xaxis:{title:{text:'Scheduled departure hour band (local)'},type:'category'},
      yaxis:{title:{text:'Share of all scheduled records'},tickformat:'.0%',range:[0,1.01]},
      legend:{orientation:'h',y:-.22,yanchor:'top',x:0,font:{size:11}},margin:{l:62,r:22,t:20,b:narrow?200:110}};
    await Promise.all([
      Plotly.react('b7-hour', [trace], lineLayout, config),
      Plotly.react('b7-heat', [heatTrace], heatLayout, config),
      Plotly.react('b7-outcomes', bars, barLayout, config)
    ]);
    byId('b7-status').textContent = 'Charts updated.';
    window.BLOG7_STATE = {airport, carrier, month, metric:key, scheduled:total.n,
      numerator:num, denominator:den, rate:den?num/den:null, line_points:y.filter(v=>v!==null).length};
  }
  const month = byId('b7-month');
  monthNames.forEach((m,i)=>option(month,String(i+1),m));
  carrierOptions();
  byId('b7-airport').addEventListener('change',()=>{carrierOptions();update();});
  ['b7-carrier','b7-month','b7-metric'].forEach(id=>byId(id).addEventListener('change',update));
  byId('b7-reset').addEventListener('click',()=>{
    byId('b7-airport').value='ALL';byId('b7-month').value='ALL';byId('b7-metric').value='disruption';
    byId('b7-carrier').value='ALL';carrierOptions();update();
  });
  let resizeTimer;
  window.addEventListener('resize',()=>{
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(update,120);
  });
  // Month cells are an additional navigation shortcut, not the only input method.
  update().then(()=>byId('b7-heat').on('plotly_click',event=>{
    const i=monthNames.indexOf(event.points[0].y);
    if(i>=0){byId('b7-month').value=String(i+1);update();}
  }));
})();
