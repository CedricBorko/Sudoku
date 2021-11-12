from __future__ import annotations

import math
from typing import List

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QFont

from components.border_components import Component
from sudoku import Cell
from utils import smallest_sum_including_x, n_digit_sums


class OutsideComponent(Component):
    def __init__(self, sudoku: "Sudoku", col: int, row: int, total: int):
        super().__init__(sudoku, [])

        self.col = col
        self.row = row
        self.total = total

    def __eq__(self, other):
        return self.col == other.col and self.row == other.row

    def __lt__(self, other):
        return (self.row * 11 + self.col) < (other.row * 11 + other.col)

    @property
    def cells(self) -> List[Cell]:
        if self.col == 0:
            return self.sudoku.get_entire_row((self.row - 1) * 9)

        if self.col == 10:
            return self.sudoku.get_entire_row((self.row - 1) * 9)[::-1]

        if self.row == 0:
            return self.sudoku.get_entire_column((self.col - 1) % 9)

        if self.row == 10:
            return self.sudoku.get_entire_column((self.col - 1) % 9)[::-1]

    def get(self, col: int, row: int):
        for cmp in self.sudoku.outside_components:
            if (cmp.col, cmp.row) == (col, row):
                return cmp

    def setup(self, col: int, row: int):
        self.col = col
        self.row = row

    def clear(self):
        pass

    def opposite(self):
        return None

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

    @staticmethod
    def can_create(col: int, row: int) -> bool:
        return (col in (0, 10) and 1 <= row <= 9) or (row in (0, 10) and 1 <= col <= 9)


class XSumsClue(OutsideComponent):
    NAME = "XSum"
    RULE = ("Blue numbers outside the grid indicate the sum of the first X cells"
            " in that row or column where X is the first digit (included in the sum).")

    def __init__(self, sudoku: "Sudoku", col: int, row: int, total: int):
        super().__init__(sudoku, col, row, total)

    def increase_total(self, num: int):
        if self.total > 4:
            return

        if self.total == 4 and num > 5:
            return

        self.total = int(str(self.total) + str(num))

    def draw(self, painter: QPainter, cell_size: int):
        painter.setPen(QPen(QColor(0, 0, 255)))
        painter.setFont(QFont("Asap", 24))
        painter.drawText(
            QRect(self.col * cell_size, self.row * cell_size, cell_size, cell_size),
            Qt.AlignHCenter | Qt.AlignVCenter,
            str(self.total)
        )

    def num_missing(self):
        return len([c.value for c in self.cells if c.value == 0 and self.cells.index(c) < self.first.value])

    def sum_sofar(self):
        return sum([c.value for c in self.cells][0:self.first.value])

    def filled_values(self):
        return [c.value for c in self.cells if self.cells.index(c) < self.first.value]

    def valid(self, index: int, number: int) -> bool:
        if index not in [c.index for c in self.cells]:
            return True

        if self.first.value != 0:
            if [c.index for c in self.cells].index(index) >= self.first.value:
                return True

            no_match = True
            for total in n_digit_sums(self.num_missing(), self.total- self.sum_sofar(), tuple(i for i in range(1, 10) if i not in (self.filled_values()))):
                if number in total:
                    no_match = False

            if no_match:
                return False

            if self.sum_sofar() > self.total:
                return False

            for total in n_digit_sums(self.first.value, self.total):
                if number in total and self.first.value in total:
                    return True

        else:
            if index == self.first.index:
                if not n_digit_sums(number - 1, self.total - number, tuple(i for i in range(1, 10) if i != number)):
                    return False

            return True

    @staticmethod
    def smallest_sum(length: int, already_present: List[int]):
        nums = [i for i in range(1, 10) if i not in already_present]
        return sum((nums[0:length - len(already_present)] + already_present))


