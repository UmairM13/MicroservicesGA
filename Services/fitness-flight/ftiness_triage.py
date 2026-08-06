from fitness import evaluate_fitness
import random

NUM_GATES = 5
FLIGHTS = [
    {"flight_id":0,"arrival":74,"departure":188,"passengers":227},
    {"flight_id":1,"arrival":904,"departure":1041,"passengers":131},
    {"flight_id":2,"arrival":538,"departure":594,"passengers":246},
    {"flight_id":3,"arrival":20,"departure":128,"passengers":221},
    {"flight_id":4,"arrival":570,"departure":661,"passengers":82},
    {"flight_id":5,"arrival":640,"departure":819,"passengers":183},
    {"flight_id":6,"arrival":474,"departure":557,"passengers":155},
    {"flight_id":7,"arrival":897,"departure":988,"passengers":47},
    {"flight_id":8,"arrival":538,"departure":562,"passengers":204},
    {"flight_id":9,"arrival":1094,"departure":1183,"passengers":227},
    {"flight_id":10,"arrival":300,"departure":420,"passengers":150},
    {"flight_id":11,"arrival":100,"departure":250,"passengers":90},
    {"flight_id":12,"arrival":780,"departure":900,"passengers":175},
    {"flight_id":13,"arrival":200,"departure":350,"passengers":200},
    {"flight_id":14,"arrival":450,"departure":580,"passengers":120},
    {"flight_id":15,"arrival":1200,"departure":1350,"passengers":80},
    {"flight_id":16,"arrival":50,"departure":160,"passengers":160},
    {"flight_id":17,"arrival":700,"departure":850,"passengers":210},
    {"flight_id":18,"arrival":350,"departure":500,"passengers":140},
    {"flight_id":19,"arrival":1000,"departure":1100,"passengers":95},
]

def score(genes, label):
    f = evaluate_fitness(genes, FLIGHTS, NUM_GATES)
    print(f"{label:28s} fitness={f:.4f}")
    return f

n = len(FLIGHTS)

# 1. Worst case: everything on one gate
score([0]*n, "All on gate 0")

# 2. Round-robin spread
score([i % NUM_GATES for i in range(n)], "Round-robin")

# 3. Greedy: assign each flight (in arrival order) to the gate that's free earliest
order = sorted(range(n), key=lambda i: FLIGHTS[i]['arrival'])
gate_free_at = [0]*NUM_GATES
genes = [0]*n
for i in order:
    # pick the gate whose last flight departed longest ago (most likely free)
    g = min(range(NUM_GATES), key=lambda g: gate_free_at[g])
    genes[i] = g
    gate_free_at[g] = FLIGHTS[i]['departure']
score(genes, "Greedy earliest-free gate")

# 4. Best of 100000 random assignments (brute-force baseline for the ceiling)
best_f, best_g = 0, None
rng = random.Random(0)
for _ in range(100000):
    g = [rng.randint(0, NUM_GATES-1) for _ in range(n)]
    f = evaluate_fitness(g, FLIGHTS, NUM_GATES)
    if f > best_f:
        best_f, best_g = f, g
score(best_g, "Best of 100k random")

# 5. What does zero penalty even require? Show the penalty breakdown of the greedy solution
print("\n(For reference: fitness 1.0 requires total_penalty=0, i.e. no conflicts,")
print(" no turnaround violations, AND no idle penalty — likely unreachable with 5 gates.)")