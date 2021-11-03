from typing import List, Tuple, Set

from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPolygon

from sudoku import tile_to_poly, Cell


class Cage:
    def __init__(self, cells: List[int], total: int):
        self.cells = cells
        self.total = total

        self.inner_offset = 5
        self.no_repeat = True

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
                print("USING", number, f"WOULD ONLY REACH {sum_so_far + number} NOT THE TOTAL ({self.total}) OF THIS CAGE")
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

        painter.drawText(QRect(8 + cell_size + edges[0].sx, 5 + cell_size + edges[0].sy, 20, 20),
                         str(self.total))


class Arrow:
    def __init__(self, origin: Tuple[int, int], path: List[Tuple[int, int]], total: int):
        self.origin = origin
        self.path = path

        self.total = total

    def valid(self, board: List[List[str]]) -> bool:
        s = 0
        for cell in self.path:
            row, col = cell
            s += board[row][col]

        return s <= self.total


class Thermometer:
    def __init__(self, sudoku: "Sudoku", path: List[int]):
        self.sudoku = sudoku
        self.bulb_position = path[0]
        self.path = path

    def __repr__(self):
        return ' -> '.join(map(str, self.path))

    def cells(self, board: List[Cell]):
        return [board[index] for index in self.path]

    def ascending(self, board: List[Cell], number: int, pos: int):
        for cell in [c for c in self.cells(board)[pos + 1:] if c.value != 0]:
            if number > cell.value:
                return False, cell
        return True, None

    def empties(self, board: List[Cell], start: int):
        cells = []
        for i in range(start + 1, len(self.path)):

            if self.cells(board)[i].value == 0:
                cells.append(self.cells(board)[i])
            else:
                cells.append(self.cells(board)[i])
                break

        return cells

    def enough_space(self, board: List[Cell], index: int, number: int):

        seq = self.empties(board, index)
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

        if number == 9 and index != len(self.path) - 1:
            if show_constraint:
                print(number, "CAN ONLY GO ON THE LAST POSITION IN A THERMOMETER")
            return False

        space_after = len(self.path[index + 1:])
        space_before = len(self.path[:index])

        if number > 9 - space_after:
            if show_constraint:
                print(number, "TOO MUCH SPACE AFTER")

            return False

        if number <= space_before:
            if show_constraint:
                print(number, "NOT ENOUGH SPACE BEFORE")
            return False

        return True

    def valid(self, board: List[Cell], pos: int, number: int, show_constraint: bool = False) -> bool:
        index = self.path.index(pos)

        if number in self.cells(board):
            if show_constraint:
                print(number, "TWICE ON THERMOMETER")
            return False

        for cell in self.cells(board)[0:index]:
            if cell.value >= number:
                return False

        ascending, cell = self.ascending(board, number, index)

        if not ascending:
            if show_constraint:
                print(number, "BIGGER THAN", cell.value, "AT", cell.index, "ON THERMOMETER")
            return False

        if not self.possible_index(number, index, show_constraint):
            return False

        space, seq = self.enough_space(board, index, number)
        seq[0] = number

        if not space:
            if show_constraint:
                print(number, "NOT ENOUGH NUMBERS AVAILABLE TO FILL SPACE", seq)
            return False

        return True

    def draw(self, painter: QPainter, board: List[Cell], cell_size: int):

        brush = QBrush(QColor("#BBBBBB"))
        painter.setBrush(brush)

        pen = QPen(QColor("#BBBBBB"), 8.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        bulb = self.cells(board)[0]
        row, col = bulb.row, bulb.column

        painter.drawEllipse(
            cell_size // 4 + cell_size + col * cell_size - 5,
            cell_size // 4 + cell_size + row * cell_size - 5,
            cell_size // 2 + 10, cell_size // 2 + 10
        )

        pen = QPen(QColor("#BBBBBB"), 20.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        for i in range(len(self.cells(board)) - 1):
            c1 = self.cells(board)[i]
            c2 = self.cells(board)[i + 1]

            painter.drawLine(
                cell_size // 2 + cell_size + c1.column * cell_size,
                cell_size // 2 + cell_size + c1.row * cell_size,
                cell_size // 2 + cell_size + c2.column * cell_size,
                cell_size // 2 + cell_size + c2.row * cell_size,
            )
