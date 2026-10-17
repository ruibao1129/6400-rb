# Run from blog/posts/post5. Existing snapshots are reused; no API key is needed.
# Call fetch_data(refresh = TRUE) only when deliberately replacing the snapshots.
fetch_data <- function(refresh = FALSE) {
  dir.create('data/raw', recursive = TRUE, showWarnings = FALSE)
  manifest_path <- 'data/raw/sources.csv'
  manifest <- if (file.exists(manifest_path)) read.csv(manifest_path, stringsAsFactors = FALSE) else data.frame()
  base <- 'https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/'
  for (table in c('b25064', 'b25070', 'boundaries')) {
    boundary <- table == 'boundaries'
    filename <- if (boundary) 'cb_2023_42_tract_500k.zip' else paste0(table, '_philadelphia.dat')
    destination <- file.path('data/raw', filename)
    if (file.exists(destination) && !refresh) next
    url <- if (boundary) paste0('https://www2.census.gov/geo/tiger/GENZ2023/shp/', filename) else paste0(base, 'acsdt5y2023-', table, '.dat')
    temporary <- tempfile(fileext = if (boundary) '.zip' else '.dat')
    old_timeout <- getOption('timeout'); options(timeout = max(old_timeout, 300))
    tryCatch(download.file(url, temporary, mode = 'wb', quiet = TRUE),
             finally = options(timeout = old_timeout))
    if (boundary) {
      stopifnot(nrow(unzip(temporary, list = TRUE)) > 0)
      stopifnot(file.copy(temporary, destination, overwrite = TRUE))
      processing <- 'Original Pennsylvania boundary ZIP'
    } else {
      lines <- readLines(temporary, warn = FALSE)
      stopifnot(grepl('^GEO_ID[|]', lines[1]))
      keep <- grepl('^1400000US42101[0-9]{6}[|]|^0500000US42101[|]', lines)
      stopifnot(sum(keep) > 1)
      writeLines(c(lines[1], lines[keep]), destination)
      processing <- 'Unmodified header and Philadelphia tract/county rows; other geographies omitted'
    }
    entry <- data.frame(file = filename, source_url = url,
      retrieved_utc = format(Sys.time(), '%Y-%m-%dT%H:%M:%SZ', tz = 'UTC'),
      processing = processing, source_md5 = unname(tools::md5sum(temporary)),
      snapshot_md5 = unname(tools::md5sum(destination)))
    if (nrow(manifest)) manifest <- manifest[manifest$file != filename, , drop = FALSE]
    manifest <- rbind(manifest, entry)
    write.csv(manifest, manifest_path, row.names = FALSE)
    unlink(temporary)
  }
  invisible(manifest)
}
