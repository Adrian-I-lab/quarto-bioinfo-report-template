# Quarto report template for bioinformatics

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
2. Clone your new repository.
3. Name the book, and optionally set its chapters and drop the gallery:

   ```bash
   python3 scripts/new_book.py --title "Your title" --subtitle "What it decides" \
     --author "Your Name" --chapters "Design;Quality;Results" --drop-gallery
   ```

   Add `--dry-run` first to see what it would change. It never overwrites edited chapters without `--force`.

4. Render it:

   ```bash
   quarto render
   ```

## Requirements

Tested with these exact versions:

- Quarto 1.9.37 (with its bundled Pandoc 3.8.3).
- R 4.3.3 with knitr 1.45, rmarkdown 2.25, ggplot2 3.4.4, yaml 2.3.8, and jsonlite 1.8.8. The starter book, the reference pages, and most gallery chapters use R.
- Python 3.11 or later for the style checks and the scaffold. They use the standard library only.
- For the Python gallery chapter: the packages pinned in `requirements-gallery.txt`, tested on Python 3.13.16. Point Quarto at that Python with `QUARTO_PYTHON`.
- Optional: the R packages downlit and xml2. Without them, code linking is off and each R page prints a warning.

## Render

```bash
quarto render                          # the starter book
quarto render --profile draft          # the starter book, with draft questions shown
quarto render --profile gallery        # the gallery
quarto render --profile gallery,draft  # the gallery, with draft questions shown
```

The rendered book is written to `_book/`. It is never committed.

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

- The checks read prose, not methods. They cannot tell a typed number from a computed one, a wrong caption from a right one, or a wrong statistic from a right one.
- The register guard is a heuristic over English. Its false-positive rate on real report prose is unknown [UNVERIFIED].
- R chapters need a local R installation. The CI job runs the tests and checks only, not a render.
- The synthetic example uses a Welch t-test on log CPM because it needs no extra packages. It is not a recommended method for count data.

## Licence

MIT. See [LICENSE](LICENSE).
