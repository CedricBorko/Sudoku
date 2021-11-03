from abc import ABC
from typing import List

from PySide6.QtGui import QPainter


class Constraint(ABC):
    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        self.sudoku = sudoku
        self.indices = indices

    @property
    def cells(self):
        return [self.sudoku.board[i] for i in self.indices]

    def valid(self, index: int, number: int):
        pass

    def draw(self, painter: QPainter, cell_size: int):
        pass
