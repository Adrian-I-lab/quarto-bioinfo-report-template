"""Fail-then-pass tests for tools/style/caption_check.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "tools" / "style" / "caption_check.py"

CAP = "Counts per sample for 500 synthetic features, coloured by group."
GOOD_FIG = f"""```{{r}}
#| label: fig-depth
#| fig-cap: "{CAP}"
#| fig-alt: "A bar chart with six bars."
plot(1)
```
"""


def run_files(files):
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for name, text in files.items():
            p = Path(tmp) / name
            p.write_text(text, encoding="utf-8")
            paths.append(str(p))
        proc = subprocess.run([sys.executable, str(CHECK), *paths],
                              capture_output=True, text=True, cwd=ROOT)
    return proc.returncode, proc.stdout


class TestCaptionCheck(unittest.TestCase):
    def test_good_figure_passes(self):
        code, out = run_files({"a.qmd": GOOD_FIG})
        self.assertEqual(code, 0, out)
        self.assertIn("figure_labels=1", out)

    def test_missing_fig_cap(self):
        code, out = run_files({"a.qmd": GOOD_FIG.replace(f'#| fig-cap: "{CAP}"\n', "")})
        self.assertEqual(code, 1)
        self.assertIn("missing fig-cap", out)

    def test_missing_fig_alt(self):
        code, out = run_files({"a.qmd": GOOD_FIG.replace('#| fig-alt: "A bar chart with six bars."\n', "")})
        self.assertEqual(code, 1)
        self.assertIn("missing fig-alt", out)

    def test_caption_without_full_stop(self):
        code, out = run_files({"a.qmd": GOOD_FIG.replace("by group.", "by group")})
        self.assertEqual(code, 1)
        self.assertIn("full stop", out)

    def test_short_caption(self):
        code, out = run_files({"a.qmd": GOOD_FIG.replace(CAP, "Counts per sample.")})
        self.assertEqual(code, 1)
        self.assertIn("fewer than 8 words", out)

    def test_multiline_caption_passes(self):
        text = GOOD_FIG.replace(f'#| fig-cap: "{CAP}"', f"#| fig-cap: >-\n#|   {CAP}")
        code, out = run_files({"a.qmd": text})
        self.assertEqual(code, 0, out)

    def test_duplicate_label_across_files(self):
        code, out = run_files({"a.qmd": GOOD_FIG, "b.qmd": GOOD_FIG})
        self.assertEqual(code, 1)
        self.assertIn("duplicate label fig-depth", out)
        code, _ = run_files({"a.qmd": GOOD_FIG, "b.qmd": GOOD_FIG.replace("fig-depth", "fig-depth-b")})
        self.assertEqual(code, 0)

    def test_table_chunk_without_caption(self):
        text = "```{r}\n#| label: tbl-counts\nknitr::kable(x)\n```\n"
        code, out = run_files({"a.qmd": text})
        self.assertEqual(code, 1)
        self.assertIn("missing tbl-cap", out)
        code, _ = run_files({"a.qmd": text.replace("\nknitr", '\n#| tbl-cap: "Counts."\nknitr')})
        self.assertEqual(code, 0)

    def test_markdown_image_without_alt(self):
        text = "![A figure of counts per sample.](a.png){#fig-a}\n"
        code, out = run_files({"a.qmd": text})
        self.assertEqual(code, 1)
        self.assertIn("no fig-alt", out)
        code, _ = run_files({"a.qmd": text.replace("{#fig-a}", '{#fig-a fig-alt="Six bars."}')})
        self.assertEqual(code, 0)

    def test_unlabelled_plot_warns(self):
        code, out = run_files({"a.qmd": "```{r}\nggplot(d)\n```\n"})
        self.assertEqual(code, 0)
        self.assertIn("unlabelled figure", out)

    def test_labels_in_source_examples_are_ignored(self):
        text = GOOD_FIG + "\n````markdown\n" + GOOD_FIG + "````\n"
        code, out = run_files({"a.qmd": text})
        self.assertEqual(code, 0, out)

    def test_empty_folder_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(CHECK), tmp], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_repository_content_passes(self):
        proc = subprocess.run([sys.executable, str(CHECK), "chapters", "reference", "gallery"],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        figs = int(proc.stdout.strip().splitlines()[-1].split("figure_labels=")[1].split()[0])
        self.assertGreaterEqual(figs, 8)


if __name__ == "__main__":
    unittest.main()
