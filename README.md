# Quarto report template for bioinformatics

> **Status: rough prototype (v0.1).** It renders and its checks pass on the two machines listed under Requirements. It has had no outside users, its CI has not yet run, and several design choices are still open. Read [Limits](#limits) before relying on it.

A Quarto book template for analysis reports in bioinformatics. Its house style keeps measurement and interpretation apart: every chapter before the synthesis describes and counts, and one labelled chapter interprets. The template ships a format layer, a starter book, a rendered gallery of every element on synthetic data, a style guide, automated style checks with tests, and instructions for AI agents.

## What you get

| Path | Purpose |
|---|---|
| `_quarto.yml`, `_quarto-*.yml` | Book settings, the HTML format, and three render profiles |
| `theme/`, `filters/` | The theme, and Lua filters for image loading and draft questions |
| `_setup.R`, `_setup.py`, `_params.yml` | Shared helpers and analysis parameters, read by every chapter |
| `index.qmd`, `chapters/`, `reference/` | The starter book: chapter skeletons, a synthesis shell, and reference pages |
| `gallery/` | Ten chapters that show every element on synthetic data |
| `STYLE-GUIDE.md` | The house style |
| `tools/style/`, `style-checks.toml` | Style checks and their shared word lists |
| `scripts/` | The check runner, the scaffold script, and optional git hooks |
| `tests/` | Tests for the helpers, the checks, and the scaffold |
| `AGENTS.md`, `CLAUDE.md`, `prompts/` | Instructions and ready prompts for AI agents |

## Start a new report

1. On GitHub, click **Use this template**. It creates a new repository with these files and no history.
2. Clone your new repository, and install what it needs (see [Requirements](#requirements)):

   ```bash
   Rscript -e 'install.packages(c("knitr", "rmarkdown", "ggplot2", "yaml", "jsonlite", "downlit", "xml2"))'
   # Only for Python chapters, including the gallery's Python chapter:
   python3 -m venv .venv && .venv/bin/pip install -r requirements-gallery.txt
   export QUARTO_PYTHON="$PWD/.venv/bin/python"
   ```

3. Name the book, and optionally set its chapters and drop the gallery:

   ```bash
   python3 scripts/new_book.py --title "Your title" --subtitle "What it decides" \
     --author "Your Name" --chapters "Design;Quality;Results" --drop-gallery
   ```

   Add `--dry-run` first to see what it would change. It never overwrites edited chapters without `--force`.

   It prints a "check link" line for each cross-reference it pointed at the first chapter, and a warning if no chapter covers the detection floor. Fix those by hand. With `--drop-gallery`, it removes the gallery files and the gallery block of this README, but other mentions of the gallery (in this README, `AGENTS.md`, `_quarto.yml`, and `requirements-gallery.txt`) stay until you edit them.

4. Render it:

   ```bash
   quarto render
   ```

## Requirements

You need:

- Quarto (tested with 1.9.37 and its bundled Pandoc 3.8.3).
- R with knitr, rmarkdown, ggplot2, yaml, and jsonlite. The starter chapters, `index.qmd`, two reference pages, and four of the ten gallery chapters run R code, so a Python-only user still needs R to render them. See [Limits](#limits).
- Python 3.11 or later for the style checks and the scaffold. They use the standard library only.
- For the Python gallery chapter: the packages pinned in `requirements-gallery.txt`. Point Quarto at that Python with `QUARTO_PYTHON`.
- Recommended: the R packages downlit and xml2. The book turns on code linking, and without these two packages each R page prints a warning.
- bash, for `scripts/check_style.sh`. The stock macOS bash 3.2 works.

It has been rendered and checked on two machines:

| | Linux (Ubuntu 24.04, cloud build, as reported by that build) | macOS (measured 2026-10-10) |
|---|---|---|
| Quarto | 1.9.37 | 1.9.37 |
| R | R 4.3.3 | R 4.5.1 |
| knitr, rmarkdown, ggplot2 | 1.45, 2.25, 3.4.4 | 1.50, 2.30, 4.0.0 |
| yaml, jsonlite | 2.3.8, 1.8.8 | 2.3.10, 2.0.0 |
| downlit, xml2 | not installed | 0.4.4, 1.4.1 |
| Python (checks) | 3.13.16 | 3.13.5, and 3.11.4 for the tests |
| Python (gallery chapter) | the pins in `requirements-gallery.txt` | the same pins, except matplotlib 3.10.0 and nbclient 0.10.2 |
| Render warnings | 7 or 8 per profile, all from missing downlit and xml2 | 0 in each of the four profiles |

## Render

```bash
quarto render                          # the starter book
quarto render --profile draft          # the starter book, with draft questions shown
quarto render --profile gallery        # the gallery
quarto render --profile gallery,draft  # the gallery, with draft questions shown
```

The rendered book is written to `_book/`. It is never committed.

Rendering uses `freeze: auto`, which re-runs a page only when that page's own source changes. After you edit `_params.yml`, `_setup.R`, or `_setup.py`, delete `_freeze/` before rendering, or the book keeps the old numbers.

## The house rules in brief

- The book is an argument. The detection floor comes before any result.
- Chapters before the synthesis describe and count. Only the synthesis interprets, under a banner.
- Numbers in prose are computed, never typed. Every percentage carries its denominator.
- A claim of no difference needs an equivalence result or the detection floor beside it.
- Every figure has a label, a caption, and alt text, and encodes significance by shape as well as colour.

The full rules are in [STYLE-GUIDE.md](STYLE-GUIDE.md).

## Style checks

```bash
bash scripts/check_style.sh
```

It runs every test and five checks, then prints one table:

| Check | Enforces |
|---|---|
| `register_guard.py` | No interpretive constructions outside the synthesis chapter |
| `absence_guard.py` | Every absence claim carries an equivalence result or the detection floor |
| `prose_lint.py` | No em dashes or filler phrases; warns on US spelling and long sentences |
| `caption_check.py` | Figures have label, caption, and alt text; labels are unique |
| `synthesis_check.py` | The synthesis has its banner, sections, Evidence, and Why it could be wrong |

When a flagged sentence is correct where it stands, add an opt-out comment with a reason on the line before it:

```markdown
<!-- register-ok: quoting the hypothesis from the study protocol -->
```

An opt-out without a reason is itself a violation. Each check has tests that show it failing on a planted defect and passing on the fix.

The optional git hooks in `scripts/hooks/` are for maintainers. They block commits that add a secret, a private IPv4 address, an absolute home path, or a term from a private word list. To use them, run `git config core.hooksPath scripts/hooks` and set `PORTFOLIO_DENYLIST` to a file of terms, one per line, with no blank lines. Without that variable they refuse every commit.

## Using it with an AI agent

Point the agent at [AGENTS.md](AGENTS.md). Claude Code reads `CLAUDE.md`, which points there. The `prompts/` folder holds five ready prompts:

- `01-scaffold-new-book.md`: start a new book from the template.
- `02-write-chapter.md`: write one chapter in the house style.
- `03-review-chapter.md`: review a chapter against the style guide, proposing edits.
- `04-add-figure.md`: add one figure with its caption, alt text, and notes.
- `05-run-style-checks.md`: run the checks and fix the content they flag.

<!-- gallery:begin -->
## The gallery

Render it with `quarto render --profile gallery`.

1. Chapter anatomy: one complete chapter, element by element.
2. Figures: captions, alt text, shape and colour, panels, tabs, and heatmaps.
3. Tables: captions, paged tables, denominators, and "not applicable" cells.
4. Callouts: each callout type and its house meaning.
5. Tabsets and layout: tabs, margin notes, footnotes, and wide content.
6. Cross-references and equations: label prefixes, equations, and citations.
7. Provenance blocks: checksums, the run manifest, and the environment.
8. Draft markers: draft questions, "To be written" sections, and opt-outs.
9. Python engine: the same conventions with Jupyter.
10. Interpretation: a worked synthesis, the only chapter that interprets.

<!-- TODO: link the rendered gallery here if it is published with GitHub Pages. -->
<!-- gallery:end -->

## Limits

This is a prototype. Known limits:

- **Python-only users still need R.** The five starter chapters, `index.qmd`, the methods and provenance pages, and four of the ten gallery chapters run R code. `new_book.py --engine python` changes only the new chapters it writes.
- **CI has not run yet.** The workflow is pinned to commit SHAs, but no run has completed. Python 3.11 was tested locally. Python 3.12 has only been checked by reading the code.
- **Only Linux and macOS were tried.** Windows is untested, and the check runner needs bash.
- **Citations are unchecked.** The DOIs and URLs in `references.bib` were written offline and have not been verified.
- **The scaffold is coarse.** `new_book.py --chapters` writes a flat chapter list, and points cross-references to removed sections at the first chapter, with a "check link" note for each. Fix those links by hand.
- The checks read prose, not methods. They cannot tell a typed number from a computed one, a wrong caption from a right one, or a wrong statistic from a right one.
- The register guard is a heuristic over English. Its false-positive rate on real report prose is unknown [UNVERIFIED].
- The CI job runs the tests and checks only, not a render. It installs no R packages, so the R tests report SKIPPED-NO-R.
- The synthetic example uses a Welch t-test on log CPM because it needs no extra packages. It is not a recommended method for count data.

## Licence

MIT. See [LICENSE](LICENSE).
