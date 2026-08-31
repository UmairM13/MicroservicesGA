import random 


def crossover(parent1: list[int], parent2: list[int], rng: random.Random, crossover_rate: float = 0.8) -> tuple[list[int], list[int]]:
    """
     Two-point crossover for the flight-gate encoding.

    Each chromosome is a flat list where position i holds the gate assigned
    to flight i. Two cut points are chosen and the segment between them is
    exchanged between the parents, so each child keeps the outer segments of
    one parent and the middle segment of the other.

    Two-point crossover is used rather than uniform crossover because gate
    assignments are interdependent: a uniform operator that recombines
    positions independently was found to break the coordinated groupings that
    make a schedule conflict-free. Preserving contiguous segments keeps those
    groupings largely intact. With probability (1 - crossover_rate) the
    parents are returned unchanged, so recombination remains a genuine but
    limited part of the search.
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