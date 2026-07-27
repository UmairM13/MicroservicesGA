
import numpy as np
import random

Nd = 9

def find_unused(row, remaining):
    for i, val in enumerate(row):
        if val in remaining: 
            return i
        

def find_value(row, value):
    for i, val in enumerate(row):
        if val == value: 
            return i
        

def cycle_crossover_rows(row1, row2):

    child1 = np.zeros(Nd, dtype=int)
    child2 = np.zeros(Nd, dtype=int)

    remaining = list(range(1, Nd + 1))
    cycle = 0 

    while 0 in child1 and 0 in child2:
        index = find_unused(row1, remaining)
        start = row1[index]

        if cycle % 2 == 0:

            while True: 
                child1[index] = row1[index]
                child2[index] = row2[index]
                remaining.remove(row1[index])

                if row2[index] == start:
                    break

                index = find_value(row1, row2[index])

        else: 

            while True: 
                child1[index] = row2[index]
                child2[index] = row1[index]
                remaining.remove(row1[index])
                if row2[index] == start:
                    break
                index = find_value(row1, row2[index])

        cycle += 1
    return child1, child2


def crossover(parent1, parent2, rng: random.Random, crossover_rate=0.8):
    
    p1 = np.array(parent1, dtype=int)
    p2 = np.array(parent2, dtype=int)

    child1 = p1.copy()
    child2 = p2.copy()

    if rng.random() < crossover_rate:

        point1 = rng.randint(0, Nd - 2)
        point2 = rng.randint(point1 + 1, Nd - 1)

        for i in range(point1, point2 + 1):
            child1[i], child2[i] = cycle_crossover_rows(p1[i], p2[i])

    return child1.tolist(), child2.tolist()



if __name__ == "__main__":

    p1 = [
        [1,2,3,4,5,6,7,8,9],
        [4,5,6,7,8,9,1,2,3],
        [7,8,9,1,2,3,4,5,6],
        [2,3,4,5,6,7,8,9,1],
        [5,6,7,8,9,1,2,3,4],
        [8,9,1,2,3,4,5,6,7],
        [3,4,5,6,7,8,9,1,2],
        [6,7,8,9,1,2,3,4,5],
        [9,1,2,3,4,5,6,7,8]
    ]
    p2 = [
        [9,8,7,6,5,4,3,2,1],
        [6,5,4,3,2,1,9,8,7],
        [3,2,1,9,8,7,6,5,4],
        [8,7,6,5,4,3,2,1,9],
        [5,4,3,2,1,9,8,7,6],
        [2,1,9,8,7,6,5,4,3],
        [7,6,5,4,3,2,1,9,8],
        [4,3,2,1,9,8,7,6,5],
        [1,9,8,7,6,5,4,3,2]
    ]

    rng = random.Random(67)
    c1, c2 = crossover(p1, p2, rng, crossover_rate=1.0)

    for i, row in enumerate(c1):
        valid = len(set(row)) == Nd
        print(f"child 1 row {i}: {row} - valid: {valid}")