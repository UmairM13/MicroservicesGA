import random

def tournament_select(
        chromosomes: list[dict],
        num_parents: int,
        tournament_size: int =2,
        selection_rate: float = 0.85
) -> list[dict]:
    """
    Select parents from a population of chromosomes using tournament selection.

    """

    parents = []

    for _ in range(num_parents):

        competitors = random.sample(chromosomes, min(tournament_size, len(chromosomes)))

        competitors.sort(key=lambda x: x['fitness'], reverse=True)

        if random.random() < selection_rate:
            parents.append(competitors[0])
        else:
            parents.append(random.choice(competitors[1:]))

    return parents



if __name__ == "__main__":

    population = [
        {"genes": [[1]], "fitness": 0.9},
        {"genes": [[2]], "fitness": 0.1},
        {"genes": [[3]], "fitness": 0.5},
        {"genes": [[4]], "fitness": 0.7},
    ]

    parents = tournament_select(population, num_parents=2)

    for p in parents:
        print(f"Selected fitness: {p['fitness']}")