"""Plot single-island vs multi-island convergence comparison."""

import matplotlib.pyplot as plt
import json

# Single island history
single_island = []  # Paste the history array from the single island run

# Multi island histories 
island_0 = []  
island_1 = []  
island_2 = [] 
island_3 = []  

# Find the best across all islands at each generation
multi_island_best = []
for gen in range(len(island_0)):
    best = max(island_0[gen], island_1[gen], island_2[gen], island_3[gen])
    multi_island_best.append(best)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(single_island, label="Single Island (pop=800)", linewidth=2)
plt.plot(multi_island_best, label="4 Islands Best (pop=200 each)", linewidth=2, linestyle="--")
plt.plot(island_0, alpha=0.3, label="Island 0")
plt.plot(island_1, alpha=0.3, label="Island 1")
plt.plot(island_2, alpha=0.3, label="Island 2")
plt.plot(island_3, alpha=0.3, label="Island 3")

plt.xlabel("Generation")
plt.ylabel("Best Fitness")
plt.title("Single Island vs 4-Island GA — Sudoku (Total Population: 800)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("experiments/convergence_comparison.png", dpi=150)
plt.show()