# Scaffold a new book

Use this prompt once, in a fresh copy of the template, to turn it into a named book.

## Prompt

```text
You are working in a fresh copy of the Quarto report template. Read AGENTS.md first.

Turn it into a new book:
1. Run: python3 scripts/new_book.py --title "{{title}}" --subtitle "{{subtitle}}" --author "{{author}}" --engine {{r_or_python}} --chapters "{{chapter names separated by ;}}" {{--drop-gallery or nothing}}
   Use --dry-run first and read the plan. Then run it for real.
2. Render the book: quarto render. For Python chapters, set QUARTO_PYTHON to a Python with the packages in requirements-gallery.txt.
3. Count unresolved cross-references: grep -oh "?@[a-z0-9-]*" _book/*.html _book/*/*.html | sort -u | wc -l
4. Run the checks: bash scripts/check_style.sh
5. Report: the files new_book.py wrote and removed, every "check link" and "warning" line it printed, the render exit code, the unresolved reference count, and the check_style.sh table. Report measured results, not intentions.

Do not write any chapter content yet. Leave index.qmd and the interpretation chapter as placeholders. Do not edit tools/style/ or style-checks.toml.
```

## Done checks

- `new_book.py` exited 0 and printed every path it wrote or removed.
- `_quarto.yml` carries the new title, subtitle, and author.
- `quarto render` exited 0, with 0 unresolved cross-references.
- `bash scripts/check_style.sh` exited 0.
