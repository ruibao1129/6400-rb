"""Create additive counts and fixed comparisons from the cached BTS NYC subset."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COUNT_COLS = ['n', 'on_time', 'late', 'cancelled', 'diverted', 'unknown',
              'dep_observed', 'dep_late']
KEYS = ['month', 'airport', 'carrier', 'hour']


def prepare():
    target = ROOT / 'data/bts_nyc_2025.csv.gz'
    manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
    assert hashlib.sha256(target.read_bytes()).hexdigest() == manifest['subset_sha256']
    f = pd.read_csv(target)
    assert len(f) == manifest['subset_rows']
    assert set(f.Month) == set(range(1, 13))
    assert set(f.Origin) == {'EWR', 'JFK', 'LGA'}
    assert f.Cancelled.isin([0, 1]).all() and f.Diverted.isin([0, 1]).all()
    assert not (f.Cancelled.eq(1) & f.Diverted.eq(1)).any()
    t = f.CRSDepTime
    valid = t.notna() & (t.eq(2400) | ((t >= 0) & (t < 2400) & (t % 100 < 60)))
    invalid_times = int((~valid).sum())
    f = f.loc[valid].copy()
    f['hour'] = (f.CRSDepTime.astype(int) // 100) % 24
    f['month'] = f.Month.astype(int)
    f['airport'] = f.Origin
    f['carrier'] = f.Reporting_Airline
    f['n'] = 1
    complete = f.Cancelled.eq(0) & f.Diverted.eq(0) & f.ArrDelay.notna()
    f['on_time'] = (complete & f.ArrDelay.lt(15)).astype(int)
    f['late'] = (complete & f.ArrDelay.ge(15)).astype(int)
    f['cancelled'] = f.Cancelled.astype(int)
    f['diverted'] = f.Diverted.astype(int)
    f['unknown'] = 1 - f[['on_time', 'late', 'cancelled', 'diverted']].sum(axis=1)
    f['dep_observed'] = (f.Cancelled.eq(0) & f.DepDelay.notna()).astype(int)
    f['dep_late'] = (f.dep_observed.eq(1) & f.DepDelay.ge(15)).astype(int)
    assert f.unknown.isin([0, 1]).all()
    return f, invalid_times


def totals(frame):
    v = {k: int(frame[k].sum()) for k in COUNT_COLS}
    v['known'] = v['n'] - v['unknown']
    v['disrupted'] = v['late'] + v['cancelled'] + v['diverted']
    v['disruption_rate'] = v['disrupted'] / v['known'] if v['known'] else None
    v['arrival_delay_rate'] = v['late'] / (v['on_time'] + v['late']) if v['on_time'] + v['late'] else None
    v['cancellation_rate'] = v['cancelled'] / v['n'] if v['n'] else None
    return v


def main():
    f, invalid = prepare()
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    grouped = f.groupby(KEYS, observed=True)[COUNT_COLS].sum().reset_index()
    assert grouped[COUNT_COLS].sum().to_dict() == f[COUNT_COLS].sum().to_dict()
    # Export numeric JSON rather than formatted percentages for browser aggregation.
    payload = {'columns': KEYS + COUNT_COLS,
               'rows': grouped[KEYS + COUNT_COLS].values.tolist(),
               'carriers': sorted(f.carrier.unique().tolist()),
               'year': 2025, 'minimum_denominator': 100}
    lookup = pd.read_csv(ROOT / 'data/carriers.csv', dtype=str)
    names = dict(zip(lookup.Code, lookup.Description))
    payload['carrier_names'] = {c: names.get(c, c) for c in payload['carriers']}
    (out / 'explorer_data.json').write_text(json.dumps(payload, separators=(',', ':')) + '\n')
    grouped.to_csv(out / 'hourly_counts.csv', index=False)
    report = {'year': 2025, 'invalid_scheduled_times_excluded': invalid,
              'overall': totals(f), 'airports': {}, 'months': {}}
    for airport, g in f.groupby('airport'):
        report['airports'][airport] = {
            'overall': totals(g),
            'morning_06_08': totals(g[g.hour.between(6, 8)]),
            'evening_18_20': totals(g[g.hour.between(18, 20)])}
    for month, g in f.groupby('month'):
        report['months'][int(month)] = totals(g)
    for key, low, high in [('morning_06_08', 6, 8), ('evening_18_20', 18, 20)]:
        report[key] = totals(f[f.hour.between(low, high)])
    # Secondary descriptive check: compare the two windows within the same
    # origin/destination/reporting-carrier/month, retaining >=30 known outcomes
    # in EACH window. Weight both rates by the same pooled cell count.
    paired = f[f.hour.between(6, 8) | f.hour.between(18, 20)].copy()
    paired['window'] = np.where(paired.hour.between(6, 8), 'morning', 'evening')
    paired['known'] = 1 - paired.unknown
    paired['bad'] = paired.late + paired.cancelled + paired.diverted
    cells = paired.groupby(['airport', 'Dest', 'carrier', 'month', 'window'])[['known', 'bad']].sum().unstack('window')
    cells = cells.dropna()
    cells = cells[(cells[('known', 'morning')] >= 30) & (cells[('known', 'evening')] >= 30)]
    assert len(cells) > 0
    weights = cells[('known', 'morning')] + cells[('known', 'evening')]
    mr = cells[('bad', 'morning')] / cells[('known', 'morning')]
    er = cells[('bad', 'evening')] / cells[('known', 'evening')]
    report['common_route_check'] = {
        'cells': len(cells), 'known_flights': int(weights.sum()),
        'morning_rate': float(np.average(mr, weights=weights)),
        'evening_rate': float(np.average(er, weights=weights)),
        'evening_minus_morning_pp': float(np.average(er-mr, weights=weights)*100),
        'share_cells_evening_higher': float((er > mr).mean()),
        'minimum_known_per_window': 30}
    cells.to_csv(out / 'common_route_cells.csv')
    report['hourly_all'] = {int(h): totals(g) for h, g in f.groupby('hour')}
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['overall', 'morning_06_08', 'evening_18_20', 'common_route_check']}, indent=2))


if __name__ == '__main__':
    main()
