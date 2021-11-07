from __future__ import annotations
import copy
import math
from abc import ABC
from typing import List

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont, Qt

from sudoku import Sudoku


class Constraint(ABC):
    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        self.sudoku = sudoku
        self.indices = indices

    @property
    def cells(self):
        return [self.sudoku.board[i] for i in self.indices]

    def valid(self, index: int, number: int):
        pass

    def draw(self, painter: QPainter, cell_size: int):
        pass


class BorderConstraint(Constraint):
    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)

    def __eq__(self, other):
        if isinstance(other, BorderConstraint):
            return sorted(self.indices) == sorted(other.indices)
        return NotImplemented

    def other_cell(self, index: int):
        return self.cells[0] if self.cells[0].index != index else self.cells[1]

    def pos(self, index: int):
        return self.indices.index(index)

    def deep_compare(self, other) -> bool:
        pass

    def create(self, indices: List[int]):
        self.indices = indices

        replace = False

        for border_constraint in self.sudoku.border_constraints:
            if border_constraint == self:

                self.sudoku.border_constraints.remove(border_constraint)
                replace = True

                if not self.deep_compare(border_constraint):
                    self.sudoku.border_constraints.append(self)
                break

        if not replace:
            self.sudoku.border_constraints.append(self)


class KropkiDot(BorderConstraint):
    def __init__(self, sudoku: "Sudoku", indices: List[int], consecutive: bool = True):
        super().__init__(sudoku, indices)

        self.consecutive = consecutive

    def __repr__(self):
        return ', '.join(map(str, self.indices)) + " white" if self.consecutive else " black"

    def deep_compare(self, other) -> bool:
        if isinstance(other, KropkiDot):
            return self.consecutive == other.consecutive
        return False

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "white": self.consecutive
        }

    def valid(self, index: int, number: int):

        other = self.other_cell(index)

        if self.consecutive:

            if other.value != 0 and number not in (other.value - 1, other.value + 1):
                return False

        else:
            if number in (5, 7, 9):
                return False

            combinations = {
                1: (2,),
                2: (1, 4),
                3: (6,),
                4: (2, 8),
                5: (),
                6: (3,),
                7: (),
                8: (4,),
                9: ()
            }

            if other.value != 0 and number not in combinations[other.value]:
                return False

        return True

    def draw(self, painter: QPainter, cell_size: int):

        painter.setBrush(QBrush(QColor(255, 255, 255) if self.consecutive else QColor(0, 0, 0)))
        painter.setPen(QPen(QColor(0, 0, 0), 2.0))
        c1 = self.cells[0]
        c2 = self.cells[1]
        rect = c1.scaled_rect(cell_size, 0.25)

        if c1.row - c2.row == -1:  # C1 above C2
            rect.setY(rect.y() + cell_size // 2)

        elif c1.row - c2.row == 1:
            rect.setY(rect.y() - cell_size // 2)

        elif c1.column - c2.column == -1:
            rect.setX(rect.x() + cell_size // 2)
        else:
            rect.setX(rect.x() - cell_size // 2)

        rect.setWidth(int(cell_size * 0.25))
        rect.setHeight(int(cell_size * 0.25))
        painter.drawEllipse(rect)


class XVSum(BorderConstraint):
    def __init__(self, sudoku: "Sudoku", indices: List[int], total: int = 5):
        super().__init__(sudoku, indices)

        self.total = total

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "total": self.total
        }

    def deep_compare(self, other) -> bool:
        if isinstance(other, XVSum):
            return self.total == other.total
        return False

    def valid(self, index: int, number: int):

        if number >= self.total:
            return False

        if self.other_cell(index).value != 0 and self.other_cell(
            index).value + number != self.total:
            return False

        if self.other_cell(index).value == 0 and self.other_cell(index).valid_numbers:
            if self.total - number not in self.other_cell(index).valid_numbers:
                return False

        return True

    def draw(self, painter: QPainter, cell_size: int):

        c1 = self.cells[0]
        c2 = self.cells[1]
        rect = c1.scaled_rect(cell_size, 0.4)

        if c1.row - c2.row == -1:  # C1 above C2
            rect.setY(rect.y() + cell_size // 2)
            painter.setPen(QPen(QColor(255, 255, 255), 2.0 if c2.row % 3 != 0 else 5.0))

            painter.drawLine(
                cell_size + cell_size * c2.column + cell_size // 4,
                cell_size + cell_size * c2.row,
                cell_size + cell_size * (c2.column + 1) - cell_size // 4,
                cell_size + cell_size * c2.row
            )

        elif c1.row - c2.row == 1:
            rect.setY(rect.y() - cell_size // 2)

            painter.setPen(QPen(QColor(255, 255, 255), 2.0 if c1.row % 3 != 0 else 5.0))

            painter.drawLine(
                cell_size + cell_size * c1.column + cell_size // 4,
                cell_size + cell_size * c1.row,
                cell_size + cell_size * (c2.column + 1) - cell_size // 4,
                cell_size + cell_size * c1.row
            )

        elif c1.column - c2.column == -1:

            rect.setX(rect.x() + cell_size // 2)
            painter.setPen(QPen(QColor(255, 255, 255), 2.0 if c2.column % 3 != 0 else 5.0))

            painter.drawLine(
                cell_size + cell_size * c2.column,
                cell_size + cell_size * min(c2.row, 8) + cell_size // 4,
                cell_size + cell_size * c2.column,
                cell_size + cell_size * (min(c2.row, 8) + 1) - cell_size // 4,
            )

        else:
            rect.setX(rect.x() - cell_size // 2)
            painter.setPen(QPen(QColor(255, 255, 255), 2.0 if c1.column % 3 != 0 else 5.0))

            painter.drawLine(
                cell_size + cell_size * c1.column,
                cell_size + cell_size * min(c2.row, 8) + cell_size // 4,
                cell_size + cell_size * c1.column,
                cell_size + cell_size * (min(c2.row, 8) + 1) - cell_size // 4,
            )

        rect.setWidth(int(cell_size * 0.4))
        rect.setHeight(int(cell_size * 0.4))
        painter.setFont(QFont("Verdana", 14))

        painter.setPen(QPen(QColor(0, 0, 0), 1.0))

        text = "V" if self.total == 5 else "X" if self.total == 10 else "XV"

        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignHCenter, text)


class LessGreater(BorderConstraint):
    def __init__(self, sudoku: "Sudoku", indices: List[int], less: bool):
        super().__init__(sudoku, indices)

        self.less = less

        self.indices.sort(reverse=not less)

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "less": self.less
        }

    def deep_compare(self, other) -> bool:
        if isinstance(other, LessGreater):
            return self.less == other.less
        return False

    def valid(self, index: int, number: int):

        if self.other_cell(index).value == 0:
            return True

        if self.pos(index) == 0 and self.other_cell(index).value < number:
            return False

        if self.pos(index) == 1 and self.other_cell(index).value > number:
            return False

        return True

    def create(self, indices: List[int]):
        super(LessGreater, self).create(indices)
        self.indices.sort(reverse=not self.less)

    def draw(self, painter: QPainter, cell_size: int):
        c1 = self.cells[0]
        c2 = self.cells[1]

        pen = QPen(QColor(100, 100, 100), 4.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        # TOP LESS THAN BOTTOM
        if c1.row - c2.row == -1:

            painter.drawLine(
                cell_size + cell_size * c2.column + cell_size // 2,
                cell_size + cell_size * c2.row - cell_size // 6,
                cell_size + cell_size * c2.column + cell_size // 2 - cell_size // 4,
                cell_size + cell_size * c2.row + cell_size // 6,
            )

            painter.drawLine(
                cell_size + cell_size * c2.column + cell_size // 2,
                cell_size + cell_size * c2.row - cell_size // 6,
                cell_size + cell_size * c2.column + cell_size // 2 + cell_size // 4,
                cell_size + cell_size * c2.row + cell_size // 6,
            )

        # BOTTOM LESS THAN TOP
        elif c1.row - c2.row == 1:

            painter.drawLine(
                cell_size + cell_size * c2.column + cell_size // 2,
                cell_size + cell_size * c1.row + cell_size // 6,
                cell_size + cell_size * c2.column + cell_size // 2 - cell_size // 4,
                cell_size + cell_size * c1.row - cell_size // 6,
            )

            painter.drawLine(
                cell_size + cell_size * c2.column + cell_size // 2,
                cell_size + cell_size * c1.row + cell_size // 6,
                cell_size + cell_size * c2.column + cell_size // 2 + cell_size // 4,
                cell_size + cell_size * c1.row - cell_size // 6,
            )

        # LEFT SMALLER THAN RIGHT
        elif c1.column - c2.column == -1:

            painter.drawLine(
                cell_size + cell_size * c2.column - cell_size // 6,
                cell_size + cell_size * c2.row + cell_size // 2,
                cell_size + cell_size * c2.column + cell_size // 6,
                cell_size + cell_size * c2.row + cell_size // 2 - cell_size // 4,
            )

            painter.drawLine(
                cell_size + cell_size * c2.column - cell_size // 6,
                cell_size + cell_size * c2.row + cell_size // 2,
                cell_size + cell_size * c2.column + cell_size // 6,
                cell_size + cell_size * c2.row + cell_size // 2 + cell_size // 4,
            )

        # LEFT BIGGER THAN RIGHT
        else:

            painter.drawLine(
                cell_size + cell_size * c1.column - cell_size // 6,
                cell_size + cell_size * c1.row + cell_size // 4,
                cell_size + cell_size * c1.column + cell_size // 6,
                cell_size + cell_size * c1.row + cell_size // 2,
            )

            painter.drawLine(
                cell_size + cell_size * c1.column + cell_size // 6,
                cell_size + cell_size * c1.row + cell_size // 2,
                cell_size + cell_size * c1.column - cell_size // 6,
                cell_size + cell_size * c1.row + cell_size // 2 + cell_size // 5,
            )


class Quadruple(BorderConstraint):
    def __init__(self, sudoku: "Sudoku", indices: List[int], numbers: List[int]):
        super().__init__(sudoku, indices)

        self.numbers = numbers
        self.selected = False

    def deep_compare(self, other):
        if isinstance(other, Quadruple):
            return sorted(self.numbers) == sorted(other.numbers)

        return False

    def empties(self):
        return [cell for cell in self.cells if cell.value == 0]

    def valid(self, index: int, number: int):
        if len(self.numbers) == 4 and number not in self.numbers:
            return False

        if len(self.empties()) <= len(self.numbers):
            if number not in self.numbers or any([cell.value == number for cell in self.cells]):
                # Putting in that number would create a conflict
                # because the forced numbers would not have enough space left
                return False

        return True

    def draw(self, painter: QPainter, cell_size: int):

        border_intersection = self.get_intersection()
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0) if not self.selected else QColor("#eb902f"), 2.0))

        size = cell_size // 3

        painter.drawEllipse(
            QPoint(
                cell_size + border_intersection[0] * cell_size,
                cell_size + border_intersection[1] * cell_size
            ),
            size, size
        )

        painter.setPen(QPen(QColor(0, 0, 0), 2.0))
        painter.setFont(QFont("Verdana", 10, QFont.Bold))
        painter.drawText(
            QRect(
                cell_size + border_intersection[0] * cell_size - cell_size // 3,
                cell_size + border_intersection[1] * cell_size - cell_size // 3,
                cell_size // 3 * 2, cell_size // 3 * 2
            ),
            Qt.AlignHCenter | Qt.AlignVCenter,
            self.get_text()

        )

    def get_text(self):
        s = ""
        for i, number in enumerate(self.numbers):
            s += str(number)
            if i not in (0, len(self.numbers) - 1) and i % 2 == 1:
                s += "\n"
        return s

    def get_intersection(self):
        return max([c.column for c in self.cells]), max([c.row for c in self.cells])

    def create(self, indices: List[int]):
        super(Quadruple, self).create(indices)
