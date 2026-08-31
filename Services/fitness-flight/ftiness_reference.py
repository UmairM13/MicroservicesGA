"""
Reference points for the flight-gate instance.

Computes the two baselines cited in the dissertation:
  1. The planted schedule the instance was constructed around
     (Section 3.1.2), fitness 0.7519.
  2. The best schedule found by simulated annealing over the same
     instance, fitness 0.8152, used as the practical ceiling when
     interpreting GA results (Section 4.4).

A random-assignment baseline is included for context.
"""

from fitness import evaluate_fitness
import math
import random

NUM_GATES = 6
FLIGHTS = [
    {"flight_id": 0,  "arrival": 81,  "departure": 128, "passengers": 32},
    {"flight_id": 1,  "arrival": 223, "departure": 278, "passengers": 134},
    {"flight_id": 2,  "arrival": 355, "departure": 442, "passengers": 72},
    {"flight_id": 3,  "arrival": 588, "departure": 675, "passengers": 299},
    {"flight_id": 4,  "arrival": 75,  "departure": 142, "passengers": 36},
    {"flight_id": 5,  "arrival": 205, "departure": 250, "passengers": 131},
    {"flight_id": 6,  "arrival": 339, "departure": 411, "passengers": 33},
    {"flight_id": 7,  "arrival": 542, "departure": 594, "passengers": 299},
    {"flight_id": 8,  "arrival": 28,  "departure": 96,  "passengers": 162},
    {"flight_id": 9,  "arrival": 156, "departure": 244, "passengers": 101},
    {"flight_id": 10, "arrival": 393, "departure": 460, "passengers": 194},
    {"flight_id": 11, "arrival": 555, "departure": 604, "passengers": 130},
    {"flight_id": 12, "arrival": 13,  "departure": 58,  "passengers": 214},
    {"flight_id": 13, "arrival": 130, "departure": 192, "passengers": 196},
    {"flight_id": 14, "arrival": 329, "departure": 385, "passengers": 42},
    {"flight_id": 15, "arrival": 503, "departure": 577, "passengers": 83},
    {"flight_id": 16, "arrival": 10,  "departure": 85,  "passengers": 170},
    {"flight_id": 17, "arrival": 225, "departure": 304, "passengers": 205},
    {"flight_id": 18, "arrival": 437, "departure": 489, "passengers": 55},
    {"flight_id": 19, "arrival": 554, "departure": 636, "passengers": 136},
    {"flight_id": 20, "arrival": 10,  "departure": 64,  "passengers": 71},
    {"flight_id": 21, "arrival": 172, "departure": 229, "passengers": 252},
    {"flight_id": 22, "arrival": 370, "departure": 433, "passengers": 103},
    {"flight_id": 23, "arrival": 540, "departure": 602, "passengers": 127},
]

N = len(FLIGHTS)

# Simulated annealing parameters. The 0.8184 figure reported in the
# dissertation was obtained with these values and SEED = 0.
SEED = 0
RESTARTS = 500          # reduce for a quicker (weaker) search
STEPS = 60_000
T_START, T_END = 0.5, 1e-4


def fit(genes):
    return evaluate_fitness(genes, FLIGHTS, NUM_GATES)


def planted_solution():
    """The schedule the instance was constructed around: flights were
    generated in blocks of four per gate, so gate = flight_id // 4."""
    return [f["flight_id"] // 4 for f in FLIGHTS]


def random_baseline(rng, samples=1000):
    return max(fit([rng.randrange(NUM_GATES) for _ in range(N)])
               for _ in range(samples))


def simulated_annealing(rng):
    """Random-restart SA with single-gene reassignment moves and a
    linear temperature schedule."""
    best_f, best_g = -1.0, None
    for _ in range(RESTARTS):
        cur = [rng.randrange(NUM_GATES) for _ in range(N)]
        cur_f = fit(cur)
        for step in range(STEPS):
            temp = T_START * (1 - step / STEPS) + T_END
            i = rng.randrange(N)
            old = cur[i]
            new = rng.randrange(NUM_GATES)
            if new == old:
                continue
            cur[i] = new
            new_f = fit(cur)
            if new_f >= cur_f or rng.random() < math.exp((new_f - cur_f) / temp):
                cur_f = new_f
            else:
                cur[i] = old
        if cur_f > best_f:
            best_f, best_g = cur_f, cur[:]
    return best_f, best_g


if __name__ == "__main__":
    rng = random.Random(SEED)

    print(f"Random baseline (best of 1000):  {random_baseline(rng):.4f}")

    p = planted_solution()
    print(f"Planted schedule (id // 4):      {fit(p):.4f}   {p}")

    print(f"\nRunning SA: {RESTARTS} restarts x {STEPS} steps "
          f"(several minutes in pure Python)...")
    sa_f, sa_g = simulated_annealing(rng)
    print(f"Best found by SA:                {sa_f:.4f}   {sa_g}")