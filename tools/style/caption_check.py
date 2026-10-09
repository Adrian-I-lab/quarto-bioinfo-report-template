#!/usr/bin/env python3
"""Figure and table caption check.

Errors:
  - A chunk with "#| label: fig-..." lacks "#| fig-cap:" or "#| fig-alt:".
  - A figure caption does not end with a full stop or has fewer than 8 words.
  - A markdown image with a {#fig-...} label lacks a caption or fig-alt.
  - A chunk with "#| label: tbl-..." lacks "#| tbl-cap:".
  - A fig-, tbl-, sec-, or eq- label appears more than once across the files.
Warnings:
  - A chunk that plots but has no fig- label, caption, or alt text
    ("unlabelled figure"). A loop that writes several figures into tabs
    cannot carry one label, but it can carry fig-alt.

Exit codes: 0 pass, 1 errors, 2 nothing examined.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qmd  # noqa: E402

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_CHUNK_START = re.compile(r"^\s*```+\s*\{(r|python)\b[^}]*\}\s*$")
_OPTION = re.compile(r"^\s*#\|\s*([\w-]+)\s*:\s*(.*)$")
_OPTION_CONT = re.compile(r"^\s*#\|\s{2,}(.*)$")
_PLOTS = re.compile(r"\bggplot\(|\bplt\.|\bprint\([\w.]*plot\w*\)|\bplot\(")
_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)\{([^}]*)\}")
_MD_LABEL = re.compile(r"\{#((?:sec|fig|tbl|eq)-[\w-]+)[^}]*\}")
_TABLE_CAPTION = re.compile(r"^\s*:\s+(.+?)\s*\{#(tbl-[\w-]+)[^}]*\}\s*$")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_chunks(lines: list[str]):
    """Yield (start_line, options, code_lines) for each executable chunk."""
    i = 0
    while i < len(lines):
        fence = _FENCE.match(lines[i])
        if fence and not _CHUNK_START.match(lines[i]):
            # A plain fenced block, such as a source example: skip it whole.
            mark = fence.group(1)
            i += 1
            while i < len(lines):
                close = _FENCE.match(lines[i])
                if close and close.group(1)[0] == mark[0] and len(close.group(1)) >= len(mark) \
                        and lines[i].strip() == close.group(1):
                    break
                i += 1
            i += 1
            continue
        if _CHUNK_START.match(lines[i]):
            start = i + 1
            options: dict[str, str] = {}
            code: list[str] = []
            last = None
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                cont = _OPTION_CONT.match(lines[i])
                m = None if cont else _OPTION.match(lines[i])
                if m:
                    last = m.group(1)
                    options[last] = _unquote(m.group(2))
                elif cont and last:
                    item = cont.group(1).strip()
                    item = _unquote(item[2:] if item.startswith("- ") else item)
                    joined = (options[last] + " " + item).strip()
                    options[last] = joined.lstrip("|>- ").strip()
                else:
                    code.append(lines[i])
                i += 1
            yield start, options, code
        i += 1


def check_file(path: Path, labels: dict) -> tuple[list[str], list[str], int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    errors, warnings = [], []
    n_fig = n_tbl = 0

    for start, opts, code in parse_chunks(lines):
        label = opts.get("label", "")
        if label:
            labels[label].append(f"{path}:{start}")
        if label.startswith("fig-"):
            n_fig += 1
            cap = opts.get("fig-cap", "")
            if not cap:
                errors.append(f"{path}:{start}: {label}: missing fig-cap")
            else:
                if not cap.rstrip().endswith("."):
                    errors.append(f"{path}:{start}: {label}: caption must end with a full stop")
                if len(cap.split()) < 8:
                    errors.append(f"{path}:{start}: {label}: caption has fewer than 8 words")
            if not opts.get("fig-alt"):
                errors.append(f"{path}:{start}: {label}: missing fig-alt")
        elif label.startswith("tbl-"):
            n_tbl += 1
            if not opts.get("tbl-cap"):
                errors.append(f"{path}:{start}: {label}: missing tbl-cap")
        elif any(_PLOTS.search(c) for c in code) and "fig-cap" not in opts and "fig-alt" not in opts:
            warnings.append(f"{path}:{start}: unlabelled figure")

    mask = _qmd.code_mask(lines)
    for n, (line, in_code) in enumerate(zip(lines, mask), start=1):
        if in_code:
            continue
        line = re.sub(r"`+[^`]*`+", " ", line)
        for m in _MD_IMAGE.finditer(line):
            attrs = m.group(3)
            if "#fig-" not in attrs:
                continue
            n_fig += 1
            if not m.group(1).strip():
                errors.append(f"{path}:{n}: markdown figure has no caption")
            if "fig-alt=" not in attrs:
                errors.append(f"{path}:{n}: markdown figure has no fig-alt")
        tc = _TABLE_CAPTION.match(line)
        if tc:
            n_tbl += 1
        for m in _MD_LABEL.finditer(line):
            labels[m.group(1)].append(f"{path}:{n}")
    return errors, warnings, n_fig, n_tbl


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Figure and table caption check.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--config", default=None, help="path to style-checks.toml")
    args = ap.parse_args(argv)

    cfg = _qmd.load_config(args.config)
    files = _qmd.collect_files(args.paths, [".qmd"], cfg.get("scan", {}).get("exclude", []))
    labels: dict[str, list[str]] = defaultdict(list)
    errors, warnings = [], []
    n_fig = n_tbl = 0
    for f in files:
        e, w, nf, nt = check_file(f, labels)
        errors.extend(e)
        warnings.extend(w)
        n_fig += nf
        n_tbl += nt
    for label, where in sorted(labels.items()):
        if len(where) > 1 and label.split("-")[0] in ("fig", "tbl", "sec", "eq"):
            errors.append(f"duplicate label {label}: {', '.join(where)}")
    for line in errors:
        print(f"ERROR {line}")
    for line in warnings:
        print(f"WARNING {line}")
    print(f"files_examined={len(files)} figure_labels={n_fig} table_labels={n_tbl} "
          f"errors={len(errors)} warnings={len(warnings)}")
    if not files:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
