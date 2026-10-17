# Run from blog/posts/post5, or render index.qmd from the website root.
# Packages are installed by the reader, never automatically during rendering.
needed <- c('sf', 'dplyr', 'readr', 'ggplot2', 'ragg')
missing <- needed[!vapply(needed, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop('Install required packages first: install.packages(c(', paste(sprintf('"%s"', missing), collapse = ', '), '))')
suppressPackageStartupMessages({library(sf); library(dplyr); library(readr); library(ggplot2)})
source('code/fetch_data.R')
fetch_data()
for (p in c('data/clean', 'figures', 'results')) dir.create(p, recursive = TRUE, showWarnings = FALSE)
manifest <- read.csv('data/raw/sources.csv', stringsAsFactors = FALSE)
stopifnot(all(unname(tools::md5sum(file.path('data/raw', manifest$file))) == manifest$snapshot_md5))
read_table <- function(id) read_delim(paste0('data/raw/', id, '_philadelphia.dat'), delim = '|', show_col_types = FALSE)
rent <- read_table('b25064'); burden <- read_table('b25070')
stopifnot(!anyDuplicated(rent$GEO_ID), !anyDuplicated(burden$GEO_ID), setequal(rent$GEO_ID, burden$GEO_ID))
dat <- left_join(burden, rent, by = 'GEO_ID')
# Negative Census sentinel values mean missing/suppressed, never negative dollars.
num_cols <- setdiff(names(dat), 'GEO_ID')
dat[num_cols] <- lapply(dat[num_cols], function(x) replace(x, x < 0, NA_real_))
cells <- function(kind, ids) paste0('B25070_', kind, sprintf('%03d', ids))
# B25070 category 11 is 'not computed'. Categories 2:10 are the valid denominator.
dat$eligible_households <- rowSums(dat[cells('E', 2:10)])
dat$burdened_households <- rowSums(dat[cells('E', 7:10)])
dat$eligible_moe <- sqrt(rowSums(dat[cells('M', 2:10)]^2))
dat$burdened_moe <- sqrt(rowSums(dat[cells('M', 7:10)]^2))
# ACS approximate 90% MOE for a proportion whose numerator is a subset.
# Use the ratio fallback when the subtraction produces a negative radicand.
proportion_moe <- function(n, d, nm, dm) {
  p <- n / d
  v <- nm^2 - p^2 * dm^2
  100 * sqrt(ifelse(v >= 0, v, nm^2 + p^2 * dm^2)) / d
}
dat <- dat %>% mutate(
  GEOID = sub('.*US', '', GEO_ID), median_rent = B25064_E001, rent_moe = B25064_M001,
  burden_pct = if_else(eligible_households > 0, 100 * burdened_households / eligible_households, NA_real_),
  burden_moe_pp = proportion_moe(burdened_households, eligible_households, burdened_moe, eligible_moe))
stopifnot(all(dat$burdened_households <= dat$eligible_households, na.rm = TRUE),
          all(dat$eligible_households == dat$B25070_E001 - dat$B25070_E011, na.rm = TRUE))
city <- filter(dat, GEO_ID == '0500000US42101')
tracts <- filter(dat, grepl('^1400000US', GEO_ID)) %>% mutate(
  included = !is.na(median_rent) & median_rent > 0 & !is.na(burden_pct) & eligible_households >= 100,
  exclusion_reason = case_when(is.na(median_rent) ~ 'Median rent unavailable',
    eligible_households < 100 ~ 'Fewer than 100 estimated households with computed ratio',
    is.na(burden_pct) ~ 'Burden unavailable', TRUE ~ 'Included'))
stopifnot(nrow(city) == 1, all(nchar(tracts$GEOID) == 11))
# Census boundaries and ACS data both use the 2023 tract vintage.
unzip_dir <- tempfile('tract_boundaries_'); dir.create(unzip_dir)
unzip('data/raw/cb_2023_42_tract_500k.zip', exdir = unzip_dir)
shp <- list.files(unzip_dir, pattern = '\\.shp$', full.names = TRUE)
geo <- st_read(shp, quiet = TRUE) %>% filter(COUNTYFP == '101') %>% st_transform(26918)
unlink(unzip_dir, recursive = TRUE)
stopifnot(!anyDuplicated(geo$GEOID), setequal(geo$GEOID, tracts$GEOID), all(st_is_valid(geo)))
geo <- left_join(geo, tracts, by = 'GEOID')
valid <- tracts %>% filter(included) %>% arrange(median_rent, GEOID)
# Equal numbers of tracts (not equal numbers of households); GEOID breaks rent ties.
make_groups <- function(x) {
  x %>% arrange(median_rent, GEOID) %>% mutate(rent_quartile = ntile(median_rent, 4)) %>%
    group_by(rent_quartile) %>% summarise(tract_count = n(), rent_min = min(median_rent),
      rent_max = max(median_rent), households = sum(eligible_households),
      burdened = sum(burdened_households), households_moe = sqrt(sum(eligible_moe^2)),
      burdened_moe = sqrt(sum(burdened_moe^2)), .groups = 'drop') %>%
    mutate(burden_pct = 100 * burdened / households,
      moe_pp = proportion_moe(burdened, households, burdened_moe, households_moe),
      lower = pmax(0, burden_pct - moe_pp), upper = pmin(100, burden_pct + moe_pp))
}
groups <- make_groups(valid)
sensitivity <- bind_rows(lapply(c(0, 100, 200, 300), function(cutoff) {
  make_groups(filter(tracts, !is.na(median_rent), median_rent > 0,
    !is.na(burden_pct), eligible_households > 0, eligible_households >= cutoff)) %>% mutate(min_households = cutoff)
}))
# Separate robustness check, removing tracts with very imprecise burden estimates.
precision_check <- make_groups(filter(valid, burden_moe_pp <= 20))
summary_stats <- data.frame(
  city_burden_pct = city$burden_pct, city_eligible_households = city$eligible_households,
  city_not_computed = city$B25070_E011, tracts_total = nrow(tracts), tracts_included = nrow(valid),
  tracts_excluded = sum(!tracts$included), lowest_rent_group_burden_pct = groups$burden_pct[1],
  highest_rent_group_burden_pct = groups$burden_pct[4],
  gap_pp = groups$burden_pct[1] - groups$burden_pct[4],
  median_tract_burden_moe_pp = median(valid$burden_moe_pp, na.rm = TRUE),
  included_household_share_pct = 100 * sum(valid$eligible_households) / city$eligible_households)
write_csv(tracts, 'data/clean/tract_analysis.csv')
write_csv(groups, 'results/rent_groups.csv')
write_csv(sensitivity, 'results/household_threshold_sensitivity.csv')
write_csv(precision_check, 'results/precision_sensitivity.csv')
write_csv(summary_stats, 'results/summary.csv')
write_csv(select(tracts, GEOID, included, exclusion_reason), 'results/tract_coverage.csv')
write_csv(city, 'results/city_summary.csv')
st_write(geo %>% select(GEOID, NAME, median_rent, rent_moe, burden_pct, burden_moe_pp,
  eligible_households, included), 'data/clean/philadelphia_tracts.gpkg', delete_dsn = TRUE, quiet = TRUE)
writeLines(capture.output(sessionInfo()), 'results/sessionInfo.txt')
# Discrete map legends show absolute dollar / percentage ranges, not quantiles.
geo$rent_band <- cut(ifelse(geo$included, geo$median_rent, NA), c(-Inf,1000,1250,1500,2000,Inf),
  right = FALSE, labels = c('Under $1,000','$1,000–1,249','$1,250–1,499','$1,500–1,999','$2,000+'))
geo$burden_band <- cut(ifelse(geo$included, geo$burden_pct, NA), c(-Inf,30,40,50,60,Inf),
  right = FALSE, labels = c('Under 30%','30–39%','40–49%','50–59%','60%+'))
base_theme <- theme_minimal(base_size = 12, base_family = 'sans') +
  theme(plot.title = element_text(face = 'bold', size = 16, color = '#18333b'),
    plot.subtitle = element_text(size = 11, color = '#45545b'),
    plot.caption = element_text(size = 9, color = '#58666b', hjust = 0),
    plot.title.position = 'plot', plot.caption.position = 'plot')
map_theme <- base_theme + theme(axis.title = element_blank(), axis.text = element_blank(),
  panel.grid = element_blank(), legend.position = 'bottom', legend.title = element_text(size = 10),
  legend.text = element_text(size = 9), plot.margin = margin(8,8,8,8))
# City Hall is an orientation marker, not a tract/neighborhood definition.
locator <- st_as_sf(data.frame(label = 'City Hall', lon = -75.1636, lat = 39.9526),
  coords = c('lon','lat'), crs = 4326) %>% st_transform(26918)
bb <- st_bbox(geo); x0 <- unname(bb['xmin']) + 1500; y0 <- unname(bb['ymin']) + 1500
add_orientation <- function(p) p +
  geom_sf(data = locator, inherit.aes = FALSE, shape = 21, fill = 'white', size = 2, stroke = .6) +
  geom_sf_label(data = locator, aes(label = label), inherit.aes = FALSE, size = 2.7,
    nudge_y = -1500, linewidth = 0, fill = 'white') +
  annotate('segment', x = x0, xend = x0 + 5000, y = y0, yend = y0, linewidth = .7) +
  annotate('text', x = x0 + 2500, y = y0 + 650, label = '5 km', size = 3) +
  annotate('segment', x = x0, xend = x0, y = unname(bb['ymax']) - 5000,
    yend = unname(bb['ymax']) - 2300, arrow = grid::arrow(length = grid::unit(.12,'inches'))) +
  annotate('text', x = x0, y = unname(bb['ymax']) - 1500, label = 'N', size = 3.5)
p_rent <- ggplot(geo) + geom_sf(aes(fill = rent_band), color = 'white', linewidth = .12) +
  scale_fill_manual(values = c('#e4f1f0','#acd6d0','#68b4ad','#288580','#085450'),
    drop = FALSE, na.value = '#e2e5e7', na.translate = TRUE, labels = function(x) ifelse(is.na(x), 'Not mapped', x), name = NULL) +
  guides(fill = guide_legend(nrow = 2, byrow = TRUE)) +
  labs(title = 'A. What residents pay', subtitle = 'Median monthly rent, including utilities') + map_theme
p_burden <- ggplot(geo) + geom_sf(aes(fill = burden_band), color = 'white', linewidth = .12) +
  scale_fill_manual(values = c('#fff0d9','#ffd39b','#f6a35c','#d96636','#983e2b'),
    drop = FALSE, na.value = '#e2e5e7', na.translate = TRUE, labels = function(x) ifelse(is.na(x), 'Not mapped', x), name = NULL) +
  guides(fill = guide_legend(nrow = 2, byrow = TRUE)) +
  labs(title = 'B. How much income it takes', subtitle = 'Rent-burdened share among computed ratios') + map_theme
p_rent <- add_orientation(p_rent); p_burden <- add_orientation(p_burden)
ragg::agg_png('figures/rent_and_burden_maps.png', width = 2200, height = 1500, res = 180)
grid::grid.newpage()
print(p_rent, vp = grid::viewport(x = .25, y = .54, width = .5, height = .90))
print(p_burden, vp = grid::viewport(x = .75, y = .54, width = .5, height = .90))
grid::grid.text('Philadelphia census tracts | ACS 2019–2023 five-year estimates', x = .025, y = .055,
  just = 'left', gp = grid::gpar(fontsize = 11, col = '#45545b'))
grid::grid.text(paste0('Gray: ', sum(!tracts$included), ' tracts with unavailable rent or fewer than 100 eligible households. Estimates have sampling error.'),
  x = .025, y = .025, just = 'left', gp = grid::gpar(fontsize = 10, col = '#45545b'))
dev.off()
groups$label <- paste0(c('Lowest rents','Lower-middle','Upper-middle','Highest rents'), '\n$',
  format(groups$rent_min, big.mark = ',', trim = TRUE), '–', format(groups$rent_max, big.mark = ',', trim = TRUE))
groups$label <- factor(groups$label, levels = groups$label)
p_groups <- ggplot(groups, aes(label, burden_pct)) +
  geom_col(fill = '#207c78', width = .62) +
  geom_errorbar(aes(ymin = lower, ymax = upper), width = .14, color = '#172e35') +
  geom_text(aes(y = upper + 2.5, label = sprintf('%.1f%%', burden_pct)), fontface = 'bold', size = 4.5) +
  scale_y_continuous(limits = c(0,75), breaks = seq(0,70,10), labels = function(x) paste0(x,'%'), expand = expansion(mult = c(0,.02))) +
  labs(title = 'Lower rents do not guarantee a lighter burden',
    subtitle = 'Tracts grouped by median rent; burden shares use pooled household counts',
    x = 'Tract median monthly gross rent', y = 'Households spending ≥30% of income on rent',
    caption = 'Source: ACS 2019–2023, B25064 and B25070. Each group contains 94 tracts.\nWhiskers: approximate 90% intervals, conditional on estimated rent groups.') +
  base_theme + theme(panel.grid.major.x = element_blank(), panel.grid.minor = element_blank(),
    axis.text.x = element_text(size = 11), axis.title.x = element_text(margin = margin(t = 12)))
ggsave('figures/burden_by_rent_group.png', p_groups, width = 10, height = 6, dpi = 180, bg = 'white', device = ragg::agg_png)
print(summary_stats)
