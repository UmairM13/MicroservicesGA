import random

def generate_population (num_flights: int, num_gates: int, size: int, seed:int | None) -> list[list[int]]:
    """
    Generate a population of candidate solutions (chromosomes) for the flight gate assignment problem. Each chromosome is a list of gate assignments for each flight.
    """

    rng = random.Random(seed)
    population = []
    for _ in range(size):
        chromosome = [rng.randint(0, num_gates - 1) for _ in range(num_flights)]
        population.append(chromosome)

    return population


  
if __name__ == "__main__":
    population = generate_population(num_flights=10, num_gates=4, size=5, seed=67)
    for i, chromosome in enumerate(population):
        print(f"Chromosome {i}: {chromosome}")
