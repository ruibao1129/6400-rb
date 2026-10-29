/* All displayed values come from reproducible Python experiments, not browser RNG. */
(() => {
  'use strict';
  const d = window.BLOG8_DATA;
  const el = id => document.getElementById(id);
  const green = '#2A9D8F', blue = '#355C7D', orange = '#D88739';
  const config = {responsive:true,displaylogo:false};
  const base = {font:{family:'Arial, sans-serif',size:13,color:'#243746'},
    paper_bgcolor:'white',plot_bgcolor:'white',margin:{l:62,r:22,t:25,b:65},
    showlegend:false,hoverlabel:{namelength:-1}};
  function histogram(h,color,name){
    return {type:'bar',x:h.counts.map((_,i)=>(h.edges[i]+h.edges[i+1])/2),
      y:h.counts,marker:{color},name,width:h.counts.map((_,i)=>(h.edges[i+1]-h.edges[i])*.96),
      customdata:h.counts.map((_,i)=>[h.edges[i],h.edges[i+1]]),
      hovertemplate:'%{customdata[0]:.2f} to %{customdata[1]:.2f} min<br>%{y:,} simulations<extra></extra>'};
  }
  function line(x,color,dash='solid'){
    return {type:'line',xref:'x',yref:'paper',x0:x,x1:x,y0:0,y1:1,line:{color,width:2,dash}};
  }
  async function update(){
    const n=el('b8-n').value,level=el('b8-level').value;
    const e=d.experiments[n], c=e.levels[level], test=e.levels['95'];
    const [lo,hi]=c.ci,mu=d.summary.reference_mean;
    el('b8-bootstrap-summary').textContent=`n = ${n}; sample mean ${e.sample_mean.toFixed(2)} min. ${level}% percentile bootstrap CI: ${lo.toFixed(2)}–${hi.toFixed(2)} min, using ${d.summary.bootstrap_resamples.toLocaleString()} resamples. This interval concerns the mean, not the next order.`;
    el('b8-coverage-summary').textContent=`${c.coverage_count} / ${d.summary.coverage_experiments.toLocaleString()} intervals cover the fixed reference mean (${mu.toFixed(2)} min): ${(100*c.coverage_rate).toFixed(1)}%. Monte Carlo SE: ${(100*c.coverage_mcse).toFixed(2)} percentage points. Mean interval width: ${c.mean_width.toFixed(2)} min. Plot shows the first 60 experiments; the percentage uses all 1,000.`;
    el('b8-null-summary').textContent=`H₀: μ = 30 min; H₁: μ > 30 min. Observed T = sample mean − 30 = ${e.observed_statistic.toFixed(2)} min. ${e.extreme_null_count.toLocaleString()} of ${d.summary.null_simulations.toLocaleString()} null statistics are at least this large. Corrected one-sided p = ${e.p_value.toFixed(4)}. At fixed α = 0.05: ${test.reject?'reject H₀':'do not reject H₀'}. The interval-confidence selector does not change this test.`;
    const bootLayout={...base,height:370,
      xaxis:{title:{text:'Bootstrap sample mean (minutes)'}},
      yaxis:{title:{text:'Resamples'},rangemode:'tozero'},
      shapes:[{type:'rect',xref:'x',yref:'paper',x0:lo,x1:hi,y0:0,y1:1,fillcolor:green,opacity:.12,line:{width:0}},line(e.sample_mean,blue,'dot'),line(lo,green),line(hi,green)]};
    const first=c.intervals.slice(0,60);
    const traces=[true,false].map(covered=>{
      const x=[],y=[];
      first.forEach((a,i)=>{if(a[2]===covered){x.push(a[0],a[1],null);y.push(i+1,i+1,null);}});
      return {type:'scatter',mode:'lines',x,y,connectgaps:false,line:{color:covered?green:orange,width:2},
        name:covered?'Covers reference mean':'Misses reference mean',
        hovertemplate:'Experiment %{y}<br>Endpoint %{x:.2f} min<extra>%{fullData.name}</extra>'};
    });
    const covLayout={...base,height:510,
      xaxis:{title:{text:'Confidence interval for the mean (minutes)'}},
      yaxis:{title:{text:'New-sample experiment'},autorange:'reversed'},
      shapes:[line(mu,blue,'dash')]};
    const nullTrace=histogram(e.null_hist,blue,'Null simulations');
    const tail={...nullTrace,x:nullTrace.x.map((x,i)=>x>=test.null_critical?x:null),
      y:nullTrace.y.map((v,i)=>nullTrace.x[i]>=test.null_critical?v:null),marker:{color:orange}};
    const minX=Math.min(e.null_hist.edges[0],e.observed_statistic);
    const maxX=Math.max(e.null_hist.edges.at(-1),e.observed_statistic);
    const nullLayout={...base,height:380,barmode:'overlay',
      xaxis:{title:{text:'T = sample mean − 30 (minutes)'},range:[minX-.3,maxX+.3]},
      yaxis:{title:{text:'Null simulations'},rangemode:'tozero'},
      shapes:[line(e.observed_statistic,green),line(test.null_critical,orange,'dash')]};
    await Promise.all([Plotly.react('b8-bootstrap',[histogram(e.bootstrap_hist,green,'Bootstrap means')],bootLayout,config),
      Plotly.react('b8-coverage',traces,covLayout,config),
      Plotly.react('b8-null',[nullTrace,tail],nullLayout,config)]);
    el('b8-status').textContent='Charts updated.';
  }
  ['b8-n','b8-level'].forEach(id=>el(id).addEventListener('change',update));
  el('b8-reset').addEventListener('click',()=>{el('b8-n').value='100';el('b8-level').value='95';update();});
  update();
})();
