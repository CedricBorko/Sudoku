from __future__ import annotations
from typing import List

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QFont

from components.border_constraints import Component
from sudoku import Cell, tile_to_poly


class RegionComponent(Component):
    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)

    def clear(self):
        pass

    def opposite(self):
        pass


class Sandwich(RegionComponent):
    NAME = "Sandwich"

    def __init__(self, sudoku: "Sudoku", col: int, row: int, total: int = 0):
        super().__init__(sudoku, [])

        self.col = col
        self.row = row
        self.total = total

    def opposite(self):
        if self.col == 0 and 1 <= self.row <= 9:
            return Sandwich(self.sudoku, 10, self.row, self.total)
        elif self.col == 10 and 1 <= self.row <= 9:
            return Sandwich(self.sudoku, 0, self.row, self.total)
        elif self.row == 0 and 1 <= self.col <= 9:
            return Sandwich(self.sudoku, self.col, 10, self.total)
        elif self.row == 10 and 1 <= self.col <= 9:
            return Sandwich(self.sudoku, self.col, 0, self.total)
        else:
            return None


    def draw(self, painter: QPainter, cell_size: int):
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Verdana", 24))
        painter.drawText(
            QRect(self.col * cell_size, self.row * cell_size, cell_size, cell_size),
            Qt.AlignHCenter | Qt.AlignVCenter,
            str(self.total)
        )

    def clear(self):
        self.col = -1
        self.row = -1
        self.total = 0

        self.indices = []

    def __eq__(self, other):
        if isinstance(other, Sandwich):
            return self.col == other.col and self.row == other.row
        return False

    def __repr__(self):
        return f"Sandwich({self.total=} {self.row=} {self.col=})"

    def __lt__(self, other):
        return (self.row * 11 + self.col) < (other.row * 11 + other.col)

    def increase_total(self, num: int):

        if self.total > 3:
            return

        if self.total == 3 and num > 5:
            return

        self.total = int(str(self.total) + str(num))

    def reduce_total(self):
        if self.total == 0:
            return

        str_total = str(self.total)
        if len(str_total) == 1:
            self.total = 0
            return

        self.total = int(str(self.total)[0:len(str(self.total)) - 1])
        if self.total < 0:
            self.total = 10

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "row": self.row,
            "col": self.col,
            "total": self.total
        }


class Cage(RegionComponent):
    def __init__(self, sudoku: "Sudoku", indices: List[int], total: int):
        super().__init__(sudoku, indices)

        self.total = total

        self.inner_offset = 5

    def to_json(self):
        return {
            "indices": self.cells,
            "total": self.total
        }

    def valid(self, board: List[Cell], number: int, show_constraint: bool = False) -> bool:

        if number >= self.total and len(self.cells) > 1:
            return False

        sum_so_far = sum(cell.value for cell in board if cell.index in self.cells)

        if sum_so_far + number > self.total:
            if show_constraint:
                print(number, f"WOULD EXCEED THE TOTAL ({self.total}) OF THIS CAGE")
            return False

        if number in [cell.value for cell in board if cell.index in self.cells] and self.no_repeat:
            if show_constraint:
                print(number, f"ALREADY IN CAGE")
            return False

        if self.space_left(board) == 1 and number + sum_so_far < self.total:
            if show_constraint:
                print("USING", number,
                      f"WOULD ONLY REACH {sum_so_far + number} NOT THE TOTAL ({self.total}) OF THIS CAGE")
            return False

        return True

    def space_left(self, board: List[Cell]) -> int:
        return len([cell for cell in board if cell.index in self.cells and cell.value == 0])

    def draw(self, painter: QPainter, board: List[Cell], cell_size: int):

        pen = QPen(QColor("#000000"), 3.0, Qt.DotLine)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        edges = tile_to_poly(board, cell_size, set(self.cells), self.inner_offset)
        for edge in edges:
            if edge.edge_type == 0:

                painter.drawLine(
                    cell_size + edge.sx + self.inner_offset,
                    cell_size + edge.sy + self.inner_offset,
                    cell_size + edge.ex - self.inner_offset,
                    cell_size + edge.ey + self.inner_offset
                )

            elif edge.edge_type == 1:
                painter.drawLine(
                    cell_size + edge.sx - self.inner_offset,
                    cell_size + edge.sy + self.inner_offset,
                    cell_size + edge.ex - self.inner_offset,
                    cell_size + edge.ey - self.inner_offset
                )

            elif edge.edge_type == 2:
                painter.drawLine(
                    cell_size + edge.sx + self.inner_offset,
                    cell_size + edge.sy - self.inner_offset,
                    cell_size + edge.ex - self.inner_offset,
                    cell_size + edge.ey - self.inner_offset
                )

            else:
                painter.drawLine(
                    cell_size + edge.sx + self.inner_offset,
                    cell_size + edge.sy + self.inner_offset,
                    cell_size + edge.ex + self.inner_offset,
                    cell_size + edge.ey - self.inner_offset
                )

        painter.setFont(QFont("Verdana", 12))

        painter.drawText(QRect(8 + cell_size + edges[0].sx, 5 + cell_size + edges[0].sy, 20, 20),
                         str(self.total))
