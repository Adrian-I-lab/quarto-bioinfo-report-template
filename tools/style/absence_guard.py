#!/usr/bin/env python3
"""Absence-claim guard.

"No difference", "unchanged", and similar phrases claim that something is
absent. Each needs, in the same paragraph, an equivalence result or the
detection floor (a marker from [absence].markers, or a cross-reference to
the detection-floor section). A denial shortly before the phrase also
excuses it ("this does not show that ... is unchanged").

This is an error by default: an unsupported absence claim makes a
statement false, not just badly placed.

Exit codes: 0 pass, 1 violations, 2 nothing examined.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qmd  # noqa: E402


def check_text(text: str, cfg: dict) -> list[str]:
    """Return the unsupported absence phrases in one paragraph."""
    absence = cfg["absence"]
    norm = _qmd.normalise(text)
    markers = [m.lower() for m in absence.get("markers", [])]
    section = absence.get("detection_floor_section")
    if section:
        markers.append("@" + section.lower())
    if any(m in norm for m in markers):
        return []
    denials = [_qmd.normalise(d) for d in cfg["register"].get("denials", [])]
    window = int(cfg["register"].get("denial_window", 90))
    found = []
    for phrase in absence["phrases"]:
        for m in re.finditer(r"\b" + re.escape(phrase.lower()) + r"\b", norm):
            before = norm[max(0, m.start() - window):m.start()]
            if not any(d in before for d in denials):
                found.append(phrase)
                break
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Absence-claim guard.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--config", default=None, help="path to style-checks.toml")
    args = ap.parse_args(argv)

    cfg = _qmd.load_config(args.config)
    exclude = cfg.get("scan", {}).get("exclude", [])
    files = _qmd.collect_files(args.paths, [".qmd"], exclude)
    findings = []
    for f in files:
        for start, text in _qmd.iter_paragraphs(f):
            for phrase in check_text(text, cfg):
                findings.append(
                    f"{f}:{start}: unsupported absence claim '{phrase}': "
                    "add an equivalence result or the detection floor to this paragraph"
                )
    for line in findings:
        print(line)
    print(f"files_examined={len(files)} violations={len(findings)}")
    if not files:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
