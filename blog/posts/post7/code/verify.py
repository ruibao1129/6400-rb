"""Independent checks of source subset, browser counts, denominators and prose."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT/'data/source_manifest.json').read_text())
    source = ROOT/'data/bts_nyc_2025.csv.gz'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['subset_sha256']
    raw = pd.read_csv(source)
    assert len(raw) == sum(m['nyc_rows'] for m in manifest['monthly_sources'])
    assert len(manifest['monthly_sources']) == 12
    assert not raw.duplicated(['FlightDate','Reporting_Airline',
        'Flight_Number_Reporting_Airline','Origin','Dest','CRSDepTime']).any()
    assert pd.to_datetime(raw.FlightDate).dt.year.eq(2025).all()
    summary = json.loads((ROOT/'results/summary.json').read_text())
    counts = pd.read_csv(ROOT/'results/hourly_counts.csv')
    assert len(raw) == summary['overall']['n']  # Verified zero invalid times for this vintage.
    assert summary['invalid_scheduled_times_excluded'] == 0
    outcome_cols = ['on_time','late','cancelled','diverted','unknown']
    assert counts[outcome_cols].sum(axis=1).eq(counts.n).all()
    assert counts.dep_late.le(counts.dep_observed).all()
    assert counts.dep_observed.le(counts.n-counts.cancelled).all()
    assert counts.n.sum() == len(raw)
    # Recalculate counts directly from raw BTS indicators, separately from analyze.py.
    hour = (raw.CRSDepTime.astype(int)//100)%24
    rng = np.random.default_rng(2025)
    carriers = ['ALL'] + sorted(raw.Reporting_Airline.unique().tolist())
    for i in range(80):
        airport = ['ALL','EWR','JFK','LGA'][i%4]
        carrier = carriers[int(rng.integers(len(carriers)))]
        month = int(rng.integers(0,13))
        mask = np.ones(len(raw),dtype=bool)
        gmask = np.ones(len(counts),dtype=bool)
        if airport != 'ALL':mask &= raw.Origin.eq(airport);gmask &= counts.airport.eq(airport)
        if carrier != 'ALL':mask &= raw.Reporting_Airline.eq(carrier);gmask &= counts.carrier.eq(carrier)
        if month:mask &= raw.Month.eq(month);gmask &= counts.month.eq(month)
        f = raw.loc[mask];g = counts.loc[gmask]
        complete = f.Cancelled.eq(0)&f.Diverted.eq(0)&f.ArrDelay.notna()
        expected = [int((complete&f.ArrDelay.lt(15)).sum()),int((complete&f.ArrDelay.ge(15)).sum()),
                    int(f.Cancelled.sum()),int(f.Diverted.sum())]
        expected.append(len(f)-sum(expected))
        assert expected == g[outcome_cols].sum().astype(int).tolist()
        assert len(f) == g.n.sum()
    for key,lo,hi in [('morning_06_08',6,8),('evening_18_20',18,20)]:
        f=raw.loc[hour.between(lo,hi)]
        known=(f.Cancelled.eq(1)|f.Diverted.eq(1)|f.ArrDelay.notna())
        bad=f.Cancelled.eq(1)|f.Diverted.eq(1)|f.ArrDelay.ge(15)
        assert abs(bad.sum()/known.sum()-summary[key]['disruption_rate'])<1e-12
    payload=json.loads((ROOT/'results/explorer_data.json').read_text())
    browser=pd.DataFrame(payload['rows'],columns=payload['columns'])
    pd.testing.assert_frame_equal(browser,counts,check_dtype=False)
    assert payload['minimum_denominator']==100
    article=(ROOT/'index.qmd').read_text()
    assert '@@' not in article
    assert f"{len(raw):,}" in article
    assert not re.search(r'NLSY|\bNLS\b|PSID|C0000100|0\.068',article)
    for name in ['plotly.min.js','explorer.js','explorer-data.js']:
        assert (ROOT/'assets'/name).is_file()
    assert (ROOT/'assets/explorer.js').read_text()==(ROOT/'code/explorer.js').read_text()
    assert (ROOT/'figures/hourly_preview.png').is_file()
    print('PASS: 12 months, source checksum, unique flight keys, outcome reconciliation.')
    print('PASS: 80 independent filter checks; fixed-window rates; browser payload matches counts.')
    print('PASS: article substitutions, no old-post data, local scripts and preview present.')


if __name__=='__main__':
    main()
