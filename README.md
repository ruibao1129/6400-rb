# Rui Bao — Computational Methods Blog

[Published website](https://ruibao1129.github.io/6400-rb/)

## Find an assignment

| Assignment | Article | Code and replication instructions |
| --- | --- | --- |
| Post 1: Simpson’s paradox | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post1/) | [Source folder and README](blog/posts/post1/) |
| Post 2: NHL scoring and wins | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post2/) | [Start here: Post 2 README](blog/posts/post2/README.md) |
| Post 3: College wage premium | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post3/) | [Source folder and README](blog/posts/post3/) |
| Post 4: Food prices | [Read](https://ruibao1129.github.io/6400-rb/blog/posts/post4/) | [Source folder and README](blog/posts/post4/) |

## Repository layout

- `blog/posts/postN/`: the source article (`index.qmd`), analysis code, and assignment-specific README. Start here when reviewing an assignment.
- Data, figures, and calculated results are documented in each assignment's README. Post 3 requires an independently obtained IPUMS extract.
- `docs/`: generated website output for GitHub Pages; these HTML files are not the analysis source.
- `_quarto.yml`: website configuration.

For replication, follow the relevant post's README. To render one article from the repository root, run `quarto render blog/posts/post2/index.qmd` (replace `post2` as needed).