class LittleKiller(OutsideComponent):
    NAME = "Little Killer"
    DOWN_RIGHT = 0
    DOWN_LEFT = 1

    TOP_RIGHT = 2
    TOP_LEFT = 3

    RULE = "Arrows outside the grid show the sum of the digits on the indicated diagonal."

    def __init__(self, sudoku: "Sudoku", col: int, row: int, total: int, direction: int):
        super().__init__(sudoku, col, row, total)

        self.direction = direction
        if self.col == 0 and self.direction in (self.DOWN_LEFT, self.TOP_LEFT):
            raise ValueError("Going the wrong direction dude")

        if self.col == 10 and self.direction in (self.DOWN_RIGHT, self.TOP_RIGHT):
            raise ValueError("Going the wrong direction dude")

        if self.row == 0 and self.direction in (self.TOP_RIGHT, self.TOP_LEFT):
            raise ValueError("Going the wrong direction dude")

        if self.row == 10 and self.direction in (self.DOWN_RIGHT, self.DOWN_LEFT):
            raise ValueError("Going the wrong direction dude")

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "row": self.row,
            "col": self.col,
            "total": self.total,
            "direction": self.direction
        }

    def get_direction(self, pos: QPoint, cell_size: int):

        match self.col, self.row:
            case 0, 0:
                self.direction = self.DOWN_RIGHT
            case 10, 10:
                self.direction = self.TOP_LEFT
            case 0, 10:
                self.direction = self.TOP_RIGHT
            case 10, 0:
                self.direction = self.DOWN_LEFT
            case 0, _:
                self.direction = self.TOP_RIGHT if pos.y() % cell_size <= cell_size // 2 else self.DOWN_RIGHT
            case _, 0:
                self.direction = self.DOWN_LEFT if pos.x() % cell_size <= cell_size // 2 else self.DOWN_RIGHT
            case 10, _:
                self.direction = self.DOWN_LEFT if pos.y() % cell_size >= cell_size // 2 else self.TOP_LEFT
            case _, 10:
                self.direction = self.TOP_LEFT if pos.x() % cell_size <= cell_size // 2 else self.TOP_RIGHT
            case _, _:
                return

        # EDGE CASES

        if (self.col == 0 and self.row == 1) or (self.col == 1 and self.row == 0):
            self.direction = self.DOWN_RIGHT

        if (self.col == 0 and self.row == 9) or (self.col == 1 and self.row == 10):
            self.direction = self.TOP_RIGHT

        if (self.col == 9 and self.row == 0) or (self.col == 10 and self.row == 1):
            self.direction = self.DOWN_LEFT

        if (self.col == 10 and self.row == 9) or (self.col == 9 and self.row == 10):
            self.direction = self.TOP_LEFT

    def draw(self, painter: QPainter, cell_size: int):
        pen = QPen(QColor(0, 0, 0), 4.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        rect = QRect(self.col * cell_size, self.row * cell_size, cell_size, cell_size)
        dst = 18

        match self.direction:

            case self.DOWN_RIGHT:

                end = QPoint(rect.bottomRight().x() - 5, rect.bottomRight().y() - 5)
                start = QPoint(rect.center().x() + dst, rect.center().y() + dst)

                angle_1 = 180
                angle_2 = 270

            case self.TOP_RIGHT:
                end = QPoint(rect.topRight().x() - 5, rect.topRight().y() + 5)
                start = QPoint(rect.center().x() + dst, rect.center().y() - dst)

                angle_1 = 90
                angle_2 = 180

            case self.DOWN_LEFT:
                end = QPoint(rect.bottomLeft().x() + 5, rect.bottomLeft().y() - 5)
                start = QPoint(rect.center().x() - dst, rect.center().y() + dst)

                angle_1 = 270
                angle_2 = 0

            case self.TOP_LEFT:
                end = QPoint(rect.topLeft().x() + 5, rect.topLeft().y() + 5)
                start = QPoint(rect.center().x() - dst, rect.center().y() - dst)

                angle_1 = 0
                angle_2 = 90

            case _:
                return

        painter.drawLine(start, end)
        painter.drawLine(
            end,
            QPoint(
                end.x() + math.cos(math.radians(angle_1)) * cell_size // 8,
                end.y() + math.sin(math.radians(angle_1)) * cell_size // 8
            )
        )

        painter.drawLine(
            end,
            QPoint(
                end.x() + math.cos(math.radians(angle_2)) * cell_size // 8,
                end.y() + math.sin(math.radians(angle_2)) * cell_size // 8
            )
        )

        painter.setFont(QFont("Asap", 16))
        painter.drawText(
            QRect(self.col * cell_size, self.row * cell_size, cell_size, cell_size),
            Qt.AlignHCenter | (Qt.AlignBottom if self.direction in (
                self.DOWN_LEFT, self.DOWN_RIGHT) else Qt.AlignTop),
            str(self.total)
        )

    def increase_total(self, num: int):
        if self.total > 7:
            return

        if self.total == 37 and num > 2:
            return

        self.total = int(str(self.total) + str(num))

    @staticmethod
    def can_create(col: int, row: int) -> bool:
        return (col in (0, 10) and 0 <= row <= 10) or (row in (0, 10) and 0 <= col <= 10)


class Sandwich(OutsideComponent):
    NAME = "Sandwich"
    RULE = ("Black numbers outside the grid indicate the sum of the digits"
            " that are between the 1 and 9 in that row or column (not including 1 and 9).")

    def __init__(self, sudoku: "Sudoku", col: int, row: int, total: int = 0):
        super().__init__(sudoku, col, row, total)

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
        painter.setFont(QFont("Asap", 24))
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

    def __repr__(self):
        return f"Sandwich({self.total=} {self.row=} {self.col=})"

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
