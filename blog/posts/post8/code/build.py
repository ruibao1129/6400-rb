"""Build English prose and display assets from computed outputs; no raw data needed."""
from pathlib import Path
import json
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plotly.offline import get_plotlyjs
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GREEN, BLUE, ORANGE = '#2A9D8F', '#355C7D', '#D88739'


def main():
    d = json.loads((ROOT / 'results/explorer_data.json').read_text())
    s, e = d['summary'], d['experiments']['100']
    assets = ROOT / 'assets'
    figures = ROOT / 'figures'
    assets.mkdir(exist_ok=True)
    figures.mkdir(exist_ok=True)
    (assets / 'plotly.min.js').write_text(get_plotlyjs())
    (assets / 'explorer-data.js').write_text('window.BLOG8_DATA=' + json.dumps(d, separators=(',', ':'), allow_nan=False) + ';\n')
    shutil.copyfile(ROOT / 'code/explorer.js', assets / 'explorer.js')
    pct = lambda v: f'{v*100:.1f}%'
    replacements = {'N': f"{s['retained_orders']:,}", 'MEAN': f"{s['reference_mean']:.2f}",
        'MEDIAN': f"{s['median']:.2f}", 'OVER45': pct(s['share_over_45']),
        'LONG_N': f"{s['orders_over_120']:,}", 'MAX': f"{s['max']:.2f} minutes",
        'SENS_MEAN': f"{s['sensitivity_mean_excluding_over_120']:.2f}",
        'SAMPLE_MEAN': f"{e['sample_mean']:.2f}", 'LO': f"{e['levels']['95']['ci'][0]:.2f}",
        'HI': f"{e['levels']['95']['ci'][1]:.2f}", 'P': f"{e['p_value']:.4f}",
        'TEST': ('reject the 30-minute null in favor of a higher mean' if e['levels']['95']['reject'] else 'do not reject the 30-minute null'),
        'RESULT': ('the one-sided test supports a mean above 30 minutes at the 5% level' if e['levels']['95']['reject'] else 'the one-sided test provides insufficient evidence that the mean exceeds 30 minutes'),
        **{f'COVER{n}': pct(d['experiments'][str(n)]['levels']['95']['coverage_rate']) for n in [20,100,400]}}
    widget = (ROOT / 'code/widget.html.in').read_text()
    article = (ROOT / 'code/article_template.qmd.in').read_text()
    for k, v in replacements.items():
        article = article.replace(f'@@{k}@@', v)
        widget = widget.replace(f'@@{k}@@', v)
    article = article.replace('@@WIDGET@@', '```{=html}\n' + widget + '\n```')
    assert '@@' not in article
    (ROOT / 'index.qmd').write_text(article)
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    def finish(fig, ax, file, xlabel, ylabel):
        ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
        ax.grid(axis='y', alpha=.18)
        fig.savefig(figures / file, dpi=180)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,4.5), layout='constrained')
    h = d['reference_hist']
    x = np.arange(len(h['counts']))*5+2.5
    ax.bar(x,np.array(h['counts'])/s['retained_orders']*100,width=4.7,color=GREEN)
    ax.axvline(s['reference_mean'],color=BLUE,label=f"Mean {s['reference_mean']:.2f} min")
    ax.set_xticks([0,30,60,90,122.5],['0','30','60','90','120+'])
    ax.set_title('An average near 30 minutes does not describe every wait',fontweight='bold')
    ax.legend(frameon=False)
    fig.supxlabel('Meituan completed non-prebook orders, Oct 17–24, 2022. Final bin pools all durations ≥120 min.',fontsize=8)
    finish(fig,ax,'delivery_distribution.png','Order creation to delivery arrival (minutes)','Orders in each 5-minute bin (%)')
    fig, ax = plt.subplots(figsize=(8,4.5), layout='constrained')
    h = e['bootstrap_hist'];edges=np.array(h['edges'])
    ax.bar((edges[:-1]+edges[1:])/2,h['counts'],width=np.diff(edges)*.95,color=GREEN)
    ax.axvspan(*e['levels']['95']['ci'],color=BLUE,alpha=.1)
    ax.axvline(e['sample_mean'],color=BLUE,linestyle=':')
    ax.set_title('One sample, 1,999 resampled means (n = 100)',fontweight='bold')
    finish(fig,ax,'bootstrap.png','Bootstrap mean (minutes)','Resamples')
    fig, ax = plt.subplots(figsize=(8,5.5), layout='constrained')
    for i,(lo,hi,cover) in enumerate(e['levels']['95']['intervals'][:60],1):
        ax.plot([lo,hi],[i,i],color=GREEN if cover else ORANGE,lw=1.7)
    ax.axvline(s['reference_mean'],color=BLUE,ls='--')
    ax.invert_yaxis();ax.set_title('New samples, new intervals; the reference mean stays fixed',fontweight='bold')
    finish(fig,ax,'coverage.png','95% percentile interval (minutes)','Experiment (first 60 of 1,000)')
    fig, ax = plt.subplots(figsize=(8,4.5), layout='constrained')
    h=e['null_hist'];edges=np.array(h['edges']);centers=(edges[:-1]+edges[1:])/2
    critical=e['levels']['95']['null_critical']
    ax.bar(centers,h['counts'],width=np.diff(edges)*.95,color=[ORANGE if c>=critical else BLUE for c in centers])
    ax.axvline(e['observed_statistic'],color=GREEN,label='Observed statistic')
    ax.axvline(critical,color=ORANGE,ls='--',label='5% right-tail threshold')
    ax.legend(frameon=False);ax.set_title('What would sample means look like under a 30-minute null?',fontweight='bold')
    finish(fig,ax,'null.png','Sample mean − 30 (minutes)','Null simulations')
    print('Built article, four static figures and interactive assets.')


if __name__ == '__main__':
    main()
