#!/usr/bin/env python3
"""Register guard: flags interpretive constructions outside the synthesis.

Every chapter before the synthesis is descriptive and quantitative. This
guard reads the prose of .qmd files and reports multi-word interpretive
constructions listed in style-checks.toml.

It is a heuristic over English, so it is a warning by default. With
--strict, any violation fails the run.

Exit codes: 0 pass (or warnings only), 1 violations with --strict,
2 nothing was examined (a check that examines nothing must not pass).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _qmd  # noqa: E402


def find_hits(text: str, phrases: list[str], denials: list[str], window: int):
    """Return (phrase, index) for each hit not excused by a nearby denial."""
    norm = _qmd.normalise(text)
    hits = []
    for phrase in phrases:
        p = _qmd.normalise(phrase)
        start = 0
        while True:
            idx = norm.find(p, start)
            if idx == -1:
                break
            before = norm[max(0, idx - window):idx]
            if not any(_qmd.normalise(d) in before for d in denials):
                hits.append((phrase, idx))
            start = idx + 1
    return sorted(hits, key=lambda h: h[1])


def check_file(path: Path, cfg: dict) -> list[str]:
    reg = cfg["register"]
    window = int(reg.get("denial_window", 90))
    opt_ok = _qmd.opt_out_lines(path)
    findings = []
    for line in _qmd.bad_opt_outs(path):
        findings.append(f"{path}:{line}: opt-out without a reason: a register-ok comment must say why")
    for start, end, text in _qmd.iter_paragraph_spans(path):
        if any(start - 2 <= n <= end for n in opt_ok):
            continue
        for phrase, _idx in find_hits(text, reg["interpretive"], reg["denials"], window):
            excerpt = " ".join(text.split())[:120]
            findings.append(f"{path}:{start}: {phrase}: {excerpt}")
    return findings


def is_exempt(path: Path, root: Path, exempt: list[str]) -> bool:
    rel = _qmd.relative(path, root)
    names = {Path(e).name for e in exempt}
    return rel in exempt or path.name in names


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--strict", action="store_true", help="fail on any violation")
    ap.add_argument("--config", default=None, help="path to style-checks.toml")
    args = ap.parse_args(argv)

    cfg = _qmd.load_config(args.config)
    root = _qmd.config_root(args.config)
    exclude = cfg.get("scan", {}).get("exclude", [])
    files = _qmd.collect_files(args.paths, [".qmd"], exclude)
    files = [f for f in files if not is_exempt(f, root, cfg["register"].get("exempt", []))]

    findings = []
    for f in files:
        findings.extend(check_file(f, cfg))
    for line in findings:
        print(line)
    print(f"files_examined={len(files)} violations={len(findings)} "
          f"strict={'yes' if args.strict else 'no'}")
    if not files:
        return 2
    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
