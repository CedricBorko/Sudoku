from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush

from alt.constraints.border_components import Component


class CellComponent(Component):
    def __init__(self, sudoku: "Sudoku", index: int):
        super().__init__(sudoku, [])

        self.index = index
        self.color = QColor(120, 120, 120, 100)

    def __repr__(self):
        return f"{self.index}"

    def __eq__(self, other):
        return self.index == other.hovered_cell

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "index": self.index,
        }

    def clear(self):
        self.index = 0

    def get(self, index: int):
        for cmp in self.sudoku.cell_components:
            if cmp.hovered_cell == index:
                return cmp


class OddDigit(CellComponent):
    NAME = "Odd digit"

    RULE = "Cells with a grey circle contain an odd digit."

    def __init__(self, sudoku: "Sudoku", index: int):
        super().__init__(sudoku, index)

    def valid(self, index: int, number: int):
        return number % 2 != 0

    def draw(self, painter: QPainter, cell_size: int):
        painter.setBrush(QBrush(self.color))  # MEDIUM GRAY COLOR
        painter.setPen(Qt.NoPen)

        size = int(cell_size * 0.8)
        rect = self.sudoku.cells[self.index].rect(cell_size)
        painter.drawEllipse(
            QPoint(rect.x() + cell_size // 2, rect.y() + cell_size // 2),
            size // 2,
            size // 2
        )


class EvenDigit(CellComponent):
    NAME = "Even digit"
    RULE = "Cells with a grey square contain an even digit."

    def __init__(self, sudoku: "Sudoku", index: int):
        super().__init__(sudoku, index)

    def valid(self, index: int, number: int):
        return number % 2 == 0

    def draw(self, painter: QPainter, cell_size: int):
        painter.setPen(Qt.NoPen)

        rect = self.sudoku.cells[self.index].scaled_rect(cell_size, 0.8)
        painter.fillRect(rect, self.color)
