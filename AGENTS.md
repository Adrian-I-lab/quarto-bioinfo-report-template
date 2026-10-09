# Instructions for AI agents

This is the canonical instruction file for agents working in this repository. Tool-specific files, such as `CLAUDE.md`, point here.

## What this repo is

A Quarto book template for analysis reports in bioinformatics. It ships a format layer, a starter book, a gallery of every formatting element on synthetic data, a house style guide, and automated style checks. The house style keeps measurement and interpretation apart. Every chapter before the synthesis describes and counts. Only the synthesis chapter interprets.

## Map

| Path | What it is |
|---|---|
| `_quarto.yml` | Book settings and the HTML format. Holds no chapter list. |
| `_quarto-starter.yml` | The default profile: the starter book's chapter list, between `# chapters:begin` and `# chapters:end`. |
| `_quarto-gallery.yml` | The gallery profile: the gallery's chapter list. |
| `_quarto-draft.yml` | The draft profile: shows draft questions. |
| `_params.yml` | Analysis parameters. A null value stops the render. |
| `_setup.R`, `_setup.py` | Shared helpers, sourced by the first chunk of every chapter. |
| `index.qmd` | The book's front page. |
| `chapters/` | The starter book's chapters. `90-interpretation.qmd` is the synthesis. |
| `reference/` | Methods, provenance, limitations, and glossary. |
| `gallery/` | Ten chapters showing every element on synthetic data. |
| `theme/house.scss` | The theme. |
| `filters/` | Lua filters for image loading and draft questions. |
| `references.bib` | Bibliography. |
| `STYLE-GUIDE.md` | The house style. Read it before writing prose. |
| `style-checks.toml` | Word lists and settings shared by the checks. |
| `tools/style/` | The style checks. |
| `scripts/check_style.sh` | Runs every test and check, and prints one table. |
| `scripts/new_book.py` | Turns a fresh copy of the template into a named book. |
| `scripts/hooks/` | Optional local git hooks for maintainers. |
| `tests/` | Tests for the helpers, the checks, and the scaffold. |
| `prompts/` | Ready prompts for common tasks. |
| `requirements-gallery.txt` | Pinned Python packages for the Python chapter. |

## Commands

```bash
quarto render                          # the starter book
quarto render --profile draft          # the starter book, with draft questions shown
quarto render --profile gallery        # the gallery
quarto render --profile gallery,draft  # the gallery, with draft questions shown
bash scripts/check_style.sh            # every test and style check
bash scripts/check_style.sh --changed  # content checks on files changed against main
python3 -m unittest discover -s tests  # the Python tests only
Rscript tests/test_setup_r.R           # the R tests only
python3 scripts/new_book.py --title "..." --subtitle "..." --author "..." --chapters "A;B;C"
```

Python chapters need `QUARTO_PYTHON` set to a Python with the packages in `requirements-gallery.txt`.

## Rules

1. Read `STYLE-GUIDE.md` before writing any prose.
2. Descriptive chapters never interpret. Interpretation lives only in the synthesis chapter, `chapters/90-interpretation.qmd`.
3. Numbers in prose are computed with inline code, never typed. Thresholds come from `_params.yml` through `report_param()`.
4. Every figure has a label, a caption, and alt text. Every table has a label and a caption.
5. The gallery uses synthetic data only. Never add a data file to the gallery.
6. Never edit `tools/style/` or `style-checks.toml` to make content pass. Fix the content. If a flagged sentence is correct where it stands, add a `register-ok` comment with a reason, and say so in your report.
7. Never commit `_book/`, `_freeze/`, `figures/`, or any other rendered output.
8. Never change a value in `_params.yml` without recording the decision and its reason in `reference/methods.qmd`. When a chapter changes a method or a step, update the methods paragraph in the same task.
9. Do not delete a draft question you were given. Answer it in prose and mark it ANSWERED, or mark it DEFERRED with a reason (see "Marking draft questions"). A placeholder question written by `new_book.py` may be replaced by the section's real questions when you write that section.
10. Run `bash scripts/check_style.sh` before you claim a task is done, and paste its table.

## Definition of done

A task is done when all of these hold:

- `bash scripts/check_style.sh` exits 0.
- `quarto render` exits 0, with 0 unresolved cross-references. Count them with `grep -oh "?@[a-z0-9-]*" _book/*.html _book/*/*.html | sort -u | wc -l`.
- Every draft question in a section you touched is answered in prose, or marked deferred with a reason.
- Your report states what you measured, not what you intended.

## Writing a new chapter

1. Copy the anatomy from `STYLE-GUIDE.md` section 4, or let `scripts/new_book.py --chapters` create the file.
2. Add the chapter to `_quarto-starter.yml`, between the chapter markers, in the order of the argument: data and instrument, detection floor, results, robustness.
3. Give every section a label of the form `sec-<chapter>-<topic>`.
4. Add each "cannot show" statement to `reference/limitations.qmd`, under its group, with a link back to the section. When no group fits, for example a limit of the statistical method, add a group heading such as "From the method".
5. If the book has no detection-floor chapter, a "count of zero" warning cannot cite a floor. Say so in the warning, and add "Detection floor" to the "Not yet implemented" table in `reference/limitations.qmd`. Do not write the words "detection floor" only to satisfy the absence guard.

## After `new_book.py`

- It prints a "check link" line for every cross-reference it repointed in `chapters/90-interpretation.qmd` and `reference/limitations.qmd`. Those links resolve, but they point at the first new chapter. Fix each one when you write the chapter it belongs to.
- It writes a flat chapter list. Add part headings in `_quarto-starter.yml` if the book needs them.
- It warns when no chapter covers the detection floor.
- `index.qmd` and the interpretation chapter stay as placeholders until the chapters they summarise exist.

## Marking draft questions

Mark each question inside its block, on the question's own line. ANSWERED names the section that answers it. DEFERRED gives the reason.

```markdown
<!-- Q
- How many features passed in each direction? ANSWERED: @sec-results-counts
- How many samples failed quality control? DEFERRED: the quality report is not yet available.
-->
```

## What the checks cannot catch

- A number typed into prose that happens to look computed.
- A caption that describes the figure wrongly.
- A detection floor computed wrongly.
- Interpretation phrased in words the lists do not hold.
- A reading whose counter-argument is weak.
- Wrong statistics. The checks read prose, not methods.

These need a human review. Say in your report which of them you could not check.

## Prompts

`prompts/` holds five ready prompts:

- `01-scaffold-new-book.md`: start a new book from the template.
- `02-write-chapter.md`: write one chapter in the house style.
- `03-review-chapter.md`: review a chapter against the style guide.
- `04-add-figure.md`: add one figure with its caption, alt text, and notes.
- `05-run-style-checks.md`: run the checks and fix the content they flag.
