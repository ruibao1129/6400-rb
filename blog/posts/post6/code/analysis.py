"""SQL parent-child matching, income measurement, IGE estimates, and figures.

Run from any working directory: python code/analysis.py
All derived numbers and the article are regenerated from the saved raw inputs.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import sqlite3

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "results" / "private" / "mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

GREEN, BLUE, ORANGE = "#2A9D8F", "#355C7D", "#F4A261"
DEMO_IGE, DEMO_LOADINGS = 0.40, np.array([0.5, 0.5, 1.0])
RAW, RESULTS, FIGURES = ROOT / "data/raw", ROOT / "results", ROOT / "figures"
MOTHER_IDS = ["R0155400", "R0312300", "R0482600", "R0782101", "R1024001",
              "R1410701", "R1778501", "R2141601", "R2350301", "R2722501",
              "R2971401", "R3279401", "R3559001", "R3897101", "R4295101",
              "R4982801", "R5626201", "R6364601", "R6909701"]
MOTHER_YEARS = list(range(1978, 1994)) + [1995, 1997, 1999]
CHILD_IDS = ["Y0309200", "Y0610500", "Y0904800", "Y1151700", "Y1386700",
             "Y1638400", "Y1908700", "Y2224100", "Y2573900", "Y2921600",
             "Y3291400", "Y3631700", "Y4240000", "Y4561200"]
DATE_IDS = {2014: "Y2990502", 2016: "Y3360902", 2018: "Y4000802", 2020: "Y4310402"}

MATCH_SQL = """
CREATE TABLE matches AS
SELECT c.child_id, c.mother_id, c.birth_year,
       c.sex, m.birth_year AS mother_birth_year
FROM children AS c
JOIN mothers AS m ON c.mother_id = m.mother_id;
"""
CHILD_AVG_SQL = """
SELECT child_id, AVG(real_income) AS child_avg,
       COUNT(DISTINCT income_year) AS child_years
