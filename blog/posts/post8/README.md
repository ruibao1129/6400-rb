# Blog8: Was Your Delivery Slow—or Was Your Sample Unlucky?

## Start here

- `index.qmd`: generated English article; four connected views.
- `code/acquire.py`: download the pinned official source into an ignored private directory.
- `code/analyze.py`: clean real orders, bootstrap means, repeat coverage experiments, simulate a null.
- `code/build.py`: generate prose, Plotly assets and static fallback figures.
- `code/verify.py`: independently recalculate the key displayed quantities.
- `results/summary.json`, `coverage.csv`: aggregate data and experiment results.
- `results/coverage_intervals.csv`: simulated intervals, not original orders.
- `data/source_manifest.json`: source URL, exact revision and archive SHA-256.

## Official source and license

Meituan and INFORMS TSL published the [research challenge dataset](https://github.com/meituan/Meituan-INFORMS-TSL-Research-Challenge).
Read its [license](https://github.com/meituan/Meituan-INFORMS-TSL-Research-Challenge/blob/main/License.txt),
[original data dictionary](https://github.com/meituan/Meituan-INFORMS-TSL-Research-Challenge/blob/main/TSL-Meituan%20challenge_background%20and%20data_20240321.pdf),
and [October 2024 clarifications](https://github.com/meituan/Meituan-INFORMS-TSL-Research-Challenge/blob/main/tsl_meituan_2024_data_report_20241015.pdf).
This research was supported by data provided by Meituan.

The publisher permits noncommercial research and teaching and restricts redistribution.
Raw archives, original order-level data and order-level duration extracts are NOT
included in this repository or website assets. Download directly from the publisher
to reproduce; retain its license and acknowledgment. Public outputs here are
aggregate research summaries and Monte Carlo statistics, not the source dataset.

## Reproduce

Use Python 3.12 and the versions in `requirements.txt`, plus Quarto 1.6.42 (RStudio).
Clone the whole website repository, keeping the folder structure.
From `blog/posts/post8/`:

```sh
python -m pip install -r requirements.txt
python code/acquire.py
python code/analyze.py
python code/build.py
python code/verify.py
```

From the website repository root:

```sh
quarto render blog/posts/post8/index.qmd
```

Downloading requires public network access and `curl`. The original ZIP is about
39 MB. It is stored in ignored `data/private/`; never force-add it to Git.
The downloader pins the published revision in the manifest and checks its digest.
To intentionally analyze a later release, archive your private cache, specify
`--revision COMMIT`, rerun all steps, and document the revision change.
Analysis needs roughly 100–300 MB memory and can take a few minutes. Displaying
the built article needs no network service, API key or Python backend.

Edit prose in `code/article_template.qmd.in` and `code/widget.html.in`; edit chart
logic in `code/explorer.js`. Rebuild afterward. Do not edit only generated copies.

## Unit of observation and cleaning

The source contains 654,343 waybills for 568,546 unique orders. A rejected waybill
may be a repeated assignment of the same order; it is not another completed order.
Sequentially retain accepted waybills (`is_courier_grabbed == 1`), exclude prebooks,
and require positive creation/arrival timestamps with arrival after creation.
Assert unique `order_id` among accepted rows rather than arbitrarily deduplicating.
Duration = (`arrive_time` − `platform_order_time`)/60 minutes. Source `dt` supplies
dates; timezone conversion is unnecessary for elapsed seconds.

Exclusions: 85,797 rejected waybills, 22,181 accepted prebooks, and 1 nonpositive or
missing duration. The resulting 546,364 orders are dated Oct 17–24, 2022. The
unweighted mean gives each retained order equal weight. This is not an all-China
estimate, a contemporary service audit, or a customer-weighted experience measure.
No courier coordinates, customer locations or original identifiers are published.

Mean 29.6467 min; median 27.9; 10.9487% exceed 45 min. All positive long waits are
retained, including 81 over 120 min (maximum 645.42). Timestamps cannot be
independently validated against operational logs. A fixed sensitivity exclusion
of durations over 120 changes the mean to 29.6228 min; it is not the main analysis.
The histogram's last bar pools 120+ minutes, so no observations disappear visually.

## Simulation design (not real additional deliveries)

Seed 20261029; n = 20, 100, 400; confidence = 90, 95, 99%. These settings are fixed,
not tuned for significance. Draw 400 IID observations WITH replacement from the
retained empirical population; smaller displayed samples are nested prefixes.
The teaching analyst sees only that displayed sample. The full reference mean is
used to evaluate coverage, not to construct the sample's interval or null test.

1. Bootstrap: within each displayed sample, draw 1,999 equally sized replacement
   samples and calculate means. Use NumPy's linear quantile interpolation for a
   two-sided percentile interval. Do not mistake it for a prediction interval.
2. Coverage: independently draw 1,000 new samples at each n from the full empirical
   reference distribution. Bootstrap EACH new sample from scratch, 1,999 times.
   Count intervals containing the known reference mean. Every generated interval
   is saved. The plot shows the FIRST 60, not selected successes. Monte Carlo SE
   is sqrt(coverage × (1−coverage)/1,000). Coverage is conditional on this IID
   reference experiment, not a guarantee about other populations or actual orders.
3. Null test: H0 mean = 30 versus H1 mean > 30. Shift the displayed sample to mean
   30 BEFORE resampling. Generate 9,999 replacement samples; statistic = mean−30.
   One-sided p = (1 + count(T_null >= T_observed))/(9,999+1). This is a bootstrap
   approximation, not an exact distribution-free test. The approximate 95th null
   percentile illustrates the fixed alpha=.05 rejection boundary. Histogram tail
   coloring is binned; numerical p uses all unbinned simulated statistics.

The two-sided CI and one-sided test are NOT inversions of each other. The confidence
control affects only the bootstrap CI and coverage display. It does not change
the one-sided 5% test. All experiments are precomputed; controls switch saved
results, not rerun a live random-number generator. Increasing bootstrap repetitions
reduces numerical noise; it does not add original observations or fix selection.

Actual orders share couriers, merchants and demand conditions. IID resampling is
an explicit teaching experiment, NOT a valid uncertainty guarantee for a cluster
of one customer's consecutive orders. No current trend or causal service change
is estimated. Thirty minutes is illustrative, not a claimed contractual promise.

## Expected results

95% coverage for n=20,100,400: 92.8%, 95.5%, 95.0%, respectively (1,000 experiments).
Default n=100 mean 29.8647, CI [27.5901,32.2399], one-sided p=.5452.
No evidence of a mean above 30 in this displayed sample is NOT proof of equality.

Bootstrap method: [SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
Accuracy/finite-sample caveats: [Hesterberg (2015)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4784504/).

Submit the public article URL and GitHub repository after rendering and publishing.
The local preview is not a submission URL. Rendering does not commit or push.
