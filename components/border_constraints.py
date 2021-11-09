from __future__ import annotations

from abc import ABC
from typing import List

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont, Qt

from sudoku import Sudoku, Cell
from utils import SmartList


class Component(ABC):
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


class BorderComponent(Component):
    def __init__(self, sudoku: Sudoku, indices: List[int]):
        super().__init__(sudoku, indices)

    def __eq__(self, other):
        if isinstance(other, BorderComponent):
            return sorted(self.indices) == sorted(other.indices)
        return NotImplemented

    def __lt__(self, other):
        return min(self.indices) < min(other.indices)

    def other_cell(self, index: int):
        return self.cells[0] if self.cells[0].index != index else self.cells[1]

    def pos(self, index: int) -> int:
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

    @property
    def first(self):
        return self.cells[0]

    @property
    def second(self):
        return self.cells[1]

    def clear(self):
        self.indices = []


class Difference(BorderComponent):
    NAME = "Difference"

    def __init__(self, sudoku: "Sudoku", indices: List[int], difference: int = 1):
        super().__init__(sudoku, indices)

        self.difference = difference

        if difference not in range(1, 9):
            raise ValueError("Ratio must be between 2 and 9")

    def __repr__(self):
        return f"Difference of {self.difference} between {self.first} and {self.second}"

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "difference": self.difference
        }

    def set_value(self, number: int):
        if 1 <= number <= 8:
            self.difference = number

    def valid(self, index: int, number: int):
        if self.first.value != 0:
            return self.first.value - self.difference == number or self.first.value + self.difference == number

        if self.second.value != 0:
            return self.second.value - self.difference == number or self.second.value + self.difference == number

        return True

    def draw(self, painter: QPainter, cell_size: int):
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))

        c1 = self.first
        c2 = self.second

        if c1.column == c2.column:  # Vertical
            center = QPoint(
                cell_size + c2.column * cell_size + cell_size // 2,
                cell_size + c2.row * cell_size
            )

        else:  # Horizontal
            center = QPoint(
                cell_size + max(c1.column, c2.column) * cell_size,
                cell_size + c1.row * cell_size + cell_size // 2
            )

        size = cell_size // 6
        painter.drawEllipse(center, size, size)

        if self.difference != 1:
            painter.setFont(QFont("Varela Round", 10, QFont.Bold))
            painter.drawText(
                QRect(center.x() - size // 2, center.y() - size // 2, size, size),
                Qt.AlignHCenter | Qt.AlignVCenter,
                str(self.difference)
            )


class Ratio(BorderComponent):
    # Valid numbers for all ratios
    VALID = {
        2: (1, 2, 3, 4, 6, 8),
        3: (1, 2, 3, 6, 9),
        4: (1, 2, 4, 8),
        5: (1, 5),
        6: (1, 6),
        7: (1, 7),
        8: (1, 8),
        9: (1, 9)
    }

    NAME = "Ratio"

    def __init__(self, sudoku: "Sudoku", indices: List[int], ratio: int = 2):
        super().__init__(sudoku, indices)

        self.ratio = ratio
        if ratio not in range(2, 10):
            raise ValueError("Ratio must be between 2 and 9")

    def set_value(self, number: int):
        if 2 <= number <= 9:
            self.ratio = number

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "ratio": self.ratio
        }

    def __repr__(self):
        return f"Ratio of {self.ratio} : {1} between {self.first} and {self.second}"

    def valid(self, index: int, number: int):
        if self.first.value != 0:
            return self.first.value / self.ratio == number or self.first.value * self.ratio == number

        if self.second.value != 0:
            return self.second.value / self.ratio == number or self.second.value * self.ratio == number

        if number not in self.VALID[self.ratio]:
            return False

        return True

    def draw(self, painter: QPainter, cell_size: int):
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.setPen(QPen(QColor(0, 0, 0), 2.0))

        c1 = self.first
        c2 = self.second

        if c1.column == c2.column:  # Vertical
            center = QPoint(
                cell_size + c2.column * cell_size + cell_size // 2,
                cell_size + c2.row * cell_size
            )

        else:  # Horizontal
            center = QPoint(
                cell_size + c2.column * cell_size,
                cell_size + c1.row * cell_size + cell_size // 2
            )

        size = cell_size // 6
        painter.drawEllipse(center, size, size)

        painter.setPen(QPen(QColor(255, 255, 255)))
        if self.ratio != 2:
            painter.setFont(QFont("Varela Round", 10, QFont.Bold))
            painter.drawText(
                QRect(center.x() - size // 2, center.y() - size // 2, size, size),
                Qt.AlignHCenter | Qt.AlignVCenter,
                str(self.ratio)
            )


class XVSum(BorderComponent):
    NAME = "XV Sum"

    def __init__(self, sudoku: "Sudoku", indices: List[int], total: int = 5):
        super().__init__(sudoku, indices)

        self.total = total

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "total": self.total
        }

    def set_value(self, v_pressed: bool, x_pressed: bool):
        if v_pressed and x_pressed:
            self.total = 15
        elif v_pressed:
            self.total = 5
        elif x_pressed:
            self.total = 10

    def deep_compare(self, other) -> bool:
        if isinstance(other, XVSum):
            return self.total == other.total
        return False

    def valid(self, index: int, number: int) -> bool:

        if number >= self.total:
            return False

        if self.other_cell(index).value != 0 and self.other_cell(
            index).value + number != self.total:
            return False

        if self.other_cell(index).value == 0 and self.other_cell(index).valid_numbers:
            if self.total - number not in self.other_cell(index).valid_numbers:
                return False

        if number == 5:
            return False

        if self.total == 15 and number < 6:
            return False

        return True

    def draw(self, painter: QPainter, cell_size: int):

        c1 = self.cells[0]
        c2 = self.cells[1]
        rect_size = cell_size // 3
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))

        if c1.row == c2.row:
            painter.drawEllipse(
                QPoint(
                    cell_size + cell_size * max(c1.column, c2.column),
                    cell_size + cell_size * c2.row + cell_size // 2
                ),
                cell_size // 4, cell_size // 4
            )

            rect = QRect(
                cell_size + cell_size * max(c1.column, c2.column) - rect_size // 2,
                cell_size + cell_size * c2.row + cell_size // 2 - rect_size // 2,
                rect_size,
                rect_size
            )

        else:

            painter.drawEllipse(
                QPoint(
                    cell_size + cell_size * c2.column + cell_size // 2,
                    cell_size + cell_size * max(c1.row, c2.row)
                ),
                cell_size // 4, cell_size // 4
            )

            rect = QRect(
                cell_size + cell_size * c2.column + cell_size // 2 - rect_size // 2,
                cell_size + cell_size * max(c1.row, c2.row) - rect_size // 2,
                rect_size,
                rect_size
            )

        painter.setFont(QFont("Verdana", 14 if self.total != 15 else 12, QFont.Bold))

        painter.setPen(QPen(QColor(0, 0, 0), 1.0))

        text = "V" if self.total == 5 else "X" if self.total == 10 else "XV"

        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignHCenter, text)


