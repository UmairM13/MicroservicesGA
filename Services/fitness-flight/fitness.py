""" Flight Scheduling Problem - Fitness Function """

MIN_TURNAROUND = 45


def evaluate_fitness(genes: list[int], flights: list[dict], num_gates: int) -> float:
    conflict_penalty = 0.0
    turnaround_penalty = 0.0
    idle_penalty = 0.0

    gate_flights = [[] for _ in range(num_gates)]
    for i, gate in enumerate(genes):
        if 0 <= gate < num_gates:
            gate_flights[gate].append(flights[i])
        else:
            conflict_penalty += 10  # invalid gate

    for gate_id in range(num_gates):
        assigned = sorted(gate_flights[gate_id], key=lambda f: f["arrival"])

        for j in range(len(assigned) - 1):
            current = assigned[j]
            next_flight = assigned[j + 1]
            gap = next_flight["arrival"] - current["departure"]

            if gap < 0:
                overlap_minutes = abs(gap)
                conflict_penalty += overlap_minutes / 60.0
            elif gap < MIN_TURNAROUND:
                shortfall = MIN_TURNAROUND - gap
                turnaround_penalty += shortfall / 60.0
            elif gap > 120:
                idle_penalty += (gap - 120) / 360.0

    soft_penalty = (turnaround_penalty * 2) + idle_penalty

    # TIERED: conflicts dominate completely
    if conflict_penalty > 0:
        fitness = 0.1 / (1.0 + conflict_penalty)
    else:
        fitness = 0.1 + 0.9 / (1.0 + soft_penalty)

    return fitness

if __name__ == "__main__":
    from flight_data import generate_flight_data

    flights = generate_flight_data(num_flights=10, num_gates=4)

    # Terrible assignment — all flights at gate 0
    bad_genes = [0] * 10
    print(f"All at gate 0: {evaluate_fitness(bad_genes, flights, 4):.4f}")

    # Spread across gates evenly
    spread_genes = [i % 4 for i in range(10)]
    print(f"Spread evenly: {evaluate_fitness(spread_genes, flights, 4):.4f}")

    # Random assignment
    import random
    random_genes = [random.randint(0, 3) for _ in range(10)]
    print(f"Random: {evaluate_fitness(random_genes, flights, 4):.4f}")