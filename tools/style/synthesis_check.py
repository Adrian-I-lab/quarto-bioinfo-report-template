#!/usr/bin/env python3
"""Structure check for the interpretation chapter.

Checks that the chapter carries the banner callout, the sections "What was
measured", "The reading", "What the data does not show", "Questions for
the bench", and "Recommendation", and that every numbered item under "The
reading" has both "Evidence:" and "Why it could be wrong:".

A "To be written" callout in place of reading items passes with a
warning, so the starter template passes.

Exit codes: 0 pass, 1 a missing element, 2 a file does not exist.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qmd  # noqa: E402

BANNER = "This chapter is interpretation, not a result"
SECTIONS = [
    "What was measured",
    "The reading",
    "What the data does not show",
    "Questions for the bench",
    "Recommendation",
]
_ITEM = re.compile(r"^\d+[.)]\s")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def check_file(path: Path) -> tuple[list[str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    mask = _qmd.code_mask(lines)
    errors, warnings = [], []

    if not any(BANNER in line for line, m in zip(lines, mask) if not m):
        errors.append(f"{path}: missing the banner callout '{BANNER}'")

    # Headings inside callouts and other divs are titles, not sections.
    headings = {}
    depth = 0
    for n, (line, m) in enumerate(zip(lines, mask), start=1):
        if m:
            continue
        stripped = line.strip()
        if stripped.startswith(":::"):
            depth = depth + 1 if stripped.rstrip(":").strip() else max(0, depth - 1)
            continue
        h = _HEADING.match(line)
        if h and depth == 0:
            headings[n] = (len(h.group(1)), h.group(2))
    for name in SECTIONS:
        if not any(name.lower() in text.lower() for _lvl, text in headings.values()):
            errors.append(f"{path}: missing section '{name}'")

    start = next((n for n, (_l, t) in headings.items() if "the reading" in t.lower()), None)
    if start is None:
        return errors, warnings
    level = headings[start][0]
    end = next((n for n, (lvl, _t) in sorted(headings.items()) if n > start and lvl <= level),
               len(lines) + 1)
    items: list[tuple[int, list[str]]] = []
    for n in range(start + 1, end):
        line = lines[n - 1]
        if mask[n - 1]:
            continue
        if _ITEM.match(line):
            items.append((n, [line]))
        elif items:
            items[-1][1].append(line)
    section_text = "\n".join(lines[start:end - 1])
    if not items:
        if "To be written" in section_text:
            warnings.append(f"{path}:{start}: 'The reading' has no items yet (To be written)")
        else:
            errors.append(f"{path}:{start}: 'The reading' has no numbered items")
    for k, (n, body) in enumerate(items, start=1):
        text = " ".join(body)
        for need in ("Evidence:", "Why it could be wrong:"):
            if need not in text:
                errors.append(f"{path}:{n}: reading item {k} lacks '{need}'")
    return errors, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Structure check for the interpretation chapter.")
    ap.add_argument("paths", nargs="*",
                    default=["chapters/90-interpretation.qmd", "gallery/g10-interpretation.qmd"])
    args = ap.parse_args(argv)

    missing = [p for p in args.paths if not Path(p).is_file()]
    for p in missing:
        print(f"{p}: file does not exist")
    files = [Path(p) for p in args.paths if Path(p).is_file()]
    errors, warnings = [], []
    for f in files:
        e, w = check_file(f)
        errors.extend(e)
        warnings.extend(w)
    for line in errors:
        print(f"ERROR {line}")
    for line in warnings:
        print(f"WARNING {line}")
    print(f"files_examined={len(files)} errors={len(errors)} warnings={len(warnings)}")
    if missing or not files:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
