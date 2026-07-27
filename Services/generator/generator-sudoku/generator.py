import numpy as np
import random

Nd = 9

def _in_row(given, row, value):
    return value in given[row]

def _in_col(given, col, value):
    return value in given[:, col]

def _in_block(given, row, col, value):
    block_row, block_col = 3 * (row // 3), 3 * (col // 3)
    return value in given[block_row:block_row+3, block_col:block_col+3]

def build_helper(puzzle: list[list[int]]) -> list[list[list[int]]]:
    """
    Build a helper grid for a given Sudoku puzzle, where each cell contains a list of possible values that can be placed in that cell.
    """

    given = np.array(puzzle, dtype=int)
    helper = [[[] for _ in range(Nd)] for _ in range(Nd)]

    for row in range(Nd):
        for col in range(Nd):

            if given [row][col] != 0:
                helper[row][col] = [int(given[row][col])]

            else:
                for value in range (1, 10):
                    if (not _in_row(given, row, value) and
                        not _in_col(given, col, value) and
                        not _in_block(given, row, col, value)):
                        helper[row][col].append(value)

    
    return helper


def generate_chromosome(puzzle: list[list[int]], helper, rng:random.Random) -> list[list[int]]:
    """
    Generate a chromosome (candidate solution) for a given Sudoku puzzle, using the helper grid to fill in the empty cells with valid values.
    """

    given = np.array(puzzle, dtype=int)
    grid = np.zeros((Nd, Nd), dtype=int)

    for i in range(Nd):
        
        row = np.zeros(Nd, dtype=int)

        for j in range(Nd):
            if given[i][j] != 0:
                row[j] = int(given[i][j])
            else:
                row[j] = rng.choice(helper[i][j])

        while len(set(row)) != Nd:
            for j in range(Nd):
                if given[i][j] == 0:
                    row[j] = rng.choice(helper[i][j])

        grid[i] = row

    return grid.tolist()



def generate_population(puzzle: list[list[int]], size: int, seed:int | None=None) -> list[list[list[int]]]:
    """
    Generate a full population of chromosomes
    """

    helper = build_helper(puzzle)
    rng = random.Random(seed)
    return [generate_chromosome(puzzle, helper, rng) for _ in range(size)]



if __name__ == "__main__":
    puzzle = [
        [0,3,0,0,7,0,0,5,0],
        [5,0,0,1,0,6,0,0,9],
        [0,0,1,0,0,0,4,0,0],
        [0,9,0,0,5,0,0,6,0],
        [6,0,0,4,0,2,0,0,7],
        [0,4,0,0,1,0,0,3,0],
        [0,0,2,0,0,0,8,0,0],
        [9,0,0,3,0,5,0,0,2],
        [0,1,0,0,2,0,0,7,0]
    ]

    chromosomes = generate_population(puzzle, 5, seed=1)

    for i, chromosome in enumerate(chromosomes):

        valid = all(len(set(row)) == Nd for row in chromosome)
        print(f"Chromosome {i} is valid: {valid}")