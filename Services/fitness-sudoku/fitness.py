""" Solves a Sudoku puzzle using a genetic algorithm. 
Adapted from a genetic algorithm implementation by Christian T. Jacobs,
originally produced as coursework for the CS3M6 Evolutionary Computation
module at the University of Reading (Copyright (c) 2009, 2017 Christian
Thomas Jacobs). Original: https://github.com/ctjacobs/sudoku-genetic-algorithm

The column-by-block scoring formula and the product combination follow
Jacobs' implementation. Adapted for this project by Umair Mangera (2026):
re-implemented as a stateless pure function over a plain list rather than a
method on a Candidate object, so it can run as an independent microservice;
the row term is omitted because rows are guaranteed valid by the constraint-
aware generator; and block scoring is restructured with nested loops in place
of the original's explicit per-cell indexing.
"""

import numpy as np

Nd = 9

def evaluate_fitness(grid: list[list[int]]) -> float:
    """
    Score a 9x9 Sudoku grid on column and block constraint satiscation.
    Rows are assumed valid by construction, so only columns and 3x3 blocks are checked.

    Return a float in [0,1], where 1 is a perfect solution and 0 is the worst possible solution.
    """

    values = np.array(grid, dtype=int)

    column_sum = 0.0
    for i in range(Nd):
        column_count = np.zeros(Nd)
        for j in range(Nd):
            column_count[values[j][i] - 1] += 1
        column_sum += (1.0/ len(set(column_count))) / Nd

    
    block_sum = 0.0
    for i in range (0, Nd, 3):
        for j in range (0, Nd, 3):
            block_count = np.zeros(Nd)
            for k in range(3):
                for l in range(3):
                    block_count[values[i+k][j+l] - 1] += 1
            block_sum += (1.0/ len(set(block_count))) / Nd

    # A perfect gird gives column_sum = 1 and block_sum = 1
    if int(column_sum) == 1 and int(block_sum) == 1:
        return 1.0
    
    return column_sum * block_sum  

if __name__ == "__main__":
    bad_grid = [[1, 2, 3, 4, 5, 6, 7, 8, 9]] * 9
    print(f"Bad grid fitness: {evaluate_fitness(bad_grid)}")