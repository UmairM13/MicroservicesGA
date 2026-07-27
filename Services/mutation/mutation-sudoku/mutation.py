import random

Nd = 9



def column_has_given(puzzle, col, value):
    for row in range(Nd):
        if puzzle[row][col] != 0 and puzzle[row][col] == value:
            return True
    return False


def block_has_given(puzzle, row, col, value):
    block_row, block_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(3):
        for c in range(3):
            if puzzle[block_row + r][block_col + c] != 0 and puzzle[block_row + r][block_col + c] == value:
                return True
            
    return False



def mutate(genes: list[list[int]], puzzle: list[list[int]], rng: random.Random, muatation_rate: float = 0.1) -> list[list[int]]:

    """
    Mutate a chromosome by swapping two non-given values in a random row.

    Only swaps if it won't introduce column or block duplicates in the given cells. 
    """
    if rng.random() > muatation_rate:
        return genes
    
    grid = [row[:] for row in genes]

    attempts = 0

    while attempts < 100:
        row = rng.randint(0, Nd - 1)
        col1, col2 = rng.randint(0, Nd - 1), rng.randint(0, Nd - 1)

        if col1 != col2 and puzzle[row][col1] == 0 and puzzle[row][col2] == 0:

            if(not column_has_given(puzzle, col1, grid[row][col2]) and
               not block_has_given(puzzle, row, col1, grid[row][col2]) and
               not column_has_given(puzzle, col2, grid[row][col1]) and
               not block_has_given(puzzle, row, col2, grid[row][col1])):

                grid[row][col1], grid[row][col2] = grid[row][col2], grid[row][col1]
                return grid
            

        attempts += 1

    return grid




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

    chromosome = [
        [4,3,6,8,7,9,2,5,1],
        [5,2,7,1,4,6,3,8,9],
        [8,6,1,2,9,3,4,7,5],
        [1,9,3,7,5,8,2,6,4],
        [6,8,5,4,3,2,9,1,7],
        [7,4,8,6,1,5,9,3,2],
        [3,5,2,9,6,7,8,4,1],
        [9,8,4,3,7,5,6,1,2],
        [8,1,9,5,2,4,6,7,3]
    ]

    rng = random.Random(67)
    result = mutate(chromosome, puzzle, rng,  muatation_rate=1.0)
    for i in range(Nd):

        if chromosome[i] != result[i]:
            print(f"Row {i} mutated: {result[i]}")
            print(f"Still valid: {len(set(result[i])) == Nd}")