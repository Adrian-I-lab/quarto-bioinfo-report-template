"""Shared parsing for the style checks. Python 3.11+ standard library only.

The checks read prose, not code. This module removes YAML front matter,
fenced code blocks and executable chunks, HTML comments (including
multi-line draft-question blocks and opt-out comments), inline code, raw
HTML lines, Pandoc attribute blocks, and div fences. It keeps the source
line number of every prose line, so a finding points at the right line.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "style-checks.toml"

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_INLINE_CODE = re.compile(r"`+[^`\n]*`+")
_ATTR_BLOCK = re.compile(r"\{[#.][^}]*\}|\{=[a-z]+\}")
_RAW_HTML_LINE = re.compile(r"^\s*</?[A-Za-z!][^>]*>\s*$")
_DIV_FENCE = re.compile(r"^\s*:{3,}")
_NEW_BLOCK = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|\|)")
_OPT_OUT = re.compile(r"<!--\s*register-ok\b:?(.*?)(-->|$)")


def load_config(path: str | Path | None = None) -> dict:
    with open(path or DEFAULT_CONFIG, "rb") as fh:
        return tomllib.load(fh)


def config_root(path: str | Path | None = None) -> Path:
    return Path(path).resolve().parent if path else REPO_ROOT


def collect_files(paths, exts, exclude=()) -> list[Path]:
    """Expand files and folders into a sorted list of files with given extensions.

    Exclusions apply to files found inside a folder, matched against the
    path relative to that folder. A file named explicitly is always kept.
    """
    found: set[Path] = set()
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for ext in exts:
                for f in p.rglob(f"*{ext}"):
                    rel = "/" + f.relative_to(p).as_posix()
                    if any(f"/{e.strip('/')}/" in rel for e in exclude):
                        continue
                    found.add(f)
        elif p.is_file() and p.suffix in exts:
            found.add(p)
    return sorted(found)


def _strip_comments(lines: list[str]) -> list[str]:
    """Blank out HTML comments, which may span lines, keeping line count."""
    out = []
    in_comment = False
    for line in lines:
        result = ""
        rest = line
        while rest:
            if in_comment:
                end = rest.find("-->")
                if end == -1:
                    rest = ""
                else:
                    rest = rest[end + 3:]
                    in_comment = False
            else:
                start = rest.find("<!--")
                if start == -1:
                    result += rest
                    rest = ""
                else:
                    result += rest[:start]
                    rest = rest[start + 4:]
                    in_comment = True
        out.append(result)
    return out


def code_mask(lines: list[str]) -> list[bool]:
    """True for each line that is YAML front matter or inside a fenced block."""
    mask = [False] * len(lines)
    i = 0
    if lines and lines[0].strip() == "---":
        mask[0] = True
        i = 1
        while i < len(lines):
            mask[i] = True
            if lines[i].strip() in ("---", "..."):
                i += 1
                break
            i += 1
    fence = None
    while i < len(lines):
        m = _FENCE.match(lines[i])
        if fence is None and m:
            fence = m.group(1)
            mask[i] = True
        elif fence is not None:
            mask[i] = True
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                    and lines[i].strip() == m.group(1):
                fence = None
        i += 1
    return mask


def prose_lines(path: str | Path) -> list[tuple[int, str]]:
    """Every source line as (line_number, prose_text); non-prose becomes ''."""
    raw = Path(path).read_text(encoding="utf-8").splitlines()
    mask = code_mask(raw)
    # Inline code goes first, so a quoted "<!--" cannot open a comment.
    no_code = ["" if m else _INLINE_CODE.sub(" ", line) for line, m in zip(raw, mask)]
    stripped = _strip_comments(no_code)
    out = []
    for n, line in enumerate(stripped, start=1):
        if _RAW_HTML_LINE.match(line) or _DIV_FENCE.match(line):
            line = ""
        line = _ATTR_BLOCK.sub(" ", line)
        out.append((n, line))
    return out


def iter_paragraph_spans(path: str | Path):
    """Yield (first_line, last_line, text) for each prose paragraph.

    Headings, list items, and table rows each start a new paragraph.
    """
    start = end = None
    buf: list[str] = []
    for n, line in prose_lines(path):
        if not line.strip():
            if buf:
                yield start, end, " ".join(buf)
            start, buf = None, []
            continue
        if buf and _NEW_BLOCK.match(line):
            yield start, end, " ".join(buf)
            start, buf = None, []
        if start is None:
            start = n
        end = n
        buf.append(line.strip())
    if buf:
        yield start, end, " ".join(buf)


def iter_paragraphs(path: str | Path):
    """Yield (line_number, text) for each prose paragraph."""
    for start, _end, text in iter_paragraph_spans(path):
        yield start, text


def normalise(text: str) -> str:
    """Collapse all whitespace to single spaces and lower-case."""
    return " ".join(text.split()).lower()


def _opt_outs(path: str | Path):
    raw = Path(path).read_text(encoding="utf-8").splitlines()
    mask = code_mask(raw)
    for n, (line, in_code) in enumerate(zip(raw, mask), start=1):
        if in_code:
            continue
        for m in _OPT_OUT.finditer(_INLINE_CODE.sub(" ", line)):
            yield n, m.group(1).strip()


def opt_out_lines(path: str | Path) -> list[int]:
    """Line numbers carrying 'register-ok:' with a non-empty reason."""
    return [n for n, reason in _opt_outs(path) if reason]


def bad_opt_outs(path: str | Path) -> list[int]:
    """Line numbers carrying 'register-ok:' without a reason."""
    return [n for n, reason in _opt_outs(path) if not reason]


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
