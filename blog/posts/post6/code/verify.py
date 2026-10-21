"""Independent checks of estimates, clustered SEs, generated files, and joins."""
from pathlib import Path
import json
import re
import sqlite3
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    stats=json.loads((ROOT/"results/summary.json").read_text())
    con=sqlite3.connect(ROOT/"results/private/analysis.sqlite")
    matched=pd.read_sql_query("SELECT * FROM matched",con)
    for label,xcol,ycol in [("single_year","mother_single","child_single"),
                            ("multi_year","mother_avg","child_avg")]:
        x=np.log(matched[xcol].to_numpy());y=np.log(matched[ycol].to_numpy())
        dx=x-x.mean();dy=y-y.mean()
        slope=np.dot(dx,dy)/np.dot(dx,dx)
        residual=dy-slope*dx
        score=pd.DataFrame({"mother":matched.mother_id,"score":dx*residual})
        cluster=score.groupby("mother").score.sum()
        n,g=len(x),len(cluster)
        se=np.sqrt((g/(g-1)*(n-1)/(n-2))*np.dot(cluster,cluster))/np.dot(dx,dx)
        assert np.isclose(slope,stats["models"][label]["beta"],atol=1e-10)
        assert np.isclose(se,stats["models"][label]["se"],atol=1e-10)
    assert con.execute("SELECT COUNT(*) FROM matches").fetchone()[0]==stats["raw_children"]
    assert con.execute("SELECT COUNT(*)-COUNT(DISTINCT child_id) FROM matches").fetchone()[0]==0
    assert con.execute("SELECT COUNT(*) FROM child_income WHERE nominal<0 OR real_income<0").fetchone()[0]==0
    assert con.execute("SELECT COUNT(*) FROM matched WHERE mother_years<3 OR child_years<3").fetchone()[0]==0
    assert con.execute("SELECT COUNT(*) FROM lifecycle").fetchone()[0]==stats["life_n"]
    assert (matched[["mother_single","child_single","mother_avg","child_avg"]]>0).all().all()
    article=(ROOT/"index.qmd").read_text()
    assert "@@" not in article
    for src in re.findall(r"!\[[^\]]*\]\(([^)]+)\)",article):
        assert (ROOT/src).is_file(),src
    for stem in ["01_matched_earnings","02_single_vs_average","03_age_and_measurement"]:
        svg=(ROOT/f"figures/{stem}.svg").read_text().lower()
        assert "#7b2cbf" not in svg
        assert "#355c7d" in svg
        assert "#2a9d8f" in svg
        assert "#f4a261" in svg
    con.close()
    print("PASS: unique SQL links, matching samples, income construction, independent OLS and clustered SEs, article assets, and updated palette.")


if __name__=="__main__":main()
