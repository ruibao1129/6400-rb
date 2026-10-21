# Blog Post 6: Is Your First Paycheck Your Economic Destiny?

A tutorial on matching mothers and children with SQL in Python, estimating
intergenerational earnings elasticity (IGE), and explaining income measurement
and life-cycle bias.

## Read and render

`index.qmd` is the blog article. `index.html` is a rendered preview. The article
contains instructional code excerpts; `code/analysis.py` is the complete runnable
pipeline. The excerpts describe stages of that pipeline and are not a replacement
for all the preparation code.

To reproduce using the inputs included in the local delivery package:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python code/analysis.py
quarto render index.qmd
```

Tested with Python 3.12, SQLite with window-function support, and Quarto 1.6.42.
On Windows activate with `.venv\Scripts\activate`. Rendering the saved article
does not execute Python or R: all figures are already saved. The analysis runs
offline once the input CSVs and CPI cache are present.

To change prose permanently, edit `code/article_template.qmd.in`. The analysis
replaces its `@@...@@` result placeholders and regenerates `index.qmd`. Editing
only `index.qmd` will be overwritten on the next analysis run.

## Folder structure

```text
post6/
  index.qmd                  Generated article, ready for the website
  index.html                 Rendered preview
  requirements.txt
  README.md
  code/
    analysis.py              Full Python and SQL pipeline
    article_template.qmd.in  Article template (not a second Quarto page)
    matching.sql             Matching and aggregation excerpts
    acquire_inputs.py        Stage new extracts and refresh CPI if requested
    verify.py                Independent numerical and output checks
  data/
    cpi_monthly.csv          Cached official CPI series
    variable_map.csv         Income columns, waves, and year rules
    *_tagset.*               Variable selections to load in NLS Investigator
    raw/                     Original CSVs and codebooks; locally supplied
  figures/
    01_matched_earnings.*     Scatterplot and fitted association
    02_single_vs_average.*   IGE comparison and uncertainty
    03_age_and_measurement.* Empirical age check and analytical illustration
  results/
    ige_estimates.csv         Coefficients and clustered 95% intervals
    contrasts.csv            Paired differences between estimates
    sample_flow.csv          Sample-selection counts
    annual_cpi.csv            Annual averages and deflators
    interview_date_audit.csv Actual year versus survey-wave checks
    sensitivity.csv          Cohort controls and final-income cap checks
    analytical_example.csv   Explicit assumptions for the hypothetical example
    summary.json             Machine-readable article statistics
    input_sha256.json        Input fingerprints
    private/                 Rebuilt SQLite database and individual-level results
