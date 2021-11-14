from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import List, Dict

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QFont, Qt

from sudoku import Sudoku, Cell
from utils import SmartList


class Component(ABC):

    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        self.sudoku = sudoku
        self.indices = indices

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def setup(self):
        pass

    @property
    def cells(self) -> List[Cell]:
        return [self.sudoku.board[i] for i in self.indices]

    @property
    def first(self) -> Cell:
        return self.cells[0]

    @property
    def last(self) -> Cell:
        return self.cells[-1]

    @property
    def second(self) -> Cell:
        return self.cells[1]

    def valid(self, index: int, number: int) -> bool:
        """

        :param index: Cell index in Sudoku Grid
        :param number: Number to test at that index
        :return: Number can be put at that position
        """
        pass

    def draw(self, painter: QPainter, cell_size: int) -> None:
        pass

    @abstractmethod
    def to_json(self) -> Dict:
        pass


class BorderComponent(Component):
    """A Component in the Grid that lies on a border between 2 or 4 (Quadruple) Cells"""

    def __init__(self, sudoku: Sudoku, indices: List[int]):
        super().__init__(sudoku, indices)

    def __eq__(self, other):
        if isinstance(other, BorderComponent):
            return sorted(self.indices) == sorted(other.indices)
        return NotImplemented

    def __lt__(self, other):
        return min(self.indices) < min(other.indices)

    def to_json(self) -> Dict:
        pass

    def get(self, selected_indices: List[int]) -> BorderComponent:

        for cmp in self.sudoku.border_components:
            if sorted(cmp.indices) == sorted(selected_indices):
                return cmp

    def other_cell(self, index: int) -> Cell:
        """

        :param index: Index of the Cell looked at
        :return: The Cell that is on the other index
        E.g. Index corresponds to Left Cell in a XVSum Component -> Return Right Cell
        """

        return self.cells[0] if self.cells[0].index != index else self.cells[1]

    def pos(self, index: int) -> int:
        return self.indices.index(index)

    def clear(self):
        self.indices = []


