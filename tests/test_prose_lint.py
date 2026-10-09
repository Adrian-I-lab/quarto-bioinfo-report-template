"""Fail-then-pass tests for tools/style/prose_lint.py.

Defect files are written to a temporary folder at test time. Dashes are
built from escapes, so no tracked file holds a literal em dash.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINT = ROOT / "tools" / "style" / "prose_lint.py"
EM = "\u2014"
EN = "\u2013"


def lint(text, name="doc.qmd", *flags):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(LINT), *flags, str(path)],
            capture_output=True, text=True, cwd=ROOT,
        )
    return proc.returncode, proc.stdout


def counts(out):
    last = out.strip().splitlines()[-1]
    fields = dict(part.split("=") for part in last.split())
    return int(fields["errors"]), int(fields["warnings"])


class TestProseLint(unittest.TestCase):
    def test_em_dash_in_prose(self):
        code, out = lint(f"The depth fell {EM} sharply.\n")
        self.assertEqual(code, 1)
        self.assertIn("EM-DASH", out)
        code, out = lint("The depth fell sharply.\n")
        self.assertEqual(code, 0)

    def test_em_dash_in_yaml_comment(self):
        code, out = lint(f"---\ntitle: x # a note {EM} here\n---\n\nText.\n")
        self.assertEqual(code, 1)
        self.assertIn("EM-DASH", out)
        code, _ = lint("---\ntitle: x # a note, here\n---\n\nText.\n")
        self.assertEqual(code, 0)

    def test_spaced_en_dash(self):
        code, out = lint(f"The depth fell {EN} sharply.\n")
        self.assertEqual(code, 1)
        self.assertIn("SPACED-EN-DASH", out)

    def test_unspaced_numeric_range_is_allowed(self):
        code, out = lint(f"Samples 3{EN}6 were sequenced again.\n")
        self.assertEqual(code, 0, out)

    def test_banned_phrase(self):
        code, out = lint("We filtered the table in order to remove noise.\n")
        self.assertEqual(code, 1)
        self.assertIn("BANNED", out)
        code, _ = lint("We filtered the table to remove noise.\n")
        self.assertEqual(code, 0)

    def test_banned_phrase_inside_inline_code_is_skipped(self):
        code, out = lint("Avoid `in order to` in prose.\n", "guide.md")
        self.assertEqual(code, 0, out)

    def test_us_spelling_warns(self):
        code, out = lint("Each point has a color.\n")
        self.assertEqual(code, 0)
        self.assertEqual(counts(out), (0, 1))
        self.assertIn("'color' -> 'colour'", out)
        code, _ = lint("Each point has a color.\n", "doc.qmd", "--strict")
        self.assertEqual(code, 1)
        _, out = lint("Each point has a colour.\n")
        self.assertEqual(counts(out), (0, 0))

    def test_spelling_inside_inline_code_passes(self):
        _, out = lint("Set `color = 'red'` in the call.\n")
        self.assertEqual(counts(out), (0, 0))

    def test_spelling_opt_out(self):
        _, out = lint("The argument is named color. <!-- spelling-ok -->\n")
        self.assertEqual(counts(out), (0, 0))

    def test_long_sentence_warns(self):
        words = " ".join(["word"] * 50)
        _, out = lint(f"This {words} ends.\n")
        self.assertEqual(counts(out), (0, 1))
        self.assertIn("LONG-SENTENCE", out)
        short = " ".join(["word"] * 20)
        _, out = lint(f"This {short} ends. This {short} ends.\n")
        self.assertEqual(counts(out), (0, 0))

    def test_abbreviation_does_not_split(self):
        # 30 words with "e.g." in the middle stays one sentence of 30 words.
        text = " ".join(["word"] * 14) + " e.g. Word " + " ".join(["word"] * 14) + ".\n"
        _, out = lint(text)
        self.assertEqual(counts(out), (0, 0))
        text = " ".join(["word"] * 20) + " e.g. Word " + " ".join(["word"] * 20) + ".\n"
        _, out = lint(text)
        self.assertEqual(counts(out), (0, 1))

    def test_empty_folder_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(LINT), tmp], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_repository_has_no_errors(self):
        proc = subprocess.run([sys.executable, str(LINT), "."], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        examined = int(proc.stdout.strip().splitlines()[-1].split("files_examined=")[1].split()[0])
        self.assertGreaterEqual(examined, 15 if (ROOT / "gallery").exists() else 1)


if __name__ == "__main__":
    unittest.main()
