"""Generate article prose, local Plotly assets and listing preview from results."""
from pathlib import Path
import json
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]


def main():
    s = json.loads((ROOT / 'results/summary.json').read_text())
    data = json.loads((ROOT / 'results/explorer_data.json').read_text())
    assets = ROOT / 'assets'
    assets.mkdir(exist_ok=True)
    (assets / 'plotly.min.js').write_text(get_plotlyjs())
    (assets / 'explorer-data.js').write_text('window.BLOG7_DATA=' + json.dumps(data, separators=(',', ':')) + ';\n')
    shutil.copyfile(ROOT / 'code/explorer.js', assets / 'explorer.js')
    morning = s['morning_06_08']['disruption_rate']
    evening = s['evening_18_20']['disruption_rate']
    check = s['common_route_check']
    peak = max(s['months'], key=lambda m: s['months'][m]['disruption_rate'])
    low = min(s['months'], key=lambda m: s['months'][m]['disruption_rate'])
    import calendar
    pct = lambda x: f'{100*x:.1f}%'
    replacements = {
        'N': f"{s['overall']['n']:,}", 'UNKNOWN': f"{s['overall']['unknown']:,}",
        'UNKNOWN_SENTENCE': ('One record has an unclassified outcome; it is excluded from the disruption and arrival-delay denominators.'
                             if s['overall']['unknown'] == 1 else f"{s['overall']['unknown']:,} records have unclassified outcomes; they are excluded from the disruption and arrival-delay denominators."),
        'MORNING': pct(morning), 'EVENING': pct(evening), 'DIFF': f'{(evening-morning)*100:.1f}',
        'CELLS': f"{check['cells']:,}", 'MATCH_M': pct(check['morning_rate']),
        'MATCH_N': f"{check['known_flights']:,}",
        'MATCH_SHARE': pct(check['known_flights']/s['overall']['known']),
        'MATCH_E': pct(check['evening_rate']),
        'MATCH_INTERPRETATION': ('preserves the direction of the pooled morning advantage, although its magnitude changes'
                                 if evening > morning and check['evening_rate'] > check['morning_rate'] else
                                 'shows why the pooled time-of-day comparison should not be generalized without checking the comparison groups'),
        'TAKEAWAY': ('the morning comparison window had fewer recorded disruptions than the evening window'
                     if morning < evening else 'the morning comparison window did not have fewer recorded disruptions than the evening window'),
        'SEASONAL': f"For the pooled full-year selection, {calendar.month_name[int(peak)]} had the highest monthly disruption rate ({pct(s['months'][peak]['disruption_rate'])}), while {calendar.month_name[int(low)]} had the lowest ({pct(s['months'][low]['disruption_rate'])}). These are whole-month rates, not the individual heatmap-cell rates.",
        'CANCEL': pct(s['overall']['cancellation_rate']),
        'DIVERT': pct(s['overall']['diverted']/s['overall']['n'])}
    widget = (ROOT / 'code/widget.html.in').read_text()
    article = (ROOT / 'code/article_template.qmd.in').read_text()
    for key, value in replacements.items():
        widget = widget.replace(f'@@{key}@@', value)
        article = article.replace(f'@@{key}@@', value)
    article = article.replace('@@EXPLORER@@', '```{=html}\n' + widget + '\n```')
    assert '@@' not in article
    (ROOT / 'index.qmd').write_text(article)
    # Static preview for the blog listing, not a replacement for the interaction.
    fig, ax = plt.subplots(figsize=(8, 4.5), layout='constrained')
    for airport, color in [('EWR', '#d88739'), ('JFK', '#355C7D'), ('LGA', '#2A9D8F')]:
        columns = data['columns']
        rows = [dict(zip(columns, row)) for row in data['rows'] if row[1] == airport]
        x, y = [], []
        for h in range(24):
            selected = [r for r in rows if r['hour'] == h]
            den = sum(r['n']-r['unknown'] for r in selected)
            num = sum(r['late']+r['cancelled']+r['diverted'] for r in selected)
            x.append(h); y.append(num/den*100 if den>=100 else float('nan'))
        ax.plot(x, y, marker='o', markersize=3, color=color, label=airport)
    ax.set(xlabel='Scheduled departure hour (local)', ylabel='Disruption rate (%)',
           title='When you fly changes the historical comparison', xlim=(0, 23), ylim=(0, None))
    ax.set_xticks(range(0, 24, 3));ax.grid(axis='y',alpha=.2);ax.legend(frameon=False)
    ax.spines[['top','right']].set_visible(False)
    fig.supxlabel('BTS reporting-carrier domestic flights from NYC, 2025. Hours with <100 known outcomes omitted.',fontsize=8)
    (ROOT / 'figures').mkdir(exist_ok=True)
    fig.savefig(ROOT / 'figures/hourly_preview.png', dpi=180)
    plt.close(fig)
    print('Built index.qmd, local Plotly assets and preview.')


if __name__ == '__main__':
    main()
