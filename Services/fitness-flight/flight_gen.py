import random

def generate_hard_instance(num_flights=50, num_gates=6, seed=67):
    """Generate a harder flight scheduling instance with peak-clustered arrivals."""
    rng = random.Random(seed)
    flights = []
    for i in range(num_flights):
        # 70% of flights cluster into two peaks (morning ~7-9am, evening ~5-7pm);
        # 30% spread through the day. Times in minutes (0-1439).
        r = rng.random()
        if r < 0.35:
            arrival = rng.randint(420, 540)    # morning peak 07:00-09:00
        elif r < 0.70:
            arrival = rng.randint(1020, 1140)  # evening peak 17:00-19:00
        else:
            arrival = rng.randint(0, 1439)     # off-peak, anywhere
        duration = rng.randint(40, 120)
        departure = min(arrival + duration, 1439)
        passengers = rng.randint(20, 300)
        flights.append({
            "flight_id": i,
            "arrival": arrival,
            "departure": departure,
            "passengers": passengers,
        })
    return flights

if __name__ == "__main__":
    flights = generate_hard_instance()
    import json
    print(json.dumps(flights, indent=2))

    # sanity: score a few strategies to confirm there's headroom
    from fitness import evaluate_fitness
    NUM_GATES = 6
    n = len(flights)
    print("\nAll gate 0:", round(evaluate_fitness([0]*n, flights, NUM_GATES), 4))
    print("Round-robin:", round(evaluate_fitness([i % NUM_GATES for i in range(n)], flights, NUM_GATES), 4))
    rng = random.Random(0)
    best = max(evaluate_fitness([rng.randint(0,NUM_GATES-1) for _ in range(n)], flights, NUM_GATES) for _ in range(100000))
    print("Best of 100k random:", round(best, 4))