# Post 5: Does Cheaper Rent Mean More Affordable Housing?

Author: Rui Bao

## Start here

- **Article:** [published Post 5](https://ruibao1129.github.io/6400-rb/blog/posts/post5/) (available after the website is deployed).
- **Article source:** [index.qmd](index.qmd).
- **Analysis entry point:** [code/analysis.R](code/analysis.R), called by the article when rendered.
- **Download and snapshot code:** [code/fetch_data.R](code/fetch_data.R).
- **Main findings:** [results/summary.csv](results/summary.csv) and [results/rent_groups.csv](results/rent_groups.csv).

Question: Are Philadelphia census tracts with lower rents also places where residents face less rent burden?

## Reproduce in RStudio

1. Clone or download the whole [6400-rb repository](https://github.com/ruibao1129/6400-rb). Open `6400-rb.Rproj` at the repository root.
2. Install R, Quarto, and the following R packages once, using the R console:

   ```r
   install.packages(c("sf", "dplyr", "readr", "ggplot2", "ragg", "knitr", "rmarkdown"))
   ```

3. Open `blog/posts/post5/index.qmd` and click **Render**. The default execution directory must remain the document's folder. Saved snapshots are included, so no API key or data download is needed for an ordinary render.
4. Inspect the page at `docs/blog/posts/post5/index.html`. The three map/chart panels appear in two figure files. The generated HTML is not the analysis source.

Alternatively, run in a **Terminal at the repository root**:

```sh
quarto render blog/posts/post5/index.qmd
```

To run only the analysis in an R console starting at the repository root:

```r
setwd("blog/posts/post5")
source("code/analysis.R")
```

Do not run the `setwd()` line again if already inside the Post 5 folder. To render outside the website, copy the entire `post5` folder and render `index.qmd` there; the output will be a local `index.html` instead of the website's `docs/` path.

## File guide

| Location | Contents and purpose |
| --- | --- |
| [index.qmd](index.qmd) | Article and computed inline numbers; sources the R analysis. |
| [code/](code/) | Two readable R scripts: fetch snapshots and analyze/map them. |
| [data/raw/](data/raw/) | Unmodified Philadelphia rows extracted from two official national tables, the original Pennsylvania boundary ZIP, and retrieval/provenance manifest. |
| [data/clean/tract_analysis.csv](data/clean/tract_analysis.csv) | All 408 tracts, including exclusion reasons, estimates, and margins of error. |
| [data/clean/philadelphia_tracts.gpkg](data/clean/philadelphia_tracts.gpkg) | Joined tract geometry and key statistics, in EPSG:26918 (meters). |
| [figures/](figures/) | Side-by-side rent and burden maps plus the grouped comparison chart. |
| [results/](results/) | City summary, four rent groups, sensitivity checks, coverage audit, and R session information. |

## Data provenance

Data: **2019–2023 ACS five-year estimates**, not 2023-only observations or current rental listings. Geography: Philadelphia County, Pennsylvania (state 42, county 101), which is coterminous with Philadelphia city.

- [B25064 official bulk table](https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-b25064.dat): median gross rent and its margin of error.
- [B25070 official bulk table](https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-b25070.dat): rent-to-household-income categories and their margins of error.
- [2023 Pennsylvania cartographic boundaries](https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_42_tract_500k.zip): 1:500,000 simplified census tract polygons. Map boundaries are for visualization, not parcel-level or walking-distance analysis.
- [Snapshot provenance](data/raw/sources.csv): exact URLs, UTC retrieval times, full downloaded source MD5 checksums, subset snapshot MD5 checksums, and selection description.

The bulk ACS files do not require an API key. To keep the repository small, the fetch script retains the original header and unmodified rows whose GEO_ID starts with `1400000US42101` (tracts), plus `0500000US42101` (county). The snapshots are subsets, not complete national source files. The code downloads the national files again if a snapshot is missing; it does not scrape a website interface.

To deliberately refresh inputs, run **from this post folder**:

```r
source("code/fetch_data.R")
fetch_data(refresh = TRUE)
source("code/analysis.R")
```

Refreshing requires internet access and may reflect source revisions. Preserve the supplied snapshots if exact replication is desired. The normal analysis verifies their MD5 checksums before use.

## Definitions and calculations

- Gross rent includes contract rent plus tenant-paid utility/fuel costs. All money amounts are in 2023 dollars.
- The ACS tables already contain survey-weighted estimates. No additional microdata weights should be applied.
- In bulk-file notation, `B25070_E007:E010` are the four categories at **30% or more** of income. Their sum is the numerator.
- The denominator is `B25070_E002:E010`, equivalent to total `E001` minus the `E011` "not computed" category. We exclude not-computed ratios; we do not treat them as unburdened. Countywide, 21,010 units are in that category.
- Median rent is `B25064_E001`. Negative Census sentinel values are converted to missing; negative rent values are never mapped.
- Both maps and the main grouped analysis use tracts with a positive available median rent and at least **100 estimated households** with computed ratios. This is an estimated population threshold, not a survey sample-size threshold, and it does not guarantee precision.
- Groups contain equal numbers of tracts sorted by estimated median rent. Ties are broken deterministically by GEOID. Group shares are the sum of burdened households divided by the sum of eligible households, not the unweighted mean of tract percentages. These are groups of places, not groups of individual households classified by their own rent.
- Maps use fixed dollar and percentage bins and the same geography; gray denotes excluded tracts. City Hall is an approximate orientation marker, not a neighborhood boundary.

### Uncertainty

Published ACS margins of error are at the 90% level. For sums, the code uses the square root of the sum of squared component MOEs. For a subset proportion `p = numerator/denominator`, the approximate percentage-point MOE is:

`100 * sqrt(numerator_moe^2 - p^2 * denominator_moe^2) / denominator`.

If the radicand is negative, it uses the Census ratio fallback with a plus sign. These approximations use published MOEs, not replicate estimates, and do not model all covariance. Group intervals are conditional on estimated rent-group assignments and do not account for uncertainty in those assignments. No formal spatial clustering or causal hypothesis test is performed.

Sources: [Census MOE guidance](https://www.census.gov/data/academy/webinars/2020/calculating-margins-of-error-acs.html) and [ACS guidance on five-year estimates](https://www.census.gov/programs-surveys/acs/guidance/estimates.html).

## Expected results and checks

The supplied snapshots should produce:

- **408** Philadelphia tracts joined one-to-one; **376** included and **32** excluded.
- Included tracts cover **99.2%** of the county's estimated households with computed ratios.
- Countywide burden rate: **52.0%**, from the county table rather than averaging tract percentages.
- Four groups of **94 tracts**: burden shares **58.8%, 54.2%, 53.8%, 41.0%**, from lowest to highest median rent.
- Lowest/highest group difference: **17.8 percentage points**.
- Median tract-level burden MOE in the included set: about **16.4 percentage points**. Do not read the map as a precise ranking of adjacent tracts.

`results/household_threshold_sensitivity.csv` recomputes groups with thresholds of 0, 100, 200, and 300 estimated households (always requiring a positive denominator). `results/precision_sensitivity.csv` excludes tracts with a burden MOE greater than 20 percentage points and rebuilds the groups. Both retain the lower-rent/higher-burden direction.

The code checks unique GEOIDs, matching tract/table coverage, valid geometry, exact category-sum accounting, and numerator/denominator consistency. All figures and result tables are saved programmatically. Session package versions are in [results/sessionInfo.txt](results/sessionInfo.txt).

## Scope of interpretation

This is a descriptive comparison of places and current residents during 2019–2023. It does not estimate the effect of moving, explain rent-setting, control for household composition or housing quality, or identify individual households in need of assistance. Tracts do not coincide exactly with named neighborhoods. The 30% threshold is an analytical convention, not a full household budget assessment.

## Submission

After committing, pushing, and checking deployment, submit:

- Blog: https://ruibao1129.github.io/6400-rb/blog/posts/post5/
- Code and replication: https://github.com/ruibao1129/6400-rb/tree/main/blog/posts/post5
