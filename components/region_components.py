from __future__ import annotations

import itertools
from abc import ABC
from typing import List, Dict

from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QFont

from components.border_components import Component
from sudoku import Cell, tile_to_poly
from utils import SmartList, sum_first_n


class RegionComponent(Component, ABC):
    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)

    def clear(self):
        pass

    def opposite(self):
        pass

    def valid_location(self, index: int):
        for r_cmp in self.sudoku.region_components:
            if index in r_cmp.indices:
                return False
        return True

    def get_orthogonals(self):
        return list(itertools.chain.from_iterable(
            [[index for index in cell.neighbours] for cell in self.cells]))


class Clone(RegionComponent):
    NAME = "Clone"


    def __init__(self, sudoku: "Sudoku", indices: SmartList[int], partner: bool = False):
        super().__init__(sudoku, indices)

        self.partner = partner
        self.partner_clone = None

    def __eq__(self, other):
        if isinstance(other, Clone):
            return len(set(self.indices).intersection(set(other.indices))) > 0
        return False

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.cells,
        }

    def draw(self, painter: QPainter, cell_size: int) -> None:
        for cell in self.cells:
            painter.fillRect(cell.rect(cell_size), QColor(255, 255, 0, 90))

        if self.partner_clone is not None:
            self.partner_clone.draw(painter, cell_size)


class Cage(RegionComponent):
    NAME = "Killer Cage"
    RULE = ("Number in the indicated cage sum to the small number in its top left corner. "
            "Numbers inside the cage must not repeat.")

    def __init__(self, sudoku: "Sudoku", indices: SmartList[int], total: int = None):
        super().__init__(sudoku, indices)

        self.total = total

        self.inner_offset = 5

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "total": self.total
        }

    @classmethod
    def from_json(cls, sudoku: "Sudoku", data: Dict):
        return Cage(sudoku, data["indices"], data["total"])

    def __eq__(self, other):
        if isinstance(other, Cage):
            return len(set(self.indices).intersection(set(other.indices))) > 0
        return False

    def increase_total(self, num: int):
        if self.total is None:
            self.total = num
            return

        if self.total > 4:
            return

        if self.total == 4 and num > 5:
            return

        self.total = int(str(self.total) + str(num))

    def reduce_total(self):
        if self.total is None:
            self.total = 0
            return

        if self.total == 0:
            return

        str_total = str(self.total)
        if len(str_total) == 1:
            self.total = 0
            return

        self.total = int(str(self.total)[0:len(str(self.total)) - 1])
        if self.total < 0:
            self.total = 10

    def set_min(self):
        if self.total is not None:
            self.total = sum_first_n(len(self.indices))

    def get(self, index: int):
        for cmp in self.sudoku.region_components:
            if index in cmp.indices:
                return cmp

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

    def clear(self):
        self.indices = SmartList(max_length=9)
        self.total = 1

    def space_left(self, board: List[Cell]) -> int:
        return len([cell for cell in board if cell.index in self.cells and cell.value == 0])

    def draw(self, painter: QPainter, cell_size: int):

        pen = QPen(QColor(40, 40, 40), 2.0, Qt.DashLine)
        pen.setCapStyle(Qt.RoundCap)

        painter.setPen(pen)

        edges = tile_to_poly(self.sudoku.board, cell_size, set(self.indices), self.inner_offset)
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

        painter.setFont(QFont("Asap", 12))

        if self.total is None:
            return
        offset = 8 if self.total > 10 else 6

        top_left = QPoint(offset + cell_size + edges[0].sx, offset + cell_size + edges[0].sy)
        rect = QRect(top_left, QSize(20, 20))
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignHCenter, str(self.total))