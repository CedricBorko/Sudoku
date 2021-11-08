from typing import List

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QFont

from components.border_constraints import Component
from sudoku import Cell, tile_to_poly


class RegionComponent(Component):
    pass


class Cage:
    def __init__(self, cells: List[int], total: int):
        self.cells = cells
        self.total = total

        self.inner_offset = 5
        self.no_repeat = True

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
