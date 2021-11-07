import math
from typing import List, Tuple

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from components.border_constraints import Constraint
from sudoku import Sudoku, Cell
from utils import smallest_sum_including_x


class LineConstraint(Constraint):
    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)

        self.color = QColor("#BBBBBB")

    def __len__(self):
        return len(self.indices)

    def position_on_line(self, cell_index: int) -> int:
        return self.indices.index(cell_index)

    def center(self) -> Tuple:
        if (length := len(self.indices)) % 2 == 0:
            return self.indices[length // 2 - 1:length // 2 + 1]

        return self.sudoku.board[self.indices[length // 2]],

    def check_valid(self):
        return True

    def next_cell(self, cell_index: int) -> Cell:
        if cell_index != self.indices[-1]:
            n = self.indices[self.position_on_line(cell_index) + 1]
            return self.sudoku.board[n]

    def previous_cell(self, cell_index: int) -> Cell:
        if cell_index != self.indices[0]:
            p = self.indices[self.position_on_line(cell_index) - 1]
            return self.sudoku.board[p]

    def on_end(self, cell_index: int):
        return cell_index in (self.indices[0], self.indices[-1])

    def distance(self, i1: int, i2: int):
        return math.fabs(self.position_on_line(i1) - self.position_on_line(i2))

    def draw(self, painter: QPainter, cell_size: int):

        pen = QPen(self.color, 10.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setBrush(QBrush(self.color))

        painter.setPen(pen)

        if len(self.indices) == 1:
            painter.drawEllipse(
                self.cells[0].scaled_rect(cell_size, 0.1)
            )

        for cell in self.cells:
            if cell == self.cells[-1]:
                break

            nxt_cell = self.next_cell(cell.index)

            x1 = cell.column * cell_size + cell_size + cell_size // 2
            x2 = nxt_cell.column * cell_size + cell_size + cell_size // 2

            y1 = cell.row * cell_size + cell_size + cell_size // 2
            y2 = nxt_cell.row * cell_size + cell_size + cell_size // 2

            painter.drawLine(x1, y1, x2, y2)

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices
        }


class GermanWhispersLine(LineConstraint):
    """
    A constraint that forces digits on the line to have a difference of at least 5
    to the cell before and after
    """

    NAME = "German Whispers Line"
    HIGHS = {6, 7, 8, 9}
    LOWS = {1, 2, 3, 4}

    def __init__(self, sudoku: Sudoku, indices: List[int]):
        super().__init__(sudoku, indices)

        self.color = QColor("#10b558")

    def __eq__(self, other):
        if not isinstance(other, GermanWhispersLine):
            return False
        return self.indices == other.indices

    def valid(self, index: int, number: int):
        if number == 5:
            return False

        prev = self.previous_cell(index)
        nxt = self.next_cell(index)

        hit = None
        for cell in self.cells:
            if cell.value != 0:
                hit = cell

        if hit:
            if hit.value in self.LOWS and hit.index != index:
                if int(self.distance(hit.index, index)) % 2 == 0 and number not in self.LOWS:
                    return False

                if int(self.distance(hit.index, index)) % 2 != 0 and number not in self.HIGHS:
                    return False

            if hit.value in self.HIGHS and hit.index != index:
                if int(self.distance(hit.index, index)) % 2 == 0 and number not in self.HIGHS:
                    return False

                if int(self.distance(hit.index, index)) % 2 != 0 and number not in self.LOWS:
                    return False

        if prev and prev.value != 0 and math.fabs(prev.value - number) < 5:
            return False

        if nxt and nxt.value != 0 and math.fabs(nxt.value - number) < 5:
            return False

        return True


class PalindromeLine(LineConstraint):
    NAME = "Palindrome Line"

    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)
        for index in self.indices:
            self.opposite(index)

    def opposite(self, cell_index: int):
        pos = self.position_on_line(cell_index)
        sop = len(self) - pos - 1

        return sop

    def valid(self, index: int, number: int):

        opp = self.opposite(index)

        if self.cells[opp].value != 0 and number != self.cells[opp].value:
            return False

        return True


class Thermometer(LineConstraint):
    NAME = "Thermometer"

    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)

        if self.indices:
            self.bulb = self.sudoku.board[self.indices[0]]
        else:
            self.bulb = None

    def __repr__(self):
        return ' -> '.join(map(str, self.indices))

    def ascending(self, number: int, pos: int):
        for cell in [c for c in self.cells[pos + 1:] if c.value != 0]:
            if number > cell.value:
                return False, cell
        return True, None

    def empties(self, start: int):
        cells = []
        for i in range(start + 1, len(self.indices)):

            if self.cells[i].value == 0:
                cells.append(self.cells[i])
            else:
                cells.append(self.cells[i])
                break

        return cells

    def enough_space(self, index: int, number: int):

        seq = self.empties(index)
        if not seq:
            return True, [1]
        if all(x.value == 0 for x in seq):
            return True, seq

        return number + len(seq) - 1 < seq[-1].value, seq

    def possible_index(self, number: int, index: int, show_constraint: bool = False):
        if number == 1 and index != 0:
            if show_constraint:
                print(number, "CAN ONLY GO ON THE FIRST POSITION IN A THERMOMETER")

            return False

        if number == 9 and index != len(self.indices) - 1:
            if show_constraint:
                print(number, "CAN ONLY GO ON THE LAST POSITION IN A THERMOMETER")
            return False

        space_after = len(self.indices[index + 1:])
        space_before = len(self.indices[:index])

        if number > 9 - space_after:
            if show_constraint:
                print(number, "TOO MUCH SPACE AFTER")

            return False

        if number <= space_before:
            if show_constraint:
                print(number, "NOT ENOUGH SPACE BEFORE")
            return False

        return True

    def valid(self, index: int, number: int) -> bool:

        line_pos = self.position_on_line(index)

        for i in self.indices[line_pos + 1:]:
            cell = self.sudoku.board[i]
            if cell.value != 0 and cell.value <= number:
                return False

        for i in self.indices[:line_pos]:
            cell = self.sudoku.board[i]
            if cell.value != 0 and cell.value >= number:
                return False

        if number < line_pos + 1:
            return False

        if len(self.indices) - line_pos > 10 - number:
            return False

        nxt = self.next_cell(index)
        if nxt and nxt.valid_numbers:
            if all(number >= vn for vn in nxt.valid_numbers):
                return False

        prev = None
        for i in range(line_pos):
            if self.cells[i].value != 0:
                prev = self.cells[i]

        if prev:
            dst = line_pos - self.cells.index(prev)
            if dst > 1:
                if number - prev.value < dst:
                    return False

        return True

    def check_valid(self):
        if len(self.indices) <= 1 or len(self.indices) > 9:
            return False
        return True

    def draw(self, painter: QPainter, cell_size: int):

        brush = QBrush(QColor("#BBBBBB"))
        painter.setBrush(brush)

        pen = QPen(QColor("#BBBBBB"), 8.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if not self.bulb:
            return
        row, col = self.bulb.row, self.bulb.column

        painter.drawEllipse(
            cell_size // 4 + cell_size + col * cell_size - 5,
            cell_size // 4 + cell_size + row * cell_size - 5,
            cell_size // 2 + 10, cell_size // 2 + 10
        )

        pen = QPen(QColor("#BBBBBB"), 20.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        for i in range(len(self.cells) - 1):
            c1 = self.cells[i]
            c2 = self.cells[i + 1]

            painter.drawLine(
                cell_size // 2 + cell_size + c1.column * cell_size,
                cell_size // 2 + cell_size + c1.row * cell_size,
                cell_size // 2 + cell_size + c2.column * cell_size,
                cell_size // 2 + cell_size + c2.row * cell_size,
            )


class Arrow(LineConstraint):
    NAME = "Arrow"

    def __init__(self, sudoku: "Sudoku", indices: List[int], one_cell_sum: bool = True):
        super().__init__(sudoku, indices)

        if one_cell_sum:
            self.start = self.indices[0]
            self.start_size = 1
        else:
            self.start = self.indices[0:2]
            self.start_size = 2

        self.arrow = self.indices[self.start_size:]

    def sum_so_far(self):
        return sum([c.value for c in self.cells[self.start_size:] if c.value != 0])

    def arrow_cells(self):
        return self.cells[self.start_size:]

    def sum_cells(self):
        return self.cells[0:self.start_size + 1]

    def valid(self, index: int, number: int):

        if len(self.arrow_cells()) > 1 and number == 1:
            return False

        if self.start_size == 1:

            if index == self.start:

                if all([c.value != 0 for c in self.arrow_cells()]):
                    if number != self.sum_so_far():
                        return False

            if index in self.arrow:

                total = self.sudoku.board[self.start].value
                maximum_sum = 9

                if total != 0:
                    if self.sum_so_far() + number > total:
                        return False

                    space_left = len([c for c in self.arrow_cells() if c.value == 0])
                    if space_left == 1 and number + self.sum_so_far() != total:
                        return False

                if smallest_sum_including_x(number, len(self.cells) - 2) > maximum_sum:
                    return False

        return True

    @staticmethod
    def dot_product(v1: QPoint, v2: QPoint = QPoint(0, 1)):
        return v1.x() * v2.x() + v1.y() * v2.y()

    def length(self, vec: QPoint):
        return math.sqrt(self.dot_product(vec, vec))

    def angle(self, vec1: Tuple[int, int], vec2: Tuple[int, int] = (0, 1)):
        return math.acos(self.dot_product(vec1, vec2) / (self.length(vec1) * self.length(vec2)))

    def draw(self, painter: QPainter, cell_size: int):

        pen = QPen(QColor("#BBBBBB"), 5.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if self.arrow_cells():
            for i in range(len(self.cells) - 1):
                c1 = self.cells[i]
                c2 = self.cells[i + 1]

                painter.drawLine(
                    cell_size // 2 + cell_size + c1.column * cell_size,
                    cell_size // 2 + cell_size + c1.row * cell_size,
                    cell_size // 2 + cell_size + c2.column * cell_size,
                    cell_size // 2 + cell_size + c2.row * cell_size
                )

            # Arrow tips

            center = QPoint(cell_size // 2 + cell_size + c2.column * cell_size,
                            cell_size // 2 + cell_size + c2.row * cell_size)

            p1 = QPoint(
                cell_size // 2 + cell_size + self.cells[-2].column * cell_size,
                cell_size // 2 + cell_size + self.cells[-2].row * cell_size,
            )

            p2 = QPoint(
                cell_size // 2 + cell_size + self.cells[-1].column * cell_size,
                cell_size // 2 + cell_size + self.cells[-1].row * cell_size,
            )

            vector = p2 - p1

            length = self.length(vector)
            width = cell_size // 2

            arrow_head = width / (2 * (math.tan(45) / 2) * length)
            arrow_head_start = p2 + (-arrow_head * vector)

            normal = QPoint(-vector.y(), vector.x())
            t_normal = width / (2 * length)
            left = arrow_head_start + t_normal * normal
            right = arrow_head_start - t_normal * normal

            painter.drawLine(center, left)
            painter.drawLine(center, right)

        painter.setBrush(QBrush(QColor(255, 255, 255)))

        pen = QPen(QColor("#BBBBBB"), 6.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if self.start_size == 1:

            painter.drawEllipse(
                self.sudoku.board[self.start].scaled_rect(cell_size, 0.8)
            )
        else:

            if self.start[0] % 9 == self.start[1] % 9:

                rect = self.sudoku.board[self.start[0]].scaled_rect(cell_size, 0.8)
                rect.setHeight(cell_size * 2 * 0.9)

            else:

                rect = self.sudoku.board[self.start[0]].scaled_rect(cell_size, 0.8)
                rect.setWidth(cell_size * 2 * 0.9)

            painter.drawRoundedRect(
                rect, 10, 10
            )
