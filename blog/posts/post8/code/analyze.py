"""Real delivery summaries and explicitly conditional empirical-population experiments.

Seeds, sample sizes and benchmark are fixed here, not selected for significance.
Outputs contain aggregate research results and simulations, not original orders.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NS = [20, 100, 400]
LEVELS = [90, 95, 99]
B = 1999
R = 1000
NULL_RUNS = 9999
SEED = 20261029
MU0 = 30.0


def prepare():
    archive = ROOT / 'data/private/waybills.zip'
    source = json.loads((ROOT / 'data/source_manifest.json').read_text())
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == source['sha256']
    cols = ['dt', 'order_id', 'waybill_id', 'courier_id', 'is_courier_grabbed',
            'is_prebook', 'platform_order_time', 'arrive_time']
    with ZipFile(archive) as z:
        with z.open('all_waybill_info_meituan_0322.csv') as f:
            d = pd.read_csv(f, usecols=cols)
    flow = {'source_waybills': len(d), 'source_unique_orders': d.order_id.nunique()}
    # Sequential exclusions: zero timestamps mean unavailable, never instantaneous.
    a = d[d.is_courier_grabbed.eq(1)].copy()
    flow['rejected_waybills_excluded'] = len(d) - len(a)
    assert not a.order_id.duplicated().any(), 'Do not count reassigned orders twice.'
    flow['prebook_orders_excluded'] = int(a.is_prebook.ne(0).sum())
    a = a[a.is_prebook.eq(0)].copy()
    valid = a.platform_order_time.gt(0) & a.arrive_time.gt(a.platform_order_time)
    flow['missing_or_nonpositive_time_excluded'] = int((~valid).sum())
    a = a[valid].copy()
    a['minutes'] = (a.arrive_time - a.platform_order_time) / 60
    assert a.minutes.gt(0).all() and not a.order_id.duplicated().any()
    flow['retained_orders'] = len(a)
    flow['dates'] = sorted(a.dt.unique().tolist())
    return a, flow


def hist(x, bins):
    counts, edges = np.histogram(x, bins=bins)
    assert counts.sum() == len(x)
    return {'edges': edges.tolist(), 'counts': counts.tolist()}


def bootstrap_means(sample, rng, b=B):
    return sample[rng.integers(0, len(sample), size=(b, len(sample)))].mean(axis=1)


def main():
    frame, flow = prepare()
    x = frame.minutes.to_numpy()
    mu = float(x.mean())
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    flow.update({'reference_mean': mu, 'median': float(np.median(x)),
                 'p90': float(np.quantile(x, .9)), 'max': float(x.max()),
                 'share_over_45': float(np.mean(x > 45)),
                 'share_over_30': float(np.mean(x > MU0)),
                 'orders_over_120': int(np.sum(x > 120)),
                 'seed': SEED, 'benchmark': MU0, 'bootstrap_resamples': B,
                 'coverage_experiments': R, 'null_simulations': NULL_RUNS})
    daily = frame.groupby('dt').minutes.agg(['count', 'mean', 'median'])
    daily.to_csv(out / 'daily_summary.csv')
    # A broad, predeclared sensitivity diagnostic, never a data-dependent trimming rule.
    flow['sensitivity_mean_excluding_over_120'] = float(x[x <= 120].mean())
    # Finite reference set is sampled WITH replacement, making empirical IID draws.
    # Known truth below is ONLY this reference distribution's mean, not all Meituan orders.
    payload = {'summary': flow, 'levels': LEVELS,
               'reference_hist': hist(x, np.r_[np.arange(0, 121, 5), np.inf]), 'experiments': {}}
    # Infinity cannot appear in browser JSON. Last bin is explicitly labeled 120+.
    payload['reference_hist']['edges'][-1] = float(np.ceil(x.max()))
    nested_sample = np.random.default_rng(SEED).choice(x, max(NS), replace=True)
    coverage_rows, interval_rows = [], []
    for n in NS:
        rng_boot = np.random.default_rng(np.random.SeedSequence([SEED, n, 1]))
        rng_cov = np.random.default_rng(np.random.SeedSequence([SEED, n, 2]))
        rng_null = np.random.default_rng(np.random.SeedSequence([SEED, n, 3]))
        sample = nested_sample[:n]
        means = bootstrap_means(sample, rng_boot)
        intervals = {str(level): [] for level in LEVELS}
        for rep in range(R):
            fresh = rng_cov.choice(x, n, replace=True)
            bm = bootstrap_means(fresh, rng_cov)
            for level in LEVELS:
                alpha = 1 - level / 100
                lo, hi = np.quantile(bm, [alpha / 2, 1 - alpha / 2])
                covered = bool(lo <= mu <= hi)
                intervals[str(level)].append([float(lo), float(hi), covered])
                interval_rows.append([n, level, rep + 1, lo, hi, covered])
        # Impose H0 on THIS sample before resampling. Uncentered bootstrap is not a null.
        centered = sample - sample.mean() + MU0
        assert np.isclose(centered.mean(), MU0)
        null_stats = bootstrap_means(centered, rng_null, NULL_RUNS) - MU0
        observed = float(sample.mean() - MU0)
        extreme = int(np.sum(null_stats >= observed))
        p = (extreme + 1) / (NULL_RUNS + 1)
        exp = {'n': n, 'sample_mean': float(sample.mean()),
               'bootstrap_hist': hist(means, 45),
               'bootstrap_center': float(means.mean()),
               'sample_hist': hist(sample, np.r_[np.arange(0, 121, 5), np.inf]),
               'observed_statistic': observed, 'p_value': p, 'extreme_null_count': extreme,
               'null_hist': hist(null_stats, 65), 'levels': {}}
        exp['sample_hist']['edges'][-1] = max(121., float(np.ceil(sample.max())))
        for level in LEVELS:
            alpha = 1 - level / 100
            lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
            ints = intervals[str(level)]
            covered = sum(v[2] for v in ints)
            rate = covered / R
            critical = float(np.quantile(null_stats, 1 - alpha))
            exp['levels'][str(level)] = {
                'ci': [float(lo), float(hi)], 'intervals': ints,
                'coverage_count': covered, 'coverage_rate': rate,
                'coverage_mcse': float(np.sqrt(rate * (1-rate) / R)),
                'mean_width': float(np.mean([v[1]-v[0] for v in ints])),
                'null_critical': critical, 'alpha': alpha,
                'reject': bool(p <= alpha)}
            coverage_rows.append([n, level, covered, R, rate, exp['levels'][str(level)]['coverage_mcse'], exp['levels'][str(level)]['mean_width']])
        payload['experiments'][str(n)] = exp
        print('Finished n =', n, '95% coverage', exp['levels']['95']['coverage_rate'], flush=True)
    (out / 'summary.json').write_text(json.dumps(flow, indent=2) + '\n')
    (out / 'explorer_data.json').write_text(json.dumps(payload, separators=(',', ':'), allow_nan=False) + '\n')
    pd.DataFrame(coverage_rows, columns=['n', 'confidence', 'covered', 'experiments', 'coverage_rate', 'mcse', 'mean_width']).to_csv(out / 'coverage.csv', index=False)
    pd.DataFrame(interval_rows, columns=['n', 'confidence', 'replicate', 'lower', 'upper', 'covers_reference_mean']).to_csv(out / 'coverage_intervals.csv', index=False)
    print(json.dumps(flow, indent=2))


if __name__ == '__main__':
    main()
