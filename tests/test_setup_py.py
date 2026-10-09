"""Tests for _setup.py. Skipped cleanly when numpy, pandas, or matplotlib is missing."""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAS_NUMPY = all(
    importlib.util.find_spec(m) is not None for m in ("numpy", "pandas", "matplotlib")
)

if HAS_NUMPY:
    sys.path.insert(0, str(ROOT))
    import _setup as s  # noqa: E402


@unittest.skipUnless(HAS_NUMPY, "numpy, pandas, or matplotlib is not installed")
class TestSetupPy(unittest.TestCase):
    def test_counts_are_deterministic(self):
        a = s.synth_counts(seed=7)["counts"]
        b = s.synth_counts(seed=7)["counts"]
        self.assertTrue(a.equals(b))

    def test_counts_shape_and_names(self):
        sc = s.synth_counts(n_genes=500, n_per_group=3)
        self.assertEqual(sc["counts"].shape, (500, 6))
        self.assertEqual(sc["counts"].index[0], "gene0001")
        self.assertEqual(list(sc["samples"]["group"]).count("treated"), 3)

    def test_forty_planted_changes(self):
        truth = s.synth_counts()["truth"]
        self.assertEqual(int(truth["planted"].sum()), 40)
        self.assertTrue((truth.loc[truth["planted"], "log2FC_true"].abs() >= 1).all())

    def test_frac(self):
        self.assertEqual(s.frac(3, 12), "3 of 12 (25.0%)")
        self.assertEqual(s.fmt(1234567), "1,234,567")
        self.assertEqual(s.pct(0.5, 0), "50%")

    def test_null_param_stops_with_message(self):
        with self.assertRaisesRegex(RuntimeError, "not decided yet; record the decision in _params.yml"):
            s.report_param("decided_later", root=ROOT)
        self.assertEqual(s.report_param("fdr", root=ROOT), 0.05)

    def test_missing_param_stops(self):
        with self.assertRaisesRegex(RuntimeError, "not decided yet"):
            s.report_param("no_such_key", root=ROOT)

    def test_flat_yaml_fallback(self):
        values = s._read_flat_yaml("a: 1\nb: null\nc: 0.5 # note\nd: text\n")
        self.assertEqual(values, {"a": 1, "b": None, "c": 0.5, "d": "text"})

    def test_report_root_walks_up_and_honours_env(self):
        self.assertEqual(s.report_root(ROOT / "chapters"), ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("REPORT_ROOT")
            os.environ["REPORT_ROOT"] = tmp
            try:
                with self.assertRaisesRegex(RuntimeError, "holds no _quarto.yml"):
                    s.report_root()
            finally:
                if old is None:
                    del os.environ["REPORT_ROOT"]
                else:
                    os.environ["REPORT_ROOT"] = old

    def test_welch_p_matches_known_value(self):
        # Two-sided p for t = 2 on 10 degrees of freedom is 0.0734 (4 d.p.).
        p = s._betainc(5.0, 0.5, 10 / (10 + 4))
        self.assertAlmostEqual(p, 0.0734, places=4)

    def test_de_table(self):
        de = s.synth_de()
        self.assertEqual(len(de), 500)
        self.assertTrue(((de["FDR"] >= de["p"]) & (de["FDR"] <= 1)).all())
        self.assertTrue(de.equals(s.synth_de()))

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.txt"
            path.write_text("abc\n", encoding="utf-8")
            self.assertEqual(s.sha256_file(path), "edeaaff3f1774ad2")

    def test_embedding(self):
        emb = s.synth_embedding(n=900, k=3)
        self.assertEqual(emb.shape, (900, 3))
        self.assertEqual(emb["cluster"].nunique(), 3)


if __name__ == "__main__":
    unittest.main()
