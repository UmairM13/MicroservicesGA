"""
Summarise and plot GA experiment results.

Edit the CONFIG block below, then run:
    python ga_results.py

Rows in results.csv are per-island. Configuration-level metrics are taken
once per (num_islands, base_seed) group.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------------------------------------- CONFIG

DIR = Path(__file__).resolve().parent

# Add one entry per panel. Label is used in the printed table and as the
# panel title in the figure.
DATASETS = [
    ("1600 total population", DIR / "1600_fc_sudoku/results.csv",
     DIR / "sudoku_fc_1600.png"),
    ("3200 total population", DIR / "3200_fc_sudoku/results.csv",
     DIR / "sudoku_fc_3200.png"),
]

SUPTITLE = "Sudoku, fully topology"
OUT_PNG = DIR / "sudoku_ring.png"

# Fitness value that non-solving Sudoku runs commonly settle on.
# Set to None for the flight-gate domain, which has no such plateau.
PLATEAU = 0.8518518518518521

# -------------------------------------------------------------------------


def config_level(df):
    """Collapse per-island rows to one row per configuration run."""
    g = df.groupby(["num_islands", "base_seed"], as_index=False).agg(
        best_fitness=("config_best_fitness", "first"),
        solved=("config_solved", "first"),
        wall_clock=("wall_clock_seconds", "first"),
        pop_per_island=("pop_per_island", "first"),
    )
    solved_rows = df[df["status"] == "Solution Found"]
    if len(solved_rows):
        gens = solved_rows.groupby(
            ["num_islands", "base_seed"], as_index=False
        ).agg(gens_to_solve=("generations", "min"))
        g = g.merge(gens, on=["num_islands", "base_seed"], how="left")
    else:
        g["gens_to_solve"] = np.nan
    return g


def summarise(cfg):
    rows = []
    for n, sub in cfg.groupby("num_islands"):
        solved = sub["solved"].astype(bool)
        row = {
            "islands": n,
            "pop/island": int(sub["pop_per_island"].iloc[0]),
            "n": len(sub),
            "solved": int(solved.sum()),
            "solve_rate": round(solved.mean(), 3),
        }
        if PLATEAU is not None:
            at_plateau = np.isclose(sub["best_fitness"], PLATEAU)
            row["at_plateau"] = int(at_plateau.sum())
            row["other"] = int((~solved & ~at_plateau).sum())
        row.update({
            "median_fit": round(sub["best_fitness"].median(), 4),
            "mean_fit": round(sub["best_fitness"].mean(), 4),
            "std_fit": round(sub["best_fitness"].std(ddof=1), 4),
            "min_fit": round(sub["best_fitness"].min(), 4),
            "median_gens": (round(sub["gens_to_solve"].median(), 1)
                            if solved.any() else None),
            "median_wall_s": round(sub["wall_clock"].median(), 1),
        })
        rows.append(row)
    return pd.DataFrame(rows)


def pairwise_fisher(cfg):
    try:
        from scipy.stats import fisher_exact
    except ImportError:
        print("(scipy not installed, skipping significance tests)")
        return
    counts = {}
    for n, sub in cfg.groupby("num_islands"):
        s = int(sub["solved"].astype(bool).sum())
        counts[n] = (s, len(sub) - s)
    keys = sorted(counts)
    print("\nPairwise Fisher exact tests on solve counts:")
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            p = fisher_exact([list(counts[a]), list(counts[b])])[1]
            print(f"  {a:>2} vs {b:>2} islands: p = {p:.4f}"
                  f"{' *' if p < 0.05 else ''}")


def plot(title, cfg, out_png):
    fig, axes = plt.subplots(2, 1, figsize=(6, 5))
    counts = sorted(cfg["num_islands"].unique())
    x = np.arange(len(counts))

    ax = axes[0]
    rates, labels = [], []
    for n in counts:
        sub = cfg[cfg["num_islands"] == n]
        s = int(sub["solved"].astype(bool).sum())
        rates.append(s / len(sub))
        labels.append(f"{s}/{len(sub)}")
    bars = ax.bar(x, rates, color="#4878a8", edgecolor="black", width=0.6)
    for bar, lab in zip(bars, labels):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                lab, ha="center", va="bottom", fontsize=10)
    ax.set_xticks(x); ax.set_xticklabels(counts)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Number of islands")
    ax.set_ylabel("Solve rate")
    ax.grid(axis="y", alpha=0.3)

    ax = axes[1]
    rng = np.random.default_rng(0)
    for i, n in enumerate(counts):
        vals = cfg[cfg["num_islands"] == n]["best_fitness"].values
        jitter = rng.uniform(-0.13, 0.13, len(vals))
        hit = np.isclose(vals, 1.0)
        ax.scatter(i + jitter[~hit], vals[~hit], s=32, alpha=0.75,
                   color="#4878a8", edgecolor="black", linewidth=0.4, zorder=3)
        ax.scatter(i + jitter[hit], vals[hit], s=44, alpha=0.9,
                   color="#c44e52", edgecolor="black", linewidth=0.4,
                   zorder=4, marker="D")
        ax.hlines(np.median(vals), i - 0.28, i + 0.28,
                  color="black", linewidth=2, zorder=5)
    if PLATEAU is not None:
        ax.axhline(PLATEAU, color="grey", linestyle="--", linewidth=1,
                   alpha=0.7, zorder=1)
        ax.text(-0.45, PLATEAU + 0.004, f"plateau ({PLATEAU:.3f})",
                fontsize=8, color="grey", ha="left", va="bottom")
    ax.set_xticks(x); ax.set_xticklabels(counts)
    allv = cfg["best_fitness"]
    ax.set_ylim(allv.min() - 0.02, max(1.01, allv.max() + 0.02))
    ax.set_xlabel("Number of islands")
    ax.set_ylabel("Best fitness (per seed)")
    ax.grid(axis="y", alpha=0.3)

    full_title = f"{SUPTITLE} — {title}" if SUPTITLE else title
    fig.suptitle(full_title, fontsize=13)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    print(f"Wrote {out_png}")


def main():
    for label, path, out_png in DATASETS:
        cfg = config_level(pd.read_csv(path))
        print(f"\n=== {label} ===")
        print(f"{len(cfg)} configuration runs")
        print(summarise(cfg).to_string(index=False))
        pairwise_fisher(cfg)
        plot(label, cfg, out_png)

if __name__ == "__main__":
    main()