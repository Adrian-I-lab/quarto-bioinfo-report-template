# Write one chapter

Use this prompt to write one chapter from an analysis you describe.

## Prompt

```text
You are working in a Quarto report book built from the house template. Read AGENTS.md and STYLE-GUIDE.md first.

Write the chapter {{chapter file, for example chapters/03-results.qmd}} from this analysis:
{{describe the analysis: data, comparison, n per group, method, and what the chapter must decide}}

Follow the chapter anatomy in STYLE-GUIDE.md section 4, in order:
- the level-1 heading with its label, and the hidden setup chunk;
- the "In plain terms" tip and the "Status" note;
- the **Question.** and **Design.** lead-ins;
- an opening sentence with the method and every threshold, read from _params.yml with report_param();
- sections with labels sec-<chapter>-<topic>, each with its figure or table, a "How to read this" note before any non-obvious figure, and a draft-question block after it;
- the "A count of zero is not a measured absence" warning wherever a result can be empty;
- a closing pointer to @sec-limitations.

Rules:
- Compute every number in prose with inline code. Never type a number.
- Descriptive register only. Do not interpret. Interpretation belongs in chapters/90-interpretation.qmd.
- Every figure has a label, a caption of at least 8 words ending in a full stop, and alt text.
- Answer every draft question in the prose, or mark it DEFERRED with a reason inside the block.
- Add every "cannot show" statement to reference/limitations.qmd, under its group, with a link back to its section.
- Do not edit tools/style/ or style-checks.toml.

When you finish, run quarto render and bash scripts/check_style.sh. Report the render exit code, the unresolved reference count, the check_style.sh table, and the list of draft questions with how each was handled.
```

## Done checks

- `bash scripts/check_style.sh` exits 0.
- `quarto render` exits 0, with 0 unresolved cross-references.
- `python3 tools/style/register_guard.py --strict {{chapter file}}` reports 0 violations.
- Every draft question in the chapter is answered or marked DEFERRED with a reason.
