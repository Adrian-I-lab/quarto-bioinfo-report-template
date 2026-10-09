"""Fail-then-pass tests for tools/style/register_guard.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "tools" / "style" / "register_guard.py"
FIX = ROOT / "tests" / "fixtures" / "register"


def run(*args):
    proc = subprocess.run(
        [sys.executable, str(GUARD), *map(str, args)],
        capture_output=True, text=True, cwd=ROOT,
    )
    return proc.returncode, proc.stdout


def violations(out):
    return int(out.strip().splitlines()[-1].split("violations=")[1].split()[0])


class TestRegisterGuard(unittest.TestCase):
    def test_simple_bad_then_good(self):
        _, out = run(FIX / "bad_simple.qmd")
        self.assertEqual(violations(out), 1)
        self.assertIn("suggests that", out)
        _, out = run(FIX / "good_simple.qmd")
        self.assertEqual(violations(out), 0)

    def test_hard_wrapped_phrase_is_caught(self):
        _, out = run(FIX / "hard_wrap.qmd")
        self.assertEqual(violations(out), 1)
        self.assertIn("the simplest explanation", out)

    def test_denial_excuses_hit(self):
        _, out = run(FIX / "denial.qmd")
        self.assertEqual(violations(out), 0)

    def test_distant_denial_does_not_excuse(self):
        _, out = run(FIX / "denial_far.qmd")
        self.assertEqual(violations(out), 1)

    def test_code_and_comments_are_skipped(self):
        _, out = run(FIX / "code_and_comment.qmd")
        self.assertEqual(violations(out), 0)

    def test_opt_out_with_reason_excuses(self):
        _, out = run(FIX / "opt_out_reason.qmd")
        self.assertEqual(violations(out), 0)

    def test_opt_out_without_reason_is_reported(self):
        _, out = run(FIX / "opt_out_no_reason.qmd")
        self.assertIn("opt-out without a reason", out)
        self.assertGreaterEqual(violations(out), 1)

    def test_exempt_file_is_skipped(self):
        code, out = run(FIX / "exempt" / "90-interpretation.qmd")
        self.assertIn("files_examined=0", out)
        self.assertEqual(code, 2)

    def test_empty_folder_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run(tmp)
        self.assertEqual(code, 2)
        self.assertIn("files_examined=0", out)

    def test_strict_flips_exit_code(self):
        code, out = run(FIX / "bad_simple.qmd")
        self.assertEqual(code, 0)
        self.assertIn("strict=no", out)
        code, out = run("--strict", FIX / "bad_simple.qmd")
        self.assertEqual(code, 1)
        code, _ = run("--strict", FIX / "good_simple.qmd")
        self.assertEqual(code, 0)

    def test_repository_content_is_clean(self):
        code, out = run("--strict", ROOT / "chapters", ROOT / "gallery")
        examined = int(out.strip().splitlines()[-1].split("files_examined=")[1].split()[0])
        # The template itself (with its gallery) has at least 10 files to read.
        self.assertGreaterEqual(examined, 10 if (ROOT / "gallery").exists() else 1)
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
