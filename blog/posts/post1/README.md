# Blog Post 1: Simpson's Paradox

Author: Rui Bao

## Purpose
Explain how Hospital A can have higher survival rates for both mild and severe cases but a lower overall survival rate because the hospitals treat different proportions of those cases.

## Data source
All patient counts are hypothetical teaching data constructed for this example, not real hospital observations. No external dataset or download is required.

| Hospital | Mild survivors / patients | Severe survivors / patients | Overall survivors / patients |
| --- | --- | --- | --- |
| A | 90 / 100 | 300 / 900 | 390 / 1000 |
| B | 760 / 900 | 30 / 100 | 790 / 1000 |

## File organization
This small example keeps the article, hypothetical input counts, and base R plotting code together in `index.qmd`. This is the equivalent of separate code and data folders; no separate raw-data file is needed.

The website's `_quarto.yml` sets `docs` as its output directory. Rendering produces `docs/blog/posts/post1/index.html` and a figure asset under that page's `index_files/figure-html` directory. The chart is calculated and saved by the rendering process, rather than pasted manually.

## Reproduce
1. Clone or download https://github.com/ruibao1129/6400-rb.
2. Install R and Quarto (available with recent RStudio installations).
3. In the R console, install the rendering dependencies if needed:
   `install.packages(c("knitr", "rmarkdown"))`
4. Open the website project in RStudio, open `blog/posts/post1/index.qmd`, and click Render. Alternatively, run from the repository root:
   `quarto render blog/posts/post1/index.qmd`
5. Inspect the table, grouped bar chart, and weighted-average equations in the rendered page. No additional analysis packages are needed: the chart uses base R.

Percentages are calculated from survivor counts divided by group totals. Displayed percentages are rounded to one decimal place where needed. Weighted-average equations use exact fractions, giving overall survival rates of 39% for A and 79% for B.

## Published article
https://ruibao1129.github.io/6400-rb/blog/posts/post1/
