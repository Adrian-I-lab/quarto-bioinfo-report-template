#!/usr/bin/env python3
"""Prose linter for .qmd and .md files.

Errors:
  EM-DASH         U+2014 anywhere in the file, code and YAML included.
  SPACED-EN-DASH  U+2013 with a space on either side, used as a dash.
  BANNED          a filler phrase from [prose].banned.
Warnings:
  SPELLING        a US form from [prose.spelling]. Allow a line with
                  <!-- spelling-ok -->.
  LONG-SENTENCE   more than [prose].max_sentence_words words.

Banned-phrase, spelling, and sentence rules skip YAML, fenced code,
inline code, comments, URLs, and citation keys. The dash rules skip
nothing.

Exit codes: 0 pass, 1 errors (or warnings with --strict), 2 nothing examined.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qmd  # noqa: E402

EM_DASH = "—"
EN_DASH = "–"
_URL = re.compile(r"https?://\S+|<[^>\s]+>|\]\([^)]*\)")
_CITE = re.compile(r"\[?-?@[\w:.-]+\]?")
_ABBREV = re.compile(r"\b(e\.g|i\.e|et al|vs|Fig|Figs|approx|cf|etc)\.", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.?!])\s+(?=[\"'(*]*[A-Z0-9])")
_SPACED_EN = re.compile(rf"(\s{EN_DASH}|{EN_DASH}\s)")


def clean(text: str) -> str:
    text = _URL.sub(" ", text)
    return _CITE.sub(" ", text)


def check_file(path: Path, cfg: dict) -> tuple[list[str], list[str]]:
    prose = cfg["prose"]
    errors, warnings = [], []
    raw = path.read_text(encoding="utf-8").splitlines()

    for n, line in enumerate(raw, start=1):
        if EM_DASH in line:
            errors.append(f"{path}:{n}: EM-DASH: {line.strip()[:100]}")
        if _SPACED_EN.search(line):
            errors.append(f"{path}:{n}: SPACED-EN-DASH: {line.strip()[:100]}")

    spelling = prose.get("spelling", {})
    if spelling:
        sp_re = re.compile(r"\b(" + "|".join(map(re.escape, spelling)) + r")\b", re.IGNORECASE)
        for n, line in _qmd.prose_lines(path):
            if "spelling-ok" in raw[n - 1]:
                continue
            for m in sp_re.finditer(clean(line)):
                word = m.group(1)
                warnings.append(
                    f"{path}:{n}: SPELLING: '{word}' -> '{spelling[word.lower()]}'"
                )

    banned = [b.lower() for b in prose.get("banned", [])]
    limit = int(prose.get("max_sentence_words", 35))
    for start, text in _qmd.iter_paragraphs(path):
        norm = _qmd.normalise(clean(text))
        for phrase in banned:
            if re.search(r"\b" + re.escape(phrase) + r"\b", norm):
                errors.append(f"{path}:{start}: BANNED: '{phrase}'")
        if text.lstrip().startswith("|"):
            continue
        body = _ABBREV.sub(lambda m: m.group(1).replace(".", ""), clean(text))
        for sentence in _SENTENCE_SPLIT.split(body):
            words = len(sentence.split())
            if words > limit:
                warnings.append(
                    f"{path}:{start}: LONG-SENTENCE: {words} words: {' '.join(sentence.split())[:80]}"
                )
    return errors, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Prose linter for .qmd and .md files.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--strict", action="store_true", help="fail on warnings too")
    ap.add_argument("--config", default=None, help="path to style-checks.toml")
    args = ap.parse_args(argv)

    cfg = _qmd.load_config(args.config)
    exclude = set(cfg.get("scan", {}).get("exclude", [])) | {"tests/fixtures/"}
    files = _qmd.collect_files(args.paths, [".qmd", ".md"], exclude)

    errors, warnings = [], []
    for f in files:
        e, w = check_file(f, cfg)
        errors.extend(e)
        warnings.extend(w)
    for line in errors:
        print(f"ERROR {line}")
    for line in warnings:
        print(f"WARNING {line}")
    print(f"files_examined={len(files)} errors={len(errors)} warnings={len(warnings)}")
    if not files:
        return 2
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
