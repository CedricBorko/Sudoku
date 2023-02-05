# sudoku solver using backtracking / recursion
import copy
import math


def getPossibilities(grid, i, j):
    # find all the possibilities

    if not grid[i][j] == 0:
        return [grid[i][j]]

    exists = []

    # find what items can be placed here
    for k in range(0, 9):
        # what are the items with the same first index
        lineval = grid[i][k]
        if lineval not in exists and not lineval == 0:
            exists.append(lineval)
        # what are the items with the same second index
        colval = grid[k][j]
        if colval not in exists and not colval == 0:
            exists.append(colval)

    # what are the items in the same square

    sq_col = math.floor(i / 3) * 3
    sq_line = math.floor(j / 3) * 3

    for k in range(0, 3):
        for k2 in range(0, 3):
            line = sq_line + k
            col = sq_col + k2
            val = grid[col][line]

            if val not in exists and not val == 0:
                exists.append(val)
    available = []

    for i in range(1, 10):
        if i not in exists:
            available.append(i)
    return available


def printGrid(in_grid):
    for i in range(0, 9):
        print("[", ", ".join(map(lambda x: str(x), in_grid[i])), "],")


def simpleSolve(in_grid):
    grid = copy.deepcopy(in_grid)

    found = True
    zeroCount = 1
    while found and zeroCount > 0:
        zeroCount = 0
        found = False
        for i in range(0, 9):
            for j in range(0, 9):
                if grid[i][j] == 0:
                    zeroCount = zeroCount + 1
                    poss = getPossibilities(grid, i, j)
                    if (len(poss) == 0):
                        raise ValueError("Error at {},{} : 0 possibilities".format(i, j))
                    if (len(poss) == 1):
                        found = True
                        grid[i][j] = poss[0]

    return grid, zeroCount


def getLowestOptions(grid):
    lowest = {
        "i": -1,
        "j": -1,
        "poss": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
    for i in range(0, 9):
        for j in range(0, 9):
            if grid[i][j] == 0:
                poss = getPossibilities(grid, i, j)
                if len(poss) < len(lowest["poss"]):
                    lowest = {
                        "i": i,
                        "j": j,
                        "poss": poss
                    }
    return lowest


def solveGrid(in_grid, depth):
    grid = copy.deepcopy(in_grid)
    grid, zerocount = simpleSolve(grid)
    print(zerocount)

    solutions = []

    if zerocount == 0:
        solutions = [grid]
        return solutions
    else:
        options = getLowestOptions(grid)

        for itm in options["poss"]:
            leaf = copy.deepcopy(grid)
            leaf[options["i"]][options["j"]] = itm
            try:
                solutions += solveGrid(leaf, depth + 1)
            except ValueError:
                # invalid option so ignore
                pass
            if len(solutions) > 1:
                raise ValueError("")

    if depth == 0:
        if len(solutions) == 0:
            raise Exception("No solution found")
        # printGrid(node["solutions"][0])
    return solutions


from alt.sudoku_.board import Sudoku

s = Sudoku()
s.generate_random_board()
grid = s.to_table()

ret = solveGrid(grid, 0)
print(ret)