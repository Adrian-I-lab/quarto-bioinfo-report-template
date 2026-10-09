"""Tests for scripts/new_book.py. Every test works on a temporary copy."""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "new_book.py"
IGNORE = shutil.ignore_patterns(".git", ".venv", "_book", "_freeze", ".quarto", "figures",
                                "__pycache__", "*.quarto_ipynb")


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


TEMPLATE = (ROOT / "scripts" / "skeleton.sha256").exists()


@unittest.skipUnless(TEMPLATE, "the book has been scaffolded, so the template tests do not apply")
class TestNewBook(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.copy = Path(self._tmp.name) / "book"
        shutil.copytree(ROOT, self.copy, ignore=IGNORE)

    def tearDown(self):
        self._tmp.cleanup()

    def run_script(self, *args):
        return subprocess.run(
            [sys.executable, str(self.copy / "scripts" / "new_book.py"), *args],
            capture_output=True, text=True, cwd=self.copy,
        )

    def base_args(self):
        return ["--title", "Example two-group comparison", "--subtitle", "Which features change",
                "--author", "Example Author"]

    def test_manifest_matches_shipped_skeleton(self):
        for line in (ROOT / "scripts" / "skeleton.sha256").read_text().splitlines():
            digest, rel = line.split()
            self.assertEqual(
                hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), digest,
                f"{rel} differs from scripts/skeleton.sha256. In the template, update the manifest. "
                "In your own book, run scripts/new_book.py or delete scripts/skeleton.sha256.")

    def test_title_subtitle_and_author_replaced(self):
        proc = self.run_script(*self.base_args())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = (self.copy / "_quarto.yml").read_text()
        self.assertIn('  title: "Example two-group comparison"', text)
        self.assertIn('  subtitle: "Which features change"', text)
        self.assertIn('  author: "Example Author"', text)
        self.assertNotIn("Your Name", text)
        self.assertIn("# Chapter order is an argument", text)
        self.assertFalse((self.copy / "scripts" / "skeleton.sha256").exists())

    def test_chapters_created_in_order(self):
        proc = self.run_script(*self.base_args(), "--chapters", "Design;Quality control;Results")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        made = sorted(p.name for p in (self.copy / "chapters").glob("*.qmd"))
        self.assertEqual(made, ["01-design.qmd", "02-quality-control.qmd", "03-results.qmd",
                                "90-interpretation.qmd"])
        starter = (self.copy / "_quarto-starter.yml").read_text()
        order = [starter.index(f"chapters/{n}") for n in
                 ("01-design.qmd", "02-quality-control.qmd", "03-results.qmd", "90-interpretation.qmd")]
        self.assertEqual(order, sorted(order))
        self.assertNotIn("detection-floor", starter)
        chapter = (self.copy / "chapters" / "02-quality-control.qmd").read_text()
        for element in ("{#sec-quality-control}", 'source("../_setup.R")', "In plain terms",
                        "Status", "**Question.**", "**Design.**", "<!-- Q"):
            self.assertIn(element, chapter)
        interp = (self.copy / "chapters" / "90-interpretation.qmd").read_text()
        self.assertNotIn("@sec-design-samples", interp)
        self.assertIn("@sec-design", interp)

    def test_python_engine(self):
        proc = self.run_script(*self.base_args(), "--engine", "python", "--chapters", "Results")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        chapter = (self.copy / "chapters" / "01-results.qmd").read_text()
        self.assertIn("jupyter: python3", chapter)
        self.assertIn("import _setup as s", chapter)
        self.assertNotIn("source(", chapter)

    def test_drop_gallery(self):
        proc = self.run_script(*self.base_args(), "--drop-gallery")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.copy / "gallery").exists())
        self.assertFalse((self.copy / "_quarto-gallery.yml").exists())
        self.assertIn("remove gallery", proc.stdout)
        self.assertNotIn("<!-- gallery:begin -->", (self.copy / "README.md").read_text())

    def test_dry_run_changes_nothing(self):
        before = snapshot(self.copy)
        proc = self.run_script(*self.base_args(), "--chapters", "A;B", "--drop-gallery", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("would remove gallery", proc.stdout)
        after = snapshot(self.copy)
        changed = [k for k in set(before) | set(after) if before.get(k) != after.get(k)]
        self.assertEqual(changed, [])

    def test_refuses_to_overwrite_edited_chapters(self):
        path = self.copy / "chapters" / "02-quality.qmd"
        path.write_text(path.read_text() + "\nMy own notes.\n")
        proc = self.run_script(*self.base_args(), "--chapters", "Design")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("02-quality.qmd", proc.stderr)
        self.assertTrue(path.exists())
        proc = self.run_script(*self.base_args(), "--chapters", "Design", "--force")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(path.exists())

    @unittest.skipIf(os.environ.get("NEW_BOOK_NESTED"), "already inside a scaffolded copy")
    def test_check_style_passes_on_scaffolded_copy(self):
        proc = self.run_script(*self.base_args(), "--chapters", "Design;Quality;Results", "--drop-gallery")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # NEW_BOOK_NESTED stops the copy's own copy of this test from recursing.
        env = dict(os.environ, NEW_BOOK_NESTED="1", PYTHON=sys.executable)
        proc = subprocess.run(["bash", "scripts/check_style.sh"], capture_output=True, text=True,
                              cwd=self.copy, env=env)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("check_style: PASS", proc.stdout)

if __name__ == "__main__":
    unittest.main()
