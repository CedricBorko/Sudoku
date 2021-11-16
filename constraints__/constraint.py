from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple, Dict

from PySide6.QtGui import QPainter

from sudoku import Cell


class Constraint(ABC):
    NAME: str
    RULE: str

    def __init__(self, sudoku: "Sudoku", cells: Tuple[Cell]):
        self.sudoku = sudoku
        self.cells = cells

    def __repr__(self):
        return f"{self.NAME}: {self.RULE}"

    @property
    def indices(self) -> List[int]:
        return [cell.index for cell in self.cells]

    @property
    def values(self) -> List[int]:
        return [cell.value for cell in self.cells]

    @property
    def unfilled(self) -> List[Cell]:
        return [cell for cell in self.cells if cell.empty]

    @abstractmethod
    def to_json(self) -> Dict:
        ...

    @classmethod
    @abstractmethod
    def from_json(cls, sudoku: "Sudoku", data: Dict) -> Constraint:
        ...

    @abstractmethod
    def apply_constraint(self) -> LogicResult:
        ...

    @abstractmethod
    def draw(self, painter: QPainter, cell_size: int, is_dark_mode: bool = False) -> None:
        ...


class LogicResult(Enum):

    NULL = 0
    CHANGED = 1
    INVALID = 2
    SOLVED = 3
