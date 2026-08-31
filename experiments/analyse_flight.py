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
from scipy.stats import mannwhitneyu

# ----------------------------------------------------------------- CONFIG

DIR = Path(__file__).resolve().parent

# Add one entry per panel. Label is used in the printed table and as the
# panel title in the figure.
DATASETS = [
    ("1600 total population", DIR / "1600_ring_flight/results.csv"),
    ("3200 total population", DIR / "3200_ring_flight/results.csv"),
]

SUPTITLE = "Flight-gate, ring topology"
OUT_PNG = DIR / "flight_ring.png"


PLATEAU = None
REFERENCE_LINES = [(0.7519, "planted solution"), (0.8152, "best found by SA")]

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


def pairwise_test(cfg):
    groups = {n: sub["best_fitness"].values
              for n, sub in cfg.groupby("num_islands")}
    keys = sorted(groups)
    print("\nPairwise Mann-Whitney U on best fitness:")
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            u, p = mannwhitneyu(groups[a], groups[b],
                                alternative="two-sided")
            print(f"  {a:>2} vs {b:>2} islands: U = {u:>6.1f}, p = {p:.5f}"
                  f"{' *' if p < 0.05 else ''}")


def plot(frames):
    n_panels = len(frames)
    fig, axes = plt.subplots(2, n_panels, figsize=(6 * n_panels, 8),
                             squeeze=False)
    for col, (title, cfg) in enumerate(frames):
        counts = sorted(cfg["num_islands"].unique())
        x = np.arange(len(counts))

        ax = axes[0][col]
        means, sds = [], []
        for n in counts:
            v = cfg[cfg["num_islands"] == n]["best_fitness"]
            means.append(v.mean()); sds.append(v.std(ddof=1))
        ax.bar(x, means, yerr=sds, capsize=4, color="#4878a8",
               edgecolor="black", width=0.6)
        for i, (m, s) in enumerate(zip(means, sds)):
            ax.text(i, m + s + 0.015, f"{m:.3f}", ha="center", fontsize=10)
        ax.set_xticks(x); ax.set_xticklabels(counts)
        ax.set_ylim(0, 1.0)
        ax.set_xlabel("Number of islands")
        ax.set_ylabel("Mean best fitness" if col == 0 else "")
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.3)

        ax = axes[1][col]
        rng = np.random.default_rng(0)
        for i, n in enumerate(counts):
            vals = cfg[cfg["num_islands"] == n]["best_fitness"].values
            jitter = rng.uniform(-0.13, 0.13, len(vals))
            hit = np.isclose(vals, 1.0)
            ax.scatter(i + jitter[~hit], vals[~hit], s=32, alpha=0.75,
                       color="#4878a8", edgecolor="black", linewidth=0.4,
                       zorder=3)
            ax.scatter(i + jitter[hit], vals[hit], s=44, alpha=0.9,
                       color="#c44e52", edgecolor="black", linewidth=0.4,
                       zorder=4, marker="D")
            ax.hlines(np.median(vals), i - 0.28, i + 0.28,
                      color="black", linewidth=2, zorder=5)
        if PLATEAU is not None:
            ax.axhline(PLATEAU, color="grey", linestyle="--", linewidth=1,
                       alpha=0.7, zorder=1)
            ax.text(len(counts) - 0.45, PLATEAU - 0.012,
                    f"plateau ({PLATEAU:.3f})", fontsize=8, color="grey",
                    ha="right", va="top")
        for yv, lab in REFERENCE_LINES:
            ax.axhline(yv, color="grey", linestyle=":", linewidth=1, alpha=0.8)
            ax.text(-0.45, yv + 0.004, lab, fontsize=8, color="grey", va="bottom")
        ax.set_xticks(x); ax.set_xticklabels(counts)
        allv = cfg["best_fitness"]
        ax.set_ylim(allv.min() - 0.02, max(1.01, allv.max() + 0.02))
        ax.set_xlabel("Number of islands")
        ax.set_ylabel("Best fitness (per seed)" if col == 0 else "")
        ax.grid(axis="y", alpha=0.3)

    if SUPTITLE:
        fig.suptitle(SUPTITLE, fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    print(f"\nWrote {OUT_PNG}")


def main():
    frames = []
    for label, path in DATASETS:
        cfg = config_level(pd.read_csv(path))
        print(f"\n=== {label} ===")
        print(f"{len(cfg)} configuration runs")
        print(summarise(cfg).to_string(index=False))
        pairwise_test(cfg)
        frames.append((label, cfg))
    plot(frames)


if __name__ == "__main__":
    main()