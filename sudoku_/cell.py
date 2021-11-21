from __future__ import annotations

from typing import List

from sudoku_.sudoku import Sudoku
from utils import Constants


class Cell:

    def __init__(self, sudoku: Sudoku, index: int, value: int = Constants.EMPTY):

        self.sudoku = sudoku

        self.value = value
        self.index = index

        self.candidates = Constants.NUMBERS

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
        return self.value == Constants.EMPTY

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
