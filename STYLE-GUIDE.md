# House style guide for analysis report books

This guide states the house style for analysis reports written as Quarto books. The style checks in `tools/style/` enforce part of it. Their word lists live in `style-checks.toml`, so this guide and the checks share one source.

## 1. Purpose

This guide is for people and AI agents who write analysis report books. It covers the order of a book, the anatomy of a chapter, the register of the prose, and how numbers, figures, and tables are presented.

A report book has one job. It lets a reader check what was measured, how well, and what it can and cannot support. Every rule below serves that job.

## 2. The book is an argument

The order of the parts is part of the argument. The default order is:

1. The data and the instrument. What was measured, and how well.
2. What this design could detect. The detection floor.
3. Results.
4. Robustness.
5. Synthesis. The only place for interpretation.
6. Reference. Methods, provenance, limitations, and glossary.

The detection floor comes before any result. A result read without its detection floor is a result read without its denominator.

## 3. Part and chapter structure

- Chapters live in `chapters/NN-topic.qmd`. The number sets the order. The interpretation chapter is `chapters/90-interpretation.qmd`.
- Reference pages live in `reference/`.
- A long chapter can be split into include fragments. A fragment starts with an underscore, for example `chapters/_04-results-body.qmd`. Fragments are not chapters and are not listed in the book.
- One engine per chapter. A book may mix R and Python chapters. A single chapter never mixes them.
- An optional chapter that does not apply renders a "Not applicable to this report" note. It never disappears.

## 4. Chapter anatomy

Every chapter follows this checklist, in order.

1. A level-1 heading with a section label, for example `# Quality of the measurement {#sec-quality}`.
2. A hidden setup chunk that sources the shared setup file.
3. An "In plain terms" tip. One or two sentences a non-specialist can read.
4. A "Status" note. What data the chapter last ran on, and when.
5. A bold **Question.** lead-in. What this chapter decides.
6. A bold **Design.** lead-in. The comparison, n per group, and whether anything is tested or only described.
7. An opening sentence that states the method and every threshold. Thresholds come from `_params.yml` through inline code. They are never typed.
8. Sections. Each has its figure or table, a "How to read this" note before any non-obvious figure, and a draft-question block after it.
9. The warning "A count of zero is not a measured absence" wherever a result can be empty.
10. A closing pointer to where the chapter's limitations are gathered.

## 5. Register

Observation and interpretation are kept apart.

- Every chapter before the synthesis is descriptive and quantitative. It says what was measured and how large it was.
- Interpretation lives in one chapter. That chapter is labelled as a reading, not a result.

Why: a reviewer can check the numbers without arguing about meaning. They can then argue about meaning without re-checking the numbers.

| Descriptive (any chapter) | Interpretive (synthesis only) |
|---|---|
| 31 of 500 features passed the FDR threshold of 0.05. | The treatment `suggests that` a pathway is switched on. |
| The median log2 fold change was 1.8 among those 31. | The shift `is driven by` one cell population. |
| Replicate 3 had 40% fewer reads than the others. | The low depth `may reflect` a handling problem. |

A sentence that denies an interpretation is the wanted behaviour. "This figure says nothing about why the groups differ" belongs in a descriptive chapter.

The register guard flags interpretive constructions outside the synthesis chapter. When a flagged sentence is correct where it stands, add an opt-out comment on the line before it:

```markdown
<!-- register-ok: quoting the hypothesis from the study protocol -->
```

The reason is mandatory. An opt-out without a reason is itself a violation.

## 6. Absence claims

"No difference", "unchanged", and similar phrases claim that something is absent. Each needs, in the same paragraph, either an equivalence result or the detection floor.

- Supported: "Expression was unchanged between groups (equivalence bound 0.5 log2 units, TOST p = 0.01)."
- Supported: "No feature passed the threshold. The design could detect a change of 1.2 log2 units or more (@sec-detection-floor)."
- Not supported: "Expression was unchanged between groups."

A count of zero is a failure to detect at this design's floor. It is not a measured absence.

## 7. Numbers

- Numbers in prose are computed by inline code, never typed.
- State exact thresholds, units, denominators, and software versions.
- Every percentage carries its denominator: "12 of 40 (30.0%)".
- Use thousands separators: 12,480, not 12480.
- "Not applicable" is never written as 0. A cell that cannot have a value says "not applicable".
- Say what a denominator includes and what it excludes.

## 8. Writing rules

- Australian English. Some common pairs:

| Write | Not |
|---|---|
| colour | `color` |
| analyse | `analyze` |
| normalise | `normalize` |
| behaviour | `behavior` |
| centre | `center` |
| modelled | `modeled` |
| labelled | `labeled` |
| licence (noun) | `license` (noun) |

- Use the Oxford comma: "figures, tables, and code".
- No em dashes. Use a full stop, a comma, or brackets.
- Use colons and semicolons only where a full stop is not clearer.
- Short sentences, one idea each. The prose linter warns above 35 words.
- Plain verbs. "Use", not "utilise".
- No filler phrases. The list is in `style-checks.toml`. Examples are `it is important to note`, `in order to`, and `a number of`. When this guide quotes one, it goes inside backticks so the linter skips it.

