import math
from typing import List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from components.base_constraint import Constraint
from sudoku import Sudoku, Cell


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

    def draw(self, painter: QPainter, cell_size: int):

        pen = QPen(self.color, 14.0)
        pen.setCapStyle(Qt.RoundCap)

        painter.setPen(pen)

        """for cell in self.center():
            painter.fillRect(cell.rect(cell_size), QColor(30, 30, 30, 130))"""

        for cell in self.cells:
            if cell == self.cells[-1]:
                break

            nxt_cell = self.next_cell(cell.index)

            x1 = cell.column * cell_size + cell_size + cell_size // 2
            x2 = nxt_cell.column * cell_size + cell_size + cell_size // 2

            y1 = cell.row * cell_size + cell_size + cell_size // 2
            y2 = nxt_cell.row * cell_size + cell_size + cell_size // 2

            painter.drawLine(x1, y1, x2, y2)


class GermanWhispersLine(LineConstraint):
    """
    A constraint that forces digits on the line to have a difference of at least 5
    to the cell before and after
    """

    def __init__(self, sudoku: Sudoku, indices: List[int]):
        super().__init__(sudoku, indices)

        self.color = QColor("#10b558")

    def valid(self, index: int, number: int):
        if number == 5:
            return False

        # if not self.on_end(index) and number in (4, 6):

        prev = self.previous_cell(index)
        nxt = self.next_cell(index)

        if prev and prev.value != 0 and math.fabs(prev.value - number) < 5:
            return False

        if nxt and nxt.value != 0 and math.fabs(nxt.value - number) < 5:
            return False

        return True


class PalindromeLine(LineConstraint):
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
    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)
        self.bulb = self.sudoku.board[self.indices[0]]

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
        NUMBERS = [9, 8, 7, 6, 5, 4, 3, 2, 1]

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

    def draw(self, painter: QPainter, cell_size: int):

        brush = QBrush(QColor("#BBBBBB"))
        painter.setBrush(brush)

        pen = QPen(QColor("#BBBBBB"), 8.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

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
