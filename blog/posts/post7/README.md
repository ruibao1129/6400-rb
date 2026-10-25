# Blog7: Is an Early Flight Worth the Alarm?

## Review entry points

- `index.qmd`: generated English article and interactive Plotly views.
- `code/analyze.py`: outcome definitions, additive counts, and route-composition check.
- `code/explorer.js`: browser filters and Plotly rendering.
- `results/summary.json`: all article statistics.
- `data/source_manifest.json`: original monthly BTS URLs, row counts, and checksums.
- `data/bts_nyc_2025.csv.gz`: cached public NYC records needed for replication.

Source: [BTS Reporting Carrier On-Time Performance](https://www.transtats.bts.gov/TableInfo.asp?QO_fu146_anzr=b0-gvzr&gnoyr_VQ=FGJ).
This is 2025 domestic reporting-carrier data from JFK, LGA and EWR, not current
flight information, an international-flight census, or marketing-airline data.
The official unique-carrier lookup is cached as `data/carriers.csv`; its URL and
checksum are in the manifest. Do not confuse reporting airlines with ticket brands.

## Reproduce with the included subset

Use Python 3.12 with the pinned dependencies (a virtual environment is recommended).
From `blog/posts/post7/`:

```bash
python -m pip install -r requirements.txt
python code/analyze.py
python code/build.py
python code/verify.py
```

Then, from the repository root:

```bash
quarto render blog/posts/post7/index.qmd
```

The website was tested with Quarto 1.6.42 (bundled with RStudio). Use one Quarto
version consistently across the site. If changing versions, regenerate the full
website so the HTML and shared `docs/site_libs/` scripts stay compatible.

Edit prose in `code/article_template.qmd.in` and widget text in
`code/widget.html.in`, not only the generated `index.qmd`. Edit interactive logic
in `code/explorer.js`, not its generated copy in `assets/`. Rebuild afterward.
Numeric prose is filled programmatically from `results/summary.json`.

## Rebuild from the original source

Optional: national monthly archives total roughly 340 MB compressed. Cache them
outside this repository. From this post folder:

```bash
python code/acquire.py --cache /absolute/path/outside/repository/bts_2025
python code/analyze.py
python code/build.py
python code/verify.py
```

The downloader uses `curl`, caches the 12 national ZIP files, reads selected
columns in chunks, retains the three NYC origin airports, checks flight keys and
month coverage, and saves only the public NYC subset. Archive SHA-256 checksums
record the exact downloads used. A source revision should be documented rather
than silently mixed with an older subset.

## Definitions and comparisons

- One row is one reporting-carrier flight record, not one passenger.
- Use `CRSDepTime`, scheduled local departure time; `2400` is assigned to hour 00.
  Invalid scheduled clock values are counted and excluded, not silently repaired.
- On-time arrival: not cancelled/diverted, reported `ArrDelay < 15` minutes.
- Delayed arrival: not cancelled/diverted, reported `ArrDelay >= 15` minutes.
- Cancellation and diversion: explicit BTS indicators, not inferred from blanks.
- Unclassified: none of the four above. Do not replace missing arrival delay by zero.
- Disruption rate = (delayed arrival + cancelled + diverted) / classified outcomes.
- Arrival-delay rate = delayed / reported non-cancelled, non-diverted arrivals.
- Cancellation rate = cancelled / all scheduled records.
- Departure-delay rate = departure delay >=15 / reported non-cancelled departures.
- Browser filters add counts before calculating rates. No averages of subgroup
  percentages. Hourly/heatmap cells need >=100 eligible records; outcome bars need
  >=100 scheduled records. Blank is not zero. Summary totals are explicitly shown
  even when no hourly cells meet the plotting threshold.
- Morning 06:00–08:59 and evening 18:00–20:59 windows were set before inspection.
  Secondary check: same origin, destination, reporting airline and month, with
  >=30 classified outcomes per window. Weights are pooled counts, identical for
  the two rates. This is a descriptive composition check, not a causal adjustment.
  The retained records cover 16.3% of all classified annual outcomes, not every route.

## Interaction and limitations

Airport and reporting-airline filters affect all views. The month filter affects
the hourly and outcome plots; the calendar intentionally keeps all 12 months.
The outcome selector affects the hourly and calendar plots, not the five-category
outcome breakdown. Calendar clicks select a month; Reset restores the defaults.
Incompatible airlines are removed when changing airports. Sparse or empty groups
produce gaps and an explanatory message, not invented rates.

Plotly JavaScript is bundled locally by the pinned Python package. No CDN,
authentication, API key, live data request or backend is needed to use the charts.
The static PNG is only the blog-listing preview. Open the rendered article in a
browser for the interactive views. The data compare historical flight records,
not passenger risk, causal benefits, fares, or missed-connection costs.
No confidence intervals or significance tests are provided. Plotting thresholds
do not establish significance, precise neighboring-hour rankings, or uncertainty
about future flights.
