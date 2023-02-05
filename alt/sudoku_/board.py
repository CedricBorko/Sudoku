from __future__ import annotations

import copy
import random
import time
import timeit
from typing import List, Tuple, Optional

EMPTY = -1


class Sudoku:
    def __init__(self, size: int = 9):
        self.size = size

        self.cells = [Cell(self, i) for i in range(self.size ** 2)]

        self.initial = copy.deepcopy(self.cells)

    def __repr__(self):
        out = ""
        for i in range(self.size * self.size):
            if i != 0 and i % self.size == 0:
                out += '\n'
            out += f"{self.cells[i]}  "
        return out

    def get_coordinate_1D(self, row: int, column: int) -> int:
        """
        Returns the Index associated with a given Row and Column..
        :param row:
        :param column:
        :return: Index
        """
        return row * self.size + column

    def get_coordinate_2D(self, index: int) -> Tuple[int, int]:
        """
        Returns the Row and Column associated with a given index.
        :param index: Coordinate of a Cell
        :return: Row, Column
        """
        return index // self.size, index % self.size

    def is_valid(self, index: int, offset: int) -> bool:
        """

        :param index: index being checked
        :param offset: offset from the index being checked e.g. index = 4 offset = 1 -> checking 5
        :return: index in bounds of the grid
        """
        return 0 <= index + offset <= self.size ** 2 and not self.is_exclusion(index, offset)

    def is_exclusion(self, index: int, offset: int) -> bool:
        """

        Exclusions are "edge" cases. E.g. Cell 9 has no left neighbours because the 8th Cell is
        in the row above on the other side of the grid but index 9 - offset 1 = 8 would return
        true in the is_valid method. These cases are being checked here and excluded in the Cells
        neighours.

        :param index: index being checked
        :param offset: offset from the index being checked e.g. index = 4 offset = 1 -> checking 5
        :return: index in bounds of the grid
        """
        return (
            index % self.size == 0 and offset in (-10, -1, 8)
            or index % self.size == self.size - 1 and offset in (-8, 1, 10)
            or index // self.size == 0 and offset in (-10, -9, -8)
            or index // self.size == self.size - 1 and offset in (8, 9, 10)
        )

    def to_table(self) -> List[List[int]]:
        return [self.values(self.get_row(i)) for i in range(9)]

    def to_string(self) -> str:
        return ''.join(map(str, self.cells))

    def get_row(self, row: int) -> List[Cell]:
        return [cell for cell in self.cells if cell.row == row]

    def get_column(self, column: int) -> List[Cell]:
        return [cell for cell in self.cells if cell.column == column]

    def get_box(self, box: int) -> List[Cell]:
        return [cell for cell in self.cells if cell.box == box]

    def get_box_index(self, index: int) -> int:
        row, column = index // self.size, index % self.size

        box_x = row // 3 * 3 * self.size
        box_y = column // 3 * 3
        return (box_y * self.size // 3 + box_x) // self.size

    def get_cell(self, index: int) -> Cell:
        return self.cells[index]

    def get_positive_diagonal(self) -> List[Cell]:
        return self.get_diagonal(8, (1, -1))

    def get_negative_diagonal(self) -> List[Cell]:
        return self.get_diagonal(0, (1, 1))

    def get_diagonal(self, start: int, direction: Tuple[int, int]) -> List[Cell]:
        row, col = self.get_coordinate_2D(start)
        cells = []

        while 0 <= row <= self.size - 1 and 0 <= col <= self.size - 1:
            cells.append(self.get_cell(row * self.size + col))
            row += direction[0]
            col += direction[1]

        return cells

    def get_empty(self) -> Cell | None:
        cells = list(filter(lambda c: c.is_empty, self.cells))

        if not cells:
            return None

        return cells[0]

    @staticmethod
    def indices(cells: List[Cell]) -> List[int]:
        return [cell.index for cell in cells]

    @staticmethod
    def values(cells: List[Cell]) -> List[int]:
        return [cell.value for cell in cells]

    def count_row(self, row: int, number: int) -> int:
        return self.values(self.get_row(row)).count(number)

    def count_column(self, column: int, number: int) -> int:
        return self.values(self.get_column(column)).count(number)

    def count_box(self, box: int, number: int) -> int:
        return self.values(self.get_box(box)).count(number)

    def can_set(self, index: int, number: int) -> bool:
        cell = self.get_cell(index)
        r, c, b = cell.row, cell.column, cell.box

        return (
            self.count_row(r, number) == 0
            and self.count_column(c, number) == 0
            and self.count_box(b, number) == 0
        )

    def generate_random_board(self):
        for cell in self.cells:
            cell.value = EMPTY

        _l = list(range(1, 10))
        for row in range(3):
            for col in range(3):
                _num = random.choice(_l)
                self.cells[row * self.size + col].value = _num
                _l.remove(_num)

        _l = list(range(1, 10))
        for row in range(3, 6):
            for col in range(3, 6):
                _num = random.choice(_l)
                self.cells[row * self.size + col].value = _num
                _l.remove(_num)

        _l = list(range(1, 10))
        for row in range(6, 9):
            for col in range(6, 9):
                _num = random.choice(_l)
                self.cells[row * self.size + col].value = _num
                _l.remove(_num)

        self.brute_force(True)

    def genereate_board_with_unique_solution(self, hints: int = 30) -> None:

        full_board = Sudoku(self.size)
        full_board.generate_random_board()

        generator = Generator(full_board)
        generator.remove_numbers_from_grid(hints)
        for i in range(self.size ** 2):
            self.cells[i].value = generator.grid[i]

    def find_empty_to_count_solutions(self, board: Sudoku, curr: int):
        _k = 1

        for row in range(self.size):
            for column in range(self.size):
                if board.cells[row * self.size + column].is_empty:
                    if _k == curr:
                        return row, column

                    _k += 1
        return False

    def count_solutions(self):

        _z = 0
        solutions = []
        for row in range(self.size):
            for column in range(self.size):
                if self.cells[row * self.size + column].is_empty:
                    _z += 1

        for i in range(1, _z + 1):

            _board_copy = copy.deepcopy(self)

            _r, _c = self.find_empty_to_count_solutions(_board_copy, i)

            _board_copy_solution = _board_copy.__solveToFindNumberOfSolutions(_r, _c)

            solutions.append(tuple(c.value for c in _board_copy_solution))

            if len(list(set(solutions))) > 1:
                return True

        return False

    def __solveToFindNumberOfSolutions(self, row, column):
        index = self.get_coordinate_1D(row, column)
        for n in range(1, 10):
            if self.can_set(index, n):
                self.get_cell(index).value = n

                if self.brute_force():
                    return self.cells

                self.get_cell(index).value = EMPTY

        return False

    def is_valid_grid(self) -> bool:

        for number in (n for n in range(1, self.size + 1)):
            for row in range(self.size):
                if self.count_row(row, number) > 1:
                    return False

            for column in range(self.size):
                if self.count_column(column, number) > 1:
                    return False

            for box in range(self.size):
                if self.count_box(box, number) > 1:
                    return False

        return True

    def is_solved_grid(self) -> bool:

        for number in (n for n in range(1, self.size + 1)):
            for row in range(self.size):
                if self.count_row(row, number) != 1:
                    return False

            for column in range(self.size):
                if self.count_column(column, number) != 1:
                    return False

            for box in range(self.size):
                if self.count_box(box, number) != 1:
                    return False

        return True

    def has_solution(self):
        return self.brute_force()

    def brute_force(self, random_pick: bool = False) -> bool:

        current = self.get_empty()

        if current is None:
            return True

        numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        if random_pick:
            random.shuffle(numbers)

        for number in numbers:

            if self.can_set(current.index, number):
                current.value = number

                if self.brute_force(random_pick):
                    return True

                current.value = EMPTY

        return False


class Cell:

    def __init__(self, sudoku: Sudoku, index: int, value: int = EMPTY):

        self.sudoku = sudoku

        self.value = value
        self.index = index

        self.candidates = {1, 2, 3, 4, 5, 6, 7, 8, 9}

    def __eq__(self, other):
        if isinstance(other, Cell):
            return self.index == other.index

    def __lt__(self, other):
        if isinstance(other, Cell):
            return self.index < other.index

    def __repr__(self):
        return f"{self.index}: {self.value if not self.is_empty else '-'}"

    def __str__(self):
        return f"{self.value if self.value != -1 else '-'}"

    def __copy__(self):
        return Cell(self.sudoku, self.index, self.value)

    def as_string(self):
        return str(self.value)

    @property
    def row(self) -> int:
        return self.index // self.sudoku.size

    @property
    def column(self) -> int:
        return self.index % self.sudoku.size

    @property
    def coordinates(self):
        return self.row, self.column

    @property
    def is_empty(self):
        return self.value == EMPTY

    @property
    def box(self) -> int:
        box_x = self.row // 3 * 3 * self.sudoku.size
        box_y = self.column // 3 * 3
        return (box_y * self.sudoku.size // 3 + box_x) // self.sudoku.size

    @property
    def orthogonal_neighbours(self) -> List[Cell]:
        return [
            self.sudoku.get_cell(self.index + offset)
            for offset in (-9, -1, 1, 9) if self.sudoku.is_valid(self.index, offset)
        ]

    @property
    def diagonal_neighbours(self) -> List[Cell]:
        return [
            self.sudoku.get_cell(self.index + offset)
            for offset in (-10, -8, 8, 10) if self.sudoku.is_valid(self.index, offset)
        ]

    @property
    def neighbours(self) -> List[Cell]:
        return sorted(self.orthogonal_neighbours + self.diagonal_neighbours)

    @property
    def num_neighbours(self) -> int:
        return len(self.neighbours)


class Generator:
    def __init__(self, sudoku: Sudoku):
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

    def num_used_in_column(self, grid, col, number):
        """returns True if the number has been used in that column"""
        return number in [grid[i] for i in range(81) if i % self.sudoku.size == col]

    def num_used_in_subgrid(self, grid, row, col, number):
        """returns True if the number has been used in that subgrid/box"""

        sub_row = (row // 3) * 3
        sub_col = (col // 3) * 3
        for i in range(sub_row, (sub_row + 3)):
            for j in range(sub_col, (sub_col + 3)):
                if grid[i * self.sudoku.size + j] == number:
                    return True
        return False

    def valid_location(self, grid, row, col, number):
        """return False if the number has been used in the row, column or subgrid"""
        if self.num_used_in_row(grid, row, number):
            return False
        elif self.num_used_in_column(grid, col, number):
            return False
        elif self.num_used_in_subgrid(grid, row, col, number):
            return False
        return True

    def solve_puzzle(self, grid):
        """solve the sudoku puzzle with backtracking"""
        for i in range(81):
            row = i // 9
            col = i % 9

            if grid[i] == EMPTY:
                for number in range(1, 10):

                    if self.valid_location(grid, row, col, number):
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


if __name__ == '__main__':
    sudo = Sudoku(9)

    sudo.generate_random_board()
    sudo.genereate_board_with_unique_solution(28)
    print(sudo)
