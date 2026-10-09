"""Shared setup for every Python chapter.

Quarto renders each chapter of a book in its own session, so there is no
global setup. The first (hidden) cell of every Python chapter imports this
module. It mirrors the helpers in _setup.R. The same seeds give the same
outputs on every run, although the exact values differ from R.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SEED = 1

# ---------------------------------------------------------------------------
# Locating the book
# ---------------------------------------------------------------------------


def report_root(start: str | os.PathLike | None = None) -> Path:
    """The folder holding _quarto.yml.

    REPORT_ROOT wins when set. Otherwise walk up from the working directory.
    A book rendered against the wrong folder must fail, not guess.
    """
    env = os.environ.get("REPORT_ROOT", "")
    if env:
        root = Path(env)
        if not (root / "_quarto.yml").exists():
            raise RuntimeError(f"REPORT_ROOT is set but holds no _quarto.yml: {env}")
        return root.resolve()
    here = Path(start or os.getcwd()).resolve()
    for folder in (here, *here.parents):
        if (folder / "_quarto.yml").exists():
            return folder
    raise RuntimeError(
        "No _quarto.yml found in the working directory or any parent. "
        "Set REPORT_ROOT to the book folder."
    )


def _read_flat_yaml(text: str) -> dict:
    """A small reader for flat key: value files, used when PyYAML is absent."""
    values: dict = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if value in ("", "null", "~"):
            values[key] = None
            continue
        try:
            values[key] = int(value)
        except ValueError:
            try:
                values[key] = float(value)
            except ValueError:
                values[key] = value.strip("\"'")
    return values


_PARAMS: dict | None = None


def report_param(name: str, root: str | os.PathLike | None = None):
    """One analysis parameter from _params.yml.

    A missing or null value raises. There is never a default.
    """
    global _PARAMS
    if _PARAMS is None or root is not None:
        path = Path(root or report_root()) / "_params.yml"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        try:
            import yaml

            _PARAMS = yaml.safe_load(text) or {}
        except ImportError:
            _PARAMS = _read_flat_yaml(text)
    value = _PARAMS.get(name)
    if value is None:
        raise RuntimeError(
            f"Parameter '{name}' is not decided yet; record the decision in _params.yml"
        )
    return value


# ---------------------------------------------------------------------------
# Numbers in prose (computed, never typed)
# ---------------------------------------------------------------------------


def fmt(x) -> str:
    """Thousands separators for integers."""
    if isinstance(x, float) and not x.is_integer():
        return f"{x:,}"
    return f"{int(x):,}"


def pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f}%"


def frac(k: int, n: int) -> str:
    """Every percentage carries its denominator."""
    return f"{fmt(k)} of {fmt(n)} ({pct(k / n)})"


# ---------------------------------------------------------------------------
# Plot theme and palettes
# ---------------------------------------------------------------------------

# One named palette for the whole book. Significance must be encoded by
# shape as well as colour, so no reader depends on colour alone.
HOUSE_PAL = {
    "up": "#b5366a",
    "down": "#2c7a93",
    "ns": "#c2ccd2",
    "warn": "#c9762f",
    "ok": "#3f7d55",
}

# Okabe-Ito qualitative colours, for categories.
OKABE_ITO = [
    "#E69F00", "#56B4E9", "#009E73", "#F0E442",
    "#0072B2", "#D55E00", "#CC79A7", "#000000",
]


def theme_house() -> None:
    """Matplotlib settings that match the R theme."""
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.which": "major",
            "grid.color": "#e6ebee",
            "axes.titleweight": "bold",
            "axes.edgecolor": "#c2ccd2",
            "axes.prop_cycle": matplotlib.cycler(color=OKABE_ITO),
            "figure.dpi": 150,
            "savefig.dpi": 150,
        }
    )


# Safe to set globally here: each chapter is its own session.
theme_house()

# ---------------------------------------------------------------------------
# Honest gaps
# ---------------------------------------------------------------------------


def not_applicable(what: str, why: str) -> str:
    """Markdown for one callout in place of a section that did not run.

    Display it with IPython.display.Markdown in a cell with output: asis.
    """
    return (
        '\n::: {.callout-note appearance="simple"}\n'
        "## Not applicable to this report\n\n"
        f"This section covers {what}. It did not run because {why}. "
        "Nothing was computed and nothing is hidden.\n"
        ":::\n"
    )


# ---------------------------------------------------------------------------
# Figures for papers
# ---------------------------------------------------------------------------


def save_figure(fig, name: str) -> list[Path]:
    """Writes the same figure as PDF and PNG into figures/ (gitignored)."""
    folder = report_root() / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / f"{name}.pdf", folder / f"{name}.png"]
    fig.savefig(paths[0])
    fig.savefig(paths[1], dpi=300)
    return paths


# ---------------------------------------------------------------------------
# Synthetic data (seeded, generated at render time, never committed)
# ---------------------------------------------------------------------------


def synth_counts(n_genes: int = 500, n_per_group: int = 3, seed: int = SEED) -> dict:
    """A negative-binomial count matrix for two groups with 40 planted changes."""
    rng = np.random.default_rng(seed)
    genes = [f"gene{i:04d}" for i in range(1, n_genes + 1)]
    n = 2 * n_per_group
    samples = pd.DataFrame(
        {
            "sample": [f"S{i}" for i in range(1, n + 1)],
            "group": ["control"] * n_per_group + ["treated"] * n_per_group,
        }
    )
    base_mean = np.exp(rng.normal(4, 1.5, n_genes))
    lfc = np.zeros(n_genes)
    planted = rng.choice(n_genes, 40, replace=False)
    lfc[planted] = rng.choice([-1, 1], 40) * rng.uniform(1, 3, 40)
    mu = np.repeat(base_mean[:, None], n, axis=1)
    treated = (samples["group"] == "treated").to_numpy()
    mu[:, treated] = mu[:, treated] * (2 ** lfc)[:, None]
    size = 10.0
    counts = rng.negative_binomial(size, size / (size + mu))
    counts = pd.DataFrame(counts, index=genes, columns=samples["sample"])
    truth = pd.DataFrame(
        {"gene": genes, "planted": np.isin(np.arange(n_genes), planted), "log2FC_true": lfc}
    )
    return {"counts": counts, "samples": samples, "truth": truth}


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function, by continued fraction."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    log_front = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x > (a + 1) / (a + b + 2):
        return 1.0 - _betainc(b, a, 1 - x)
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        for num in (
            m * (b - m) * x / ((a + m2 - 1) * (a + m2)),
            -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1)),
        ):
            d = 1.0 + num * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + num / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < 1e-12:
            break
    return math.exp(log_front) * h / a


def _welch_p(x: np.ndarray, y: np.ndarray) -> float:
    """Two-sided Welch t-test p-value, standard library maths only."""
    vx, vy = x.var(ddof=1) / len(x), y.var(ddof=1) / len(y)
    se2 = vx + vy
    if se2 <= 0:
        return 1.0
    t = (x.mean() - y.mean()) / math.sqrt(se2)
    df = se2**2 / (vx**2 / (len(x) - 1) + vy**2 / (len(y) - 1))
    return _betainc(df / 2, 0.5, df / (df + t * t))


def _bh(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values."""
    n = len(p)
    order = np.argsort(p)[::-1]
    ranked = p[order] * n / np.arange(n, 0, -1)
    adjusted = np.minimum.accumulate(ranked)
    out = np.empty(n)
    out[order] = np.minimum(adjusted, 1.0)
    return out