class LessGreater(BorderComponent):
    NAME = "Less or Greater"

    def __init__(self, sudoku: "Sudoku", indices: List[int], less: bool = True):
        super().__init__(sudoku, indices)

        self.less = less

    def __repr__(self):
        return f"{self.less=}"

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "less": self.less
        }

    def invert(self):
        self.less = not self.less

    def deep_compare(self, other) -> bool:
        if isinstance(other, LessGreater):
            return self.less == other.less
        return False

    def valid(self, index: int, number: int):

        if self.other_cell(index).value == 0:
            return True
        other = self.other_cell(index)
        position = self.pos(index)

        if self.less:

            if position == 0 and number < other.value:
                return True

            if position == 1 and number > other.value:
                return True

        else:

            if position == 0 and number > other.value:
                return True

            if position == 1 and number < other.value:
                return True

        return False

    def draw(self, painter: QPainter, cell_size: int):
        c1 = self.cells[0]
        c2 = self.cells[1]

        pen = QPen(QColor(100, 100, 100), 4.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if c1.column == c2.column:  # ABOVE EACH OTHER
            if self.less:
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
            else:
                painter.drawLine(
                    cell_size + cell_size * c2.column + cell_size // 2,
                    cell_size + cell_size * c2.row + cell_size // 6,
                    cell_size + cell_size * c2.column + cell_size // 2 - cell_size // 4,
                    cell_size + cell_size * c2.row - cell_size // 6,
                )

                painter.drawLine(
                    cell_size + cell_size * c2.column + cell_size // 2,
                    cell_size + cell_size * c2.row + cell_size // 6,
                    cell_size + cell_size * c2.column + cell_size // 2 + cell_size // 4,
                    cell_size + cell_size * c2.row - cell_size // 6,
                )
        else:
            if self.less:
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
            # BOTTOM LESS THAN TOP
            else:
                painter.drawLine(
                    cell_size + cell_size * c2.column - cell_size // 6,
                    cell_size + cell_size * c2.row + cell_size // 4,
                    cell_size + cell_size * c2.column + cell_size // 6,
                    cell_size + cell_size * c2.row + cell_size // 2,
                )

                painter.drawLine(
                    cell_size + cell_size * c2.column + cell_size // 6,
                    cell_size + cell_size * c2.row + cell_size // 2,
                    cell_size + cell_size * c2.column - cell_size // 6,
                    cell_size + cell_size * c2.row + cell_size // 2 + cell_size // 5,
                )


class Quadruple(BorderComponent):
    NAME = "Quadruple"

    def __init__(self, sudoku: "Sudoku", indices: List[int], numbers: SmartList[int]):
        super().__init__(sudoku, indices)

        self.numbers = numbers
        self.selected = False

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "numbers": self.numbers
        }

    def set_value(self, number):
        self.numbers.append(number)

    def clear(self):
        super(Quadruple, self).clear()
        self.numbers = SmartList(max_length=4)

    def deep_compare(self, other) -> bool:
        if isinstance(other, Quadruple):
            return sorted(self.numbers) == sorted(other.numbers)

        return False

    def empties(self) -> List[Cell]:
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
