from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'results/summary.json').read_text())
out=ROOT/'figures';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.spines.left':False,'axes.spines.bottom':False,'savefig.dpi':180})
colors=['#2A9D8F','#355C7D','#F4A261']

def chart(keys,labels,name,title,note):
    vals=[r[k] if isinstance(k,str) else r[k[0]][k[1]] for k in keys]
    fig,ax=plt.subplots(figsize=(8,4.7),layout='constrained')
    x=np.arange(len(vals)); b=np.array([v['beta'] for v in vals])
    err=np.array([[v['beta']-v['lower'] for v in vals],
                  [v['upper']-v['beta'] for v in vals]])
    ax.bar(x,b,color=colors[:len(vals)],width=.48,zorder=3)
    ax.errorbar(x,b,yerr=err,fmt='none',ecolor='#29343c',capsize=6,zorder=4)
    for i,v in enumerate(vals):ax.text(i,v['upper']+.006,f"{v['beta']:.3f}",ha='center',weight='bold')
    ax.set_xticks(x,labels);ax.set_ylabel('Intergenerational earnings elasticity')
    ax.axhline(0,color='#777',lw=.8);ax.grid(axis='y',alpha=.18,zorder=0)
    ax.set_ylim(-.04,.16);ax.set_title(title,loc='left',weight='bold',pad=17)
    fig.supxlabel(note,fontsize=9,color='#555')
    fig.savefig(out/name);plt.close(fig)

chart(['single_year','multiyear'],['Single year near age 35','Average at ages 30–39'],
      '01_single_vs_average.png','A longer earnings snapshot gives a higher estimate',
      'Same 3,094 children; 1,753 mother clusters. Bars: OLS slopes; whiskers: 95% CIs.\nPSID-SHELF V2.1, 1968–2021. Unweighted selected sample.')
chart([('age_comparison',s) for s in ['early','middle','later']],
      ['Near age 22','Near age 35','Near age 45'],'02_age_comparison.png',
      'Point estimates rise with the age of the earnings snapshot',
      'Same 1,608 children; 1,116 mother clusters. Mother’s ages-30–39 average held fixed.\nWhiskers: 95% CIs. Separate sample from Figure 1; unweighted.\nSource: PSID-SHELF V2.1, 1968–2021; author’s calculations.')

# Paired differences are the relevant uncertainty for comparing estimates.
fig,ax=plt.subplots(figsize=(8,4.1),layout='constrained')
ks=['average_minus_single','middle_minus_early','later_minus_early']
labs=['Average minus single year','Age 35 minus age 22','Age 45 minus age 22']
for i,k in enumerate(ks):
    v=r[k];ax.errorbar(v['difference'],i,xerr=[[v['difference']-v['lower']],
      [v['upper']-v['difference']]],fmt='o',color=colors[i],capsize=6,markersize=8)
ax.set_yticks(range(3),labs);ax.invert_yaxis();ax.axvline(0,color='#777',ls='--')
ax.set_xlabel('Difference in estimated elasticity (95% paired CI)')
ax.set_title('The pattern is suggestive—not a precise verdict',loc='left',weight='bold',pad=17)
ax.grid(axis='x',alpha=.18)
fig.supxlabel('Uncertainty accounts for shared mothers and paired observations; all intervals include zero.\nSource: PSID-SHELF V2.1, 1968–2021; author’s calculations. Unweighted selected samples.',fontsize=9,color='#555')
fig.savefig(out/'03_paired_differences.png');plt.close(fig)
