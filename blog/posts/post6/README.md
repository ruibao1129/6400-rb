# Blog Post 6: Matching generations with SQL and PSID

## Start here

- Article source: `index.qmd`.
- Published article: https://ruibao1129.github.io/6400-rb/blog/posts/post6/
- Complete analysis: `code/analysis.py`.
- Fixed specification and limitations: `code/ANALYSIS_PLAN.txt`.
- Aggregate results: `results/summary.json`; charts: `figures/`.

This article uses PSID-SHELF 1968–2021 V2.1. Start with the files listed above;
the repository contains one current analysis version.

## Obtain the data

Personally download PSID-SHELF 1968–2021 V2.1 from the official ICPSR study:
https://www.icpsr.umich.edu/sites/psid/view/studies/194322
Complete the provider's registration and terms process. Obtain the full archive
`ICPSR_194322-V2.1.zip`; do not unzip its 7.9GB long file manually.

The extractor streams nine selected columns from the nested long-format archive:
`ID`, `YEAR`, `PNUM`, `REFCOUPLE`, `DEMO_BIRTH_YEAR`, `EARN_TOT_ND`,
`EARN_TOT_RD`, `REL_PAR_BM_ID`, `REL_PAR_BF_ID`.
Keep the raw archive outside the repository. Extracted person-level records go
only into ignored `private/`; never upload or redistribute them.

## Run in order

From `blog/posts/post6/`, install the requirements in a Python environment:

```bash
python -m pip install -r requirements.txt
python code/extract.py /absolute/path/to/ICPSR_194322-V2.1.zip
python code/analysis.py
python code/make_figures.py
```

Then, from the repository root:

```bash
quarto render blog/posts/post6/index.qmd
```

The extractor can resume an interrupted extraction of the identical archive.
Do not change source archives while reusing its database. For a fresh extraction,
rename the existing private directory and start a new one.
SQLite requires window-function support (available in modern Python builds).

## What each step does

1. `extract.py`: selects columns, checks unique person/year keys, creates
   `private/selected_columns.sqlite` and `results/coverage_report.json`.
2. `analysis.py`: links biological mothers and children using SQL; constructs
   age-window income averages and nearest-age observations; estimates five
   log-log slopes and paired mother-clustered confidence intervals. Saves private
   analysis samples and only aggregate estimates to `results/summary.json`.
3. `make_figures.py`: creates all three published charts from those aggregates.
4. Quarto: generates `docs/blog/posts/post6/index.html` and updates blog navigation.

After extraction, run the article's Python blocks in order in one fresh session
from this post folder, including the expandable comparison-sample join. They
create their own temporary tables and reproduce the main sample (3,094 children)
and both published slopes. The complete analysis script additionally constructs
the three-age sample and calculates clustered and paired uncertainty.

## Definitions and cautions

- Income age = survey year − 1 − birth year; earnings refer to the prior tax year.
- `EARN_TOT_RD` is individual labor earnings in 2024 dollars, not family income.
- The official construction code uses wage plus business income after 1993 and
  explicitly excludes farm labor from that point. This is a comparability limit.
- Income is observed for reference persons/spouses; other adults are not covered
  by this selected measure. Do not interpret missing income as zero.
- Exclude missing/negative earnings and standardized nominal topcodes 9,999,999.
  Retain valid zeros in averages; require positive measures for logarithms.
- Both generations need ≥3 observed income years at ages 30–39. Single income
  is nearest age 35, ties earlier; positive income is checked after selection.
- Main comparison: 3,094 children, 1,753 mothers. Single-year slope 0.0683;
  multiyear slope 0.0902. Both use the identical sample.
- Age comparison: a separate fixed sample of 1,608 children, 1,116 mothers, with
  positive observations nearest ages 22, 35, 45. Maternal average is fixed.
  Slopes: 0.0142, 0.0425, 0.0506.
- The age sample need not be a subset of the main sample: the main comparison
  additionally requires a positive maternal single-year observation.
- Unweighted selected-sample OLS, not population or causal estimates. No observed
  lifetime-income truth is available. All three primary paired 95% intervals
  include zero; a suggestive age pattern is not proof of lifecycle bias.

## Source attribution

PSID-SHELF is a University of Michigan project led by Fabian Pfeffer, with data
and construction files compiled by Davis Daumler. Use the citation and terms
provided with ICPSR study 194322, V2.1. The archive includes documentation and
construction code, notably `09 Create earnings generated variables.do`.
