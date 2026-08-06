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

def build_helper(puzzle):
    """Each empty cell -> list of values valid w.r.t. row, column, block of the GIVENS."""
    given = np.array(puzzle, dtype=int)
    helper = [[[] for _ in range(Nd)] for _ in range(Nd)]
    for row in range(Nd):
        for col in range(Nd):
            if given[row][col] != 0:
                helper[row][col] = [int(given[row][col])]
            else:
                for value in range(1, 10):
                    if (not _in_row(given, row, value) and
                        not _in_col(given, col, value) and
                        not _in_block(given, row, col, value)):
                        helper[row][col].append(value)
    return helper


def _fill_row(given_row, helper_row, empty_cols, rng):
    """Assign a value to each empty cell so the row is a permutation of 1-9,
    each value drawn from that cell's helper candidates. Backtracking over
    empty cells. Returns the completed row as a list, or None if impossible."""
    row = list(given_row)                      # givens already in place, empties are 0
    used = set(v for v in row if v != 0)

    # order empty cells by fewest candidates first (fail fast, less backtracking)
    order = sorted(empty_cols, key=lambda c: len(helper_row[c]))

    def backtrack(k):
        if k == len(order):
            return True
        col = order[k]
        cands = [v for v in helper_row[col] if v not in used]
        rng.shuffle(cands)                     # randomness -> diverse population
        for v in cands:
            row[col] = v
            used.add(v)
            if backtrack(k + 1):
                return True
            used.discard(v)
            row[col] = 0
        return False

    return row if backtrack(0) else None


def generate_chromosome(given, helper, rng):
    grid = np.zeros((Nd, Nd), dtype=int)
    for i in range(Nd):
        given_row = [int(given[i][j]) for j in range(Nd)]
        empty_cols = [j for j in range(Nd) if given[i][j] == 0]
        filled = _fill_row(given_row, helper[i], empty_cols, rng)
        if filled is None:
            # extremely rare fallback: row has no constraint-valid permutation;
            # fall back to a plain valid-permutation fill (row-unique only)
            used = set(v for v in given_row if v != 0)
            missing = [d for d in range(1, 10) if d not in used]
            rng.shuffle(missing)
            filled = list(given_row)
            it = iter(missing)
            for j in empty_cols:
                filled[j] = next(it)
        grid[i] = filled
    return grid.tolist()


def generate_population(puzzle, size, seed=None):
    given = np.array(puzzle, dtype=int)
    helper = build_helper(puzzle)
    rng = random.Random(seed)
    return [generate_chromosome(given, helper, rng) for _ in range(size)]



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