def synth_de(seed: int = SEED) -> pd.DataFrame:
    """A synthetic results table.

    Illustrative only: a two-sample Welch t-test on log CPM, which is NOT a
    recommended method for count data.
    """
    sc = synth_counts(seed=seed)
    counts = sc["counts"].to_numpy(dtype=float)
    lib = counts.sum(axis=0)
    logcpm = np.log2((counts + 1) / (lib + 1) * 1e6)
    treated = (sc["samples"]["group"] == "treated").to_numpy()
    p = np.array([_welch_p(row[treated], row[~treated]) for row in logcpm])
    out = pd.DataFrame(
        {
            "gene": sc["counts"].index,
            "log2FC": logcpm[:, treated].mean(axis=1) - logcpm[:, ~treated].mean(axis=1),
            "p": p,
        }
    )
    out["FDR"] = _bh(p)
    return out


def synth_embedding(n: int = 900, k: int = 3, seed: int = SEED) -> pd.DataFrame:
    """A 2-D point cloud of k Gaussian clusters, for scatter examples."""
    rng = np.random.default_rng(seed)
    cluster = rng.integers(1, k + 1, n)
    centres = rng.normal(0, 4, (k, 2))
    return pd.DataFrame(
        {
            "dim1": centres[cluster - 1, 0] + rng.normal(size=n),
            "dim2": centres[cluster - 1, 1] + rng.normal(size=n),
            "cluster": [f"cluster {c}" for c in cluster],
        }
    )
