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

    
    if int(column_sum) == 1 and int(block_sum) == 1:
        return 1.0
    
    return column_sum * block_sum  

if __name__ == "__main__":
    bad_grid = [[1, 2, 3, 4, 5, 6, 7, 8, 9]] * 9
    print(f"Bad grid fitness: {evaluate_fitness(bad_grid)}")