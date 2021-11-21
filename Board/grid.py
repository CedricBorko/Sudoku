from __future__ import annotations

import copy
import random
from abc import ABC, abstractmethod
from typing import List, Tuple

from PySide6.QtCore import Qt

from constraints__.constraint import LogicResult

UP_LEFT = (-1, -1)
UP_RIGHT = (-1, 1)
DOWN_LEFT = (1, -1)
DOWN_RIGHT = (1, 1)


class Direction:
    Left = 0x1
    Up = 0x2
    Down = 0x4
    Right = 0x8

    Up_Left = 0x3
    Up_Right = 0x9

    Down_Left = 0x5
    Down_Right = 0xC


class Grid:

    def __init__(self, size: int = 9):
        self.size = size
        self.cells = [Cell(self, index=ix) for ix in range(size * size)]

        self.initial = copy.deepcopy(self.cells)

        self.diagonal_positive = False
        self.diagonal_negative = False

        self.chain = []

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

    def get_empty(self):
        cells = sorted([cell for cell in self.cells if cell.empty], key=lambda c: len(c.untested))
        if not cells:
            return None

        return cells[0]

    def set(self, index: int, value: int):
        if value < 1 or value > self.size:
            raise ValueError(f"Value must be between 1 and {self.size}")

        self.get_cell(index).value = value

    def get_row(self, row: int) -> List[Cell]:
        return self.cells[row * self.size:row * self.size + self.size]

    def get_column(self, column: int) -> List[Cell]:
        return [cell for cell in self.cells if cell.column == column]

    def get_box(self, box: int) -> List[Cell]:
        return [cell for cell in self.cells if cell.box == box]

    def get_cell(self, index: int) -> Cell:
        return self.cells[index]

    def get_positive_diagonal(self):
        return self.get_diagonal(8, (1, -1))

    def get_negative_diagonal(self):
        return self.get_diagonal(0, (1, 1))

    def get_diagonal(self, start: int, direction: Tuple[int, int]):
        row, col = self.get_coordinate_2D(start)
        cells = []

        while 0 <= row <= self.size - 1 and 0 <= col <= self.size - 1:
            cells.append(self.get_cell(row * self.size + col))
            row += direction[0]
            col += direction[1]

        return cells

    def apply_base_constraints(self):
        for cell in self.cells:
            if cell.empty:
                for number in cell.untested:
                    if not self.is_valid(cell.index, number):
                        cell.untested.remove(number)

    @staticmethod
    def values(cells: List[Cell]) -> List[int]:
        return [cell.value for cell in cells]

    @staticmethod
    def indices(cells: List[Cell]) -> List[int]:
        return [cell.index for cell in cells]

    def is_valid(self, index: int, number: int, echo: bool = False) -> bool:

        cell = self.get_cell(index)

        if self.values(self.get_row(cell.row)).count(number) != 0:
            if echo:
                print(number, "twice in row", cell.row + 1)
            return False

        if self.values(self.get_column(cell.column)).count(number) != 0:
            if echo:
                print(number, "twice in column", cell.column + 1)
            return False

        if self.values(self.get_box(cell.box)).count(number) != 0:
            if echo:
                print(number, "twice in box", cell.box + 1)
            return False

        if self.diagonal_positive:
            if index not in self.indices(self.get_positive_diagonal()):
                return True

            if self.values(self.get_positive_diagonal()).count(number) != 0:
                if echo:
                    print(number, "twice on positive diagonal")
                return False

        if self.diagonal_negative:
            if index not in self.indices(self.get_negative_diagonal()):
                return True

            if self.values(self.get_negative_diagonal()).count(number) != 0:
                if echo:
                    print(number, "twice on positive diagonal")
                return False

        return True

    def calculate_valid_numbers(self):
        for cell in self.cells:
            if not cell.empty: continue
            cell.candidates = self.valid_numbers(cell.index)

    def valid_numbers(self, index: int):
        return [number for number in range(1, 10) if self.is_valid(index, number)]

    def solve(self, echo: bool = False) -> bool:

        self.calculate_valid_numbers()
        next_cell = self.get_empty()

        if next_cell is None:
            return True

        for n in next_cell.candidates:
            if self.is_valid(next_cell.index, n, echo):
                next_cell.value = n
                if self.solve(echo):
                    return True
                next_cell.value = -1
        return False

    def randomize(self):
        while self.values(self.cells).count(-1) > self.size * self.size - 21:
            r, c, n = random.randint(0, 8), random.randint(0, 8), random.randint(1, 9)
            if self.is_valid(r * self.size + c, n):
                self.set(r * self.size + c, n)

    def set_candidates(self):
        result = LogicResult.CHANGED

        for cell in self.cells:
            cell.candidates = self.valid_numbers(cell.index)


class Cell:
    def __init__(self, grid: Grid, index: int):

        self.grid = grid
        self.index = index
        self.value = -1

        self.candidates = {1, 2, 3, 4, 5, 6, 7, 8, 9}
        self.pencil_corner = set()
        self.colors = set()

        self.tested_numbers = set()
        self.untested = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def clear(self):
        self.value = -1

        self.candidates.clear()
        self.pencil_corner.clear()
        self.colors.clear()

        self.tested_numbers.clear()
        self.untested = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    @property
    def row(self) -> int:
        return self.index // self.grid.size

    @property
    def column(self) -> int:
        return self.index % self.grid.size

    @property
    def coordinates(self):
        return self.row, self.column

    @property
    def empty(self):
        return self.value == -1

    @property
    def box(self) -> int:
        box_x = self.row // 3 * 3 * self.grid.size
        box_y = self.column // 3 * 3
        return (box_y * self.grid.size // 3 + box_x) // self.grid.size

    def __eq__(self, other):
        if isinstance(other, Cell):
            return self.index == other.index

    def __lt__(self, other):
        if isinstance(other, Cell):
            return self.index < other.index

    def __repr__(self):
        return f"{self.index}: {self.value if not self.empty else '-'}"

    def __str__(self):
        return f"{self.value if self.value != -1 else '-'}"


if __name__ == '__main__':
    g = Grid(9)
