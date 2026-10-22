# Rui Bao — Computational Methods Blog

[Published website](https://ruibao1129.github.io/6400-rb/)

## Find an assignment

| Assignment | Article | Code and replication instructions |
| --- | --- | --- |
| Post 1: Simpson’s paradox | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post1/) | [Start here: Post 1 README](blog/posts/post1/README.md) |
| Post 2: NHL scoring and wins | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post2/) | [Start here: Post 2 README](blog/posts/post2/README.md) |
| Post 3: College wage premium | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post3/) | [Start here: Post 3 README](blog/posts/post3/README.md) |
| Post 4: Food prices | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post4/) | [Start here: Post 4 README](blog/posts/post4/README.md) |
| Post 5: Philadelphia rent burden | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post5/) | [Start here: Post 5 README](blog/posts/post5/README.md) |
| Post 6: Intergenerational earnings and SQL | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post6/) | [Start here: Post 6 README](blog/posts/post6/README.md) |

## Repository layout

- `blog/posts/postN/`: the source article (`index.qmd`), analysis code, and assignment-specific README. Start here when reviewing an assignment.
- Data, figures, and calculated results are documented in each assignment's README. Post 3 requires an independently obtained IPUMS extract.
- `docs/`: generated website output for GitHub Pages; these HTML files are not the analysis source.
- `6400-rb.Rproj`: open this file in RStudio to use the website project.
- `_quarto.yml`: website configuration.

Each post folder is the review entry point; its README identifies the code to run, required data, and generated results. For Post 5, begin with [the replication guide](blog/posts/post5/README.md), then [the analysis script](blog/posts/post5/code/analysis.R).

**Reviewing Posts 1–3:** start with the assignment's README in the table above, then its `index.qmd`. Each QMD contains both the article and executable R code; there is no missing standalone script. Post 1 uses explicitly hypothetical counts; Post 2 includes cached source pages and cleaned data; Post 3 requires the privately obtained IPUMS extract. `docs/` is only the generated website.

For replication, follow the relevant post's README. To render one article from the repository root, run `quarto render blog/posts/post2/index.qmd` (replace `post2` as needed).

## Other website files

`images/`, `files/`, the root QMD pages, and `styles.css` support the portfolio website. Each post README identifies its own inputs.
