from typing import Dict, Tuple

from PySide6.QtGui import QPainter

from constraints__.constraint import Constraint, LogicResult
from sudoku import Cell


class XVConstraint(Constraint):

    NAME = "XV Sum"
    RULE = "Cells connected by a V sum to 5, by an X sum to 10, by an XV sum to 15."

    def __init__(self, sudoku: "Sudoku", cells: Tuple[Cell]):
        super().__init__(sudoku, cells)

        self.total = 5

    @property
    def first(self) -> Cell:
        return self.cells[0]

    @property
    def second(self) -> Cell:
        return self.cells[1]

    def to_json(self) -> Dict:
        return {
            "name": self.NAME,
            "cells": self.indices,
            "total": self.total
        }

    @classmethod
    def from_json(cls, sudoku: "Sudoku", data: Dict) -> Constraint:
        pass

    def apply_constraint(self) -> LogicResult:
        pass

    def draw(self, painter: QPainter, cell_size: int, is_dark_mode: bool = False) -> None:
        pass

