import random


def mutate(genes: list[int], num_gates: int, mutation_rate: float = 0.06) -> list[int]:
    """
    Mutate a chromosome by randomly changing some of its genes based on the mutation rate.
    """

    result = genes[:]
    for i in range(len(genes)):
        if random.random() < mutation_rate:
            result[i] = random.randint(0, num_gates - 1)
    return result


if __name__ == "__main__":
    orignal = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
    mutated = mutate(orignal, 4, mutation_rate=0.5)
    print("Original:", orignal)
    print("Mutated:", mutated)
    