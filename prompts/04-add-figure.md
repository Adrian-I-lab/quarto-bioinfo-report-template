# Add one figure

Use this prompt to add one figure to an existing chapter.

## Prompt

```text
You are working in a Quarto report book built from the house template. Read AGENTS.md and STYLE-GUIDE.md sections 10 and 13 first.

Add one figure to {{chapter file}}, in section {{section label}}, showing {{what the figure shows}}.

1. Chunk label: fig-<chapter>-<topic>.
2. fig-cap: what is plotted, n, the encoding, any threshold lines, whether scales are shared, and what a pale or zero value means. At least 8 words, ending in a full stop.
3. fig-alt: what a sighted reader would see, in one or two sentences.
4. Colour from HOUSE_PAL or OKABE_ITO. Encode significance by shape as well as colour.
5. If the figure is not obvious to read (for example a heatmap), put a "How to read this" note (callout-note, appearance simple) before it.
6. Put a draft-question block after it.
7. If it is one of the chapter's strongest figures, add a short note on what it cannot be used as evidence for.
8. If it is meant for a paper, also call save_figure(plot, "<name>").

Then run python3 tools/style/caption_check.py chapters reference and bash scripts/check_style.sh, and render the book. Report the caption check output, the render exit code, and the check_style.sh table.
```

## Done checks

- `python3 tools/style/caption_check.py chapters reference` exits 0.
- The new label is unique.
- `quarto render` exits 0, with 0 unresolved cross-references.
