"""Audit source exclusions and all nine experiment/confidence combinations."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from analyze import prepare, bootstrap_means, SEED, B, NULL_RUNS, MU0

ROOT = Path(__file__).resolve().parents[1]


def main():
    frame, flow = prepare()
    d=json.loads((ROOT/'results/explorer_data.json').read_text())
    s=d['summary']; x=frame.minutes.to_numpy()
    assert flow['source_waybills'] == flow['rejected_waybills_excluded'] + flow['prebook_orders_excluded'] + flow['missing_or_nonpositive_time_excluded'] + len(x)
    assert np.isclose(x.mean(), s['reference_mean'])
    assert len(x)==s['retained_orders']==546364
    assert sum(d['reference_hist']['counts'])==len(x)
    nested=np.random.default_rng(SEED).choice(x,400,replace=True)
    table=pd.read_csv(ROOT/'results/coverage.csv')
    for key,e in d['experiments'].items():
        n=int(key);sample=nested[:n]
        assert np.isclose(sample.mean(),e['sample_mean'])
        bm=bootstrap_means(sample,np.random.default_rng(np.random.SeedSequence([SEED,n,1])))
        null=bootstrap_means(sample-sample.mean()+MU0,np.random.default_rng(np.random.SeedSequence([SEED,n,3])),NULL_RUNS)-MU0
        extreme=int(np.count_nonzero(null>=e['observed_statistic']))
        assert extreme==e['extreme_null_count']
        assert e['p_value']==(extreme+1)/(NULL_RUNS+1)
        assert sum(e['bootstrap_hist']['counts'])==B and sum(e['null_hist']['counts'])==NULL_RUNS
        widths=[]
        # Replay the first fresh sample independently of saved interval arithmetic.
        cov_rng=np.random.default_rng(np.random.SeedSequence([SEED,n,2]))
        fresh=cov_rng.choice(x,n,replace=True)
        fresh_means=bootstrap_means(fresh,cov_rng)
        for level,c in e['levels'].items():
            alpha=1-int(level)/100
            assert np.allclose(c['ci'],np.quantile(bm,[alpha/2,1-alpha/2]))
            assert np.allclose(c['intervals'][0][:2],np.quantile(fresh_means,[alpha/2,1-alpha/2]))
            ints=np.array(c['intervals']);expected=(ints[:,0]<=x.mean())&(x.mean()<=ints[:,1])
            assert np.array_equal(expected,ints[:,2].astype(bool))
            assert int(expected.sum())==c['coverage_count']
            assert np.isclose(expected.mean(),c['coverage_rate'])
            assert np.isclose(c['coverage_rate'],table[(table.n==n)&(table.confidence==int(level))].coverage_rate.iloc[0])
            assert c['reject']==(e['p_value']<=alpha)
            widths.append(c['ci'][1]-c['ci'][0])
        assert all(a<=b for a,b in zip(widths,widths[1:]))
    assert '@@' not in (ROOT/'index.qmd').read_text()
    assert (ROOT/'assets/explorer.js').read_bytes()==(ROOT/'code/explorer.js').read_bytes()
    print('PASS: official source checksum, unique completed orders and sequential exclusions.')
    print('PASS: real-data summaries; seeded samples, bootstrap quantiles and centered-null p-values.')
    print('PASS: all nine coverage/width combinations; generated article and assets consistent.')


if __name__=='__main__':main()