FROM child_income
WHERE age BETWEEN 30 AND 39
GROUP BY child_id
HAVING COUNT(DISTINCT income_year) >= 3
"""


def read_inputs(con):
    c = pd.read_csv(RAW / "children.csv")
    m = pd.read_csv(RAW / "mothers.csv")
    dates = pd.read_csv(RAW / "child_dates.csv").set_index("C0000100")
    assert c.C0000100.is_unique and m.R0000100.is_unique and dates.index.is_unique
    children = c[["C0000100", "C0000200", "C0005700", "C0005400"]].rename(columns={
        "C0000100": "child_id", "C0000200": "mother_id", "C0005700": "birth_year", "C0005400": "sex"})
    mother_extract = pd.DataFrame({"mother_id": m.R0000100, "birth_year": 1900 + m.R0000500, "sex": m.R0214800})
    children.to_sql("children", con, index=False, if_exists="replace")
    mother_extract.to_sql("mother_extract", con, index=False, if_exists="replace")
    con.executescript("""
    CREATE TABLE mothers AS
    SELECT m.mother_id,m.birth_year FROM mother_extract m
    WHERE m.sex=2 AND EXISTS (SELECT 1 FROM children c WHERE c.mother_id=m.mother_id);
    """)
    con.executescript("CREATE UNIQUE INDEX child_key ON children(child_id); CREATE UNIQUE INDEX mother_key ON mothers(mother_id);")
    con.executescript(MATCH_SQL)
    assert con.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == len(c)
    unmatched = con.execute("SELECT COUNT(*) FROM children c LEFT JOIN mothers m ON c.mother_id=m.mother_id WHERE m.mother_id IS NULL").fetchone()[0]
    assert unmatched == 0

    # The first ten child questions explicitly name the calendar year in the codebook.
    # Starting in 2014, the wording uses the year before the actual interview.
    child_rows, date_audit = [], []
    for wave, variable in zip(range(1994, 2021, 2), CHILD_IDS):
        reference = pd.Series(wave - 1, index=c.index, dtype="float64")
        if wave in DATE_IDS:
            interview_year = c.C0000100.map(dates[DATE_IDS[wave]])
            reference = (interview_year - 1).where(interview_year > 0)
            date_audit.append({"wave": wave, "valid_dates": int((interview_year > 0).sum()),
                               "actual_year_differs_from_wave": int(((interview_year > 0) & (interview_year != wave)).sum())})
        child_rows.append(pd.DataFrame({"child_id": c.C0000100, "wave": wave,
                                       "income_year": reference, "nominal": c[variable]}))
    child_raw = pd.concat(child_rows, ignore_index=True)
    mother_raw = pd.concat([pd.DataFrame({"mother_id": m.R0000100, "income_year": year,
                                         "nominal": m[variable]})
                            for variable, year in zip(MOTHER_IDS, MOTHER_YEARS)], ignore_index=True)
    child_raw.to_sql("child_reports", con, index=False, if_exists="replace")
    mother_raw.to_sql("mother_reports", con, index=False, if_exists="replace")
    monthly = pd.read_csv(ROOT / "data/cpi_monthly.csv", parse_dates=["observation_date"])
    monthly["year"] = monthly.observation_date.dt.year
    counts = monthly.groupby("year").CPIAUCNS.count()
    assert counts.eq(12).all()
    cpi = monthly.groupby("year", as_index=False).CPIAUCNS.mean().rename(columns={"CPIAUCNS": "cpi"})
    base = float(cpi.loc[cpi.year.eq(2019), "cpi"].iloc[0])
    cpi["factor"] = base / cpi.cpi
    cpi.to_sql("cpi", con, index=False, if_exists="replace")
    cpi.to_csv(RESULTS / "annual_cpi.csv", index=False)
    con.executescript("""
    CREATE TABLE child_income AS
    WITH ranked AS (
      SELECT r.*, ROW_NUMBER() OVER (
        PARTITION BY child_id, income_year ORDER BY wave DESC
      ) AS report_rank
      FROM child_reports r
      WHERE nominal >= 0 AND income_year BETWEEN 1978 AND 2020
    )
    SELECT r.child_id, c.mother_id, r.wave, CAST(r.income_year AS INTEGER) AS income_year,
           r.income_year-c.birth_year AS age, r.nominal,
           r.nominal*p.factor AS real_income
    FROM ranked r JOIN children c ON r.child_id=c.child_id
    JOIN cpi p ON r.income_year=p.year
    WHERE r.report_rank=1;
    CREATE UNIQUE INDEX child_year_key ON child_income(child_id,income_year);
    CREATE TABLE mother_income AS
    SELECT r.mother_id, r.income_year, r.income_year-m.birth_year AS age,
           r.nominal, r.nominal*p.factor AS real_income
    FROM mother_reports r JOIN mothers m ON r.mother_id=m.mother_id
    JOIN cpi p ON r.income_year=p.year
    WHERE r.nominal >= 0;
    CREATE UNIQUE INDEX mother_year_key ON mother_income(mother_id,income_year);
    """)
    pd.DataFrame(date_audit).to_csv(RESULTS / "interview_date_audit.csv", index=False)
    mapping = []
    for variable, year in zip(MOTHER_IDS, MOTHER_YEARS):
        mapping.append({"generation": "mother", "variable": variable, "wave": year+1,
                        "reference_rule": str(year), "date_variable": ""})
    for wave, variable in zip(range(1994,2021,2),CHILD_IDS):
        mapping.append({"generation": "child", "variable": variable, "wave": wave,
                        "reference_rule": "actual interview year - 1" if wave in DATE_IDS else str(wave-1),
                        "date_variable": DATE_IDS.get(wave, "")})
    pd.DataFrame(mapping).to_csv(ROOT / "data/variable_map.csv", index=False)
    return {"raw_children": len(c), "raw_mothers":con.execute("SELECT COUNT(*) FROM mothers").fetchone()[0],
            "original_main_respondents":len(m),"unmatched": unmatched}


def construct_sample(con):
    # Aggregate each generation before matching. Joining two person-year tables
    # directly would multiply rows and change the implicit observation weights.
    con.execute("CREATE TABLE child_avgs AS " + CHILD_AVG_SQL)
    con.executescript("""
    CREATE TABLE mother_avgs AS
    SELECT mother_id, AVG(real_income) AS mother_avg,
           COUNT(DISTINCT income_year) AS mother_years
    FROM mother_income WHERE age BETWEEN 30 AND 39
    GROUP BY mother_id HAVING COUNT(DISTINCT income_year)>=3;
    CREATE TABLE child_single AS
    WITH ranked AS (
      SELECT *, ROW_NUMBER() OVER (PARTITION BY child_id ORDER BY ABS(age-35),income_year) AS rn
      FROM child_income WHERE age BETWEEN 30 AND 39
    ) SELECT child_id, real_income AS child_single, age AS child_single_age,
             income_year AS child_single_year FROM ranked WHERE rn=1;
    CREATE TABLE mother_single AS
    WITH ranked AS (
      SELECT *, ROW_NUMBER() OVER (PARTITION BY mother_id ORDER BY ABS(age-35),income_year) AS rn
      FROM mother_income WHERE age BETWEEN 30 AND 39
    ) SELECT mother_id, real_income AS mother_single, age AS mother_single_age,
             income_year AS mother_single_year FROM ranked WHERE rn=1;
    CREATE TABLE early_single AS
    WITH ranked AS (
      SELECT *, ROW_NUMBER() OVER (PARTITION BY child_id ORDER BY ABS(age-22),income_year) AS rn
      FROM child_income WHERE age BETWEEN 20 AND 24
    ) SELECT child_id, real_income AS early_single, age AS early_age,
             income_year AS early_year FROM ranked WHERE rn=1;
    CREATE TABLE candidates AS
    SELECT a.*, c.child_avg,c.child_years,m.mother_avg,m.mother_years,
           cs.child_single,cs.child_single_age,cs.child_single_year,
           ms.mother_single,ms.mother_single_age,ms.mother_single_year
    FROM matches a JOIN child_avgs c ON a.child_id=c.child_id
    JOIN mother_avgs m ON a.mother_id=m.mother_id
    JOIN child_single cs ON a.child_id=cs.child_id
    JOIN mother_single ms ON a.mother_id=ms.mother_id;
    CREATE TABLE matched AS
    SELECT * FROM candidates
    WHERE mother_avg>0 AND child_avg>0 AND mother_single>0 AND child_single>0;
    CREATE TABLE lifecycle AS
    SELECT m.*,e.early_single,e.early_age,e.early_year
    FROM matched m JOIN early_single e ON m.child_id=e.child_id WHERE e.early_single>0;
    """)
    main = pd.read_sql_query("SELECT * FROM matched ORDER BY child_id", con)
    life = pd.read_sql_query("SELECT * FROM lifecycle ORDER BY child_id", con)
    assert main.child_id.is_unique and life.child_id.is_unique
    assert len(main) > 100 and len(life) > 100
    assert main.mother_years.ge(3).all() and main.child_years.ge(3).all()
    assert set(life.child_id).issubset(set(main.child_id))
    for table, idname, avgs, output in [("child_income", "child_id", "child_avgs", "child_avg"),
                                       ("mother_income", "mother_id", "mother_avgs", "mother_avg")]:
        long = pd.read_sql_query(f"SELECT * FROM {table} WHERE age BETWEEN 30 AND 39",con)
        expected = long.groupby(idname).real_income.agg(["mean", "count"])
        expected = expected[expected["count"]>=3]
        actual = pd.read_sql_query(f"SELECT * FROM {avgs}",con).set_index(idname)
        assert np.allclose(expected["mean"].sort_index(), actual[output].sort_index())
    main.to_csv(RESULTS / "private/matched_analysis.csv", index=False)
    life.to_csv(RESULTS / "private/lifecycle_analysis.csv", index=False)
    flow = [
        ("Unique children in downloaded extract", con.execute("SELECT COUNT(*) FROM children").fetchone()[0]),
        ("Linked to a mother", con.execute("SELECT COUNT(*) FROM matches").fetchone()[0]),
        ("At least 3 valid income years in their thirties", con.execute("SELECT COUNT(*) FROM child_avgs").fetchone()[0]),
        ("Both generations have at least 3 valid income years", len(pd.read_sql_query("SELECT * FROM candidates",con))),
        ("Positive averages and positive selected single years", len(main)),
        ("Also positive selected child income in early twenties", len(life)),
    ]
    pd.DataFrame(flow,columns=["step","children"]).to_csv(RESULTS/"sample_flow.csv",index=False)
    return main, life


def fit_ige(frame, x_col, y_col, controls=False):
    x, y = np.log(frame[x_col].to_numpy()), np.log(frame[y_col].to_numpy())
    X = np.column_stack([np.ones(len(frame)), x])
    if controls:
        birth = frame.birth_year.to_numpy()-1980
        mother_birth = frame.mother_birth_year.to_numpy()-1960
        X = np.column_stack([X, frame.sex.eq(2).astype(float), birth, birth**2, mother_birth])
    bread = np.linalg.inv(X.T@X)
    b = bread @ X.T @ y
    residual = y-X@b
    groups, inv = np.unique(frame.mother_id.to_numpy(), return_inverse=True)
    scores = np.zeros((len(groups),X.shape[1]))
    np.add.at(scores,inv,X*residual[:,None])
    correction = len(groups)/(len(groups)-1)*(len(frame)-1)/(len(frame)-X.shape[1])
    influence = (scores@bread)[:,1]*np.sqrt(correction)
    se = float(np.sqrt(np.sum(influence**2)))
    critical = float(student_t.ppf(.975,len(groups)-1))
    result = {"beta":float(b[1]),"se":se,"lower":float(b[1]-critical*se),
              "upper":float(b[1]+critical*se),"n":len(frame),"mothers":len(groups),
              "intercept":float(b[0])}
    return result, influence


def compare(a, b, influence_a, influence_b):
    delta = b["beta"]-a["beta"]
    se = float(np.sqrt(np.sum((influence_b-influence_a)**2)))
    critical = float(student_t.ppf(.975,a["mothers"]-1))
    return {"difference":delta,"se":se,"lower":delta-critical*se,"upper":delta+critical*se,
            "p":float(2*student_t.sf(abs(delta/se),a["mothers"]-1))}


def style():
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,
        "text.color":BLUE,"axes.labelcolor":BLUE,"xtick.color":BLUE,
        "ytick.color":BLUE,"axes.edgecolor":BLUE,"axes.titleweight":"bold",
        "axes.spines.top":False,"axes.spines.right":False,"savefig.facecolor":"white"})


def save(fig, stem):
    for extension in ["png","svg"]:
        fig.savefig(FIGURES/f"{stem}.{extension}",dpi=200,bbox_inches="tight")
    plt.close(fig)


def figures(main,life,models):
    style()
    fig,ax=plt.subplots(figsize=(9,5.3))
    ax.scatter(main.mother_avg,main.child_avg,s=20,color=GREEN,alpha=.35,edgecolors="none",label="One dot per adult child")
    x=np.geomspace(main.mother_avg.min(),main.mother_avg.max(),150)
    result=models["multi_year"]
    ax.plot(x,np.exp(result["intercept"])*x**result["beta"],color=BLUE,lw=2.6,label="Fitted log–log relationship")
    bins=main.assign(bin=pd.qcut(main.mother_avg,8,duplicates="drop"))
    binned=bins.groupby("bin",observed=True).agg(mother=("mother_avg",lambda v:np.exp(np.log(v).mean())),
                                               child=("child_avg",lambda v:np.exp(np.log(v).mean())),n=("child_id","size"))
    ax.scatter(binned.mother,binned.child,s=75,color=ORANGE,edgecolors=BLUE,lw=.7,zorder=4,label="Grouped geometric means")
    binned.reset_index(drop=True).to_csv(RESULTS/"binned_income.csv",index=False)
    ax.set_xscale("log");ax.set_yscale("log")
    ticks=[1000,5000,10000,25000,50000,100000]
    for axis in [ax.xaxis,ax.yaxis]:
        axis.set_major_locator(matplotlib.ticker.FixedLocator(ticks))
        axis.set_major_formatter(FuncFormatter(lambda v,p:f"${v/1000:g}k"))
        axis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel("Mother’s average annual earnings, ages 30–39")
    ax.set_ylabel("Child’s average annual earnings, ages 30–39")
    ax.set_title("Matching families is only the first step",loc="left",pad=19)
    ax.grid(color=GREEN,alpha=.12);ax.set_axisbelow(True)
    ax.legend(frameon=False,loc="upper left",fontsize=9)
    fig.subplots_adjust(bottom=.24)
    fig.text(.125,.025,f"NLSY79 mother–child sample: {len(main):,} children. Both axes use logarithmic scales.\nAmounts are 2019 dollars; each average uses at least three distinct income years.",fontsize=9,color=BLUE)
    save(fig,"01_matched_earnings")

    fig,ax=plt.subplots(figsize=(9,4.0))
    for y,key,label,col in [(1,"single_year","One year per generation",GREEN),(0,"multi_year","Several years per generation",BLUE)]:
        r=models[key]
        ax.errorbar(r["beta"],y,xerr=[[r["beta"]-r["lower"]],[r["upper"]-r["beta"]]],fmt="o",color=col,capsize=5,ms=10,lw=2.5)
        ax.annotate(f'{r["beta"]:.3f}',(r["beta"],y),xytext=(0,15),textcoords="offset points",ha="center",color=col,fontweight="bold")
    ax.axvline(0,color=ORANGE,lw=1.4,linestyle="--")
    ax.set_yticks([1,0],["One year per generation","Several years per generation"])
    ax.set_ylim(-.6,1.6);ax.set_xlabel("Estimated intergenerational earnings elasticity")
    ax.set_title("Does one paycheck tell the whole story?",loc="left",pad=17)
    ax.grid(axis="x",color=GREEN,alpha=.12)
    fig.subplots_adjust(bottom=.30)
    fig.text(.125,.025,f"Same {len(main):,} children in both models. Dots are estimates; whiskers are 95% intervals,\nclustered by mother. Single years are the available years nearest age 35.",fontsize=9,color=BLUE)
    save(fig,"02_single_vs_average")

    fig,axes=plt.subplots(1,2,figsize=(12,4.5),gridspec_kw={"width_ratios":[1.0,1.1]})
    ax=axes[0]
    for y,key,col in [(1,"early_child",GREEN),(0,"mature_child",BLUE)]:
        r=models[key]
        ax.errorbar(r["beta"],y,xerr=[[r["beta"]-r["lower"]],[r["upper"]-r["beta"]]],fmt="o",color=col,capsize=4,ms=9,lw=2)
        ax.annotate(f'{r["beta"]:.3f}',(r["beta"],y),xytext=(0,13),textcoords="offset points",ha="center",color=col)
    ax.set_yticks([1,0],["Child: early twenties","Child: thirties"])
    ax.set_title(f"Observed: the same {len(life):,} children",loc="left",fontsize=12,pad=20)
    ax.set_xlabel("Estimated IGE");ax.set_ylim(-.6,1.6)
    ax.axvline(0,color=ORANGE,ls="--",lw=1);ax.grid(axis="x",color=GREEN,alpha=.12)
    ax=axes[1]
    for y,value,col in zip([2,1,0],DEMO_IGE*DEMO_LOADINGS,[GREEN,ORANGE,BLUE]):
        ax.plot([0,value],[y,y],color=col,lw=3)
        ax.scatter([value],[y],color=col,s=85,zorder=3)
        ax.text(value+.015,y,f"{value:.2f}",va="center",color=col,fontweight="bold")
    ax.set_yticks([2,1,0],["One early-career year","Several early-career years","One midcareer year"])
    ax.set_xlim(0,.52);ax.set_ylim(-.6,2.6)
    ax.set_xlabel("Implied slope when the true IGE is 0.40")
    ax.set_title("Illustration: true lifetime IGE = 0.40",loc="left",fontsize=12,pad=20)
    ax.grid(axis="x",color=GREEN,alpha=.12)
    fig.subplots_adjust(wspace=.95,bottom=.32)
    fig.text(.125,.025,"Left: mother’s multiyear income is held fixed; whiskers are mother-clustered 95% intervals.\nRight: early earnings reveal half of the long-run log-earnings differences; midcareer earnings reveal all.\nThe right panel is an analytical illustration, not NLS data or an estimated lifetime benchmark.",fontsize=9,color=BLUE)
    save(fig,"03_age_and_measurement")


def main():
    for folder in [RESULTS/"private",FIGURES]:folder.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(RESULTS/"private/analysis.sqlite")
    # Rebuild deterministically instead of appending to a previous run.
    con.close();(RESULTS/"private/analysis.sqlite").unlink(missing_ok=True)
    con=sqlite3.connect(RESULTS/"private/analysis.sqlite")
    summary=read_inputs(con)
    main_sample,life=construct_sample(con)
    models,inf={},{}
    for key,data,x,y in [("single_year",main_sample,"mother_single","child_single"),
                          ("multi_year",main_sample,"mother_avg","child_avg"),
                          ("early_child",life,"mother_avg","early_single"),
                          ("mature_child",life,"mother_avg","child_single")]:
        models[key],inf[key]=fit_ige(data,x,y)
    contrasts={"multi_minus_single":compare(models["single_year"],models["multi_year"],inf["single_year"],inf["multi_year"]),
               "mature_minus_early":compare(models["early_child"],models["mature_child"],inf["early_child"],inf["mature_child"])}
    sensitivities=[]
    for key,x,y in [("single_year","mother_single","child_single"),("multi_year","mother_avg","child_avg")]:
        result,_=fit_ige(main_sample,x,y,controls=True)
        sensitivities.append({"specification":"Sex and birth-cohort controls","model":key,**result})
        cap=main_sample.copy()
        # This is explicitly a sensitivity of the final income measures, not annual reconstruction.
        cap[x]=cap[x].clip(upper=100000);cap[y]=cap[y].clip(upper=100000)
        result,_=fit_ige(cap,x,y)
        sensitivities.append({"specification":"Final income measures capped at $100k (2019 dollars)","model":key,**result})
    pd.DataFrame(sensitivities).to_csv(RESULTS/"sensitivity.csv",index=False)
    pd.DataFrame([{"model":k,**v} for k,v in models.items()]).to_csv(RESULTS/"ige_estimates.csv",index=False)
    pd.DataFrame([{"contrast":k,**v} for k,v in contrasts.items()]).to_csv(RESULTS/"contrasts.csv",index=False)
    summary.update({"main_n":len(main_sample),"main_mothers":int(main_sample.mother_id.nunique()),
        "life_n":len(life),"life_mothers":int(life.mother_id.nunique()),
        "birth_min":int(main_sample.birth_year.min()),"birth_max":int(main_sample.birth_year.max()),
        "mother_years_mean":float(main_sample.mother_years.mean()),"child_years_mean":float(main_sample.child_years.mean()),
        "mother_years_min":int(main_sample.mother_years.min()),"mother_years_max":int(main_sample.mother_years.max()),
        "child_years_min":int(main_sample.child_years.min()),"child_years_max":int(main_sample.child_years.max()),
        "mother_age_mean":float(main_sample.mother_single_age.mean()),"child_age_mean":float(main_sample.child_single_age.mean()),
        "early_age_mean":float(life.early_age.mean()),"late_age_mean":float(life.child_single_age.mean()),
        "models":models,"contrasts":contrasts,
        "ten_percent_exact":float(100*(1.10**models["multi_year"]["beta"]-1))})
    (RESULTS/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [RAW/"children.csv",RAW/"mothers.csv",RAW/"child_dates.csv",ROOT/"data/cpi_monthly.csv"]}
    (RESULTS/"input_sha256.json").write_text(json.dumps(hashes,indent=2)+"\n")
    example=pd.DataFrame({"case":["Early single year","Early multiyear average","Midcareer single year"],
                          "true_ige":DEMO_IGE,"age_loading":DEMO_LOADINGS})
    example["implied_slope"]=example.true_ige*example.age_loading
    example.to_csv(RESULTS/"analytical_example.csv",index=False)
    figures(main_sample,life,models)
    # SQL shown in the post is the same SELECT/JOIN and aggregation used above.
    (ROOT/"code/matching.sql").write_text(MATCH_SQL+"\n"+CHILD_AVG_SQL+";\n")
    template=(ROOT/"code/article_template.qmd.in").read_text()
    values={"RAW_CHILDREN":f'{summary["raw_children"]:,}',"RAW_MOTHERS":f'{summary["raw_mothers"]:,}',
        "MAIN_N":f'{len(main_sample):,}',"MAIN_MOTHERS":f'{summary["main_mothers"]:,}',
        "LIFE_N":f'{len(life):,}',"SINGLE":f'{models["single_year"]["beta"]:.3f}',
        "MULTI":f'{models["multi_year"]["beta"]:.3f}',"IGE_SHARE":f'{100*models["multi_year"]["beta"]:.1f}',"EARLY":f'{models["early_child"]["beta"]:.3f}',
        "LATE":f'{models["mature_child"]["beta"]:.3f}',"PERCENT":f'{summary["ten_percent_exact"]:.1f}',
        "M_YEARS":f'{summary["mother_years_mean"]:.1f}',"C_YEARS":f'{summary["child_years_mean"]:.1f}',
        "MULTI_LOW":f'{models["multi_year"]["lower"]:.3f}',"MULTI_HIGH":f'{models["multi_year"]["upper"]:.3f}',
        "SINGLE_LOW":f'{models["single_year"]["lower"]:.3f}',"SINGLE_HIGH":f'{models["single_year"]["upper"]:.3f}',
        "GAP":f'{contrasts["multi_minus_single"]["difference"]:.3f}',
        "GAP_LOW":f'{contrasts["multi_minus_single"]["lower"]:.3f}',"GAP_HIGH":f'{contrasts["multi_minus_single"]["upper"]:.3f}'}
    for key,value in values.items():template=template.replace("@@"+key+"@@",value)
    assert "@@" not in template
    (ROOT/"index.qmd").write_text(template)
    con.commit();con.close()
    print(json.dumps(summary,indent=2))


if __name__=="__main__":main()
