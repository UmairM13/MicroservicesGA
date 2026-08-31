"""
Sudoku crossover: row-wise two-point selection with cycle crossover.

Adapted from a genetic algorithm implementation by Christian T. Jacobs,
originally produced as coursework for the CS3M6 Evolutionary Computation
module at the University of Reading (Copyright (c) 2009, 2017 Christian
Thomas Jacobs). Original: https://github.com/ctjacobs/sudoku-genetic-algorithm

The cycle crossover algorithm and the row-wise application follow Jacobs'
implementation. Adapted for this project by Umair Mangera (2026):
re-implemented as stateless module-level functions over plain lists rather
than methods on a CycleCrossover object, so the operator can run as an
independent microservice; an explicit random.Random instance is injected
rather than seeding the global random module, so a run is reproducible from
its seed; and the two-point selection is simplified to two ordered draws
in place of the original's resample loop.
"""

import numpy as np
import random

Nd = 9

def find_unused(row, remaining):
    """ Index of the first cell in row that is still in remaining, or None if all are used. """
    for i, val in enumerate(row):
        if val in remaining: 
            return i
        

def find_value(row, value):
    for i, val in enumerate(row):
        if val == value: 
            return i
        

def cycle_crossover_rows(row1, row2):
    """ Cycle crossover on a single pair of rows.
    Both rows are assumed to be valid permutations of 1..9, 
    so the result is guaranteed to be valid as well.
    
    Alternate cycles are copied from the parents to the children, 
    starting with row1 for child1 and row2 for child2."""

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
    """ Crossover of two full Sudok grids.
    
    A contiguous block of rows between the two cut points is exchanged between the parents, 
    and cycle crossover is applied to each pair of rows in that block.
    With probability (1 - crossover_rate) the parents are returned unchanged, 
    so recombination remains"""
    
    p1 = np.array(parent1, dtype=int)
    p2 = np.array(parent2, dtype=int)

    child1 = p1.copy()
    child2 = p2.copy()

    if rng.random() < crossover_rate:
        ## Two ordered cut pionts are drawn
        # point2 is guaranteed to be greater than point1, so the block is non-empty
        # so at least one row is exchanged between the parents
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