```

The local delivery package includes raw inputs for immediate replication. The
`.gitignore` keeps raw microdata, individual-level derived files, and caches out
of Git by default. The code, cached CPI, variable map/tagsets, aggregate results,
and figures are ready to track. A fresh GitHub checkout requires the NLS extracts
described below. No passwords, tokens, or restricted geographic data are used.

## Data sources and re-extraction

1. **NLSY79 Child and Young Adult, 1986–2020**, release April 17, 2023.
   Use [NLS Investigator](https://www.nlsinfo.org/investigator/) and select
   `NLSY79 Child & Young Adult`. Load `data/children_tagset.CHILDYA`, or select
   child ID `C0000100`, mother ID `C0000200`, birth year `C0005700`, sex `C0005400`,
   and all child dollar-income variables in `data/variable_map.csv`.
   The original local extract also includes race, version, and income-band
   follow-ups. These extra fields are not needed for the IGE.
2. **NLSY79, 1979–2022**, release November 12, 2024.
   Select `NLSY79 (National Longitudinal Survey of Youth 1979)`.
   Load `data/mothers_tagset.NLSY79`, or select respondent ID `R0000100`, birth
   year `R0000500`, sex `R0214800`, and all mother dollar-income variables in the
   map. Extra downloaded years are harmless. A full extract can include all
   12,686 original respondents: SQL retains only female respondents whose IDs
   occur as mother IDs in the child file. The local package already supplies
   those 4,943 mothers.
3. **Child interview-year supplement.** In the Child/Young Adult study, load
   `data/child_dates_tagset.CHILDYA`. The analysis needs `C0000100` plus
   `Y2990502` (2014), `Y3360902` (2016), `Y4000802` (2018), and `Y4310402` (2020).
   The supplied supplement also includes interview years for 2004–2012.
4. **BLS CPI-U, all items, U.S. city average, not seasonally adjusted**, series
   `CPIAUCNS`, retrieved through [FRED](https://fred.stlouisfed.org/series/CPIAUCNS),
   October 20, 2026. The cached monthly data cover 1978–2020. Each annual CPI
   is the mean of twelve months. Real earnings = nominal earnings × CPI(2019) /
   CPI(income reference year).

Choose Basic Download to obtain CSV and codebook files. To stage three downloaded
ZIPs (filenames may differ):

```bash
python code/acquire_inputs.py --children /path/children.zip --mothers /path/mothers.zip --dates /path/dates.zip
python code/analysis.py
python code/verify.py
quarto render index.qmd
```

The helper also accepts CSV paths. It copies a same-name `.cdb` when present.
Use `--refresh-cpi` only when intentionally replacing the saved CPI cache.

## Measurement choices

- Match `C0000200` (MPUBID) to `R0000100` (CASEID), retaining `C0000100` (CPUBID)
  as the child key. Unique-key checks precede the join, and SQL checks that every
  child matches exactly one mother. Do not join on names or inferred birth order.
- Income is reported annual wage and salary earnings, including commissions/tips
  as defined by each question. It excludes business income and transfers. The
  child wage question combines military earnings from 2000 onward; 1994–1998
  asks military earnings separately. This is an additional comparability limit.
- Keep dollar-report columns only. `Q15-5-A` follow-ups contain income-band codes
  and are not added to dollar amounts. Do not interpret a category value of `2`
  as two dollars.
- Negative values are survey codes and become missing. Valid zero dollar reports
  enter averages. Valid skips are not automatically recoded to zero.
- Child questions through the 2012 wave explicitly reference 1993, 1995, …, 2011
  in their codebooks. For 2014–2020 use the actual interview-year variable minus
  one, matching the question wording. Never universally substitute wave minus one.
  Mother variables used here explicitly reference the previous calendar year,
  from 1978 to 1999; later mother waves are not used in this analysis.
- Age is income reference year minus birth year: age attained by December 31,
  not age on the interview day. Maternal birth codes 57–64 become 1957–1964.
- If two child waves report the same income year, retain the latest wave among
  valid nonnegative dollar reports. The unique child-year index enforces one
  contribution per distinct year.
- Calculate each generation's arithmetic mean of real earnings within ages
  30–39, with at least three distinct valid income years. The observed years
  need not be consecutive. These are averages of available years, not ten-year
  complete histories. Maternal averages have 3–8 observations; child averages
  have 3–4 in the delivered sample. Mothers' histories end in 1999 in this design,
  so coverage within the age window differs by birth cohort.
- Select one year nearest age 35 within the same age window, breaking ties toward
  the earlier income year. Select the nearest year from all valid reports, even
  if zero. Do not skip a zero to find a positive replacement. Require positive
  selected single-year and average earnings for both generations, then use this
  identical 286-child sample for the two primary log–log regressions.
- For the age diagnostic, hold mothers' average earnings fixed and compare child
  income nearest age 22 in ages 20–24 with the child's selected thirties income.
  Requiring positive early income yields the same 221 children for both age
  regressions. This is a selected subsample, not the full main sample.

## Estimation and interpretation

The primary model is unweighted OLS of log child earnings on log mother earnings,
with an intercept. Each child receives one observation. Siblings share a mother,
so standard errors cluster by mother, with the finite-sample correction
`G/(G-1) * (N-1)/(N-K)` and Student-t critical values with `G-1` degrees of freedom.
The code estimates paired coefficient differences from the difference in
cluster influence functions, retaining the covariance between the estimates.

`sensitivity.csv` reports the same sample with child sex and birth-cohort controls,
and a separate cap of $100,000 (2019 dollars) on final income measures. The latter
is a simple robustness check, not a reconstruction of topcoded annual reports.
Topcoded reports otherwise remain as provided in the public files.

In the delivered analysis, the single-year IGE is approximately 0.095 and the
multiyear IGE approximately 0.162. Their difference is not statistically precise.
The within-child age diagnostic is nearly flat and does not establish the
direction or size of empirical life-cycle bias.

The right panel of Figure 3 therefore gives an explicitly hypothetical analytical
demonstration. Let lifetime log earnings satisfy `c* = a + 0.40 p* + u`. Suppose
early log earnings equal an age intercept plus `0.5 c*` and independent zero-mean
temporary noise, while midcareer log earnings use loading 1. Holding the parent's
long-run measure fixed, the expected regression slopes are 0.20 and 0.40.
Averaging independent early log-earnings observations reduces noise but retains
the loading 0.5. With zero temporary shocks the same loading also holds exactly
for the log of average earnings. The illustration is a measurement model, not
simulated survey observations or an estimated lifetime benchmark.

No model estimates a causal effect. The selected, unweighted sample is not a
national population estimate. Attrition, missing reports, positivity restrictions,
maternal work interruptions, changing income definitions, and topcoding remain
limitations. Averaging and approximate age alignment cannot remove every source
of life-cycle or measurement bias.

## Sources

- [NLS mother–child ID definitions](https://nlsinfo.org/content/cohorts/nlsy79-children/other-documentation/codebook-supplement/appendix-h-identification).
- [Official linkage tutorial](https://www.nlsinfo.org/content/getting-started/introduction-to-the-nls/tutorials-and-videos/linking-nlsy79-mothers-and-their-children).
- [NLS Child/Young Adult income definitions and topcoding](https://www.nlsinfo.org/content/cohorts/nlsy79-children/topical-guide/income/introduction).
- [BLS CPI-U via FRED](https://fred.stlouisfed.org/series/CPIAUCNS).
- Haider, Steven, and Gary Solon. 2006. “Life-Cycle Variation in the Association
  between Current and Lifetime Earnings.” *American Economic Review* 96(4):
  1308–1320. [DOI](https://doi.org/10.1257/aer.96.4.1308).

## Website placement

Place the entire folder at `blog/posts/post6/` in the website project. Render the
post and blog listing, inspect the published figures, then commit and push the
source plus the generated `docs` output using the site's existing workflow.
The article's GitHub link points to that exact project folder.

Plot marks use green `#2A9D8F`, muted deep blue `#355C7D`, and orange `#F4A261`.
