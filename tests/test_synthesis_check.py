"""Fail-then-pass tests for tools/style/synthesis_check.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "tools" / "style" / "synthesis_check.py"

BANNER = """::: {.callout-important}
## This chapter is interpretation, not a result
No number in it is new.
:::
"""

GOOD = BANNER + """
## What was measured

A table.

## The reading

1. **Reading one.** A sentence.
   *Evidence:* @sec-a.
   *Why it could be wrong:* a counter-argument.
2. **Reading two.** A sentence.
   *Evidence:* @sec-b.
   *Why it could be wrong:* a counter-argument.

## What the data does not show

Text.

## Questions for the bench

Text.

## Recommendation

Text.
"""

SKELETON = GOOD.replace(
    GOOD[GOOD.index("1. **Reading one"):GOOD.index("## What the data")],
    "::: {.callout-important}\n## To be written\nItems go here.\n:::\n\n",
)


def run_text(text):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "90-interpretation.qmd"
        path.write_text(text, encoding="utf-8")
        proc = subprocess.run([sys.executable, str(CHECK), str(path)],
                              capture_output=True, text=True, cwd=ROOT)
    return proc.returncode, proc.stdout


class TestSynthesisCheck(unittest.TestCase):
    def test_complete_chapter_passes(self):
        code, out = run_text(GOOD)
        self.assertEqual(code, 0, out)

    def test_missing_why_on_item_two_fails_then_passes(self):
        bad = GOOD[: GOOD.index("2. **Reading two")] + GOOD[GOOD.index("2. **Reading two"):].replace(
            "   *Why it could be wrong:* a counter-argument.\n", "")
        code, out = run_text(bad)
        self.assertEqual(code, 1)
        self.assertIn("reading item 2 lacks 'Why it could be wrong:'", out)
        code, _ = run_text(GOOD)
        self.assertEqual(code, 0)

    def test_missing_recommendation_fails(self):
        code, out = run_text(GOOD.replace("## Recommendation", "## Next"))
        self.assertEqual(code, 1)
        self.assertIn("missing section 'Recommendation'", out)

    def test_missing_banner_fails(self):
        code, out = run_text(GOOD.replace("This chapter is interpretation, not a result", "Notes"))
        self.assertEqual(code, 1)
        self.assertIn("banner", out)

    def test_skeleton_passes_with_warning(self):
        code, out = run_text(SKELETON)
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING", out)

    def test_missing_file_exits_2(self):
        proc = subprocess.run([sys.executable, str(CHECK), "no/such/file.qmd"],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 2)

    def test_repository_chapters_pass(self):
        proc = subprocess.run([sys.executable, str(CHECK)], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()
