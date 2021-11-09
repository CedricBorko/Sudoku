from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QImage

from components.border_constraints import Component, LessGreater


class CellComponent(Component):
    def __init__(self, sudoku: "Sudoku", index: int):
        super().__init__(sudoku, [index])

        self.index = index

    def __repr__(self):
        return f"{self.index}"

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "index": self.index,
        }


class OddDigit(CellComponent):
    NAME = "Odd digit"

    def __init__(self, sudoku: "Sudoku", index: int):
        super().__init__(sudoku, index)

    def valid(self, index: int, number: int):
        return number % 2 != 0

    def draw(self, painter: QPainter, cell_size: int):
        painter.setBrush(QBrush(QColor("#CCCCCC")))  # MEDIUM GRAY COLOR
        painter.setPen(Qt.NoPen)

        size = int(cell_size * 0.8)
        painter.drawEllipse(self.cells[0].rect(cell_size).center(), size // 2, size // 2)


class EvenDigit(CellComponent):
    NAME = "Even digit"

    def __init__(self, sudoku: "Sudoku", index: int):
        super().__init__(sudoku, index)

    def valid(self, index: int, number: int):
        return number % 2 == 0

    def draw(self, painter: QPainter, cell_size: int):
        painter.setPen(Qt.NoPen)

        painter.fillRect(self.cells[0].scaled_rect(cell_size, 0.8), QColor("#CCCCCC"))
