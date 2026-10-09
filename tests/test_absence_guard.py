"""Fail-then-pass tests for tools/style/absence_guard.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "tools" / "style" / "absence_guard.py"


def run_text(text):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "chapter.qmd"
        path.write_text(text, encoding="utf-8")
        proc = subprocess.run([sys.executable, str(GUARD), str(path)],
                              capture_output=True, text=True, cwd=ROOT)
    return proc.returncode, proc.stdout


class TestAbsenceGuard(unittest.TestCase):
    def test_bare_absence_claim_fails(self):
        code, out = run_text("Expression was unchanged between groups.\n")
        self.assertEqual(code, 1)
        self.assertIn("unchanged", out)

    def test_equivalence_result_passes(self):
        code, out = run_text(
            "Expression was unchanged between groups "
            "(equivalence bound 0.5 log2 units, TOST p = 0.01).\n")
        self.assertEqual(code, 0, out)

    def test_detection_floor_reference_passes(self):
        code, out = run_text(
            "Expression was unchanged between groups at this design's floor "
            "(@sec-detection-floor).\n")
        self.assertEqual(code, 0, out)

    def test_denial_passes(self):
        code, out = run_text("This figure does not show that expression is unchanged.\n")
        self.assertEqual(code, 0, out)

    def test_hard_wrapped_phrase_is_caught(self):
        code, out = run_text("There was no\ndifference between the groups.\n")
        self.assertEqual(code, 1)
        self.assertIn("no difference", out)

    def test_marker_in_another_paragraph_does_not_count(self):
        code, _ = run_text(
            "The equivalence test is described later.\n\n"
            "There was no difference between the groups.\n")
        self.assertEqual(code, 1)

    def test_empty_folder_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(GUARD), tmp], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_repository_content_is_clean(self):
        proc = subprocess.run(
            [sys.executable, str(GUARD), "chapters", "reference", "gallery"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout)


if __name__ == "__main__":
    unittest.main()