class Difference(BorderComponent):
    """ Signals the Difference between the involved Cells"""

    NAME = "Difference"
    RULE = ("Cells separated by a white dot have a difference of the number inside it. "
            "If no number is given the difference is 1.")

    def __init__(self, sudoku: "Sudoku", indices: List[int], difference: int = 1):
        super().__init__(sudoku, indices)

        self.difference = difference

        if difference not in range(1, 9):
            raise ValueError("Ratio must be between 2 and 9")

    def __repr__(self):
        return f"Difference of {self.difference} between {self.first} and {self.second}"

    def to_json(self) -> Dict:
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "difference": self.difference
        }

    def set_value(self, number: int) -> None:
        if 1 <= number <= 8:
            self.difference = number

    def valid(self, index: int, number: int):
        """
        Return True if the difference between the 2 Cells is equal to the difference attribute
        """

        if number - self.difference < 1 and number + self.difference > 9:
            # No Possible match in range 1 to 9
            return False

        if self.other_cell(index).value == 0:
            # No restriction
            return True

        else:
            return math.fabs(number - self.other_cell(index).value) == self.difference

    def draw(self, painter: QPainter, cell_size: int) -> None:
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(50, 50, 50), 2.0))

        if self.first.column == self.second.column:  # Vertical
            center = QPoint(
                cell_size + self.second.column * cell_size + cell_size // 2,
                cell_size + self.second.row * cell_size
            )

        else:  # Horizontal
            center = QPoint(
                cell_size + max(self.first.column, self.second.column) * cell_size,
                cell_size + self.first.row * cell_size + cell_size // 2
            )

        size = cell_size // 7
        painter.drawEllipse(center, size, size)

        if self.difference != 1:
            painter.setFont(QFont("Asap", cell_size // 6, QFont.Bold))
            painter.drawText(
                QRect(center.x() - size // 2, center.y() - size // 2, size, size),
                Qt.AlignHCenter | Qt.AlignVCenter,
                str(self.difference)
            )


class Ratio(BorderComponent):
    """ Signals the Ratio between the involved Cells"""

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
    RULE = ("Cells separated by a black dot have a ratio of the number inside it. "
            "If no number is given the ratio is 2.")

    def __init__(self, sudoku: "Sudoku", indices: List[int], ratio: int = 2):
        super().__init__(sudoku, indices)

        self.ratio = ratio
        if ratio not in range(2, 10):
            raise ValueError("Ratio must be between 2 and 9")

    def set_value(self, number: int):
        if 2 <= number <= 9:
            self.ratio = number

    def to_json(self) -> Dict:
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
            "ratio": self.ratio
        }

    def __repr__(self):
        return f"Ratio of {self.ratio} : {1} between {self.first} and {self.second}"

    def valid(self, index: int, number: int) -> bool:

        if number not in self.VALID[self.ratio]:
            # No Possible match in range 1 to 9
            return False

        if self.other_cell(index).value == 0:
            # No restriction
            return True

        return (number == self.other_cell(index).value / self.ratio
                or number == self.other_cell(index).value * self.ratio)

    def draw(self, painter: QPainter, cell_size: int):
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.setPen(QPen(QColor(0, 0, 0), 2.0))

        if self.first.column == self.second.column:  # Vertical
            center = QPoint(
                cell_size + self.second.column * cell_size + cell_size // 2,
                cell_size + self.second.row * cell_size
            )

        else:  # Horizontal
            center = QPoint(
                cell_size + self.second.column * cell_size,
                cell_size + self.first.row * cell_size + cell_size // 2
            )

        size = cell_size // 7
        painter.drawEllipse(center, size, size)

        painter.setPen(QPen(QColor(255, 255, 255)))
        if self.ratio != 2:
            painter.setFont(QFont("Asap", cell_size // 6, QFont.Bold))
            painter.drawText(
                QRect(center.x() - size // 2, center.y() - size // 2, size, size),
                str(self.ratio),
                Qt.AlignHCenter | Qt.AlignVCenter

            )


class XVSum(BorderComponent):
    """Signals that the Sum of the involved Cells is 5, 10 or 15"""

    NAME = "XV Sum"
    RULE = ("Cells separated by a V sum to 5. "
            "Cells separated by an X sum to 10. "
            "Cells separated by an XV sum to 15.")

    def __init__(self, sudoku: "Sudoku", indices: List[int], total: int = 5):
        super().__init__(sudoku, indices)

        self.total = total

    def to_json(self) -> Dict:
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

    def valid(self, index: int, number: int) -> bool:

        if number == 5:
            # 5 Cannot be in 5, 10 or 15 Two Cell sums
            return False

        if self.total == 15 and number < 6:
            # 15 Can only be made with 6, 7, 8 and 9
            return False

        if number > self.total:
            #  Too big :)
            return False

        other = self.other_cell(index)

        if (val := other.value) != 0:
            return val + number == self.total

        return True

    def draw(self, painter: QPainter, cell_size: int):
        c1 = self.cells[0]
        c2 = self.cells[1]
        rect_size = cell_size // 4
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

        painter.setFont(
            QFont("Asap", cell_size // 4 if self.total != 15 else cell_size // 7, QFont.Bold))
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))

        text = "V" if self.total == 5 else "X" if self.total == 10 else "XV"

        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignHCenter, text)


class LessGreater(BorderComponent):
    NAME = "Less or Greater"

    RULE = "The inequality sign points to the smaller number at the edge."

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

    def valid(self, index: int, number: int):

        other = self.other_cell(index)
        position = self.pos(index)

        if self.other_cell(index).value == 0:
            if self.less and position == 0 and number == 9:
                return False

            if not self.less and position == 0 and number == 1:
                return False

            return True

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

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))

        border_center = QPoint(
            cell_size + cell_size * c2.column + (cell_size // 2 if c1.column == c2.column else 0),
            cell_size + cell_size * c2.row + (cell_size // 2 if c1.row == c2.row else 0)
        )

        painter.drawEllipse(border_center, cell_size // 4, cell_size // 4)
        pen = QPen(QColor(100, 100, 100), 4.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        size = cell_size // 4

        if c1.column == c2.column:  # ABOVE EACH OTHER

            if self.less:  # POINTING UP

                painter.drawLine(
                    border_center.x(),
                    border_center.y() - size // 2,
                    border_center.x() - size // 2,
                    border_center.y() + cell_size // 6,
                )

                painter.drawLine(
                    border_center.x(),
                    border_center.y() - size // 2,
                    border_center.x() + size // 2,
                    border_center.y() + cell_size // 6,
                )
            else:  # POINTING DOWN
                painter.drawLine(
                    border_center.x(),
                    border_center.y() + size // 2,
                    border_center.x() - size // 2,
                    border_center.y() - cell_size // 6,
                )

                painter.drawLine(
                    border_center.x(),
                    border_center.y() + size // 2,
                    border_center.x() + size // 2,
                    border_center.y() - cell_size // 6,
                )
        else:

            if self.less:  # POINTING LEFT
                painter.drawLine(
                    border_center.x() - cell_size // 6,
                    border_center.y(),
                    border_center.x() + size // 2,
                    border_center.y() - size // 2,
                )

                painter.drawLine(
                    border_center.x() - cell_size // 6,
                    border_center.y(),
                    border_center.x() + size // 2,
                    border_center.y() + size // 2,
                )

            else:  # POINTING RIGHT
                painter.drawLine(
                    border_center.x() + cell_size // 6,
                    border_center.y(),
                    border_center.x() - size // 2,
                    border_center.y() - size // 2,
                )

                painter.drawLine(
                    border_center.x() + cell_size // 6,
                    border_center.y(),
                    border_center.x() - size // 2,
                    border_center.y() + size // 2,
                )


class Quadruple(BorderComponent):
    NAME = "Quadruple"

    RULE = "All numbers in the large white circle must appear at least once in the four surrounding cells."

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

    def __repr__(self):
        return f"{self.indices} - {self.numbers}"

    def set_value(self, number):
        self.numbers.append(number)

    def setup(self, selected: List[int]):
        self.indices = selected
        self.numbers = SmartList([], max_length=4, sort_=True)

    def clear(self):
        self.indices = []
        self.numbers = SmartList([], max_length=4, sort_=True)

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
        painter.setPen(QPen(QColor(0, 0, 0) if not self.selected else QColor("#eb902f"), 3.0))

        size = cell_size // 3

        painter.drawEllipse(
            QPoint(
                cell_size + border_intersection[0] * cell_size,
                cell_size + border_intersection[1] * cell_size
            ),
            size, size
        )

        painter.setPen(QPen(QColor(0, 0, 0), 2.0))
        painter.setFont(QFont("Asap", cell_size // 6, QFont.Bold))
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
