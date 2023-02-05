import copy
import random

EMPTY = -1


class SudokuGenerator:
    def __init__(self, sudoku: "Sudoku"):
        self.sudoku = sudoku

        self.grid = [self.sudoku.cells[i].value for i in range(self.sudoku.size ** 2)]
        self.counter = 0

    def __repr__(self):
        out = ""
        for i in range(self.sudoku.size * self.sudoku.size):
            if i != 0 and i % self.sudoku.size == 0:
                out += '\n'
            out += f"{self.grid[i]}  "
        return out

    def remove_numbers_from_grid(self, hints: int):
        """remove numbers from the grid to create the puzzle"""

        non_empty_squares = [i for i in range(self.sudoku.size ** 2) if self.grid[i] != EMPTY]
        non_empty_squares_count = len(non_empty_squares)
        empty_squares_count = self.sudoku.size - non_empty_squares_count
        rounds = 3
        while rounds > 0 and non_empty_squares_count != hints:

            index = random.choice(non_empty_squares)
            non_empty_squares.remove(index)

            non_empty_squares_count -= 1

            removed_square = self.grid[index]
            self.grid[index] = EMPTY

            grid_copy = copy.deepcopy(self.grid)

            self.counter = 0
            self.solve_puzzle(grid_copy)

            if self.counter != 1:
                self.grid[index] = removed_square
                non_empty_squares_count += 1
                rounds -= 1
        return

    def num_used_in_row(self, grid, row, number):
        """returns True if the number has been used in that row"""
        return number in [grid[i] for i in range(81) if i // self.sudoku.size == row]

    def num_used_in_column(self, grid, column, number):
        """returns True if the number has been used in that column"""
        return number in [grid[i] for i in range(81) if i % self.sudoku.size == column]

    def num_used_in_subgrid(self, grid, row, column, number):
        """returns True if the number has been used in that subgrid/box"""

        sub_row = (row // 3) * 3
        sub_col = (column // 3) * 3
        for i in range(sub_row, (sub_row + 3)):
            for j in range(sub_col, (sub_col + 3)):
                if grid[i * self.sudoku.size + j] == number:
                    return True
        return False

    def valid_location(self, grid, row, column, number):
        """return False if the number has been used in the row, column or subgrid"""
        if self.num_used_in_row(grid, row, number):
            return False
        elif self.num_used_in_column(grid, column, number):
            return False
        elif self.num_used_in_subgrid(grid, row, column, number):
            return False
        return True

    def solve_puzzle(self, grid):
        """solve the sudoku puzzle with backtracking"""
        for i in range(81):
            row = i // 9
            column = i % 9

            if grid[i] == EMPTY:
                for number in range(1, 10):

                    if self.valid_location(grid, row, column, number):
                        grid[i] = number
                        if not self.find_empty_square(grid):
                            self.counter += 1
                            break
                        else:
                            if self.solve_puzzle(grid):
                                return True
                break
        grid[i] = EMPTY
        return False

    def find_empty_square(self, grid):
        """return the next empty square coordinates in the grid"""
        for i in range(81):
            if grid[i] == EMPTY:
                return i // self.sudoku.size, i % self.sudoku.size
        return
