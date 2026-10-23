"""Fixed-specification PSID trial; only aggregate results leave private/."""
from pathlib import Path
import json
import sqlite3
import numpy as np
import pandas as pd
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]


def fit(df, x, y):
    X = np.column_stack([np.ones(len(df)), np.log(df[x])])
    Y = np.log(df[y].to_numpy())
    bread = np.linalg.inv(X.T @ X)
    beta = bread @ X.T @ Y
    groups, inverse = np.unique(df.mother_id, return_inverse=True)
    scores = np.zeros((len(groups), 2))
    np.add.at(scores, inverse, X * (Y - X @ beta)[:, None])
    influence = (scores @ bread)[:, 1] * np.sqrt(
        len(groups) / (len(groups)-1) * (len(df)-1)/(len(df)-2))
    se = float(np.linalg.norm(influence))
    c = t.ppf(.975, len(groups)-1)
    return dict(beta=float(beta[1]), se=se, lower=float(beta[1]-c*se),
                upper=float(beta[1]+c*se), n=len(df), mothers=len(groups)), influence


def difference(a, b):
    delta = b[0]['beta']-a[0]['beta']
    se = float(np.linalg.norm(b[1]-a[1]))
    c = t.ppf(.975, a[0]['mothers']-1)
    return dict(difference=delta, se=se, lower=float(delta-c*se),
                upper=float(delta+c*se), p=float(2*t.sf(abs(delta/se), a[0]['mothers']-1)))


def main():
    con = sqlite3.connect(ROOT/'private/selected_columns.sqlite')
    con.executescript('''
    CREATE TEMP TABLE valid AS
    SELECT ID, YEAR, YEAR-1-DEMO_BIRTH_YEAR age, EARN_TOT_RD income
    FROM person_year WHERE REFCOUPLE=1 AND EARN_TOT_ND>=0
      AND EARN_TOT_ND<9999999 AND EARN_TOT_RD>=0;
    CREATE INDEX valid_id ON valid(ID);
    CREATE TEMP TABLE links AS
    SELECT ID, MIN(REL_PAR_BM_ID) mother_id FROM person_year GROUP BY ID
    HAVING COUNT(DISTINCT REL_PAR_BM_ID)=1 AND MIN(REL_PAR_BM_ID)>0;
    CREATE TEMP TABLE averages AS
    SELECT ID, AVG(income) average_income, COUNT(*) n_years
    FROM valid WHERE age BETWEEN 30 AND 39 GROUP BY ID HAVING COUNT(*)>=3;
    CREATE TEMP TABLE singles AS
    SELECT ID, income, ROW_NUMBER() OVER
      (PARTITION BY ID ORDER BY ABS(age-35), YEAR) rn
    FROM valid WHERE age BETWEEN 30 AND 39;
    ''')
    main_df = pd.read_sql_query('''
    SELECT l.ID, l.mother_id, c.average_income child_average,
      m.average_income mother_average, cs.income child_single,
      ms.income mother_single, c.n_years child_years,m.n_years mother_years
    FROM links l JOIN averages c ON l.ID=c.ID
    JOIN averages m ON l.mother_id=m.ID
    JOIN singles cs ON l.ID=cs.ID AND cs.rn=1
    JOIN singles ms ON l.mother_id=ms.ID AND ms.rn=1
    WHERE c.average_income>0 AND m.average_income>0
      AND cs.income>0 AND ms.income>0 ORDER BY l.ID''', con)
    a = fit(main_df, 'mother_single', 'child_single')
    b = fit(main_df, 'mother_average', 'child_average')
    age_df = pd.read_sql_query('''
    WITH windows AS (
      SELECT *, CASE WHEN age BETWEEN 20 AND 24 THEN 'early'
                     WHEN age BETWEEN 30 AND 39 THEN 'middle'
                     ELSE 'later' END stage,
                CASE WHEN age BETWEEN 20 AND 24 THEN 22
                     WHEN age BETWEEN 30 AND 39 THEN 35 ELSE 45 END target
      FROM valid WHERE age BETWEEN 20 AND 24 OR age BETWEEN 30 AND 49),
    ranked AS (SELECT *,ROW_NUMBER() OVER
      (PARTITION BY ID,stage ORDER BY ABS(age-target),YEAR) rn FROM windows),
    pivoted AS (SELECT ID,
      MAX(CASE WHEN stage='early' THEN income END) early,
      MAX(CASE WHEN stage='middle' THEN income END) middle,
      MAX(CASE WHEN stage='later' THEN income END) later
      FROM ranked WHERE rn=1 GROUP BY ID)
    SELECT l.ID,l.mother_id,m.average_income mother_average,p.early,p.middle,p.later
    FROM links l JOIN averages c ON l.ID=c.ID
    JOIN averages m ON l.mother_id=m.ID JOIN pivoted p ON l.ID=p.ID
    WHERE m.average_income>0 AND p.early>0 AND p.middle>0 AND p.later>0
    ORDER BY l.ID''', con)
    ages = {s:fit(age_df, 'mother_average', s) for s in ['early','middle','later']}
    report = dict(single_year=a[0], multiyear=b[0], average_minus_single=difference(a,b),
                  mean_years=dict(child=float(main_df.child_years.mean()),mother=float(main_df.mother_years.mean())),
                  age_comparison={s:v[0] for s,v in ages.items()},
                  middle_minus_early=difference(ages['early'],ages['middle']),
                  later_minus_early=difference(ages['early'],ages['later']),
                  later_minus_middle=difference(ages['middle'],ages['later']))
    main_df.to_pickle(ROOT/'private/main_trial.pkl')
    age_df.to_pickle(ROOT/'private/age_trial.pkl')
    (ROOT/'results/summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
