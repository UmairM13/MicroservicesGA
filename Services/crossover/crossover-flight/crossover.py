import random 


def crossover(parent1: list[int], parent2: list[int], rng: random.Random, crossover_rate: float = 0.8) -> tuple[list[int], list[int]]:
    """
    Perform crossover between two parent chromosomes to produce two offspring chromosomes. Crossover is done by randomly selecting a crossover point and swapping the genes after that point between the two parents.
    """

    if rng.random() > crossover_rate:
        return parent1[:], parent2[:]

    n = len(parent1)
    if n < 2:
        return parent1[:], parent2[:]

    # two cut points
    a = rng.randint(0, n - 1)
    b = rng.randint(0, n - 1)
    if a > b:
        a, b = b, a

    child1 = parent1[:a] + parent2[a:b] + parent1[b:]
    child2 = parent2[:a] + parent1[a:b] + parent2[b:]
    return child1, child2


if __name__ == "__main__":
    parent1 = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    parent2 = [2, 2, 2, 2, 2, 3, 3, 3, 3, 3]

    rng = random.Random(67)
    
    child1, child2 = crossover(parent1, parent2, rng)

    print("Parent 1:", parent1)
    print("Parent 2:", parent2)
    print("Child 1:", child1)
    print("Child 2:", child2)