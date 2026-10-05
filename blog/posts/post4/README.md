# Blog Post 4: Eating Out vs. Eating In

Author: Rui Bao

## Research question
Did U.S. food-away-from-home prices rise faster than food-at-home prices between January 2015 and December 2024?

## Reproduce
1. Place this folder at `blog/posts/post4` inside the 6400-rb Quarto website.
2. Install R, Quarto (bundled with RStudio), and these packages:
   `install.packages(c("readr", "dplyr", "ggplot2", "knitr"))`
3. Open `index.qmd` in RStudio and click Render, or run from the website root:
   `quarto render blog/posts/post4/index.qmd`
4. With the supplied snapshots, no data download is needed. If a raw CSV is absent, the code downloads that series from FRED and records the URL and retrieval time. To deliberately refresh a series, remove its CSV and matching `.source.txt` file, then render with internet access.
5. For the whole website, render from its root so that navigation and the blog listing update. This project uses `docs` as the website output directory. Inspect the published page after deploying through the existing GitHub Pages workflow.

## Organization
- `index.qmd`: complete article and analysis code; numerical prose is generated from results.
- `data/raw/`: original FRED CSV snapshots and source/retrieval records.
- `figures/`: three programmatically saved PNG figures.
- `results/monthly_analysis.csv`: monthly CPI, rebased index, and 12-month inflation.
- `results/cumulative_changes.csv`: January 2015 to December 2024 changes.
- `results/series_dictionary.csv`: series IDs, categories, and source URLs.
- `results/sessionInfo.txt`: R version and package information from the latest render.

## Data and definitions
Source: U.S. Bureau of Labor Statistics CPI-U, U.S. city average, monthly, not seasonally adjusted; retrieved through FRED.

| FRED ID | Category |
| --- | --- |
| CUUR0000SAF11 | Food at home |
| CUUR0000SEFV | Food away from home |
| CUUR0000SAF111 | Cereals and bakery products |
| CUUR0000SAF112 | Meats, poultry, fish and eggs |
| CUUR0000SEFJ | Dairy and related products |
| CUUR0000SAF113 | Fruits and vegetables |
| CUUR0000SAF114 | Nonalcoholic beverages and beverage materials |
| CUUR0000SAF115 | Other food at home |

Full source pages follow `https://fred.stlouisfed.org/series/SERIES_ID`.
Food at home is a grocery-price measure, not a complete measure of the cost of cooking. Food away from home is broader than a single restaurant type.

Downloaded dates: January 2014–December 2024. Displayed analysis: January 2015–December 2024. The extra year supplies denominators for 2015 year-over-year changes. This fixed historical window is not a latest-data claim.

Rebased index = 100 * CPI(t) / CPI(January 2015).
Year-over-year inflation = 100 * (CPI(t) / CPI(t-12) - 1).
Cumulative change = 100 * (CPI(December 2024) / CPI(January 2015) - 1).

The script requires every expected monthly observation for all eight series and stops on missing, duplicate, or nonpositive observations. It does not interpolate. Series are already official published aggregates, so no person-level survey weights are applied. Category growth rates are not expenditure-weighted contributions. All computed tables and figures are written by code.

## Submission
After publishing and checking the live page, submit BOTH:
- Blog: https://ruibao1129.github.io/6400-rb/blog/posts/post4/
- Repository: https://github.com/ruibao1129/6400-rb

These are intended submission destinations; local rendering does not publish them.
