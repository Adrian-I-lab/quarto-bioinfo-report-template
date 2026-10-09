#!/usr/bin/env python3
"""Turn a fresh copy of the template into a named book.

Usage:
  python3 scripts/new_book.py --title T --subtitle S --author A
      [--engine r|python] [--chapters "Design;Quality;Results"]
      [--drop-gallery] [--dry-run] [--force]

What it does:
  - Sets the book title, subtitle, and author in _quarto.yml, by replacing
    those three lines. Comments and everything else stay as they are.
  - With --chapters, replaces the shipped skeleton chapters with one new
    chapter per name, numbered 01 onwards, and rewrites the chapter list
    between the "# chapters:begin" and "# chapters:end" markers in
    _quarto-starter.yml. The interpretation chapter and the reference pages
    are always kept. Cross-references to removed skeleton sections are
    pointed at the first new chapter, so the book still renders.
  - With --engine python, new chapters use a Python setup cell.
  - With --drop-gallery, deletes gallery/ and _quarto-gallery.yml, and
    removes the gallery links from README.md.
  - With --dry-run, prints the plan and writes nothing.

It refuses to replace chapters that differ from the shipped skeleton,
unless --force is given, so it never overwrites a user's work. The
shipped skeleton is recorded in scripts/skeleton.sha256. A real run
removes that file, because from then on the chapters are the user's.
Python 3.11+ standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKELETON = [
    "chapters/01-design.qmd",
    "chapters/02-quality.qmd",
    "chapters/03-detection-floor.qmd",
    "chapters/04-results.qmd",
    "chapters/05-robustness.qmd",
]
MANIFEST = "scripts/skeleton.sha256"
REF_FILES = ["chapters/90-interpretation.qmd", "reference/limitations.qmd"]

R_SETUP = '''```{r}
#| include: false
source("../_setup.R")
```'''

PY_SETUP = '''```{python}
#| include: false
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent))
import _setup as s  # noqa: E402
```'''

CHAPTER = """{front}# {name} {{#sec-{slug}}}

{setup}

::: {{.callout-tip}}
## In plain terms
To be written. One or two sentences a non-specialist can read.
:::

::: {{.callout-note}}
## Status
Not yet run. Say what data this chapter last ran on, and when.
:::

**Question.** To be written. What this chapter decides.

**Design.** To be written. The comparison, n per group, and whether anything is tested or only described.

This chapter uses an FDR threshold of {fdr}. Replace this sentence with the method and every threshold, each read from `_params.yml`.

## First section {{#sec-{slug}-first}}

::: {{.callout-important}}
## To be written
Add this section's figure or table, with a "How to read this" note before any non-obvious figure.
:::

<!-- Q
- What does this section measure, and with what denominator?
-->

Limitations from this chapter are gathered in @sec-limitations.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise SystemExit(f"new_book: cannot make a file name from chapter name {name!r}")
    return slug


def chapter_text(name: str, slug: str, engine: str) -> str:
    if engine == "python":
        return CHAPTER.format(front="---\njupyter: python3\n---\n\n", name=name, slug=slug,
                              setup=PY_SETUP, fdr='`{python} s.report_param("fdr")`')
    return CHAPTER.format(front="", name=name, slug=slug, setup=R_SETUP,
                          fdr='`r report_param("fdr")`')


def replace_key(text: str, key: str, value: str, path: str) -> str:
    pattern = re.compile(rf"^(  {key}:)[ \t].*$", re.MULTILINE)
    hits = pattern.findall(text)
    if len(hits) != 1:
        raise SystemExit(f"new_book: expected exactly one '  {key}:' line in {path}, found {len(hits)}")
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return pattern.sub(lambda m: f'{m.group(1)} "{escaped}"', text)


def edited_skeleton(root: Path) -> list[str]:
    """Skeleton chapters that differ from the shipped versions."""
    manifest = {}
    path = root / MANIFEST
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    for line in lines:
        digest, name = line.split(maxsplit=1)
        manifest[name] = digest
    changed = []
    for rel in SKELETON:
        path = root / rel
        if path.exists() and sha256(path) != manifest.get(rel):
            changed.append(rel)
    shipped = set(SKELETON) | {"chapters/90-interpretation.qmd"}
    for path in sorted((root / "chapters").glob("*.qmd")):
        rel = path.relative_to(root).as_posix()
        if rel not in shipped:
            changed.append(rel)
    return changed


