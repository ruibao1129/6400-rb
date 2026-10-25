"""Download official monthly BTS files and retain the three NYC origin airports.

Run: python code/acquire.py --cache /path/outside/repository
National archives are cached outside the repository; only the NYC subset is saved.
"""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
YEAR = 2025
URL = ('https://www.transtats.bts.gov/PREZIP/'
       'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip')
COLS = ['FlightDate', 'Month', 'DayofMonth', 'DayOfWeek', 'Reporting_Airline',
        'Flight_Number_Reporting_Airline', 'Origin', 'Dest', 'CRSDepTime',
        'DepTime', 'DepDelay', 'ArrDelay', 'Cancelled', 'Diverted']


def checksum(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def month_data(month, cache):
    archive = cache / f'{YEAR}_{month}.zip'
    # The initial exploratory January download uses a padded filename.
    padded = cache / f'{YEAR}_{month:02d}.zip'
    if not archive.exists() and padded.exists():
        archive = padded
    url = URL.format(year=YEAR, month=month)
    if not archive.exists():
        subprocess.run(['curl', '--fail', '--location', '--retry', '3',
                        '--connect-timeout', '30', '--max-time', '300',
                        '--silent', '--show-error', url, '-o', str(archive)], check=True)
    selected, national_rows = [], 0
    with zipfile.ZipFile(archive) as z:
        member = next(n for n in z.namelist() if n.lower().endswith('.csv'))
        with z.open(member) as stream:
            for frame in pd.read_csv(stream, usecols=COLS, chunksize=100000):
                national_rows += len(frame)
                selected.append(frame.loc[frame.Origin.isin(['JFK', 'LGA', 'EWR'])].copy())
    data = pd.concat(selected, ignore_index=True)
    assert data.Month.eq(month).all()
    record = {'month': month, 'url': url, 'archive_sha256': checksum(archive),
              'national_rows': national_rows, 'nyc_rows': len(data)}
    print(f'{YEAR}-{month:02d}: {national_rows:,} national / {len(data):,} NYC records', flush=True)
    return data, record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda m: month_data(m, args.cache), range(1, 13)))
    data = pd.concat([r[0] for r in results], ignore_index=True)
    keys = ['FlightDate', 'Reporting_Airline', 'Flight_Number_Reporting_Airline', 'Origin', 'Dest', 'CRSDepTime']
    assert not data.duplicated(keys).any(), 'Duplicate flight keys: investigate before analysis.'
    assert set(data.Month) == set(range(1, 13))
    data = data.sort_values(keys).reset_index(drop=True)
    target = ROOT / 'data/bts_nyc_2025.csv.gz'
    target.parent.mkdir(exist_ok=True)
    data.to_csv(target, index=False, compression={'method': 'gzip', 'mtime': 0})
    manifest = {'year': YEAR, 'source': 'BTS Reporting Carrier On-Time Performance (1987-present)',
                'source_table': 'https://www.transtats.bts.gov/TableInfo.asp?QO_fu146_anzr=b0-gvzr&gnoyr_VQ=FGJ',
                'origin_airports': ['EWR', 'JFK', 'LGA'], 'columns': COLS,
                'subset_sha256': checksum(target), 'subset_rows': len(data),
                'monthly_sources': [r[1] for r in results]}
    (ROOT / 'data/source_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    lookup = ROOT / 'data/carriers.csv'
    lookup_url = 'https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_haVdhR_PNeeVRef'
    if not lookup.exists():
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                        '--max-time', '60', lookup_url, '-o', str(lookup)], check=True)
    manifest['carrier_lookup'] = {'url': lookup_url, 'sha256': checksum(lookup)}
    (ROOT / 'data/source_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Saved {len(data):,} NYC records to {target.name}', flush=True)


if __name__ == '__main__':
    main()
