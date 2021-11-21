from typing import Tuple, Dict

from PySide6.QtGui import QPainter, QColor

from constraints__.constraint import Constraint, LogicResult
from sudoku_.sudoku import Cell


class EvenConstraint(Constraint):

    NAME = "Even Digit"
    RULE = "This Cell must containt an even digit."

    def __init__(self, sudoku: "Sudoku", cells: Tuple[Cell]):
        super().__init__(sudoku, cells)

    @property
    def cell(self) -> Cell:
        return self.cells[0]

    def to_json(self) -> Dict:
        return {
            "type": self.NAME,
            "cells": self.indices
        }

    @classmethod
    def from_json(cls, sudoku: "Sudoku", data: Dict) -> Constraint:
        return cls(sudoku, data["cells"])

    def apply_constraint(self) -> LogicResult:
        numbers = tuple(filter(lambda n: n % 2 == 0, self.cell.valid_numbers))
        result = LogicResult.CHANGED if numbers != self.cell.valid_numbers else LogicResult.NULL
        if not numbers:
            return LogicResult.INVALID

        self.cell.valid_numbers = numbers

        return result

    def draw(self, painter: QPainter, cell_size: int, is_dark_mode: bool = False) -> None:

        color = QColor(90, 90, 90, 100) if not is_dark_mode else QColor(160, 160, 160, 90)
        painter.fillRect(self.cell.rect(cell_size), color)


