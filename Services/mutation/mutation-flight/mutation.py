import random


def mutate(genes: list[int], num_gates: int, rng: random.Random, mutation_rate: float = 0.06) -> list[int]:
    """
    Mutate a chromosome by randomly changing some of its genes based on the mutation rate.
    """

    result = genes[:]
    for i in range(len(genes)):
        if rng.random() < mutation_rate:
            result[i] = rng.randint(0, num_gates - 1)
    return result


if __name__ == "__main__":
    orignal = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
    rng = random.Random(67)
    mutated = mutate(orignal, 4, rng, mutation_rate=0.5)
    print("Original:", orignal)
    print("Mutated:", mutated)
    