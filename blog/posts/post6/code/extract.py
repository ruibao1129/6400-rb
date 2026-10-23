"""Read only selected PSID-SHELF columns; keep microdata outside the website repo."""
from pathlib import Path
import io
import sys
import json
import sqlite3
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path('/Users/baorui/Downloads/ICPSR_194322-V2.1.zip')
COLS = ['ID', 'YEAR', 'PNUM', 'REFCOUPLE', 'DEMO_BIRTH_YEAR',
        'EARN_TOT_ND', 'EARN_TOT_RD', 'REL_PAR_BM_ID', 'REL_PAR_BF_ID']


def main():
    private = ROOT / 'private'
    private.mkdir(exist_ok=True)
    target = private / 'selected_columns.sqlite'
    con = sqlite3.connect(target)
    exists = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='person_year'").fetchone()[0]
    total = con.execute('SELECT COUNT(*) FROM person_year').fetchone()[0] if exists else 0
    with zipfile.ZipFile(SOURCE) as outer:
        member = next(n for n in outer.namelist()
                      if n.endswith('PSIDSHELF_1968_2021_LONG_7.9_GB.zip'))
        with zipfile.ZipFile(io.BytesIO(outer.read(member))) as inner:
            with inner.open(inner.namelist()[0]) as stream:
                with pd.io.stata.StataReader(stream, columns=COLS,
                                             convert_categoricals=False,
                                             chunksize=50000) as reader:
                    labels = reader.variable_labels()
                    # Read label metadata once. Otherwise pandas revisits the end
                    # of a compressed Stata file for every chunk, forcing repeated
                    # decompression. Selected columns are all numeric, not strLs.
                    reader.value_labels()
                    reader._lines_read = total  # Resume only this verified source.
                    for chunk in reader:
                        chunk.to_sql('person_year', con, if_exists='append', index=False)
                        total += len(chunk)
                        if total % 100000 == 0:
                            print(f'Read {total:,} person-year records', flush=True)
    con.execute('CREATE UNIQUE INDEX IF NOT EXISTS person_year_key ON person_year(ID,YEAR)')
    report = {'source_archive': SOURCE.name, 'rows': total,
              'selected_variable_labels': {k: labels[k] for k in COLS}}
    report['survey_coverage'] = pd.read_sql_query('''
        SELECT MIN(YEAR) AS first_wave, MAX(YEAR) AS last_wave,
               COUNT(DISTINCT YEAR) AS waves, COUNT(DISTINCT ID) AS people
        FROM person_year''', con).to_dict('records')[0]
    # Earnings refer to the prior tax year, not the survey year.
    report['positive_individual_earnings_coverage'] = []
    for low, high in [(20, 24), (30, 39), (40, 49)]:
        result = pd.read_sql_query('''
            SELECT COUNT(*) AS records, COUNT(DISTINCT ID) AS people
            FROM person_year
            WHERE (YEAR - 1 - DEMO_BIRTH_YEAR) BETWEEN ? AND ?
              AND EARN_TOT_ND > 0 AND REFCOUPLE = 1''', con,
                                   params=(low, high)).to_dict('records')[0]
        report['positive_individual_earnings_coverage'].append(
            {'income_year_ages': [low, high], **result})
    con.commit()
    con.close()
    (ROOT / 'results/coverage_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
