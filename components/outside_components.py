from __future__ import annotations

import math

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QFont

from components.border_constraints import Component


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


class XSumsClue(OutsideComponent):
    NAME = "XSum"

    def __init__(self, sudoku: "Sudoku", col: int, row: int, total: int):
        super().__init__(sudoku, col, row, total)

    def draw(self, painter: QPainter, cell_size: int):
        painter.setPen(QPen(QColor(0, 0, 255)))
        painter.setFont(QFont("Verdana", 24))
        painter.drawText(
            QRect(self.col * cell_size, self.row * cell_size, cell_size, cell_size),
            Qt.AlignHCenter | Qt.AlignVCenter,
            str(self.total)
        )


class LittleKiller(OutsideComponent):
    NAME = "Little Killer"
    DOWN_RIGHT = 0
    DOWN_LEFT = 1

    TOP_RIGHT = 2
    TOP_LEFT = 3

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

    def get_direction(self, pos: QPoint, cell_size: int):

        # TODO EDGE CASES

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


    def draw(self, painter: QPainter, cell_size: int):
        pen = QPen(QColor(0, 0, 0), 5.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        rect = QRect(self.col * cell_size, self.row * cell_size, cell_size, cell_size)

        match self.direction:

            case self.DOWN_RIGHT:

                end = QPoint(rect.bottomRight().x() - 5, rect.bottomRight().y() - 5)
                start = QPoint(rect.center().x() + 15, rect.center().y() + 15)

                angle_1 = 180
                angle_2 = 270

            case self.TOP_RIGHT:
                end = QPoint(rect.topRight().x() - 5, rect.topRight().y() + 5)
                start = QPoint(rect.center().x() + 15, rect.center().y() - 15)

                angle_1 = 90
                angle_2 = 180

            case self.DOWN_LEFT:
                end = QPoint(rect.bottomLeft().x() + 5, rect.bottomLeft().y() - 5)
                start = QPoint(rect.center().x() - 15, rect.center().y() + 15)

                angle_1 = 270
                angle_2 = 360

            case self.TOP_LEFT:
                end = QPoint(rect.topLeft().x() + 5, rect.topLeft().y() + 5)
                start = QPoint(rect.center().x() - 15, rect.center().y() - 15)

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

        painter.setFont(QFont("Verdana", 16))
        painter.drawText(
            QRect(self.col * cell_size, self.row * cell_size, cell_size, cell_size),
            Qt.AlignHCenter | (Qt.AlignBottom if self.direction in (self.DOWN_LEFT, self.DOWN_RIGHT) else Qt.AlignTop),
            str(self.total)
        )

    def increase_total(self, num: int):
        if self.total > 7:
            return

        if self.total == 37 and num > 2:
            return

        self.total = int(str(self.total) + str(num))


class Sandwich(OutsideComponent):
    NAME = "Sandwich"

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

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "row": self.row,
            "col": self.col,
            "total": self.total
        }