def plan(args, root: Path) -> tuple[dict[Path, str], list[Path]]:
    """Return (files to write, paths to remove)."""
    writes: dict[Path, str] = {}
    removes: list[Path] = []

    quarto = root / "_quarto.yml"
    text = quarto.read_text(encoding="utf-8")
    text = replace_key(text, "title", args.title, "_quarto.yml")
    text = replace_key(text, "subtitle", args.subtitle, "_quarto.yml")
    text = replace_key(text, "author", args.author, "_quarto.yml")
    writes[quarto] = text

    if args.chapters:
        names = [n.strip() for n in args.chapters.split(";") if n.strip()]
        if not names:
            raise SystemExit("new_book: --chapters needs at least one name")
        edited = edited_skeleton(root)
        if edited and not args.force:
            raise SystemExit(
                "new_book: these chapters differ from the shipped skeleton, so they may hold "
                "your work: " + ", ".join(edited) + ". Re-run with --force to replace them."
            )
        removed_labels: set[str] = set()
        for rel in SKELETON:
            path = root / rel
            if path.exists():
                removed_labels.update(re.findall(r"\{#(sec-[\w-]+)", path.read_text(encoding="utf-8")))
                removes.append(path)
        entries = ["    - index.qmd"]
        slugs = []
        for i, name in enumerate(names, start=1):
            slug = slugify(name)
            slugs.append(slug)
            rel = f"chapters/{i:02d}-{slug}.qmd"
            target = root / rel
            if target in removes:
                removes.remove(target)
            writes[target] = chapter_text(name, slug, args.engine)
            entries.append(f"    - {rel}")
        starter = root / "_quarto-starter.yml"
        stext = starter.read_text(encoding="utf-8")
        block = re.compile(r"(    # chapters:begin\n).*?(    # chapters:end\n)", re.DOTALL)
        if len(block.findall(stext)) != 1:
            raise SystemExit("new_book: chapter markers not found exactly once in _quarto-starter.yml")
        writes[starter] = block.sub(lambda m: m.group(1) + "\n".join(entries) + "\n" + m.group(2), stext)
        # Point references to removed skeleton sections at the first new chapter.
        for rel in REF_FILES:
            path = root / rel
            if not path.exists():
                continue
            ref_text = path.read_text(encoding="utf-8")
            new_text = re.sub(
                r"@(sec-[\w-]+)",
                lambda m: f"@sec-{slugs[0]}" if m.group(1) in removed_labels else m.group(0),
                ref_text,
            )
            if new_text != ref_text:
                writes[path] = new_text
    elif args.engine == "python":
        raise SystemExit("new_book: --engine python applies to new chapters, so use it with --chapters")

    if args.drop_gallery:
        for rel in ("gallery", "_quarto-gallery.yml"):
            if (root / rel).exists():
                removes.append(root / rel)
        readme = root / "README.md"
        if readme.exists():
            rtext = readme.read_text(encoding="utf-8")
            new = re.sub(r"<!-- gallery:begin -->.*?<!-- gallery:end -->\n?", "", rtext, flags=re.DOTALL)
            if new != rtext:
                writes[readme] = new
    return writes, removes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Turn a fresh copy of the template into a named book.")
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", required=True)
    ap.add_argument("--author", required=True)
    ap.add_argument("--engine", choices=["r", "python"], default="r")
    ap.add_argument("--chapters", help='chapter names separated by ";", for example "Design;Quality;Results"')
    ap.add_argument("--drop-gallery", action="store_true", help="delete the gallery and its profile")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and write nothing")
    ap.add_argument("--force", action="store_true", help="replace chapters that differ from the skeleton")
    ap.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    writes, removes = plan(args, root)
    prefix = "would " if args.dry_run else ""
    for path in removes:
        print(f"{prefix}remove {path.relative_to(root).as_posix()}")
    for path in writes:
        print(f"{prefix}write  {path.relative_to(root).as_posix()}")
    if args.dry_run:
        return 0
    for path in removes:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    for path, text in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    # The book is now the user's own. Without the manifest, a later run treats
    # every existing chapter as the user's work and needs --force.
    manifest = root / MANIFEST
    if manifest.exists():
        manifest.unlink()
        print(f"remove {MANIFEST}")
    print("new_book: done. Next: quarto render, then bash scripts/check_style.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
