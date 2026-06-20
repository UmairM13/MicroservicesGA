import random 


def crossover(parent1: list[int], parent2: list[int], crossover_rate: float = 0.8) -> tuple[list[int], list[int]]:
    """
    Perform crossover between two parent chromosomes to produce two offspring chromosomes. Crossover is done by randomly selecting a crossover point and swapping the genes after that point between the two parents.
    """

    if random.random() > crossover_rate:
        return parent1, parent2

    point = random.randint(1, len(parent1) - 1)

    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]

    return child1, child2


if __name__ == "__main__":
    parent1 = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    parent2 = [2, 2, 2, 2, 2, 3, 3, 3, 3, 3]

    child1, child2 = crossover(parent1, parent2)

    print("Parent 1:", parent1)
    print("Parent 2:", parent2)
    print("Child 1:", child1)
    print("Child 2:", child2)