## 9. Evidence tags

Claims about software and analysis carry a tag when their status matters.

| Tag | Meaning |
|---|---|
| [VERIFIED] | Checked directly, in this run. |
| [PARTIAL] | Checked for some cases, not all. |
| [UNVERIFIED] | Not checked. |
| [STALE] | Checked once, but the thing has changed since. |
| [CONTRADICTED] | A check found the opposite. |
| [Likely] or [Guessing] | An uncertain claim, with the level of confidence stated. |

Keep five things apart: a method being available, a method being run, an observed result, a validation of that result, and an interpretation of it. An absent measurement is not a failed one. It never enters a rate.

## 10. Figures

- Every figure has a label, a caption, and alt text.
- The caption says what is plotted, n, the encoding, any threshold lines, whether scales are shared, and what a pale or zero cell means.
- One palette for the whole book, safe for colour-vision deficiency. Significance is encoded by shape as well as colour.
- A "How to read this" note comes before any non-obvious figure, especially a heatmap.
- After the strongest figures, a short note says what the figure cannot be used as evidence for.
- Figures meant for papers are saved as PDF and PNG with `save_figure()`.

## 11. Tables

- Every table has a label and a caption.
- Long tables use paged data frames.
- A cell that cannot have a value says "not applicable", never 0.

## 12. Callouts

| Type | Title pattern | Meaning |
|---|---|---|
| tip | In plain terms | Lay summary at the top of a chapter. |
| note | Status | What data the chapter ran on, and when. |
| note, simple | How to read this | Read before a non-obvious figure. |
| important | A caveat, for example "Which number this chapter uses" | Read before the numbers. |
| warning, simple | A count of zero is not a measured absence | Wherever a result can be empty. |
| caution | No run manifest | Provenance is missing. |
| note, simple | Not applicable to this report | A gated section that did not run. |
| important | This chapter is interpretation, not a result | Banner on the synthesis chapter. |
| important | To be written | A section the author still has to fill. |

## 13. Cross-references

- Label prefixes: `sec-` for sections, `fig-` for figures, `tbl-` for tables, `eq-` for equations.
- Section labels follow `sec-<chapter>-<topic>`, for example `sec-quality-depth`.
- Every limitation and every interpretation item links to the section it came from.

## 14. Methods, limitations, and provenance

These three pages do different jobs.

- **Methods** says what was done. It is publication-ready prose generated from the run's parameters and package versions. It cites every package with its version.
- **Limitations** gathers every "cannot show" statement in the book, grouped by source. Each links back to its section. It also lists what is not yet implemented. An absent section is a gap, not a clean bill.
- **Provenance** records the inputs with checksums, the run manifest, and the resolved environment. It reports what loaded, not what a lockfile pins.

A check that could not run counts as a failure, not a pass.

## 15. Glossary format

Each entry is a bold term, a full stop, then one to three sentences. The definition says what the term is, and what it is not.

> **Detection floor**. The smallest effect this design could detect with stated power. It is not the smallest effect that exists.

## 16. Draft mode and questions

Each section carries the questions its prose must answer, in an HTML comment:

```markdown
<!-- Q
- What fraction of samples passed quality control?
- Which threshold removed the most samples?
-->
```

The comment is invisible in a normal render. `quarto render --profile draft` shows each block as a collapsed callout. Before a chapter is done, each question is answered in prose or marked as deferred with a reason.

## 17. The interpretation chapter

The synthesis chapter opens with the banner "This chapter is interpretation, not a result". No number in it is new. Its sections are:

1. **What was measured.** A table that restates the numbers, with a column of section links.
2. **The reading.** Numbered items. Each gives the reading in one sentence, then *Evidence:* (sections and numbers), then *Why it could be wrong:* (the strongest counter-argument).
3. **What the data does not show.** The mirror of the reading. It is the more important of the two.
4. **Questions for the bench.** Each names a measurement, and what each outcome would mean.
5. **Recommendation.** One paragraph. What to do next, and what not to do.

## 18. What the checks enforce, and what they cannot

| Rule | Automated by |
|---|---|
| No interpretive constructions outside the synthesis | `register_guard.py` (warning by default, `--strict` in the runner) |
| Opt-outs carry a reason | `register_guard.py` |
| Absence claims carry an equivalence result or the detection floor | `absence_guard.py` |
| No em dashes, no spaced en dashes | `prose_lint.py` (error) |
| No filler phrases | `prose_lint.py` (error) |
| Australian spelling | `prose_lint.py` (warning) |
| Sentences of 35 words or fewer | `prose_lint.py` (warning) |
| Figures have label, caption, and alt text; labels are unique | `caption_check.py` |
| The synthesis has its banner, sections, Evidence, and Why it could be wrong | `synthesis_check.py` |
| Numbers are computed, not typed | human review |
| A caption describes the figure correctly | human review |
| The detection floor is computed correctly | human review |
| A reading is reasonable, and its counter-argument is the strongest one | human review |
| Interpretation phrased in words the lists do not hold | human review |

Run every check with `bash scripts/check_style.sh`.
